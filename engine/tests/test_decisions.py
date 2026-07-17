"""Tests para engine/decisions.py — reglas deterministas.

Casos de referencia:
  - n < min_sample → insufficient_sample
  - p-valor alto → compatible_with_model
  - p-valor bajo → model_not_demonstrated (nunca "bug")
  - Cada recomendación trazable a rule.key + version.
  - Lenguaje honesto: nunca "bug"/"manipulado"/"anomalía" en output.
"""

from engine.decisions import (
    REGISTERED_RULES,
    AnalysisContext,
    evaluate,
)


def _make_context(**overrides: object) -> AnalysisContext:
    """Construye un AnalysisContext con valores por defecto."""
    kwargs: dict[str, object] = {
        "n": 100,
        "successes": 25,
        "p0": 0.25,
        "p_value": 0.5,
        "effect_size": 0.0,
        "method_used": "exact_binomial",
        "metric": "hundo_rate",
        "min_sample": 50,
        "has_mixed_lucky_normal": False,
        "has_mixed_rulesets": False,
        "has_mixed_periods": False,
    }
    kwargs.update(overrides)
    return AnalysisContext(**kwargs)  # type: ignore[arg-type]


class TestInsufficientSample:
    def test_n_below_threshold(self):
        """n por debajo del umbral → insufficient_sample."""
        ctx = _make_context(n=5, min_sample=30)
        recs = evaluate(ctx)
        assert any(r.rule_key == "insufficient_sample" for r in recs)

    def test_n_above_threshold_no_insufficient(self):
        """n suficiente no genera insufficient_sample."""
        ctx = _make_context(n=100, min_sample=30)
        recs = evaluate(ctx)
        assert not any(r.rule_key == "insufficient_sample" for r in recs)

    def test_insufficient_sample_params(self):
        """La recomendación incluye n y min_sample en params."""
        ctx = _make_context(n=5, min_sample=30)
        recs = evaluate(ctx)
        rec = next(r for r in recs if r.rule_key == "insufficient_sample")
        assert rec.params["n"] == 5
        assert rec.params["min_sample"] == 30


class TestSeparateLuckyAndNormal:
    def test_mixed_lucky_normal_generates_warning(self):
        """has_mixed_lucky_normal=True → separate_lucky_and_normal."""
        ctx = _make_context(has_mixed_lucky_normal=True)
        recs = evaluate(ctx)
        assert any(r.rule_key == "separate_lucky_and_normal" for r in recs)

    def test_not_mixed_no_warning(self):
        """has_mixed_lucky_normal=False → no genera warning."""
        ctx = _make_context(has_mixed_lucky_normal=False)
        recs = evaluate(ctx)
        assert not any(r.rule_key == "separate_lucky_and_normal" for r in recs)


class TestMixedRulesets:
    def test_mixed_rulesets_generates_warning(self):
        """has_mixed_rulesets=True → mixed_rulesets_or_periods."""
        ctx = _make_context(has_mixed_rulesets=True)
        recs = evaluate(ctx)
        assert any(r.rule_key == "mixed_rulesets_or_periods" for r in recs)

    def test_mixed_periods_generates_warning(self):
        """has_mixed_periods=True → mixed_rulesets_or_periods."""
        ctx = _make_context(has_mixed_periods=True)
        recs = evaluate(ctx)
        assert any(r.rule_key == "mixed_rulesets_or_periods" for r in recs)


class TestCompatibleWithModel:
    def test_high_p_value_compatible(self):
        """p-valor alto y n suficiente → compatible_with_model."""
        ctx = _make_context(p_value=0.8, n=100, min_sample=50)
        recs = evaluate(ctx)
        assert any(r.rule_key == "compatible_with_model" for r in recs)

    def test_low_n_no_compatible(self):
        """n insuficiente → no compatible_with_model (primero insufficient_sample)."""
        ctx = _make_context(p_value=0.8, n=5, min_sample=50)
        recs = evaluate(ctx)
        assert not any(r.rule_key == "compatible_with_model" for r in recs)


