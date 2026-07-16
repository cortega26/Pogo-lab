"""Tests para engine/probability.py — fixtures calculadas a mano + property-based.

Casos de referencia (plan §F, §J):
  - Lucky (f=12) -> k=4, p_hundo = (1/4)^3 = 1/64
  - Estandar (f=1) -> k=15, p_hundo = (1/15)^3 = 1/3375
  - Good friends (f=1), Great (f=2), Ultra (f=3), Best (f=5)
"""

from fractions import Fraction
from math import isclose

import pytest
from hypothesis import assume, given
from hypothesis import strategies as st

from engine.probability import (
    expected_successes,
    iv_sum_distribution,
    outcome_distribution,
    p_at_least_one,
    p_hundo,
    p_specific_iv,
    p_stat_at_least,
    p_sum_at_least,
    p_zero,
    per_trade_success_prob,
    possible_values,
    trades_for_confidence,
)


class TestPossibleValues:
    def test_lucky_floor(self):
        """Lucky f=12 -> k=4."""
        assert possible_values(12) == 4

    def test_standard_floor_1(self):
        """Estandar f=1 -> k=15."""
        assert possible_values(1) == 15

    def test_max_floor(self):
        """f=15 -> k=1."""
        assert possible_values(15) == 1

    def test_min_floor(self):
        """f=0 -> k=16."""
        assert possible_values(0) == 16


class TestPHundo:
    def test_lucky_hundo(self):
        """Lucky f=12 -> p_hundo = 1/64."""
        assert p_hundo(12) == Fraction(1, 64)

    def test_standard_hundo(self):
        """Estandar f=1 -> p_hundo = 1/3375."""
        assert p_hundo(1) == Fraction(1, 3375)

    def test_best_friends_hundo(self):
        """Best friends f=5 -> p_hundo = (1/11)^3."""
        assert p_hundo(5) == Fraction(1, 1331)

    @given(st.integers(min_value=0, max_value=15))
    def test_p_hundo_is_fraction_between_0_and_1(self, f):
        prob = p_hundo(f)
        assert 0 < prob <= 1

    @given(st.integers(min_value=0, max_value=15))
    def test_p_specific_iv_is_reciprocal_of_k(self, f):
        k = possible_values(f)
        assert p_specific_iv(f) == Fraction(1, k)


class TestPStatAtLeast:
    def test_stat_15_given_lucky(self):
        """Lucky f=12, t=15 -> P = 1/4."""
        assert p_stat_at_least(12, 15) == Fraction(1, 4)

    def test_stat_below_floor_returns_at_least_floor(self):
        """t < f -> P = (16 - f) / k = 1."""
        assert p_stat_at_least(5, 3) == Fraction(1, 1)

    def test_stat_at_min_possible(self):
        """f=5, t=5 -> P = (16-5)/11 = 1."""
        assert p_stat_at_least(5, 5) == Fraction(1, 1)

    def test_stat_above_max_returns_0(self):
        """f=5, t=16 -> P = 0/k = 0."""
        assert p_stat_at_least(5, 16) == Fraction(0, 1)

    @given(
        st.integers(min_value=0, max_value=15),
        st.integers(min_value=0, max_value=16),
    )
    def test_stat_at_least_is_probability(self, f, t):
        prob = p_stat_at_least(f, t)
        assert 0 <= prob <= 1


