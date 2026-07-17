"""Servicios de dominio compartidos para apps/mechanics.

Contiene el resolver de piso `f` para trade_iv, usado por calculators (M3)
y trades (M4). Una sola fuente de verdad (DRY, no-negociable del proyecto).
"""

from datetime import datetime
from typing import Any

from django.db import models
from django.utils import timezone

from apps.mechanics.models import Mechanic, MechanicRuleSet

_FLOOR_KEYS: dict[str, str] = {
    "good": "floor.friendship.good",
    "great": "floor.friendship.great",
    "ultra": "floor.friendship.ultra",
    "best": "floor.friendship.best",
}


class RulesetUnavailableError(RuntimeError):
    """No hay ruleset publicado para trade_iv en esta fecha."""


def resolve_trade_floor(
    friendship_level: str,
    trade_type: str,
    at: datetime | None = None,
) -> tuple[int, int | None]:
    """Resuelve el piso `f` desde el ruleset publicado de trade_iv.

    Devuelve (f, ruleset_version).
    Lucky/trade_type in (lucky, lucky_guaranteed) sobrescribe con floor.lucky.
    Lanza RulesetUnavailableError si no hay ruleset publicado.
    """
    try:
        mechanic = Mechanic.objects.get(key="trade_iv", status="active")
    except Mechanic.DoesNotExist as e:
        raise RulesetUnavailableError("Mecanica trade_iv no encontrada.") from e

    now = at if at is not None else timezone.now()
    qs = (
        MechanicRuleSet.objects.filter(
            mechanic=mechanic,
            is_published=True,
            effective_from__lte=now,
        )
        .filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=now),
        )
        .order_by("-version")
    )

    ruleset = qs.first()
    if ruleset is None:
        raise RulesetUnavailableError(
            "No hay ruleset publicado para trade_iv vigente en esta fecha."
        )

    params: dict[str, Any] = {p.key: p.value for p in ruleset.parameters.all()}
    if trade_type in ("lucky", "lucky_guaranteed"):
        floor = int(params.get("floor.lucky", 12))
    else:
        key = _FLOOR_KEYS.get(friendship_level, "floor.friendship.good")
        floor = int(params.get(key, 1))
    return floor, ruleset.version
