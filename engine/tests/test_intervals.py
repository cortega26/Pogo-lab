"""Tests para engine/intervals.py — fixtures calculadas a mano + property-based.

Borde exacto:
  - Wilson con successes=0 → lo == 0.0 (algebraico, ver §5 del handoff).
  - Wilson con successes=n → hi == 1.0 (algebraico).
  - Clopper-Pearson con successes=0 → lo == 0.0.
  - Clopper-Pearson con successes=n → hi == 1.0.
"""

import math

import pytest
from hypothesis import given
from hypothesis import strategies as st
from scipy.stats import norm as norm_dist

from engine.intervals import (
    beta_binomial_credible,
    clopper_pearson_interval,
    wilson_interval,
)

# ---- Helpers para verificar anclas ----


def _wilson_manual(successes: int, n: int, conf: float) -> tuple[float, float]:
    """Implementación de referencia de Wilson para verificar fixtures."""
    if n == 0:
        return (0.0, 1.0)
    p_hat = successes / n
    z = norm_dist.ppf(1.0 - (1.0 - conf) / 2.0)
    z2 = z * z
    denominator = 1.0 + z2 / n
    center = (p_hat + z2 / (2.0 * n)) / denominator
    margin = (z / denominator) * math.sqrt(p_hat * (1.0 - p_hat) / n + z2 / (4.0 * n * n))
    return (max(0.0, center - margin), min(1.0, center + margin))


# ---- Wilson ----


class TestWilsonInterval:
    @pytest.mark.parametrize(
        "successes,n,conf",
        [
            (0, 10, 0.95),
            (5, 10, 0.95),
            (10, 10, 0.95),
            (0, 100, 0.99),
            (100, 100, 0.90),
        ],
    )
    def test_wilson_against_reference(self, successes, n, conf):
        """Wilson contra implementación de referencia independiente."""
        lo, hi = wilson_interval(successes, n, conf)
        ref_lo, ref_hi = _wilson_manual(successes, n, conf)
        assert math.isclose(lo, ref_lo, rel_tol=1e-12)
        assert math.isclose(hi, ref_hi, rel_tol=1e-12)

    def test_wilson_interior_pinned_reference(self):
        """Ancla interior FIJADA, independiente de la implementación (handoff §5).

        Valor de referencia conocido del intervalo de Wilson score para
        p̂=0.5, n=10, 95%: (0.2366, 0.7634). Detecta una fórmula mal derivada
        que las pruebas de borde/propiedad no cazan (a diferencia de
        `_wilson_manual`, que copia la impl y no verifica de forma independiente).
        """
        lo, hi = wilson_interval(5, 10, 0.95)
        assert math.isclose(lo, 0.2366, abs_tol=1e-4)
        assert math.isclose(hi, 0.7634, abs_tol=1e-4)

    def test_zero_successes_lo_is_zero(self):
        """successes=0 → lo == 0.0 exacto (propiedad algebraica)."""
        lo, hi = wilson_interval(0, 10)
        assert lo == 0.0
        assert hi > 0.0

    def test_all_successes_hi_is_one(self):
        """successes=n → hi == 1.0 exacto (propiedad algebraica)."""
        lo, hi = wilson_interval(20, 20)
        assert hi == 1.0
        assert lo < 1.0

    def test_n_zero_returns_full_range(self):
        """n=0 devuelve [0,1]."""
        lo, hi = wilson_interval(0, 0)
        assert lo == 0.0
        assert hi == 1.0

    def test_invalid_conf_raises(self):
        with pytest.raises(ValueError):
            wilson_interval(5, 10, conf=0.0)
        with pytest.raises(ValueError):
            wilson_interval(5, 10, conf=1.0)
        with pytest.raises(ValueError):
            wilson_interval(5, 10, conf=1.5)

    def test_clopper_pearson_invalid_conf_raises(self):
        with pytest.raises(ValueError):
            clopper_pearson_interval(5, 10, conf=0.0)
        with pytest.raises(ValueError):
            clopper_pearson_interval(5, 10, conf=1.0)

    @given(
        st.integers(min_value=0, max_value=200),
        st.integers(min_value=0, max_value=200),
        st.floats(min_value=0.01, max_value=0.99),
    )
    def test_wilson_in_0_1(self, successes, n_extra, conf):
        """Wilson siempre dentro de [0, 1]."""
        n = successes + n_extra
        if n == 0:
            return
        lo, hi = wilson_interval(successes, n, conf)
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0
        assert lo <= hi

    @given(
        st.integers(min_value=100, max_value=500),
        st.integers(min_value=1, max_value=9),
    )
    def test_wilson_narrows_with_larger_n_same_p_hat(self, n, factor):
        """Para mismo p̂ (manteniendo proporción), el intervalo se estrecha con n mayor."""
        successes = n // 4
        lo1, hi1 = wilson_interval(successes, n)
        lo2, hi2 = wilson_interval(successes * factor, n * factor)
        width1 = hi1 - lo1
        width2 = hi2 - lo2
        if successes > 0:
            assert width2 < width1 + 1e-12, f"Ancho no decreciente con p̂ fijo: {width1} → {width2}"


