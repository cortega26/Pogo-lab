"""Servicios de dominio para apps/trades.

Registro, validacion, dedup, bulk import, CSV export y dashboard.
"""

import csv
import hashlib
import io
from datetime import datetime
from typing import Any

from django.db import transaction
from django.db.models import Count, Q

from apps.mechanics.services import RulesetUnavailableError, resolve_trade_floor
from engine.observations import ivs_consistent_with_floor

from .models import TradeObservation, TradeSession

FRIENDSHIP_LEVELS = ("good", "great", "ultra", "best")
TRADE_TYPES = ("normal", "lucky", "lucky_guaranteed")

DEDUP_SEPARATOR = "|"


def _compute_dedup_hash(
    owner_id: int,
    observed_at: datetime,
    friendship_level: str,
    trade_type: str,
    atk: int,
    def_: int,
    hp: int,
    species: str,
) -> str:
    """Hash SHA256 determinista para deduplicacion.

    La granularidad es de DIA (no segundo) a proposito: incluir el timestamp
    exacto haria que el dedup nunca dispare, lo cual es necesario para poder
    re-importar el mismo CSV sin duplicar observaciones.
    """
    day = observed_at.date().isoformat()
    canonical = DEDUP_SEPARATOR.join(
        [
            str(owner_id),
            day,
            friendship_level,
            trade_type,
            str(atk),
            str(def_),
            str(hp),
            species,
        ]
    )
    return hashlib.sha256(canonical.encode()).hexdigest()


def _derive_is_lucky(trade_type: str) -> bool:
    """Deriva is_lucky de trade_type.

    Elimina el modo de fallo de consistencia: is_lucky NO se acepta como
    input independiente.
    """
    return trade_type in ("lucky", "lucky_guaranteed")


def _determine_state(
    atk: int,
    def_: int,
    hp: int,
    friendship_level: str,
    trade_type: str,
    _owner_id: int,
    _observed_at: datetime,
    _species: str,
    _dedup_hash: str,
    resolved_floor: int | None = None,
) -> tuple[str, str]:
    """Determina el estado y motivo de una observacion segun la tabla §6.

    Devuelve (state, exclusion_reason).
    Si se provee resolved_floor, se usa directamente en lugar de resolver.
    """
    if not (0 <= atk <= 15 and 0 <= def_ <= 15 and 0 <= hp <= 15):
        return ("excluded", "IV fuera de rango [0,15]")

    if resolved_floor is not None:
        f = resolved_floor
    else:
        try:
            f, _ruleset_version = resolve_trade_floor(friendship_level, trade_type)
        except RulesetUnavailableError:
            f = 0

    if not ivs_consistent_with_floor(f, atk, def_, hp):
        return (
            "suspicious",
            f"Inconsistente con el piso f={f} del ruleset (modelo re-roll [f,15])",
        )

    return ("valid", "")


def register_observation(
    *,
    owner_id: int,
    observed_at: datetime,
    friendship_level: str,
    trade_type: str,
    atk: int,
    def_: int,
    hp: int,
    species: str = "",
    session: TradeSession | None = None,
    lucky_guaranteed: bool | None = None,
    special_trade: bool | None = None,
    oldest_age_bucket: str = "",
    event_context: str = "",
    app_version: str = "",
    input_method: str = "manual",
    contribution_optin: bool = False,
    notes: str = "",
    state: str | None = None,
    exclusion_reason: str = "",
    resolved: dict | None = None,
) -> TradeObservation:
    """Registra una observacion con validacion y dedup.

    Si no se provee state, se determina automaticamente segun la tabla §6.
    """
    if friendship_level not in FRIENDSHIP_LEVELS:
        raise ValueError(f"friendship_level inválido: {friendship_level!r}")
    if trade_type not in TRADE_TYPES:
        raise ValueError(f"trade_type inválido: {trade_type!r}")

    is_lucky = _derive_is_lucky(trade_type)

    dedup_hash = _compute_dedup_hash(
        owner_id,
        observed_at,
        friendship_level,
        trade_type,
        atk,
        def_,
        hp,
        species,
    )

    existing = (
        TradeObservation.objects.filter(owner_id=owner_id, dedup_hash=dedup_hash)
        .exclude(state="deleted")
        .first()
    )
    if existing is not None:
        return existing

    if state is None:
        state, exclusion_reason = _determine_state(
            atk,
            def_,
            hp,
            friendship_level,
            trade_type,
            owner_id,
            observed_at,
            species,
            dedup_hash,
            resolved_floor=resolved["floor"] if resolved else None,
        )

    if resolved is not None:
        ruleset = resolved["ruleset"]
    else:
        try:
            _f, ruleset = resolve_trade_floor(friendship_level, trade_type)
        except RulesetUnavailableError:
            ruleset = None

    obs = TradeObservation.objects.create(
        session=session,
        owner_id=owner_id,
        observed_at=observed_at,
        friendship_level=friendship_level,
        trade_type=trade_type,
        is_lucky=is_lucky,
        lucky_guaranteed=lucky_guaranteed,
        atk=atk,
        iv_def=def_,
        hp=hp,
        species=species,
        special_trade=special_trade,
        oldest_age_bucket=oldest_age_bucket,
        event_context=event_context,
        app_version=app_version,
        input_method=input_method,
        ruleset=ruleset,
        state=state,
        exclusion_reason=exclusion_reason,
        contribution_optin=contribution_optin,
        dedup_hash=dedup_hash,
        notes=notes,
    )
    return obs


