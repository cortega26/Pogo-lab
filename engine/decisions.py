"""Reglas de decisión deterministas y versionadas.

Nunca se usa un LLM en runtime (ADR-0006).
Las recomendaciones son trazables a DecisionRule.key + version.
"""

from dataclasses import dataclass, field


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
    ...


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
