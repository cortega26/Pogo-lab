"""Servicio de dominio de la calculadora.

Obtiene el piso `f` del ruleset vigente (M2) y delega en engine/probability.
"""

import hashlib
import json
from base64 import b64decode, b64encode
from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import Any

from django.conf import settings
from django.core.cache import cache
from django.db import models
from django.utils import timezone

from apps.mechanics.models import Mechanic, MechanicRuleSet
from engine import ALGORITHM_VERSION
from engine.probability import (
    expected_successes,
    p_at_least_one,
    p_zero,
    per_trade_success_prob,
    trades_for_confidence,
)

SHARE_URL_VERSION = "v1"


@dataclass(frozen=True)
class CalcInput:
    """Entrada de la calculadora (plan §H)."""

    friendship_level: str  # "good", "great", "ultra", "best"
    trade_type: str  # "normal", "lucky", "lucky_guaranteed"
    n: int  # numero de intercambios
    target_kind: str  # "hundo", "stat_min", "sum_min"
    threshold: int | None = None  # para stat_min o sum_min
    confidence: float = 0.5
    floor_override: int | None = None  # override manual del piso


@dataclass(frozen=True)
class CalcResult:
    """Resultado del calculo (plan §H)."""

    p_per_trade: float
    p_cumulative: float
    expected_successes: float
    p_zero: float
    trades_for_confidence: int
    floor: int
    k: int
    ruleset_version: int | None
    algorithm_version: str
    assumptions: list[str] = field(default_factory=list)
    params: dict[str, Any] = field(default_factory=dict)


_FLOOR_KEYS: dict[str, str] = {
    "good": "floor.friendship.good",
    "great": "floor.friendship.great",
    "ultra": "floor.friendship.ultra",
    "best": "floor.friendship.best",
}


class RulesetUnavailableError(RuntimeError):
    """No hay ruleset publicado para trade_iv en esta fecha."""


def _validate_floor_override(value: object) -> int:
    """Valida y normaliza `floor_override`: debe ser un entero en [0, 15].

    Lanza ValueError si el tipo es invalido o el valor cae fuera de rango.
    Sin esta validacion un piso >= 16 produce k <= 0 (division por cero o
    probabilidades negativas) en engine/probability.
    """
    try:
        floor = int(value)  # type: ignore[call-overload]
    except (TypeError, ValueError) as exc:
        raise ValueError("floor_override debe ser un entero") from exc
    if not 0 <= floor <= 15:
        raise ValueError("floor_override debe estar en el rango [0, 15]")
    return floor


def _resolve_floor(
    friendship_level: str,
    trade_type: str,
    ruleset_version: int | None = None,
) -> tuple[int, int | None]:
    """Resuelve el piso `f` desde el ruleset publicado de trade_iv.

    Devuelve (f, ruleset_version). Lucky sobrescribe con floor.lucky.
    Lanza RulesetUnavailableError si no hay ruleset publicado.
    """
    try:
        mechanic = Mechanic.objects.get(key="trade_iv", status="active")
    except Mechanic.DoesNotExist as e:
        raise RulesetUnavailableError("Mecanica trade_iv no encontrada.") from e

    now = timezone.now()
    qs = MechanicRuleSet.objects.filter(
        mechanic=mechanic,
        is_published=True,
        effective_from__lte=now,
    )
    if ruleset_version is not None:
        qs = qs.filter(version=ruleset_version)
    qs = qs.filter(
        models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=now),
    ).order_by("-version")

    ruleset = qs.first()
    if ruleset is None:
        raise RulesetUnavailableError(
            "No hay ruleset publicado para trade_iv vigente en esta fecha."
        )

    params = {p.key: p.value for p in ruleset.parameters.all()}
    if trade_type in ("lucky", "lucky_guaranteed"):
        floor = int(params.get("floor.lucky", 12))
    else:
        key = _FLOOR_KEYS.get(friendship_level, "floor.friendship.good")
        floor = int(params.get(key, 1))
    return floor, ruleset.version


def _cache_key(inputs: CalcInput, ruleset_version: int | None) -> str:
    raw = json.dumps(
        {
            "inputs": asdict(inputs),
            "ruleset_version": ruleset_version,
            "algo": ALGORITHM_VERSION,
        },
        sort_keys=True,
        default=str,
    )
    return "calc:" + hashlib.sha256(raw.encode()).hexdigest()


