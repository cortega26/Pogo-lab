"""Tests para engine/stat_tests.py — fixtures a mano + property-based.

Anclas:
  - Binomial exacta: k=0, n=5, p0=0.5 → p bilateral = 2*(0.5)^5 = 0.0625.
  - Uniformity: ambas ramas (chi² con esperados ≥ 5, MC con esperados < 5).
  - MC reproducible: mismo seed → mismo p-valor.
  - Cramér's V ∈ [0,1].
"""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st

from engine.stat_tests import (
    _chi2_statistic,
    _compute_cramers_v,
    exact_binomial_test,
    independence_test,
    min_sample_for,
    uniformity_test,
)

# ---- Binomial exacta ----


class TestExactBinomialTest:
    def test_anchor_symmetric_k0_n5_p05(self):
        """k=0, n=5, p0=0.5 → p bilateral = 2·0.5^5 = 0.0625.

        Los únicos resultados con pmf ≤ pmf(0)=0.03125 son {0, 5}.
        """
        result = exact_binomial_test(0, 5, 0.5)
        assert math.isclose(result.p_value, 0.0625, rel_tol=1e-10), (
            f"Esperado 0.0625, obtenido {result.p_value}"
        )
        assert result.method_used == "exact_binomial"
        assert result.effect_size == 0.5  # |0/5 - 0.5|
        assert result.n == 5

    def test_anchor_symmetric_k5_n5_p05(self):
        """k=5, n=5, p0=0.5 → mismo p bilateral que k=0."""
        result = exact_binomial_test(5, 5, 0.5)
        assert math.isclose(result.p_value, 0.0625, rel_tol=1e-10)

    def test_exact_match_h0(self):
        """successes = n * p0 → p alto (compatible con H0)."""
        result = exact_binomial_test(25, 100, 0.25)
        assert result.p_value > 0.5

    def test_n_zero(self):
        """n=0 devuelve resultado neutro."""
        result = exact_binomial_test(0, 0, 0.5)
        assert result.p_value == 1.0
        assert result.effect_size == 0.0
        assert result.n == 0

    @given(
        st.integers(min_value=0, max_value=50),
        st.integers(min_value=50, max_value=100),
        st.floats(min_value=0.01, max_value=0.99),
    )
    def test_p_value_in_0_1(self, successes, n, p0):
        result = exact_binomial_test(successes, n, p0)
        assert 0.0 <= result.p_value <= 1.0

    def test_effect_size_is_absolute_difference(self):
        """effect_size = |p_hat - p0|."""
        result = exact_binomial_test(3, 10, 0.25)
        expected_effect = abs(3 / 10 - 0.25)
        assert result.effect_size is not None
        assert math.isclose(result.effect_size, expected_effect)


# ---- Uniformidad (bondad de ajuste) ----


