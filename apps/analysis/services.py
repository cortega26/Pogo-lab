"""Servicios de dominio para apps/analysis.

run_personal_analysis:
  - Filtra a state="valid" ÚNICAMENTE.
  - Separa Lucky vs normal obligatoriamente.
  - Separa por ruleset/periodo.
  - Delega en engine/ para los cálculos estadísticos.
  - Fija algoritmo, semilla y versiones para reproducibilidad.
"""

import hashlib
import json
from collections import Counter
from typing import Any

from django.db import models

from apps.mechanics.models import MechanicRuleSet
from apps.mechanics.services import (
    RulesetUnavailableError,
    floor_for_ruleset,
    resolve_trade_floor,
)
from apps.trades.models import TradeObservation
from engine import ALGORITHM_VERSION
from engine.intervals import wilson_interval
from engine.probability import p_hundo
from engine.stat_tests import exact_binomial_test, min_sample_for, uniformity_test

from .models import AnalysisResult, AnalysisRun


def _valid_observations(
    owner_id: int,
    filters: dict[str, Any] | None = None,
) -> models.QuerySet:
    """Observaciones `state="valid"` del owner, con filtros opcionales."""
    qs = TradeObservation.objects.filter(owner_id=owner_id, state="valid")
    if filters:
        if "friendship_level" in filters:
            qs = qs.filter(friendship_level=filters["friendship_level"])
        if "trade_type" in filters:
            qs = qs.filter(trade_type=filters["trade_type"])
        if "observed_after" in filters:
            qs = qs.filter(observed_at__gte=filters["observed_after"])
        if "observed_before" in filters:
            qs = qs.filter(observed_at__lte=filters["observed_before"])
    return qs


def _build_groups(base_qs: models.QuerySet) -> list[dict[str, Any]]:
    """Agrupa observaciones válidas en poblaciones con el MISMO piso.

    - Lucky: por `ruleset` (el piso Lucky no depende del nivel de amistad).
    - Normal: por `(friendship_level, ruleset)`, porque el piso depende del
      nivel de amistad (good=1/great=2/ultra=3/best=5). Nunca se mezclan pisos
      distintos en un mismo grupo (evita falsas anomalías de uniformidad).
    """
    groups: list[dict[str, Any]] = []

    lucky_qs = base_qs.filter(is_lucky=True)
    for rs_id in lucky_qs.values_list("ruleset_id", flat=True).distinct():
        groups.append(
            {
                "label": f"lucky-rs{rs_id}",
                "is_lucky": True,
                "friendship_level": None,
                "ruleset_id": rs_id,
                "observations": lucky_qs.filter(ruleset_id=rs_id),
            }
        )

    normal_qs = base_qs.filter(is_lucky=False)
    combos = normal_qs.values("friendship_level", "ruleset_id").distinct().order_by()
    for combo in combos:
        fl = combo["friendship_level"]
        rs_id = combo["ruleset_id"]
        groups.append(
            {
                "label": f"normal-{fl}-rs{rs_id}",
                "is_lucky": False,
                "friendship_level": fl,
                "ruleset_id": rs_id,
                "observations": normal_qs.filter(friendship_level=fl, ruleset_id=rs_id),
            }
        )

    return groups


def _group_floor(group: dict[str, Any]) -> int | None:
    """Piso `f` del grupo, LEÍDO del ruleset (nunca hardcodeado).

    Usa el ruleset bajo el que se registraron las observaciones; si el grupo no
    tiene ruleset asociado, cae al vigente. Devuelve None si no hay ningún
    ruleset publicado del que leer el piso (el grupo no se analiza).
    """
    trade_type = "lucky" if group["is_lucky"] else "normal"
    friendship_level = group["friendship_level"] or "good"
    rs_id = group["ruleset_id"]

    if rs_id is not None:
        ruleset = MechanicRuleSet.objects.filter(pk=rs_id).first()
        if ruleset is not None:
            return floor_for_ruleset(ruleset, friendship_level, trade_type)

    try:
        f, _ = resolve_trade_floor(friendship_level, trade_type)
    except RulesetUnavailableError:
        return None
    return f


def _floor_for_version(
    ruleset_version: int,
    friendship_level: str,
    trade_type: str,
) -> int | None:
    """Piso `f` leído del ruleset de ESA versión (no del vigente).

    Para el agregado pooled sobre filas anonimizadas, que solo llevan
    `ruleset_version`. Si la versión no existe (p. ej. 0 = sin ruleset), cae al
    vigente; devuelve None si tampoco hay ninguno publicado.
    """
    ruleset = MechanicRuleSet.objects.filter(
        mechanic__key="trade_iv",
        version=ruleset_version,
        is_published=True,
    ).first()
    if ruleset is not None:
        return floor_for_ruleset(ruleset, friendship_level, trade_type)
    try:
        f, _ = resolve_trade_floor(friendship_level, trade_type)
    except RulesetUnavailableError:
        return None
    return f


