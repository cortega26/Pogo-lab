"""Servicio de dominio de la calculadora.

Obtiene el piso `f` del ruleset vigente (M2) y delega en engine/probability.
"""

import hashlib
import json
from base64 import b64decode, b64encode
from dataclasses import asdict, dataclass, field
from decimal import ROUND_HALF_UP, Decimal
from typing import TYPE_CHECKING, Any

from django.conf import settings
from django.core.cache import cache

from apps.mechanics.services import resolve_trade_floor
from engine import ALGORITHM_VERSION
from engine.probability import (
    expected_successes,
    p_at_least_one,
    p_zero,
    per_trade_success_prob,
    trades_for_confidence,
)

if TYPE_CHECKING:
    from apps.mechanics.models import MechanicRuleSet

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
    _ruleset_version: int | None = None,
) -> tuple[int, "MechanicRuleSet | None"]:
    """Resuelve el piso `f` delegando en mechanics.services.resolve_trade_floor.

    Mantiene compatibilidad con la API actual (parametro ruleset_version
    ignorado — el shared resolver siempre devuelve el vigente).
    """
    return resolve_trade_floor(friendship_level, trade_type)


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
        ruleset = None
    else:
        floor, ruleset = _resolve_floor(inputs.friendship_level, inputs.trade_type)

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
        ruleset_version=ruleset.version if ruleset else None,
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
        _, ruleset = _resolve_floor(inputs.friendship_level, inputs.trade_type)
        ruleset_version = ruleset.version if ruleset else None
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


# ══════════════════════════════════════════════════════════════════════════════
# Share URL genérico para todas las calculadoras
# ══════════════════════════════════════════════════════════════════════════════

GENERIC_SHARE_VERSION = "gv1"


def encode_calc_share(calc_type: str, params: dict) -> str:
    """Codifica parámetros de cualquier calculadora en un fragmento de URL.

    Args:
        calc_type: Tipo de calculadora (cp, cost, pvp, catch, types).
        params: Diccionario con los parámetros (valores simples: str, int, float).

    Returns:
        Fragmento base64url para ?share=.
    """
    payload: dict[str, str | int | float | bool] = {"v": GENERIC_SHARE_VERSION, "t": calc_type}
    # Filtrar valores no serializables y convertir a tipos planos
    for k, v in params.items():
        if v is None:
            continue
        if isinstance(v, (str, int, float, bool)):
            payload[k] = v

    raw = json.dumps(payload, sort_keys=True, separators=(",", ":"))
    encoded = b64encode(raw.encode()).decode().rstrip("=").replace("+", "-").replace("/", "_")
    return encoded


def decode_calc_share(encoded: str) -> tuple[str, dict]:
    """Decodifica un fragmento de URL genérico.

    Returns:
        Tupla (calc_type, params_dict).
    """
    try:
        padded = encoded.replace("-", "+").replace("_", "/")
        pad = 4 - len(padded) % 4
        if pad != 4:
            padded += "=" * pad
        raw = b64decode(padded.encode()).decode()
        payload = json.loads(raw)
    except (json.JSONDecodeError, Exception) as exc:
        raise ValueError("URL de calculadora inválida") from exc

    if payload.get("v") != GENERIC_SHARE_VERSION:
        raise ValueError("Versión de URL no soportada")

    calc_type = payload.pop("t")
    payload.pop("v", None)
    return calc_type, payload
