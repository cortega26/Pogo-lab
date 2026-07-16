"""Tests para engine/rulesets.py — schemas, constantes y validación.

Casos de referencia:
  - FriendshipLevel y TradeType tienen todos los valores esperados.
  - FRIENDSHIP_FLOORS cubre todos los niveles.
  - LUCKY_FLOOR = 12.
  - validate_parameters acepta datos válidos y rechaza inválidos.
  - resolve_active_ruleset resuelve por fecha correctamente.
"""

from datetime import UTC, datetime

import pytest

from engine.rulesets import (
    FRIENDSHIP_FLOORS,
    LUCKY_FLOOR,
    FriendshipLevel,
    MechanicRuleSet,
    RuleParameterValue,
    resolve_active_ruleset,
    validate_parameters,
)


def _utc(year, month, day, hour=0, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


class TestFriendshipFloors:
    def test_all_levels_have_floor(self):
        for level in FriendshipLevel:
            assert level in FRIENDSHIP_FLOORS, f"Falta piso para {level}"

    def test_lucky_floor_is_12(self):
        assert LUCKY_FLOOR == 12

    def test_floors_are_increasing(self):
        levels = list(FriendshipLevel)
        floors = [FRIENDSHIP_FLOORS[level] for level in levels]
        for i in range(1, len(floors)):
            assert floors[i] > floors[i - 1], f"Los pisos no son crecientes: {floors}"

    def test_specific_floors(self):
        assert FRIENDSHIP_FLOORS[FriendshipLevel.GOOD] == 1
        assert FRIENDSHIP_FLOORS[FriendshipLevel.GREAT] == 2
        assert FRIENDSHIP_FLOORS[FriendshipLevel.ULTRA] == 3
        assert FRIENDSHIP_FLOORS[FriendshipLevel.BEST] == 5


class TestRuleParameterValue:
    def test_frozen_dataclass(self):
        p = RuleParameterValue(key="test", value=1, data_type="integer")
        with pytest.raises(AttributeError):
            p.value = 2  # type: ignore[misc]


class TestMechanicRuleSet:
    def test_immutable_when_published(self):
        rs = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=1,
            name="test",
            effective_from=_utc(2026, 1, 1),
            effective_to=None,
            is_published=True,
        )
        assert rs.is_published
        with pytest.raises(AttributeError):
            rs.version = 2  # type: ignore[misc]


class TestValidateParameters:
    def test_valid_trade_iv_params(self):
        params = [
            RuleParameterValue(key="floor.friendship.good", value=1, data_type="integer"),
            RuleParameterValue(key="floor.friendship.great", value=2, data_type="integer"),
            RuleParameterValue(key="floor.friendship.ultra", value=3, data_type="integer"),
            RuleParameterValue(key="floor.friendship.best", value=5, data_type="integer"),
            RuleParameterValue(key="floor.lucky", value=12, data_type="integer"),
        ]
        errors = validate_parameters("trade_iv", params)
        assert errors == []

    def test_missing_required_param(self):
        params = [
            RuleParameterValue(key="floor.friendship.good", value=1, data_type="integer"),
        ]
        errors = validate_parameters("trade_iv", params)
        assert any("Falta el parámetro obligatorio" in e for e in errors)

    def test_unknown_param(self):
        params = [
            RuleParameterValue(key="floor.friendship.good", value=1, data_type="integer"),
            RuleParameterValue(key="floor.friendship.great", value=2, data_type="integer"),
            RuleParameterValue(key="floor.friendship.ultra", value=3, data_type="integer"),
            RuleParameterValue(key="floor.friendship.best", value=5, data_type="integer"),
            RuleParameterValue(key="floor.lucky", value=12, data_type="integer"),
            RuleParameterValue(key="floor.unknown", value=99, data_type="integer"),
        ]
        errors = validate_parameters("trade_iv", params)
        assert any("Parámetro desconocido" in e for e in errors)

    def test_wrong_type(self):
        params = [
            RuleParameterValue(key="floor.friendship.good", value="abc", data_type="string"),  # type: ignore[arg-type]
            RuleParameterValue(key="floor.friendship.great", value=2, data_type="integer"),
            RuleParameterValue(key="floor.friendship.ultra", value=3, data_type="integer"),
            RuleParameterValue(key="floor.friendship.best", value=5, data_type="integer"),
            RuleParameterValue(key="floor.lucky", value=12, data_type="integer"),
        ]
        errors = validate_parameters("trade_iv", params)
        assert any("se esperaba tipo integer" in e for e in errors)

    def test_value_out_of_range(self):
        params = [
            RuleParameterValue(key="floor.friendship.good", value=-1, data_type="integer"),
            RuleParameterValue(key="floor.friendship.great", value=2, data_type="integer"),
            RuleParameterValue(key="floor.friendship.ultra", value=3, data_type="integer"),
            RuleParameterValue(key="floor.friendship.best", value=5, data_type="integer"),
            RuleParameterValue(key="floor.lucky", value=12, data_type="integer"),
        ]
        errors = validate_parameters("trade_iv", params)
        assert any("menor que mínimo" in e for e in errors)

    def test_no_schema_for_unknown_mechanic(self):
        params = [
            RuleParameterValue(key="foo", value=1, data_type="integer"),
        ]
        errors = validate_parameters("unknown_mechanic", params)
        assert any("No hay schema definido" in e for e in errors)


class TestResolveActiveRuleset:
    def test_resolves_correct_ruleset(self):
        now = _utc(2026, 7, 15)
        rs1 = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=1,
            name="v1",
            effective_from=_utc(2026, 1, 1),
            effective_to=_utc(2026, 6, 30),
            is_published=True,
        )
        rs2 = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=2,
            name="v2",
            effective_from=_utc(2026, 7, 1),
            effective_to=None,
            is_published=True,
        )
        result = resolve_active_ruleset([rs1, rs2], now)
        assert result is not None
        assert result.version == 2

    def test_returns_none_if_no_match(self):
        rs = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=1,
            name="v1",
            effective_from=_utc(2026, 1, 1),
            effective_to=_utc(2026, 6, 30),
            is_published=True,
        )
        result = resolve_active_ruleset([rs], _utc(2026, 12, 1))
        assert result is None

    def test_ignores_unpublished(self):
        rs = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=1,
            name="v1",
            effective_from=_utc(2026, 1, 1),
            effective_to=None,
            is_published=False,
        )
        result = resolve_active_ruleset([rs], _utc(2026, 7, 15))
        assert result is None

    def test_future_ruleset_not_returned(self):
        rs = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=1,
            name="v1",
            effective_from=_utc(2027, 1, 1),
            effective_to=None,
            is_published=True,
        )
        result = resolve_active_ruleset([rs], _utc(2026, 7, 15))
        assert result is None

    def test_returns_highest_version_on_overlap(self):
        now = _utc(2026, 7, 15)
        rs1 = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=1,
            name="v1",
            effective_from=_utc(2026, 1, 1),
            effective_to=None,
            is_published=True,
        )
        rs2 = MechanicRuleSet(
            mechanic_key="trade_iv",
            version=2,
            name="v2",
            effective_from=_utc(2026, 6, 1),
            effective_to=None,
            is_published=True,
        )
        result = resolve_active_ruleset([rs1, rs2], now)
        assert result is not None
        assert result.version == 2
