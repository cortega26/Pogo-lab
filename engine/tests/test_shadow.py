"""Tests de engine/shadow.py — comparativa Shadow vs Purified.

Fixtures verificadas:
  Shadow tiene +20 % ataque, mismos CP/HP, power-up ×1.2 stardust.
  Purified tiene costos ×0.9 en stardust y caramelos.
"""

import pytest

from engine.shadow import (
    SHADOW_ATK_MULTIPLIER,
    SHADOW_DEF_MULTIPLIER,
    compare_shadow_purified,
)


class TestCompareShadowPurified:
    def test_same_cp_hp(self):
        """Shadow y Purified tienen el mismo CP y HP (el multiplicador no afecta CP)."""
        r = compare_shadow_purified(234, 159, 207, 15, 15, 15, 40.0, from_level=1.0)
        assert r.cp_shadow == r.cp_purified
        assert r.hp_shadow == r.hp_purified

    def test_shadow_higher_atk(self):
        """Shadow tiene +20 % ataque efectivo en PvE."""
        r = compare_shadow_purified(234, 159, 207, 15, 15, 15, 40.0, from_level=1.0)
        assert r.atk_shadow == pytest.approx(r.atk_purified * SHADOW_ATK_MULTIPLIER, abs=0.1)

    def test_shadow_higher_cost(self):
        """Shadow cuesta más stardust que Purified."""
        r = compare_shadow_purified(234, 159, 207, 15, 15, 15, 40.0, from_level=1.0)
        assert r.dust_shadow > r.dust_purified

    def test_shadow_damage_advantage(self):
        r = compare_shadow_purified(234, 159, 207, 15, 15, 15, 40.0)
        assert r.shadow_damage_advantage_pct() == pytest.approx(20.0, abs=0.5)

    def test_machamp_l40(self):
        """Machamp L40 15/15/15: Shadow con 20 % más daño, ~324k dust vs ~140k purified."""
        r = compare_shadow_purified(234, 159, 207, 15, 15, 15, 40.0, from_level=1.0)
        assert r.dust_shadow == 324_000
        assert r.dust_purified < r.dust_shadow


class TestConstants:
    def test_shadow_atk_multiplier(self):
        assert SHADOW_ATK_MULTIPLIER == 1.2

    def test_shadow_def_penalty(self):
        assert pytest.approx(0.833, abs=0.01) == SHADOW_DEF_MULTIPLIER
