"""Tests de engine/costs.py — costos de power-up.

Fixtures verificadas:
  L1→L40 normal: 270,000 dust, 192 candy (consenso comunitario)
  L1→L40 lucky: 135,000 dust (50 % descuento)
  L1→L40 shadow: 324,000 dust (20 % recargo)
  L1→L50: 520,000 dust
  L20→L30: 75,000 dust
"""

from dataclasses import FrozenInstanceError

import pytest

from engine.costs import (
    LUCKY_STARDUST_MULTIPLIER,
    SHADOW_STARDUST_MULTIPLIER,
    _cost_for_powerup,
    _level_to_powerup_index,
    power_up_cost,
    power_ups_needed,
)


class TestLevelToPowerupIndex:
    def test_level_1_is_zero(self):
        assert _level_to_powerup_index(1.0) == 0

    def test_level_1_5_is_one(self):
        assert _level_to_powerup_index(1.5) == 1

    def test_level_40_is_78(self):
        assert _level_to_powerup_index(40.0) == 78

    def test_level_50_is_98(self):
        assert _level_to_powerup_index(50.0) == 98


class TestPowerUpsNeeded:
    def test_l1_to_l40(self):
        assert power_ups_needed(1.0, 40.0) == 78

    def test_l20_to_l40(self):
        assert power_ups_needed(20.0, 40.0) == 40

    def test_zero_when_same_level(self):
        assert power_ups_needed(25.0, 25.0) == 0


class TestCostPerPowerup:
    def test_first_powerup_is_200_dust(self):
        d, c, x = _cost_for_powerup(0)
        assert d == 200
        assert c == 1
        assert x == 0

    def test_early_tiers_are_one_candy(self):
        for pu in range(5 * 4):
            _, c, _ = _cost_for_powerup(pu)
            assert c == 1

    def test_candy_xl_zero_before_level_40(self):
        for pu in range(78):
            _, _, x = _cost_for_powerup(pu)
            assert x == 0


class TestPowerUpCost:
    def test_l1_to_l40(self):
        """Total verificado: 270,000 dust, 192 candy."""
        r = power_up_cost(1.0, 40.0)
        assert r.total_stardust == 270_000
        assert r.total_candy == 192
        assert r.total_candy_xl == 0
        assert r.power_ups == 78

    def test_l1_to_l40_lucky(self):
        """Lucky: exactamente 50 % del stardust."""
        r = power_up_cost(1.0, 40.0, is_lucky=True)
        assert r.total_stardust == 135_000
        assert r.total_candy == 192  # caramelos no cambian

    def test_l1_to_l40_shadow(self):
        """Shadow: 20 % más de stardust."""
        r = power_up_cost(1.0, 40.0, is_shadow=True)
        assert r.total_stardust == 324_000
        assert r.total_candy == 192

    def test_l1_to_l20(self):
        r = power_up_cost(1.0, 20.0)
        assert r.total_stardust == 45_000
        assert r.power_ups == 38

    def test_l20_to_l30(self):
        r = power_up_cost(20.0, 30.0)
        assert r.total_stardust == 75_000
        assert r.power_ups == 20

    def test_l20_to_l40(self):
        r = power_up_cost(20.0, 40.0)
        assert r.total_stardust == 225_000
        assert r.power_ups == 40

    def test_l40_to_l50(self):
        r = power_up_cost(40.0, 50.0)
        assert r.total_stardust == 250_000
        assert r.power_ups == 20
        assert r.total_candy_xl > 0

    def test_l1_to_l50(self):
        r = power_up_cost(1.0, 50.0)
        assert r.total_stardust == 520_000
        assert r.power_ups == 98

    def test_from_greater_than_to_raises(self):
        with pytest.raises(ValueError):
            power_up_cost(40.0, 20.0)

    def test_same_level_costs_zero(self):
        r = power_up_cost(25.0, 25.0)
        assert r.total_stardust == 0
        assert r.power_ups == 0

    def test_powerup_cost_is_immutable(self):
        r = power_up_cost(1.0, 20.0)
        with pytest.raises(FrozenInstanceError):
            r.total_stardust = 999  # type: ignore[misc]


class TestMultiplierConstants:
    def test_lucky_is_half(self):
        assert LUCKY_STARDUST_MULTIPLIER == 0.5

    def test_shadow_is_120_percent(self):
        assert SHADOW_STARDUST_MULTIPLIER == 1.2


class TestCostMonotonicity:
    """El costo total crece con el nivel."""

    def test_cost_increases_with_level(self):
        r1 = power_up_cost(1.0, 20.0)
        r2 = power_up_cost(1.0, 40.0)
        assert r2.total_stardust > r1.total_stardust
        assert r2.total_candy > r1.total_candy

    def test_longer_range_costs_more(self):
        r1 = power_up_cost(20.0, 25.0)
        r2 = power_up_cost(20.0, 30.0)
        assert r2.total_stardust > r1.total_stardust
