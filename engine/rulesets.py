"""Schemas de parámetros de ruleset (dataclasses) y validación.

Define el contrato entre los modelos Django de MechanicRuleSet/RuleParameter
y el motor matemático. Los pisos de IV por amistad y Lucky viven aquí como
datos configurables, nunca hardcodeados.

La validación de parámetros es un contrato del engine puro (sin Django).
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class FriendshipLevel(Enum):
    GOOD = "good"
    GREAT = "great"
    ULTRA = "ultra"
    BEST = "best"


class TradeType(Enum):
    NORMAL = "normal"
    LUCKY = "lucky"
    LUCKY_GUARANTEED = "lucky_guaranteed"


class SourceType(Enum):
    OFICIAL = "oficial"
    COMMUNITY_RESEARCH = "community_research"
    DATAMINING = "datamining"
    INFERENCE = "inference"
    INTERNAL_HYPOTHESIS = "internal_hypothesis"


class ConfidenceLevel(Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    HYPOTHETICAL = "hypothetical"


@dataclass(frozen=True)
class RuleParameterValue:
    """Valor de un parámetro de ruleset."""

    key: str
    value: float | int | bool | dict
    data_type: str
    unit: str | None = None


@dataclass(frozen=True)
class SourceClaim:
    """Afirmación citada por una fuente."""

    source_title: str
    source_url: str | None
    source_type: SourceType
    confidence_level: ConfidenceLevel
    quote_summary: str | None = None


@dataclass(frozen=True)
class MechanicRuleSet:
    """Ruleset inmutable de una mecánica.

    Una vez publicado, no se modifica — los cambios crean una nueva versión.
    """

    mechanic_key: str
    version: int
    name: str
    effective_from: datetime
    effective_to: datetime | None
    parameters: tuple[RuleParameterValue, ...] = field(default_factory=tuple)
    claims: tuple[SourceClaim, ...] = field(default_factory=tuple)
    confidence_level: ConfidenceLevel = ConfidenceLevel.MEDIUM
    is_published: bool = False


FRIENDSHIP_FLOORS: dict[FriendshipLevel, int] = {
    FriendshipLevel.GOOD: 1,
    FriendshipLevel.GREAT: 2,
    FriendshipLevel.ULTRA: 3,
    FriendshipLevel.BEST: 5,
}

LUCKY_FLOOR: int = 12


# --- Schemas de validación ---

PARAMETER_SCHEMAS: dict[str, dict[str, dict]] = {
    "trade_iv": {
        "floor.friendship.good": {"type": "integer", "min": 0, "max": 15, "required": True},
        "floor.friendship.great": {"type": "integer", "min": 0, "max": 15, "required": True},
        "floor.friendship.ultra": {"type": "integer", "min": 0, "max": 15, "required": True},
        "floor.friendship.best": {"type": "integer", "min": 0, "max": 15, "required": True},
        "floor.lucky": {"type": "integer", "min": 0, "max": 15, "required": True},
    },
}


def validate_parameters(
    mechanic_key: str,
    rule_params: list["RuleParameterValue"] | list,
) -> list[str]:
    """Valida parámetros de un ruleset contra el schema definido para la mecánica.

    Args:
        mechanic_key: Código interno de la mecánica (ej. "trade_iv").
        rule_params: Lista de objetos con atributos key, value, data_type.

    Returns:
        Lista de errores de validación. Vacía si todo es válido.
    """
    schema = PARAMETER_SCHEMAS.get(mechanic_key)
    if schema is None:
        return [f"No hay schema definido para la mecánica '{mechanic_key}'."]

    errors: list[str] = []
    param_map = {p.key: p for p in rule_params}
    required_keys = {k for k, v in schema.items() if v.get("required")}
    provided_keys = set(param_map.keys())

    missing = required_keys - provided_keys
    for key in sorted(missing):
        errors.append(f"Falta el parámetro obligatorio '{key}'.")

    unknown = provided_keys - schema.keys()
    for key in sorted(unknown):
        errors.append(f"Parámetro desconocido '{key}' para mecánica '{mechanic_key}'.")

    for key, rules in schema.items():
        param = param_map.get(key)
        if param is None:
            continue
        expected_type = rules["type"]
        type_map = {
            "integer": (int,),
            "float": (int, float),
            "boolean": (bool,),
            "string": (str,),
            "json": (dict, list),
        }
        if not isinstance(param.value, type_map.get(expected_type, (object,))):
            errors.append(
                f"'{key}': se esperaba tipo {expected_type}, "
                f"se recibió {type(param.value).__name__}."
            )
            continue
        if expected_type == "integer" and isinstance(param.value, bool):
            errors.append(f"'{key}': bool no es un entero válido.")
            continue
        if expected_type in ("integer", "float") and not isinstance(param.value, bool):
            min_val = rules.get("min")
            max_val = rules.get("max")
            if min_val is not None and param.value < min_val:
                errors.append(f"'{key}': valor {param.value} menor que mínimo {min_val}.")
            if max_val is not None and param.value > max_val:
                errors.append(f"'{key}': valor {param.value} mayor que máximo {max_val}.")

    return errors


def resolve_active_ruleset(
    rulesets: list["MechanicRuleSet"],
    at_datetime: datetime,
) -> "MechanicRuleSet | None":
    """Resuelve el ruleset activo para una mecánica en una fecha dada.

    Busca el ruleset publicado con effective_from <= at_datetime
    y (effective_to es null o > at_datetime). Devuelve el de versión más alta
    si hay múltiples coincidencias.
    """
    candidates = [
        rs
        for rs in rulesets
        if rs.is_published
        and rs.effective_from <= at_datetime
        and (rs.effective_to is None or rs.effective_to > at_datetime)
    ]
    if not candidates:
        return None
    return max(candidates, key=lambda rs: rs.version)
