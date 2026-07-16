"""Tests para engine/decisions.py — reglas deterministas.

Casos de referencia:
  - n < min_sample → insufficient_sample
  - p-valor alto → compatible_with_model
  - p-valor bajo → model_not_demonstrated (nunca "bug")
"""

import pytest

from engine.decisions import AnalysisContext, evaluate


class TestEvaluate:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_insufficient_sample(self):
        """n por debajo del umbral → regla insufficient_sample."""
        ctx = AnalysisContext(
            n=5,
            successes=0,
            p0=0.25,
            p_value=1.0,
            effect_size=None,
            method_used="exact_binomial",
            metric="hundo_rate",
            min_sample=30,
        )
        recs = evaluate(ctx)
        assert any(r.rule_key == "insufficient_sample" for r in recs)

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_compatible_with_model(self):
        """p-valor alto y n suficiente → compatible_with_model."""

    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_no_anomaly_conclusion(self):
        """Nunca se genera una recomendación que afirme "bug"."""
        ctx = AnalysisContext(
            n=100,
            successes=1,
            p0=0.25,
            p_value=0.001,
            effect_size=0.24,
            method_used="exact_binomial",
            metric="hundo_rate",
            min_sample=30,
        )
        recs = evaluate(ctx)
        rule_keys = {r.rule_key for r in recs}
        assert "bug_conclusion" not in rule_keys
        assert "anomaly" not in rule_keys


class TestRegisteredRules:
    @pytest.mark.skip(reason="esqueleto M0 — implementar en M5")
    def test_all_rules_have_version(self):
        """Toda regla registrada tiene versión definida."""
        from engine.decisions import REGISTERED_RULES

        assert len(REGISTERED_RULES) > 0
        for _key, version in REGISTERED_RULES.items():
            assert version != ""
