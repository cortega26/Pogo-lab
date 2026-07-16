"""Tests para engine/stat_tests.py — fixtures calculadas a mano.

Casos de referencia:
  - Hundo rate observado = esperado (p-valor alto, compatible)
  - Hundo rate observado ≠ esperado (p-valor bajo, posible anomalía)
  - Uniformidad de valores IV (chi² vs Monte Carlo según n)
"""

import pytest


class TestExactBinomialTest:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_observed_equals_expected(self):
        """Datos generados bajo H0 → p-valor alto."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_observed_far_from_expected(self):
        """Datos lejos de H0 → p-valor bajo."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_small_n(self):
        """n pequeño, successes=1, p0=0.5 → test exacto."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_lucky_hundo_reference(self):
        """Lucky f=12, n=256, esperados=4, p0=1/64."""


class TestUniformityTest:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_chisquare_when_expected_ge_5(self):
        """Todos los esperados ≥ 5 → usa chi²."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_monte_carlo_when_expected_lt_5(self):
        """Algún esperado < 5 → usa Monte Carlo."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_reproducible_with_seed(self):
        """Misma semilla → mismo p-valor MC."""


class TestIndependenceTest:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5 (v1.1)")
    def test_independent_pairs(self):
        """Pares generados independientemente → p-valor alto."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5 (v1.1)")
    def test_dependent_pairs(self):
        """Pares con dependencia artificial → p-valor bajo."""


class TestMinSampleFor:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_metric_has_defined_minimum(self):
        """Toda métrica conocida tiene un umbral > 0."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_unknown_metric_raises(self):
        """Métrica desconocida → KeyError."""