def compute_scenario(inputs: CalcInput) -> CalcResult:
    """Calcula el escenario completo desde CalcInput.

    Obtiene el piso del ruleset, computa P por intercambio y P acumulada,
    y devuelve el resultado con metadatos de trazabilidad.

    Si el usuario provee floor_override, se usa ese piso en lugar del ruleset.
    """
    if inputs.floor_override is not None:
        floor = _validate_floor_override(inputs.floor_override)
        ruleset_version = None
    else:
        floor, ruleset_version = _resolve_floor(inputs.friendship_level, inputs.trade_type)

    target: dict[str, Any] = {"kind": inputs.target_kind}
    if inputs.threshold is not None:
        target["threshold"] = inputs.threshold

    p_single = per_trade_success_prob(floor, target)
    p_cum = p_at_least_one(p_single, inputs.n)

    if inputs.floor_override is not None:
        assumptions = [
            "Los IVs post-intercambio siguen una distribucion uniforme en [f, 15].",
            "Los stats (Att/Def/HP) son independientes entre si (S3).",
            f"Piso f={floor} definido manualmente por el usuario.",
        ]
    else:
        assumptions = [
            "Los IVs post-intercambio siguen una distribucion uniforme en [f, 15].",
            "Los stats (Att/Def/HP) son independientes entre si (S3).",
            "El piso f proviene de datos comunitarios verificados (M2).",
        ]
        if inputs.trade_type in ("lucky", "lucky_guaranteed"):
            assumptions.append("Los intercambios Lucky usan piso 12 segun datos comunitarios.")

    return CalcResult(
        p_per_trade=_round(p_single),
        p_cumulative=_round(p_cum),
        expected_successes=_round(expected_successes(p_single, inputs.n)),
        p_zero=_round(p_zero(p_single, inputs.n)),
        trades_for_confidence=trades_for_confidence(p_single, inputs.confidence),
        floor=floor,
        k=16 - floor,
        ruleset_version=ruleset_version,
        algorithm_version=ALGORITHM_VERSION,
        assumptions=assumptions,
        params={
            "friendship_level": inputs.friendship_level,
            "trade_type": inputs.trade_type,
            "n": inputs.n,
            "target_kind": inputs.target_kind,
            "threshold": inputs.threshold,
            "confidence": inputs.confidence,
        },
    )


def _round(value: float, places: int = 6) -> float:
    return float(Decimal(str(value)).quantize(Decimal(f"0.{'0' * places}"), rounding=ROUND_HALF_UP))


def compute_scenario_cached(inputs: CalcInput) -> CalcResult:
    """Como compute_scenario, pero con cache por hash.

    La clave incluye inputs + ruleset_version + algorithm_version.
    """
    if inputs.floor_override is not None:
        ruleset_version = None
    else:
        _, ruleset_version = _resolve_floor(inputs.friendship_level, inputs.trade_type)
    key = _cache_key(inputs, ruleset_version)
    result = cache.get(key)
    if result is not None:
        return result
    result = compute_scenario(inputs)
    cache.set(key, result, timeout=getattr(settings, "CALC_CACHE_TIMEOUT", 3600))
    return result


def encode_share_url(inputs: CalcInput) -> str:
    """Codifica CalcInput en un fragmento de URL determinista.

    Formato: version + base64url(json).
    """
    payload = {
        "v": SHARE_URL_VERSION,
        "fl": inputs.friendship_level,
        "tt": inputs.trade_type,
        "n": inputs.n,
        "tk": inputs.target_kind,
        "th": inputs.threshold,
        "c": inputs.confidence,
        "fo": inputs.floor_override,
    }
    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    encoded = b64encode(raw.encode()).decode().rstrip("=").replace("+", "-").replace("/", "_")
    return encoded


def decode_share_url(encoded: str) -> CalcInput:
    """Decodifica un fragmento de URL al CalcInput original.

    Lanza ValueError si el formato es invalido.
    """
    try:
        padded = encoded.replace("-", "+").replace("_", "/")
        pad = 4 - len(padded) % 4
        if pad != 4:
            padded += "=" * pad
        raw = b64decode(padded.encode()).decode()
        payload = json.loads(raw)
    except (json.JSONDecodeError, Exception) as exc:
        raise ValueError("URL de calculo invalida") from exc

    if payload.get("v") != SHARE_URL_VERSION:
        raise ValueError("Version de URL no soportada")

    floor_override = payload.get("fo")
    if floor_override is not None:
        floor_override = _validate_floor_override(floor_override)

    return CalcInput(
        friendship_level=payload["fl"],
        trade_type=payload["tt"],
        n=int(payload["n"]),
        target_kind=payload["tk"],
        threshold=payload.get("th"),
        confidence=float(payload.get("c", 0.5)),
        floor_override=floor_override,
    )
