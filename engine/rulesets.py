"""Schemas de parámetros de ruleset (dataclasses).

Define el contrato entre los modelos Django de MechanicRuleSet/RuleParameter
y el motor matemático. Los pisos de IV por amistad y Lucky viven aquí como
datos configurables, nunca hardcodeados.
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime


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
    data_type: str  # "integer" | "float" | "boolean" | "json"
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
