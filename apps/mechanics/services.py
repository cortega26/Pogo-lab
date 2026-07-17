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


def _floor_from_params(
    params: dict[str, Any],
    friendship_level: str,
    trade_type: str,
) -> int:
    """Extrae el piso `f` de los parámetros de un ruleset.

    Lucky/trade_type in (lucky, lucky_guaranteed) sobrescribe con floor.lucky;
    en otro caso usa floor.friendship.<nivel>.
    """
    if trade_type in ("lucky", "lucky_guaranteed"):
        return int(params.get("floor.lucky", 12))
    key = _FLOOR_KEYS.get(friendship_level, "floor.friendship.good")
    return int(params.get(key, 1))


def floor_for_ruleset(
    ruleset: MechanicRuleSet,
    friendship_level: str,
    trade_type: str,
) -> int:
    """Piso `f` leído de un ruleset ESPECÍFICO (el vigente al registrar la obs).

    A diferencia de `resolve_trade_floor` (que resuelve el vigente por fecha),
    lee el piso del ruleset dado — necesario para analizar observaciones
    históricas con el piso bajo el que se registraron.
    """
    params: dict[str, Any] = {p.key: p.value for p in ruleset.parameters.all()}
    return _floor_from_params(params, friendship_level, trade_type)


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
    return _floor_from_params(params, friendship_level, trade_type), ruleset.version
