"""Tests para engine/rulesets.py — schemas y constantes.

Casos de referencia:
  - FriendshipLevel y TradeType tienen todos los valores esperados.
  - FRIENDSHIP_FLOORS cubre todos los niveles.
  - LUCKY_FLOOR = 12.
"""

import pytest


class TestFriendshipFloors:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_all_levels_have_floor(self):
        """Todo FriendshipLevel tiene un piso definido en FRIENDSHIP_FLOORS."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_lucky_floor_is_12(self):
        """LUCKY_FLOOR == 12."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_floors_are_increasing(self):
        """Los pisos son estrictamente crecientes con la amistad."""


class TestRuleParameterValue:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_frozen_dataclass(self):
        """RuleParameterValue es congelado (frozen=True)."""


class TestMechanicRuleSet:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_inmutable_when_published(self):
        """Un ruleset publicado es inmutable."""
