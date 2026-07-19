"""Reglas de decisión deterministas y versionadas.

Nunca se usa un LLM en runtime (ADR-0006).
Las recomendaciones son trazables a DecisionRule.key + version.
"""

from dataclasses import dataclass, field

from engine.probability import trades_for_confidence


@dataclass
class Recommendation:
    """Recomendación generada por una regla."""

    rule_key: str
    rule_version: str
    message_key: str
    severity: str  # "info" | "warning" | "critical"
    params: dict = field(default_factory=dict)


@dataclass
class AnalysisContext:
    """Contexto para evaluar reglas de decisión."""

    n: int
    successes: int
    p0: float
    p_value: float
    effect_size: float | None
    method_used: str
    metric: str
    min_sample: int
    ruleset_version: str | None = None
    algorithm_version: str | None = None
    has_mixed_lucky_normal: bool = False
    has_mixed_rulesets: bool = False
    has_mixed_periods: bool = False


IGNORED_WORDS: set[str] = {
    "bug",
    "manipulado",
    "manipulación",
    "anomalía",
    "anomalia",
    "trucado",
    "amañado",
    "amaniado",
    "fraudulento",
}


def _decision_from_rule(rule_key: str, **params: object) -> Recommendation:
    """Construye una recomendación trazable a partir de rule.key + version."""
    version = REGISTERED_RULES.get(rule_key, "unknown")
    severities: dict[str, str] = {
        "insufficient_sample": "warning",
        "separate_lucky_and_normal": "warning",
        "mixed_rulesets_or_periods": "warning",
        "compatible_with_model": "info",
        "model_not_demonstrated": "warning",
        "trades_needed_for_confidence": "info",
        "small_effect_more_data": "info",
        "no_anomaly_conclusion": "info",
    }
    return Recommendation(
        rule_key=rule_key,
        rule_version=version,
        message_key=f"decision.{rule_key}",
        severity=severities.get(rule_key, "info"),
        params={k: v for k, v in params.items() if v is not None},
    )


def evaluate(context: AnalysisContext) -> list[Recommendation]:
    """Evalúa reglas deterministas sobre un resultado de análisis.

    Reglas implementadas:
      - insufficient_sample: n por debajo del umbral mínimo.
      - separate_lucky_and_normal: mezcla de datos Lucky y normales.
      - mixed_rulesets_or_periods: datos de distintos rulesets/periodos.
      - compatible_with_model: p-valor no significativo.
      - model_not_demonstrated: p-valor significativo pero tamaño pequeño.
      - trades_needed_for_confidence: cuántos intercambios para confianza dada.
      - small_effect_more_data: efecto pequeño, más datos necesarios.
      - no_anomaly_conclusion: nunca afirmar "bug"/"manipulado".

    Args:
        context: Contexto del análisis.

    Returns:
        Lista de recomendaciones aplicables, ordenadas por severidad.
    """
    recommendations: list[Recommendation] = []
    alpha = 0.05

    # 1. insufficient_sample
    if context.n < context.min_sample:
        recommendations.append(
            _decision_from_rule(
                "insufficient_sample",
                n=context.n,
                min_sample=context.min_sample,
            )
        )

    # 2. separate_lucky_and_normal
    if context.has_mixed_lucky_normal:
        recommendations.append(
            _decision_from_rule(
                "separate_lucky_and_normal",
                n=context.n,
            )
        )

    # 3. mixed_rulesets_or_periods
    if context.has_mixed_rulesets or context.has_mixed_periods:
        recommendations.append(
            _decision_from_rule(
                "mixed_rulesets_or_periods",
                has_mixed_rulesets=context.has_mixed_rulesets,
                has_mixed_periods=context.has_mixed_periods,
            )
        )

    # 4. compatible_with_model
    if context.p_value >= alpha and context.n >= context.min_sample:
        recommendations.append(
            _decision_from_rule(
                "compatible_with_model",
                p_value=round(context.p_value, 4),
                n=context.n,
            )
        )

    # 5. model_not_demonstrated: p-valor bajo pero no se afirma "demostrado"
    if context.p_value < alpha and context.n >= context.min_sample:
        recommendations.append(
            _decision_from_rule(
                "model_not_demonstrated",
                p_value=round(context.p_value, 4),
                effect_size=(
                    round(context.effect_size, 4) if context.effect_size is not None else None
                ),
            )
        )

    # 6. trades_needed_for_confidence
    if context.metric == "hundo_rate" and context.n >= context.min_sample and context.p0 > 0:
        n_needed = trades_for_confidence(context.p0, 0.95)
        recommendations.append(
            _decision_from_rule(
                "trades_needed_for_confidence",
                p0=context.p0,
                n_observed=context.n,
                n_for_95pct=n_needed,
            )
        )

    # 7. small_effect_more_data
    if (
        context.effect_size is not None
        and context.effect_size < 0.1
        and context.p_value < alpha
        and context.n >= context.min_sample
    ):
        recommendations.append(
            _decision_from_rule(
                "small_effect_more_data",
                effect_size=round(context.effect_size, 4),
                n=context.n,
            )
        )

    # 8. no_anomaly_conclusion: garantía de que ninguna recomendación
    #    afirma "bug", "manipulado" ni "anomalía" como conclusión.
    all_params_text = " ".join(str(v) for r in recommendations for v in r.params.values())
    has_ignored_words = any(
        word in r.message_key.lower() or word in all_params_text.lower()
        for r in recommendations
        for word in IGNORED_WORDS
    )
    if not has_ignored_words:
        recommendations.append(_decision_from_rule("no_anomaly_conclusion"))

    severity_order = {"critical": 0, "warning": 1, "info": 2}
    recommendations.sort(key=lambda r: severity_order.get(r.severity, 99))

    return recommendations


# Reglas registradas con su versión
REGISTERED_RULES: dict[str, str] = {
    "insufficient_sample": "1.0",
    "separate_lucky_and_normal": "1.0",
    "mixed_rulesets_or_periods": "1.0",
    "compatible_with_model": "1.0",
    "model_not_demonstrated": "1.0",
    "trades_needed_for_confidence": "1.0",
    "small_effect_more_data": "1.0",
    "no_anomaly_conclusion": "1.0",
}
