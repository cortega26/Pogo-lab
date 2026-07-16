"""Tests para engine/probability.py — fixtures calculadas a mano.

Casos de referencia (plan §F, §J):
  - Lucky (f=12) → k=4, p_hundo = (1/4)^3 = 1/64
  - Estándar (f=1) → k=15, p_hundo = (1/15)^3 = 1/3375
  - Good friends (f=1), Great (f=2), Ultra (f=3), Best (f=5)
"""

import pytest


class TestPossibleValues:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_lucky_floor(self):
        """Lucky f=12 → k=4."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_standard_floor_1(self):
        """Estándar f=1 → k=15."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_max_floor(self):
        """f=15 → k=1."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_min_floor(self):
        """f=0 → k=16."""


class TestPHundo:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_lucky_hundo(self):
        """Lucky f=12 → p_hundo = 1/64."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_standard_hundo(self):
        """Estándar f=1 → p_hundo = 1/3375."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_best_friends_hundo(self):
        """Best friends f=5 → p_hundo = (1/11)^3."""


class TestPStatAtLeast:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_stat_15_given_lucky(self):
        """Lucky f=12, t=15 → P = 1/4."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_stat_below_floor_returns_1(self):
        """t < f → P = 1."""


class TestIVSumDistribution:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_support_bounds(self):
        """Soporte [3f, 45], extremos tienen probabilidad > 0."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_distribution_sums_to_1(self):
        """Σ P(s) = 1 exacto."""


class TestPAutLeastOne:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_p_at_least_one_lucky_hundo_n_10(self):
        """Lucky f=12, n=10, p_hundo=1/64 → P = 1-(63/64)^10."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_p_zero_matches_1_minus_p_at_least_one(self):
        """P(zero) + P(at_least_one) = 1."""


class TestTradesForConfidence:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_lucky_hundo_50_percent_confidence(self):
        """c=0.5, p=1/64 → n ~ 44."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_confidence_never_exceeds_1(self):
        """n finito, c < 1 siempre."""


class TestPerTradeSuccessProb:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_hundo_target_delegates_to_p_hundo(self):
        """target={"kind": "hundo"} → igual a p_hundo(f)."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_stat_min_target(self):
        """target={"kind": "stat_min", "threshold": 15} → p_stat_at_least(f, 15)."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M3")
    def test_sum_min_target(self):
        """target={"kind": "sum_min", "threshold": 42} → p_sum_at_least(f, 42)."""