def _hundo_payload(n: int, successes: int, f: int) -> dict[str, Any]:
    """Igual que _hundo_rate_analysis pero con n/successes ya calculados."""
    p0 = float(p_hundo(f))
    min_n = min_sample_for("hundo_rate")
    payload: dict[str, Any] = {
        "n": n,
        "successes": successes,
        "p0": p0,
        "floor": f,
        "observed_rate": successes / n if n > 0 else 0.0,
        "min_sample": min_n,
    }
    if n >= min_n:
        result = exact_binomial_test(successes, n, p0)
        lo, hi = wilson_interval(successes, n)
        payload.update(
            {
                "stat": result.stat,
                "p_value": result.p_value,
                "effect_size": result.effect_size,
                "method_used": result.method_used,
                "ci_lo": lo,
                "ci_hi": hi,
            }
        )
    else:
        payload["insufficient_sample"] = True
    return payload


def _stat_uniformity_payloads(
    counts_by_stat: dict[str, list[int]], n: int, f: int, seed: int | None
) -> dict[str, dict[str, Any]]:
    """Igual que _stat_uniformity_analysis pero con counts ya calculados por stat."""
    k = 16 - f
    values = list(range(f, 16))
    probs = [1.0 / k] * k
    min_n = min_sample_for("stat_uniformity")
    results: dict[str, dict[str, Any]] = {}
    for stat_name, counts in counts_by_stat.items():
        payload: dict[str, Any] = {
            "n": n,
            "min_sample": min_n,
            "counts": counts,
            "values": values,
        }
        if n >= min_n:
            result = uniformity_test(counts, probs, seed=seed)
            payload.update(
                {
                    "stat": result.stat,
                    "p_value": result.p_value,
                    "effect_size": result.effect_size,
                    "method_used": result.method_used,
                    "min_expected": result.min_expected,
                }
            )
        else:
            payload["insufficient_sample"] = True
        results[stat_name] = payload
    return results


def _sum_uniformity_payload(
    sum_counts: list[int],
    sum_values: list[int],
    sum_probs: list[float],
    n: int,
    seed: int | None,
) -> dict[str, Any]:
    """Igual que _sum_uniformity_analysis pero con counts/values/probs ya calculados."""
    min_n = min_sample_for("sum_uniformity")
    payload: dict[str, Any] = {
        "n": n,
        "min_sample": min_n,
        "counts": sum_counts,
        "values": sum_values,
    }
    if n >= min_n:
        result = uniformity_test(sum_counts, sum_probs, seed=seed)
        payload.update(
            {
                "stat": result.stat,
                "p_value": result.p_value,
                "effect_size": result.effect_size,
                "method_used": result.method_used,
                "min_expected": result.min_expected,
            }
        )
    else:
        payload["insufficient_sample"] = True
    return payload


def _hundo_rate_analysis(
    observations: models.QuerySet,
    f: int,
) -> dict[str, Any]:
    """Análisis de tasa de hundos con prueba binomial exacta."""
    agg = observations.aggregate(
        n=models.Count("id"),
        successes=models.Count("pk", filter=models.Q(atk=15, iv_def=15, hp=15)),
    )
    return _hundo_payload(agg["n"], agg["successes"], f)


def _stat_uniformity_analysis(
    observations: models.QuerySet,
    f: int,
    seed: int | None,
) -> dict[str, Any]:
    """Análisis de uniformidad por stat (Att, Def, HP)."""
    obs_list = list(observations)
    n = len(obs_list)
    counts_by_stat: dict[str, list[int]] = {}
    for stat_name, field in [("atk", "atk"), ("def", "iv_def"), ("hp", "hp")]:
        counter: Counter = Counter(getattr(o, field) for o in obs_list)
        counts_by_stat[stat_name] = [counter.get(v, 0) for v in range(f, 16)]
    return _stat_uniformity_payloads(counts_by_stat, n, f, seed)