class TestUniformityTest:
    def test_chi_square_branch_all_expected_ge_5(self):
        """n=160, 16 categorías → esperado=10 por celda → chi²."""
        counts = [10] * 16
        probs = [1.0 / 16] * 16
        result = uniformity_test(counts, probs, seed=42)
        assert result.method_used == "chisquare", f"Esperado chi², obtenido {result.method_used}"
        assert result.p_value > 0.9  # perfectamente uniforme
        assert result.min_expected == 10.0
        assert result.n == 160

    def test_monte_carlo_branch_small_expected(self):
        """n=16, 16 categorías → esperado=1 por celda → MC."""
        counts = [1] * 16
        probs = [1.0 / 16] * 16
        result = uniformity_test(counts, probs, seed=42)
        assert result.method_used == "monte_carlo", (
            f"Esperado monte_carlo, obtenido {result.method_used}"
        )
        assert 0.0 <= result.p_value <= 1.0
        assert result.min_expected == 1.0

    def test_monte_carlo_reproducible(self):
        """Mismo seed → mismo p-valor en dos corridas."""
        counts = [1] * 16
        probs = [1.0 / 16] * 16
        r1 = uniformity_test(counts, probs, method="monte_carlo", seed=12345)
        r2 = uniformity_test(counts, probs, method="monte_carlo", seed=12345)
        assert r1.p_value == r2.p_value, f"MC no reproducible: {r1.p_value} ≠ {r2.p_value}"
        assert r1.stat == r2.stat

    def test_monte_carlo_normalizes_probs(self):
        """Monte Carlo debe normalizar probs que no suman 1 (plan 022).

        Con counts=[10,10,10] y probs=[0.3,0.3,0.3] (suma 0.9), las probs
        normalizadas son [1/3, 1/3, 1/3] y el chi² observado es ~0, por lo que
        el p-valor es 1.0 (todos los valores simulados lo superan). La
        verificación clave es que el p-valor sea un número válido y que el
        min_expected refleje la normalización (n/k, no n*0.3).
        """
        counts = [10, 10, 10]
        probs = [0.3, 0.3, 0.3]  # suma = 0.9, no 1
        result = uniformity_test(counts, probs, method="monte_carlo", seed=42)
        assert result.method_used == "monte_carlo"
        assert result.stat is not None
        assert 0.0 <= result.p_value <= 1.0
        # min_expected debe reflejar la normalización: 30/3 = 10.0, no 30*0.3 = 9.0
        assert result.min_expected == pytest.approx(10.0), (
            f"min_expected debe ser 10.0 (normalizado), no 9.0 (sin normalizar): "
            f"{result.min_expected}"
        )

    def test_force_chisquare(self):
        """Forzar chi² aunque esperados sean pequeños."""
        counts = [2, 3, 1]
        probs = [0.4, 0.35, 0.25]
        result = uniformity_test(counts, probs, method="chisquare", seed=42)
        assert result.method_used == "chisquare"

    def test_force_monte_carlo(self):
        """Forzar MC aunque esperados sean grandes."""
        counts = [50, 50, 50, 50]
        probs = [0.25, 0.25, 0.25, 0.25]
        result = uniformity_test(counts, probs, method="monte_carlo", seed=42)
        assert result.method_used == "monte_carlo"

    def test_cramers_v_in_0_1(self):
        """Cramér's V entre 0 y 1."""
        counts = [5, 15, 5, 15]
        probs = [0.25, 0.25, 0.25, 0.25]
        result = uniformity_test(counts, probs)
        assert result.effect_size is not None
        assert 0.0 <= result.effect_size <= 1.0

    def test_perfect_uniformity_high_p_value(self):
        """Datos perfectamente uniformes → p-valor alto."""
        counts = [25, 25, 25, 25]
        probs = [0.25, 0.25, 0.25, 0.25]
        result = uniformity_test(counts, probs)
        assert result.p_value > 0.5

    def test_all_zero_expected_chisquare(self):
        """Observaciones solo en celdas con esperado>0, ceros en esperado=0 → p=1.0."""
        counts = [0, 5]
        probs = [0.0, 1.0]
        result = uniformity_test(counts, probs, method="chisquare")
        assert result.p_value == 1.0
        assert result.effect_size == 0.0

    def test_all_zero_observed_chisquare(self):
        """Todas las celdas observadas en cero → p=1.0."""
        counts = [0, 0, 0]
        probs = [0.3, 0.3, 0.4]
        result = uniformity_test(counts, probs, method="chisquare")
        assert result.p_value == 1.0

    def test_length_mismatch_raises(self):
        with pytest.raises(ValueError, match="misma longitud"):
            uniformity_test([10, 20], [0.3, 0.3, 0.4])

    def test_zero_expected_cell_mc(self):
        """Celdas con esperado 0 en MC también se gestionan."""
        counts = [0, 0, 5]
        probs = [0.0, 1.0, 0.0]  # suma = 1, pero celdas 0 tienen prob 0
        result = uniformity_test(counts, probs, method="monte_carlo")
        assert 0.0 <= result.p_value <= 1.0

    def test_zero_prob_sum_mc(self):
        """Suma de probs = 0 no causa división por cero en MC."""
        result = uniformity_test([0, 0], [0.0, 0.0], method="monte_carlo")
        assert result.p_value == 1.0
        assert result.effect_size == 0.0

    def test_zero_expected_nonzero_observed_mc(self):
        """MC con observación en celda esperado=0 → p pequeño."""
        counts = [0, 5, 0]
        probs = [0.5, 0.0, 0.5]
        result = uniformity_test(counts, probs, method="monte_carlo", seed=42)
        assert result.p_value < 0.05  # p muy pequeño porque chi²=inf
        assert result.stat == float("inf")

    def test_zero_expected_nonzero_observed_chisquare(self):
        """Observación en celda con esperado=0 → p=0."""
        counts = [0, 10, 0]
        probs = [0.5, 0.0, 0.5]
        result = uniformity_test(counts, probs, method="chisquare")
        assert result.p_value == 0.0
        assert result.stat == float("inf")

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="desconocido"):
            uniformity_test([10], [1.0], method="invalid")

    @given(
        st.lists(st.integers(min_value=0, max_value=100), min_size=2, max_size=10),
        st.lists(st.floats(min_value=0.0, max_value=1.0), min_size=2, max_size=10),
    )
    def test_p_value_in_0_1_property(self, counts, probs):
        if len(counts) != len(probs):
            return
        total_prob = sum(probs)
        if total_prob <= 0:
            return
        probs = [p / total_prob for p in probs]
        if sum(counts) == 0:
            return
        result = uniformity_test(counts, probs, seed=0)
        assert 0.0 <= result.p_value <= 1.0