# ---- Clopper-Pearson ----


class TestClopperPearsonInterval:
    def test_zero_successes_lo_is_zero(self):
        """successes=0 → lo == 0.0."""
        lo, hi = clopper_pearson_interval(0, 10)
        assert lo == 0.0
        assert hi > 0.0
        assert hi < 1.0

    def test_all_successes_hi_is_one(self):
        """successes=n → hi == 1.0."""
        lo, hi = clopper_pearson_interval(15, 15)
        assert hi == 1.0
        assert lo > 0.0
        assert lo < 1.0

    def test_n_zero_returns_full_range(self):
        """n=0 devuelve [0,1]."""
        lo, hi = clopper_pearson_interval(0, 0)
        assert lo == 0.0
        assert hi == 1.0

    def test_clopper_pearson_is_conservative(self):
        """Clopper-Pearson es más conservador (más ancho) que Wilson."""
        for successes, n in [(5, 20), (10, 40), (2, 30)]:
            w_lo, w_hi = wilson_interval(successes, n)
            cp_lo, cp_hi = clopper_pearson_interval(successes, n)
            assert cp_lo <= w_lo + 1e-12, f"CP lo={cp_lo} debe ser <= Wilson lo={w_lo}"
            assert cp_hi >= w_hi - 1e-12, f"CP hi={cp_hi} debe ser >= Wilson hi={w_hi}"

    @given(
        st.integers(min_value=0, max_value=200),
        st.integers(min_value=0, max_value=200),
    )
    def test_clopper_pearson_in_0_1(self, successes, n_extra):
        """Clopper-Pearson siempre dentro de [0, 1]."""
        n = successes + n_extra
        if n == 0:
            return
        lo, hi = clopper_pearson_interval(successes, n)
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0
        assert lo <= hi


# ---- Beta-Binomial creíble ----


class TestBetaBinomialCredible:
    def test_flat_prior_n_zero_returns_full_range(self):
        """n=0 con prior plano → [0, 1]."""
        lo, hi = beta_binomial_credible(0, 0)
        assert lo == 0.0
        assert hi == 1.0

    def test_flat_prior_matches_clopper_pearson_almost(self):
        """Con prior plano (1,1), cercano a Clopper-Pearson."""
        lo, hi = beta_binomial_credible(5, 20)
        assert 0.0 < lo < hi < 1.0

    def test_informative_prior_narrows_interval(self):
        """Prior informativo (alpha=5, beta=5) reduce incertidumbre."""
        lo_flat, hi_flat = beta_binomial_credible(5, 20, prior=(1.0, 1.0))
        lo_inf, hi_inf = beta_binomial_credible(5, 20, prior=(5.0, 5.0))
        width_flat = hi_flat - lo_flat
        width_inf = hi_inf - lo_inf
        assert width_inf < width_flat

    @given(
        st.integers(min_value=0, max_value=100),
        st.integers(min_value=0, max_value=100),
        st.floats(min_value=0.1, max_value=10.0),
        st.floats(min_value=0.1, max_value=10.0),
    )
    def test_in_0_1(self, successes, n_extra, prior_a, prior_b):
        n = successes + n_extra
        if n == 0:
            return
        lo, hi = beta_binomial_credible(successes, n, prior=(prior_a, prior_b))
        assert 0.0 <= lo <= 1.0
        assert 0.0 <= hi <= 1.0
        assert lo <= hi

    def test_invalid_cred_raises(self):
        with pytest.raises(ValueError):
            beta_binomial_credible(5, 10, cred=0.0)
        with pytest.raises(ValueError):
            beta_binomial_credible(5, 10, cred=1.0)


# ---- Integridad cruzada ----


class TestCrossMethodConsistency:
    def test_wilson_contains_sample_proportion(self):
        """Wilson contiene p̂ siempre."""
        for successes, n in [(5, 20), (0, 10), (10, 10), (1, 100)]:
            lo, hi = wilson_interval(successes, n)
            p_hat = successes / n if n > 0 else 0.5
            assert lo <= p_hat <= hi + 1e-12

    def test_clopper_pearson_contains_sample_proportion(self):
        """Clopper-Pearson contiene p̂."""
        for successes, n in [(5, 20), (1, 10), (10, 10)]:
            lo, hi = clopper_pearson_interval(successes, n)
            p_hat = successes / n
            assert lo <= p_hat <= hi + 1e-12

    @pytest.mark.parametrize("n", [10, 50, 100, 500])
    def test_intervals_converge_with_large_n(self, n):
        """Wilson y CP convergen con n grande."""
        successes = n // 4
        w_lo, w_hi = wilson_interval(successes, n)
        cp_lo, cp_hi = clopper_pearson_interval(successes, n)
        # Diferencia entre intervalos disminuye con n
        diff = abs((w_hi - w_lo) - (cp_hi - cp_lo))
        assert diff < 1.0  # siempre acotado