def _sum_uniformity_analysis(
    observations: models.QuerySet,
    f: int,
    seed: int | None,
) -> dict[str, Any]:
    """Análisis de uniformidad de la suma de IV."""
    from engine.probability import iv_sum_distribution

    obs_list = list(observations)
    n = len(obs_list)
    dist = iv_sum_distribution(f)
    counter: Counter = Counter(o.atk + o.iv_def + o.hp for o in obs_list)
    sum_values = sorted(dist.keys())
    sum_counts = [counter.get(v, 0) for v in sum_values]
    sum_probs = [float(dist[v]) for v in sum_values]
    return _sum_uniformity_payload(sum_counts, sum_values, sum_probs, n, seed)


def _detect_mixing(qs: models.QuerySet) -> dict[str, bool]:
    """Detecta si hay mezcla de Lucky/normal o rulesets en el queryset."""
    lucky_count = qs.filter(is_lucky=True).count()
    normal_count = qs.filter(is_lucky=False).count()
    ruleset_count = qs.filter(is_lucky=False).values("ruleset").distinct().count()

    return {
        "has_mixed_lucky_normal": lucky_count > 0 and normal_count > 0,
        "has_mixed_rulesets": ruleset_count > 1,
        "has_mixed_periods": False,  # M6: dataset comunitario
    }