class TestIVSumDistribution:
    def test_support_bounds(self):
        """Soporte [3f, 45], extremos tienen probabilidad > 0."""
        dist = iv_sum_distribution(5)
        assert min(dist.keys()) == 15
        assert max(dist.keys()) == 45
        assert dist[15] > Fraction(0, 1)
        assert dist[45] > Fraction(0, 1)

    def test_distribution_sums_to_1(self):
        """Sigma P(s) = 1 exacto."""
        dist = iv_sum_distribution(1)
        total = sum(dist.values(), Fraction(0, 1))
        assert total == Fraction(1, 1)

    def test_lucky_distribution(self):
        """f=12 -> k=4 -> soporte [36, 45], 10 valores."""
        dist = iv_sum_distribution(12)
        assert min(dist.keys()) == 36
        assert max(dist.keys()) == 45
        total = sum(dist.values(), Fraction(0, 1))
        assert total == Fraction(1, 1)

    @given(st.integers(min_value=0, max_value=15))
    def test_distribution_sums_to_1_property(self, f):
        dist = iv_sum_distribution(f)
        total = sum(dist.values(), Fraction(0, 1))
        assert total == Fraction(1, 1)

    @given(st.integers(min_value=0, max_value=15))
    def test_all_probabilities_positive(self, f):
        dist = iv_sum_distribution(f)
        for prob in dist.values():
            assert prob > Fraction(0, 1)

    @given(st.integers(min_value=0, max_value=15))
    def test_support_is_contiguous(self, f):
        dist = iv_sum_distribution(f)
        keys = sorted(dist.keys())
        assert keys == list(range(min(keys), max(keys) + 1))


class TestPAutLeastOne:
    def test_p_at_least_one_lucky_hundo_n_10(self):
        """Lucky f=12, n=10, p_hundo=1/64 -> P = 1-(63/64)^10."""
        expected = 1.0 - (63.0 / 64.0) ** 10
        result = p_at_least_one(float(Fraction(1, 64)), 10)
        assert isclose(result, expected, rel_tol=1e-12)

    def test_p_zero_matches_1_minus_p_at_least_one(self):
        """P(zero) + P(at_least_one) = 1."""
        p = float(Fraction(1, 64))
        n = 10
        assert isclose(p_at_least_one(p, n) + p_zero(p, n), 1.0, rel_tol=1e-12)

    def test_n_0_returns_0(self):
        assert p_at_least_one(0.5, 0) == 0.0

    def test_p_0_returns_0(self):
        assert p_at_least_one(0.0, 10) == 0.0

    def test_p_1_returns_1(self):
        assert p_at_least_one(1.0, 5) == 1.0

    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.integers(min_value=0, max_value=100),
    )
    def test_p_at_least_one_in_range(self, p, n):
        assume(0.0 <= p <= 1.0)
        result = p_at_least_one(p, n)
        assert 0.0 <= result <= 1.0


class TestTradesForConfidence:
    def test_lucky_hundo_50_percent_confidence(self):
        """c=0.5, p=1/64 -> n = 45."""
        n = trades_for_confidence(1.0 / 64.0, 0.5)
        assert n == 45
        # Verifica que realmente cumple la condicion
        prob = 1.0 - (1.0 - 1.0 / 64.0) ** 45
        assert prob >= 0.5

    def test_confidence_never_exceeds_1(self):
        """n finito, c < 1 siempre."""
        n = trades_for_confidence(0.5, 0.999)
        assert n >= 1
        prob = 1.0 - (1.0 - 0.5) ** n
        assert prob >= 0.999

    def test_p_1_returns_1(self):
        assert trades_for_confidence(1.0, 0.5) == 1

    def test_p_0_returns_0(self):
        assert trades_for_confidence(0.0, 0.5) == 0

    def test_c_0_returns_0(self):
        assert trades_for_confidence(0.5, 0.0) == 0

    def test_lucky_hundo_90_percent(self):
        """c=0.9, p=1/64 -> n = 147."""
        n = trades_for_confidence(1.0 / 64.0, 0.9)
        assert n == 147

    def test_lucky_hundo_95_percent(self):
        """c=0.95, p=1/64 -> n = 191."""
        n = trades_for_confidence(1.0 / 64.0, 0.95)
        assert n == 191

    def test_standard_hundo_50_percent(self):
        """c=0.5, p=1/3375 -> n = 2340."""
        n = trades_for_confidence(1.0 / 3375.0, 0.5)
        assert n == 2340
        prob = 1.0 - (1.0 - 1.0 / 3375.0) ** 2340
        assert prob >= 0.5