class TestModelNotDemonstrated:
    def test_low_p_value_model_not_demonstrated(self):
        """p-valor < 0.05 y n suficiente → model_not_demonstrated."""
        ctx = _make_context(p_value=0.01, n=100, min_sample=50)
        recs = evaluate(ctx)
        assert any(r.rule_key == "model_not_demonstrated" for r in recs)

    def test_low_p_value_includes_effect_size(self):
        """model_not_demonstrated incluye effect_size en params."""
        ctx = _make_context(p_value=0.001, effect_size=0.24, n=100, min_sample=50)
        recs = evaluate(ctx)
        rec = next(r for r in recs if r.rule_key == "model_not_demonstrated")
        assert "p_value" in rec.params
        assert "effect_size" in rec.params

    def test_low_n_no_model_not_demonstrated(self):
        """No se aplica con n insuficiente."""
        ctx = _make_context(p_value=0.01, n=5, min_sample=50)
        recs = evaluate(ctx)
        assert not any(r.rule_key == "model_not_demonstrated" for r in recs)


class TestTradesNeededForConfidence:
    def test_hundo_rate_includes_trades_needed(self):
        """Métrica hundo_rate con n suficiente → trades_needed_for_confidence."""
        ctx = _make_context(metric="hundo_rate", p0=1.0 / 64.0, n=200, min_sample=50)
        recs = evaluate(ctx)
        assert any(r.rule_key == "trades_needed_for_confidence" for r in recs)

    def test_non_hundo_rate_no_trades_needed(self):
        """Otras métricas no generan trades_needed_for_confidence."""
        ctx = _make_context(metric="stat_uniformity")
        recs = evaluate(ctx)
        assert not any(r.rule_key == "trades_needed_for_confidence" for r in recs)

    def test_trades_needed_includes_n_for_95(self):
        """Incluye n_for_95pct en params."""
        ctx = _make_context(metric="hundo_rate", p0=1.0 / 64.0, n=200, min_sample=50)
        recs = evaluate(ctx)
        rec = next(r for r in recs if r.rule_key == "trades_needed_for_confidence")
        assert "n_for_95pct" in rec.params


class TestSmallEffectMoreData:
    def test_small_effect_generates_info(self):
        """Efecto pequeño (<0.1) y p-valor bajo → small_effect_more_data."""
        ctx = _make_context(effect_size=0.05, p_value=0.01, n=100, min_sample=50)
        recs = evaluate(ctx)
        assert any(r.rule_key == "small_effect_more_data" for r in recs)

    def test_large_effect_no_small_effect(self):
        """Efecto grande (>0.1) no genera small_effect_more_data."""
        ctx = _make_context(effect_size=0.3, p_value=0.01, n=100, min_sample=50)
        recs = evaluate(ctx)
        assert not any(r.rule_key == "small_effect_more_data" for r in recs)

    def test_high_p_value_no_small_effect(self):
        """p-valor alto no genera small_effect_more_data."""
        ctx = _make_context(effect_size=0.05, p_value=0.5, n=100, min_sample=50)
        recs = evaluate(ctx)
        assert not any(r.rule_key == "small_effect_more_data" for r in recs)

    def test_effect_size_none_no_small_effect(self):
        """effect_size=None no genera small_effect_more_data."""
        ctx = _make_context(effect_size=None, p_value=0.01, n=100, min_sample=50)
        recs = evaluate(ctx)
        assert not any(r.rule_key == "small_effect_more_data" for r in recs)


