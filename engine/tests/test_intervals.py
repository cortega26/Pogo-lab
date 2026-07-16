"""Tests para engine/intervals.py — fixtures calculadas a mano.

Casos de referencia:
  - Wilson con n=100, successes=50, conf=0.95
  - Clopper-Pearson con n=1, successes=0 (caso extremo)
  - consistency: Wilson y CP coinciden en el límite de n grande
"""

import pytest


class TestWilsonInterval:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_symmetric_case(self):
        """n=100, successes=50, conf=0.95 → intervalo alrededor de 0.5."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_zero_successes(self):
        """successes=0 → límite inferior = 0."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_all_successes(self):
        """successes=n → límite superior = 1."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_probability_in_0_1(self):
        """Intervalo siempre contenido en [0, 1]."""


class TestClopperPearsonInterval:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_conservative_vs_wilson(self):
        """CP es más conservador (más ancho) que Wilson."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_zero_successes(self):
        """successes=0 → [0, 1 - (a/2)^(1/n)]."""


class TestBetaBinomialCredible:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5 (v1.1)")
    def test_uniform_prior_matches_binomial_likelihood(self):
        """Prior (1,1) → posterior Beta(1+s, 1+n-s)."""


class TestConsistency:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_large_n_agreement(self):
        """Wilson y CP convergen para n grande (ej. n=10000)."""