class TestPerTradeSuccessProb:
    def test_hundo_target_delegates_to_p_hundo(self):
        """target={"kind": "hundo"} -> igual a p_hundo(f)."""
        for f in [1, 5, 12]:
            expected = float(p_hundo(f))
            result = per_trade_success_prob(f, {"kind": "hundo"})
            assert isclose(result, expected, rel_tol=1e-12)

    def test_stat_min_target(self):
        """target={"kind": "stat_min", "threshold": 15} -> p_stat_at_least(f, 15)."""
        for f in [1, 5, 12]:
            expected = float(p_stat_at_least(f, 15))
            result = per_trade_success_prob(f, {"kind": "stat_min", "threshold": 15})
            assert isclose(result, expected, rel_tol=1e-12)

    def test_sum_min_target(self):
        """target={"kind": "sum_min", "threshold": 42} -> p_sum_at_least(f, 42)."""
        for f in [1, 5, 12]:
            expected = float(p_sum_at_least(f, 42))
            result = per_trade_success_prob(f, {"kind": "sum_min", "threshold": 42})
            assert isclose(result, expected, rel_tol=1e-12)

    def test_unknown_target_raises(self):
        with pytest.raises(ValueError, match="Tipo de objetivo desconocido"):
            per_trade_success_prob(1, {"kind": "invalid"})


class TestOutcomeDistribution:
    def test_sums_to_1(self):
        dist = outcome_distribution(0.25, 10)
        assert isclose(sum(dist), 1.0, rel_tol=1e-12)

    def test_length_n_plus_1(self):
        dist = outcome_distribution(0.5, 5)
        assert len(dist) == 6

    def test_n_0_returns_single_1(self):
        dist = outcome_distribution(0.5, 0)
        assert dist == [1.0]

    def test_expected_matches_n_times_p(self):
        p = 0.25
        n = 20
        dist = outcome_distribution(p, n)
        mean = sum(i * dist[i] for i in range(n + 1))
        assert isclose(mean, expected_successes(p, n), rel_tol=1e-12)

    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.integers(min_value=0, max_value=30),
    )
    def test_distribution_sums_to_1_property(self, p, n):
        assume(0.0 <= p <= 1.0)
        dist = outcome_distribution(p, n)
        assert isclose(sum(dist), 1.0, rel_tol=1e-10)

    @given(
        st.floats(min_value=0.0, max_value=1.0),
        st.integers(min_value=0, max_value=30),
    )
    def test_all_values_non_negative(self, p, n):
        assume(0.0 <= p <= 1.0)
        dist = outcome_distribution(p, n)
        assert all(v >= -1e-12 for v in dist)
        assert all(v <= 1.0 + 1e-12 for v in dist)


class TestDocsExamplesAntiDrift:
    """Gate M3: ejemplos de docs/plan.md y AGENTS.md verificados contra engine.

    Una sola fuente de verdad: engine/probability.py.
    """

    def test_agentes_lucky_p_hundo(self):
        """AGENTS.md: Lucky f=12 -> k=4, p_hundo = 1/64."""
        assert possible_values(12) == 4
        assert p_hundo(12) == Fraction(1, 64)

    def test_agentes_standard_p_hundo(self):
        """AGENTS.md: estandar f=1 -> k=15, p_hundo = 1/3375."""
        assert possible_values(1) == 15
        assert p_hundo(1) == Fraction(1, 3375)

    def test_best_friends_floor_5(self):
        """plan.md: Best f=5 -> k=11, p_hundo = 1/1331."""
        assert possible_values(5) == 11
        assert p_hundo(5) == Fraction(1, 1331)

    def test_good_friends_floor_1(self):
        """Seed: Good friends f=1."""
        assert possible_values(1) == 15

    def test_great_friends_floor_2(self):
        """Seed: Great friends f=2."""
        assert possible_values(2) == 14

    def test_ultra_friends_floor_3(self):
        """Seed: Ultra friends f=3."""
        assert possible_values(3) == 13
