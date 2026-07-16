"""Pruebas estadísticas para el análisis de datos de IV.

Reglas:
- Hundos: binomial exacta (chi² es inválido porque los esperados son minúsculos).
- Uniformidad por stat: chi² solo si todos los esperados ≥ 5; si no, Monte Carlo.
- Independencia Att/Def/HP: G-test o MC.
- Siempre: tamaño de efecto, umbrales mínimos, advertencia de comparaciones múltiples.
"""

from dataclasses import dataclass


@dataclass
class TestResult:
    """Resultado de una prueba estadística."""

    stat: float
    p_value: float
    effect_size: float | None
    method_used: str
    n: int
    min_expected: float | None = None


def exact_binomial_test(successes: int, n: int, p0: float) -> TestResult:
    """Prueba binomial exacta (bilateral) vía scipy.stats.binomtest.

    Para hundos y eventos raros. Chi² no debe usarse aquí.

    Args:
        successes: Número de éxitos observados.
        n: Número total de intentos.
        p0: Probabilidad bajo H0.

    Returns:
        TestResult con stat, p_value, effect_size (diferencia absoluta), method_used="exact_binomial".
    """
    ...


def uniformity_test(
    counts: list[int],
    expected_probs: list[float],
    method: str = "auto",
    seed: int | None = None,
) -> TestResult:
    """Bondad de ajuste para evaluar uniformidad de valores de IV.

    Usa chi² si todos los esperados ≥ 5; si no, Monte Carlo con seed fijo.

    Args:
        counts: Frecuencias observadas por categoría.
        expected_probs: Probabilidades esperadas bajo H0 (deben sumar 1).
        method: "auto" | "chisquare" | "monte_carlo".
        seed: Semilla para Monte Carlo (fija para reproducibilidad).

    Returns:
        TestResult con method_used="chisquare" o "monte_carlo", effect_size (Cramér's V).
    """
    ...


def independence_test(
    pairs: list[tuple[int, int]],
    method: str = "auto",
    seed: int | None = None,
) -> TestResult:
    """Prueba de independencia entre pares de stats (Att/Def, Att/HP, Def/HP).

    G-test o Monte Carlo. Incluye advertencia de comparaciones múltiples (Holm).

    Args:
        pairs: Lista de pares (valor_stat1, valor_stat2).
        method: "auto" | "g_test" | "monte_carlo".
        seed: Semilla para reproducibilidad.

    Returns:
        TestResult con method_used, effect_size (Cramér's V).
    """
    ...


def min_sample_for(metric: str) -> int:
    """Umbral mínimo de observaciones requerido para una métrica.

    Por debajo del umbral, la inferencia no se muestra y se reemplaza por
    "muestra insuficiente".

    Args:
        metric: Identificador de la métrica ("hundo_rate", "uniformity", etc.).

    Returns:
        Número mínimo de observaciones.
    """
    ...