def _input_fingerprint(owner_id: int, filters: dict[str, Any] | None) -> str:
    """Hash determinista de owner + filtros + algoritmo + datos observados.

    Cambia cuando se añaden, editan o eliminan observaciones válidas que
    coinciden con los filtros, garantizando que una ejecución previa se
    reutiliza solo si la entrada es idéntica.
    """
    qs = _valid_observations(owner_id, filters)
    agg = qs.aggregate(c=models.Count("id"), m=models.Max("updated_at"))
    signature = {
        "owner_id": owner_id,
        "filters": filters or {},
        "algorithm_version": ALGORITHM_VERSION,
        "count": agg["c"] or 0,
        "max_updated": agg["m"].isoformat() if agg["m"] else None,
    }
    raw = json.dumps(signature, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()


def _deterministic_seed_from_data(data: Any) -> int:
    """Deriva una semilla determinista del hash SHA256 de los datos.

    Los datos se serializan a JSON con claves ordenadas para garantizar que la
    misma entrada produce siempre el mismo hash, independientemente del orden
    de inserción de los dicts.
    """
    raw = json.dumps(data, sort_keys=True, default=str)
    digest = hashlib.sha256(raw.encode()).digest()
    return int.from_bytes(digest[:8], byteorder="big") % (2**31)


def _deterministic_seed_from_rows(rows: list[dict[str, Any]]) -> int:
    """Deriva una semilla determinista del hash del dataset completo.

    Si la lista está vacía, devuelve 0.
    """
    if not rows:
        return 0
    return _deterministic_seed_from_data(rows)


def run_personal_analysis(
    owner_id: int,
    filters: dict[str, Any] | None = None,
    seed: int | None = None,
    code_sha: str = "",
    input_fingerprint: str | None = None,
) -> AnalysisRun:
    """Ejecuta análisis estadístico personal sobre observaciones válidas.

    Separa obligatoriamente Lucky de normal y por ruleset.
    Reproducible: mismo seed + algorithm_version produce el mismo resultado.

    Args:
        owner_id: ID del usuario propietario.
        filters: Filtros opcionales (friendship_level, trade_type, fechas).
        seed: Semilla para Monte Carlo (None → determinista a partir de owner_id+filters).
        code_sha: SHA del código para trazabilidad.
        input_fingerprint: Hash de la entrada; si no se pasa se calcula.

    Returns:
        AnalysisRun creado.
    """
    if seed is None:
        seed = _deterministic_seed_from_data({"owner_id": owner_id, "filters": filters})
    if input_fingerprint is None:
        input_fingerprint = _input_fingerprint(owner_id, filters)

    run = AnalysisRun.objects.create(
        owner_id=owner_id,
        filters=filters or {},
        algorithm_version=ALGORITHM_VERSION,
        random_seed=seed,
        code_sha=code_sha,
        input_fingerprint=input_fingerprint,
    )

    base_qs = _valid_observations(owner_id, filters)
    grupos = _build_groups(base_qs)

    # Detectar mezcla en TODO el conjunto de observaciones válidas
    mixing = _detect_mixing(base_qs)
    run.mixing_flags = mixing
    run.save(update_fields=["mixing_flags"])

    for grupo in grupos:
        obs_qs: models.QuerySet = grupo["observations"]
        # Piso leído del ruleset del grupo (nunca hardcodeado). Si no hay
        # ruleset del que leerlo, no se analiza el grupo (honestidad).
        f = _group_floor(grupo)
        if f is None:
            continue
        label: str = grupo["label"]

        # 1. Tasa de hundos
        hundo_payload = _hundo_rate_analysis(obs_qs, f)
        AnalysisResult.objects.create(
            run=run,
            metric_key=f"hundo_rate-{label.lower().replace(' ', '_')}",
            payload=hundo_payload,
        )

        total_n = obs_qs.count()

        # 2. Uniformidad por stat
        if total_n > 0:
            stat_results = _stat_uniformity_analysis(obs_qs, f, seed)
            for stat_name, payload in stat_results.items():
                AnalysisResult.objects.create(
                    run=run,
                    metric_key=f"stat_uniformity_{stat_name}-{label.lower().replace(' ', '_')}",
                    payload=payload,
                )

            # 3. Uniformidad de suma
            sum_payload = _sum_uniformity_analysis(obs_qs, f, seed)
            AnalysisResult.objects.create(
                run=run,
                metric_key=f"sum_uniformity-{label.lower().replace(' ', '_')}",
                payload=sum_payload,
            )

    return run


def get_or_run_personal_analysis(
    owner_id: int,
    filters: dict[str, Any] | None = None,
    seed: int | None = None,
    code_sha: str = "",
) -> AnalysisRun:
    """Reutiliza un AnalysisRun si la entrada (owner+filtros+datos) no cambió."""
    fingerprint = _input_fingerprint(owner_id, filters)
    existing = (
        AnalysisRun.objects.filter(owner_id=owner_id, input_fingerprint=fingerprint)
        .order_by("-created_at")
        .first()
    )
    if existing is not None:
        return existing
    return run_personal_analysis(
        owner_id,
        filters=filters,
        seed=seed,
        code_sha=code_sha,
        input_fingerprint=fingerprint,
    )


def compute_pooled_statistics(
    anonymized_rows: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    """Estadísticas pooled (sin owner) usando las mismas pruebas del engine.

    Reutiliza la misma disciplina que run_personal_analysis:
    - Agrupa por (is_lucky, friendship_level, ruleset_version).
    - Resuelve el piso con floor_for_ruleset desde el ruleset de ESA versión
      (nunca hardcodeado, nunca del ruleset activo indiscriminadamente).
    - Llama a los mismos builders que la ruta personal (`_hundo_payload`,
      `_stat_uniformity_payloads`, `_sum_uniformity_payload`) para que ningún
      métrico diverja entre M5 y M6.

    Recibe filas anonimizadas en el formato de build_dataset_version:
        {atk, def, hp, friendship_level, trade_type, is_lucky, ruleset_version, observed_month}
    """
    from engine.probability import iv_sum_distribution

    groups: dict[tuple, list[dict]] = {}
    for row in anonymized_rows:
        key = (row["is_lucky"], row["friendship_level"], row.get("ruleset_version", 0))
        groups.setdefault(key, []).append(row)

    results: list[dict[str, Any]] = []
    dataset_seed = _deterministic_seed_from_rows(anonymized_rows)
    for (is_lucky, friendship_level, ruleset_version), group_rows in groups.items():
        n = len(group_rows)
        trade_type = "lucky" if is_lucky else "normal"

        f = _floor_for_version(ruleset_version, friendship_level, trade_type)
        if f is None:
            continue

        successes = sum(
            1 for r in group_rows if r["atk"] == 15 and r["def"] == 15 and r["hp"] == 15
        )

        counts_by_stat: dict[str, list[int]] = {}
        for stat_name, field in [("atk", "atk"), ("def", "def"), ("hp", "hp")]:
            counter: Counter = Counter(r[field] for r in group_rows)
            counts_by_stat[stat_name] = [counter.get(v, 0) for v in range(f, 16)]

        dist = iv_sum_distribution(f)
        sum_counter: Counter = Counter(r["atk"] + r["def"] + r["hp"] for r in group_rows)
        sum_values = sorted(dist.keys())
        sum_counts = [sum_counter.get(v, 0) for v in sum_values]
        sum_probs = [float(dist[v]) for v in sum_values]

        results.append(
            {
                "is_lucky": is_lucky,
                "friendship_level": friendship_level,
                "ruleset_version": ruleset_version,
                "n": n,
                "floor": f,
                "hundo_analysis": _hundo_payload(n, successes, f),
                "statistics": _stat_uniformity_payloads(counts_by_stat, n, f, dataset_seed),
                "sum_analysis": _sum_uniformity_payload(
                    sum_counts, sum_values, sum_probs, n, dataset_seed
                ),
            }
        )

    return results