def bulk_create_observations(
    observations: list[dict[str, Any]],
) -> list[TradeObservation]:
    """Crea multiples observaciones en una transaccion.

    Cada dict debe tener al menos: owner_id, observed_at, friendship_level,
    trade_type, atk, def_, hp.

    Resuelve el piso y ruleset una unica vez por combinacion distinta de
    (friendship_level, trade_type) en lugar de una vez por fila.
    """
    resolved_cache: dict[tuple[str, str], dict] = {}

    def _resolve(friendship_level: str, trade_type: str) -> dict:
        key = (friendship_level, trade_type)
        if key not in resolved_cache:
            try:
                f, ruleset = resolve_trade_floor(friendship_level, trade_type)
            except RulesetUnavailableError:
                f, ruleset = 0, None
            resolved_cache[key] = {
                "floor": f,
                "ruleset_version": ruleset.version if ruleset else None,
                "ruleset": ruleset,
            }
        return resolved_cache[key]

    results: list[TradeObservation] = []
    with transaction.atomic():
        for data in observations:
            resolved = _resolve(data["friendship_level"], data["trade_type"])
            results.append(register_observation(**data, resolved=resolved))
    return results


def parse_csv_row(
    row: dict[str, str],
    row_num: int,
    owner_id: int,
) -> dict[str, Any] | str:
    """Parsea una fila de CSV y devuelve datos validados o mensaje de error.

    El valor de retorno es un dict con los campos para register_observation
    si la fila es valida, o un str con el mensaje de error si es invalida.
    """
    try:
        observed_at = datetime.fromisoformat(row.get("observed_at", ""))
    except (ValueError, TypeError):
        return f"Fila {row_num}: observed_at invalido"

    friendship_level = row.get("friendship_level", "").strip()
    if friendship_level not in FRIENDSHIP_LEVELS:
        return f"Fila {row_num}: friendship_level invalido: {friendship_level}"

    trade_type = row.get("trade_type", "").strip()
    if trade_type not in TRADE_TYPES:
        return f"Fila {row_num}: trade_type invalido: {trade_type}"

    try:
        atk = int(row.get("atk", ""))
        def_ = int(row.get("def", ""))
        hp = int(row.get("hp", ""))
    except (ValueError, TypeError):
        return f"Fila {row_num}: IVs deben ser enteros"

    species = row.get("species", "").strip()

    return {
        "owner_id": owner_id,
        "observed_at": observed_at,
        "friendship_level": friendship_level,
        "trade_type": trade_type,
        "atk": atk,
        "def_": def_,
        "hp": hp,
        "species": species,
        "input_method": "csv",
    }


def import_csv(
    csv_content: str,
    owner_id: int,
) -> dict[str, Any]:
    """Importa observaciones desde contenido CSV.

    Devuelve dict con:
      - created: list[TradeObservation] exitosas
      - errors: list[str] errores por fila
      - total: int filas procesadas
      - valid_count: int
      - error_count: int
    """
    cleaned = csv_content.lstrip("\ufeff")
    reader = csv.DictReader(io.StringIO(cleaned))
    created: list[TradeObservation] = []
    errors: list[str] = []
    total = 0

    observations_data: list[dict[str, Any]] = []
    for row_num, row in enumerate(reader, start=2):
        total += 1
        result = parse_csv_row(row, row_num, owner_id)
        if isinstance(result, str):
            errors.append(result)
        else:
            observations_data.append(result)

    if observations_data:
        created = bulk_create_observations(observations_data)

    return {
        "created": created,
        "errors": errors,
        "total": total,
        "valid_count": len(created),
        "error_count": len(errors),
    }


def _sanitize_csv_cell(value: str) -> str:
    """Prefija un apostrofo a celdas que empiezan con caracteres peligrosos.

    Anti spreadsheet-injection: si el primer caracter es = + - @ tab o cr,
    se prefija ' para que Excel/Sheets lo traten como texto.
    """
    if value and value[0] in ("=", "+", "-", "@", "\t", "\r"):
        return "'" + value
    return value


def export_csv(owner_id: int) -> str:
    """Genera CSV de las observaciones del usuario.

    NOTA: notes es privado y NO se exporta.
    Aplica anti spreadsheet-injection a celdas de texto.
    """
    observations = (
        TradeObservation.objects.filter(
            owner_id=owner_id,
        )
        .exclude(state="deleted")
        .order_by("-observed_at")
    )

    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(
        [
            "observed_at",
            "friendship_level",
            "trade_type",
            "is_lucky",
            "atk",
            "def",
            "hp",
            "species",
            "state",
        ]
    )

    for obs in observations:
        writer.writerow(
            [
                obs.observed_at.isoformat(),
                obs.friendship_level,
                obs.trade_type,
                str(obs.is_lucky),
                obs.atk,
                obs.iv_def,
                obs.hp,
                _sanitize_csv_cell(obs.species),
                obs.state,
            ]
        )

    return output.getvalue()


def dashboard_stats(owner_id: int) -> dict[str, Any]:
    """Totales del dashboard separando Lucky vs normal.

    Devuelve dict con totales generales y por tipo.
    """
    base = TradeObservation.objects.filter(
        owner_id=owner_id,
    ).exclude(state="deleted")

    aggregated = base.aggregate(
        total=Count("id"),
        lucky=Count("pk", filter=Q(is_lucky=True)),
        normal=Count("pk", filter=Q(is_lucky=False)),
    )

    return aggregated