class TestNoAnomalyConclusion:
    def test_never_contains_bug_or_manipulado_or_anomalia(self):
        """Output nunca contiene 'bug', 'manipulado' ni 'anomalía' en message_keys ni params."""
        for p_val, eff, n in [
            (0.001, 0.5, 500),
            (0.0001, 0.3, 1000),
            (0.99, 0.0, 100),
        ]:
            ctx = _make_context(p_value=p_val, effect_size=eff, n=n, min_sample=50)
            recs = evaluate(ctx)
            forbidden = {"bug", "manipulado", "manipulación", "anomalía", "anomalia"}
            for rec in recs:
                all_text = (
                    rec.rule_key.lower()
                    + " "
                    + rec.message_key.lower()
                    + " "
                    + " ".join(str(v).lower() for v in rec.params.values())
                )
                for word in forbidden:
                    assert word not in all_text, (
                        f"Encontrado '{word}' en recomendación {rec.rule_key}: {all_text}"
                    )

    def test_no_anomaly_conclusion_rule_present(self):
        """La regla no_anomaly_conclusion siempre se incluye si no hay palabras prohibidas."""
        ctx = _make_context()
        recs = evaluate(ctx)
        assert any(r.rule_key == "no_anomaly_conclusion" for r in recs)


class TestTraceability:
    def test_every_recommendation_has_version(self):
        """Cada recomendación referencia rule.key + version de REGISTERED_RULES."""
        ctx = _make_context(n=5, min_sample=30)
        recs = evaluate(ctx)
        for rec in recs:
            assert rec.rule_key in REGISTERED_RULES, f"rule_key={rec.rule_key} no registrada"
            assert rec.rule_version == REGISTERED_RULES[rec.rule_key], (
                f"Version mismatch para {rec.rule_key}"
            )

    def test_recommendations_ordered_by_severity(self):
        """Recomendaciones ordenadas: critical antes de warning antes de info."""
        ctx = _make_context(
            n=5,
            min_sample=30,
            has_mixed_lucky_normal=True,
        )
        recs = evaluate(ctx)
        severities = [r.severity for r in recs]
        severity_order = {"critical": 0, "warning": 1, "info": 2}
        for i in range(len(severities) - 1):
            assert severity_order[severities[i]] <= severity_order[severities[i + 1]], (
                f"Orden incorrecto: {severities}"
            )


class TestRegisteredRules:
    def test_all_rules_have_version(self):
        """Toda regla registrada tiene versión definida."""
        assert len(REGISTERED_RULES) == 8
        for key, version in REGISTERED_RULES.items():
            assert version == "1.0", f"Versión inesperada para {key}: {version}"

    def test_all_rules_covered_by_evaluate(self):
        """Todas las reglas registradas pueden generarse por evaluate."""
        ctxes = [
            _make_context(n=5, min_sample=30),
            _make_context(has_mixed_lucky_normal=True),
            _make_context(has_mixed_rulesets=True),
            _make_context(p_value=0.8),
            _make_context(p_value=0.01, effect_size=0.05),
            _make_context(metric="hundo_rate"),
        ]
        all_keys: set[str] = set()
        for ctx in ctxes:
            for rec in evaluate(ctx):
                all_keys.add(rec.rule_key)

        missing = {
            "insufficient_sample",
            "separate_lucky_and_normal",
            "mixed_rulesets_or_periods",
            "compatible_with_model",
            "model_not_demonstrated",
            "trades_needed_for_confidence",
            "small_effect_more_data",
            "no_anomaly_conclusion",
        } - all_keys
        assert not missing, f"Reglas no cubiertas: {missing}"


class TestEdgeCases:
    def test_n_zero(self):
        """n=0 con min_sample>0 → insufficient_sample y no_anomaly_conclusion."""
        ctx = _make_context(n=0, successes=0, min_sample=30, p_value=1.0)
        recs = evaluate(ctx)
        keys = {r.rule_key for r in recs}
        assert "insufficient_sample" in keys
        assert "no_anomaly_conclusion" in keys

    def test_p_zero(self):
        """p0=0 no causa división por cero en trades_needed."""
        ctx = _make_context(metric="hundo_rate", p0=0.0)
        recs = evaluate(ctx)
        trades = [r for r in recs if r.rule_key == "trades_needed_for_confidence"]
        assert len(trades) <= 1  # puede no generarse si p0=0

    def test_effect_size_none_handled(self):
        """effect_size=None no rompe ninguna regla."""
        ctx = _make_context(effect_size=None, p_value=0.001, n=100)
        recs = evaluate(ctx)
        assert any(r.rule_key == "model_not_demonstrated" for r in recs)