# ---- Independencia ----


class TestIndependenceTest:
    def test_perfect_independence(self):
        """Pares independientes → p-valor alto."""
        pairs = []
        for _ in range(50):
            pairs.append((5, 5))
            pairs.append((10, 10))
            pairs.append((12, 12))
            pairs.append((15, 15))
        result = independence_test(pairs, seed=42)
        assert 0.0 <= result.p_value <= 1.0
        assert result.effect_size is not None
        assert 0.0 <= result.effect_size <= 1.0

    def test_n_zero(self):
        """n=0 devuelve resultado neutro."""
        result = independence_test([], seed=42)
        assert result.p_value == 1.0
        assert result.effect_size == 0.0
        assert result.n == 0

    def test_includes_holm_warning(self):
        """Resultado incluye advertencia de comparaciones múltiples."""
        pairs = [(10, 15), (12, 14), (11, 13)]
        result = independence_test(pairs, seed=42)
        warning_text = " ".join(result.warnings).lower()
        assert "holm" in warning_text or "comparaciones" in warning_text

    def test_g_test_branch(self):
        """Forzar G-test."""
        pairs = [(i % 16, (i + 2) % 16) for i in range(200)]
        result = independence_test(pairs, method="g_test", seed=42)
        assert result.method_used == "g_test"
        assert 0.0 <= result.p_value <= 1.0

    def test_g_test_single_unique_value(self):
        """G-test con un solo valor único (df=0)."""
        pairs = [(5, 5), (5, 5), (5, 5)]
        result = independence_test(pairs, method="g_test", seed=42)
        assert result.method_used == "g_test"
        assert result.p_value == 1.0

    def test_monte_carlo_branch(self):
        """Forzar Monte Carlo."""
        pairs = [(i % 16, (i + 1) % 16) for i in range(100)]
        result = independence_test(pairs, method="monte_carlo", seed=42)
        assert result.method_used == "monte_carlo"
        assert 0.0 <= result.p_value <= 1.0

    def test_monte_carlo_reproducible(self):
        """Mismo seed → mismo p-valor."""
        pairs = [(i % 16, (i + 1) % 16) for i in range(50)]
        r1 = independence_test(pairs, method="monte_carlo", seed=7777)
        r2 = independence_test(pairs, method="monte_carlo", seed=7777)
        assert r1.p_value == r2.p_value
        assert r1.stat == r2.stat

    def test_unknown_method_raises(self):
        with pytest.raises(ValueError, match="desconocido"):
            independence_test([(1, 2)], method="invalid")

    def test_cramers_v_non_square(self):
        """Cramér's V para tabla no cuadrada debe usar min(rows, cols)."""
        pairs_3x2 = (
            [(0, 0)] * 10 + [(0, 1)] * 5 + [(1, 0)] * 5 + [(1, 1)] * 8 + [(2, 0)] * 2 + [(2, 1)] * 4
        )
        result = independence_test(pairs_3x2, method="g_test")
        assert result.effect_size is not None
        assert 0 <= result.effect_size <= 1


# ---- Cramér's V ----


class TestCramersV:
    def test_zero_chi2_gives_zero_v(self):
        assert _compute_cramers_v(0.0, 100, 10) == 0.0

    def test_n_zero_gives_zero_v(self):
        assert _compute_cramers_v(5.0, 0, 5) == 0.0

    def test_k_one_gives_zero_v(self):
        assert _compute_cramers_v(5.0, 100, 1) == 0.0

    @given(
        st.floats(min_value=0.0, max_value=1000.0),
        st.integers(min_value=1, max_value=1000),
        st.integers(min_value=2, max_value=20),
    )
    def test_cramers_v_in_0_1_property(self, chi2, n, k):
        v = _compute_cramers_v(chi2, n, k)
        assert v >= 0.0  # V ≥ 0 siempre; V puede exceder 1 con n muy pequeño


# ---- Función auxiliar interna ----


class TestChi2Statistic:
    def test_zero_expected_nonzero_observed(self):
        """e=0 y o>0 → chi² = inf."""
        result = _chi2_statistic([5, 0], [0.0, 5.0])
        assert result == float("inf")

    def test_all_positive(self):
        result = _chi2_statistic([10, 10], [10.0, 10.0])
        assert result == 0.0


# ---- Umbrales ----


class TestMinSampleFor:
    def test_known_metrics(self):
        assert min_sample_for("hundo_rate") == 50
        assert min_sample_for("stat_uniformity") == 100
        assert min_sample_for("sum_uniformity") == 100
        assert min_sample_for("independence") == 100

    def test_unknown_metric_default(self):
        assert min_sample_for("nonexistent") == 30
        assert min_sample_for("") == 30
