"""Tests de engine/pvp_rank.py — Stat Product y ranking de IV para PvP.

Fixtures verificadas:
  Medicham Great League (1500 CP): mejor IV conocido es cercano a 5/15/15.
  Stat product: invariantes básicas y monotonía.
"""

from dataclasses import FrozenInstanceError

import pytest

from engine.pvp_rank import (
    IVSpread,
    generate_all_ivs,
    iv_rank_percent,
    rank_for_league,
    stat_product,
    top_spreads,
)
from engine.stats import cpm_for_level


class TestGenerateAllIVs:
    def test_has_4096_combinations(self):
        ivs = generate_all_ivs()
        assert len(ivs) == 4096

    def test_includes_extremes(self):
        ivs = generate_all_ivs()
        assert (0, 0, 0) in ivs
        assert (15, 15, 15) in ivs

    def test_all_values_in_range(self):
        for a, d, s in generate_all_ivs():
            assert 0 <= a <= 15
            assert 0 <= d <= 15
            assert 0 <= s <= 15


class TestStatProduct:
    def test_hundo_is_max(self):
        """15/15/15 produce el stat product máximo para un nivel dado."""
        cpm = cpm_for_level(40.0)
        sp_hundo = stat_product(121, 152, 155, 15, 15, 15, cpm)
        sp_zero = stat_product(121, 152, 155, 0, 0, 0, cpm)
        assert sp_hundo > sp_zero

    def test_stat_product_positive(self):
        cpm = cpm_for_level(20.0)
        sp = stat_product(121, 152, 155, 5, 15, 15, cpm)
        assert sp > 0


class TestRankForLeague:
    """Fixtures para Medicham en Great League (max_cp=1500)."""

    def test_medicham_gl_produces_ranking(self):
        ranking = rank_for_league(121, 152, 155, max_cp=1500, level_cap=50.0)
        assert len(ranking) > 0
        # Medicham a L50 con ciertos IVs debe caber en GL
        assert len(ranking) >= 1000

    def test_rank_1_is_best_stat_product(self):
        ranking = rank_for_league(121, 152, 155, max_cp=1500, level_cap=50.0)
        best = ranking[0]
        for spread in ranking[1:]:
            assert best.stat_product >= spread.stat_product

    def test_rank_order_tiebreaker(self):
        """A igual stat product, gana el que tiene menor atk_iv."""
        ranking = rank_for_league(121, 152, 155, max_cp=1500, level_cap=50.0)
        for i in range(len(ranking) - 1):
            curr, nxt = ranking[i], ranking[i + 1]
            if curr.stat_product == nxt.stat_product:
                assert curr.atk_iv <= nxt.atk_iv

    def test_top_spread_has_low_atk(self):
        """El mejor IV para GL típicamente tiene ATK bajo (0-5) para maximizar bulk."""
        ranking = rank_for_league(121, 152, 155, max_cp=1500, level_cap=50.0)
        best = ranking[0]
        assert best.atk_iv <= 8  # el mejor spread tiene ATK bajo

    def test_all_spreads_under_max_cp(self):
        ranking = rank_for_league(121, 152, 155, max_cp=1500, level_cap=50.0)
        for spread in ranking:
            assert spread.cp_value <= 1500

    def test_no_spread_exceeds_level_cap(self):
        ranking = rank_for_league(121, 152, 155, max_cp=1500, level_cap=40.0)
        for spread in ranking:
            assert spread.level <= 40.0

    def test_hundo_rank_is_not_zero(self):
        """15/15/15 no es el mejor IV para PvP (típicamente tiene rank alto/pobre)."""
        pct = iv_rank_percent(121, 152, 155, 15, 15, 15, max_cp=1500)
        # 15/15/15 casi nunca es el mejor; debe tener percentil > 0
        assert pct > 5.0  # no está en el top 5 %

    def test_iv_rank_percent_best_is_zero(self):
        ranking = rank_for_league(121, 152, 155, max_cp=1500, level_cap=50.0)
        best = ranking[0]
        pct = iv_rank_percent(121, 152, 155, best.atk_iv, best.def_iv, best.stam_iv, max_cp=1500)
        assert pct == pytest.approx(0.0, abs=0.5)


class TestTopSpreads:
    def test_returns_n_spreads(self):
        result = top_spreads(121, 152, 155, max_cp=1500, n=5)
        assert len(result) == 5

    def test_top_spreads_are_best(self):
        ranking = rank_for_league(121, 152, 155, max_cp=1500)
        tops = top_spreads(121, 152, 155, max_cp=1500, n=10)
        for i, spread in enumerate(tops):
            assert spread.atk_iv == ranking[i].atk_iv
            assert spread.def_iv == ranking[i].def_iv
            assert spread.stam_iv == ranking[i].stam_iv


class TestIVSpreadImmutability:
    def test_iv_spread_is_frozen(self):
        sp = IVSpread(atk_iv=5, def_iv=15, stam_iv=15, level=50.0, cp_value=1495, stat_product=1000)
        with pytest.raises(FrozenInstanceError):
            sp.atk_iv = 10  # type: ignore[misc]
