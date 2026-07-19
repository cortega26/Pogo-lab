"""Pruebas estadísticas para el análisis de datos de IV.

Reglas:
- Hundos: binomial exacta (chi² es inválido porque los esperados son minúsculos).
- Uniformidad por stat: chi² solo si todos los esperados ≥ 5; si no, Monte Carlo.
- Independencia Att/Def/HP: G-test o MC.
- Siempre: tamaño de efecto, umbrales mínimos, advertencia de comparaciones múltiples.
"""

import math
from dataclasses import dataclass, field

import numpy as np
from scipy.stats import binomtest, chi2, chisquare


@dataclass
class TestResult:
    """Resultado de una prueba estadística."""

    stat: float
    p_value: float
    effect_size: float | None
    method_used: str
    n: int
    min_expected: float | None = None
    warnings: list[str] = field(default_factory=list)


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
    if n == 0:
        return TestResult(
            stat=0.0,
            p_value=1.0,
            effect_size=0.0,
            method_used="exact_binomial",
            n=0,
        )

    p_hat = successes / n
    result = binomtest(successes, n, p0, alternative="two-sided")

    effect = abs(p_hat - p0)

    return TestResult(
        stat=float(result.statistic),
        p_value=float(result.pvalue),
        effect_size=effect,
        method_used="exact_binomial",
        n=n,
    )


def _compute_cramers_v(chi2_stat: float, n: int, k: int) -> float:
    """Cramér's V a partir de chi², n y número de categorías k."""
    if n <= 0 or k <= 1:
        return 0.0
    return math.sqrt(chi2_stat / (n * (k - 1)))


def _chi2_statistic(observed: list[int], expected: list[float]) -> float:
    """Calcula el estadístico chi² de bondad de ajuste."""
    total = 0.0
    for o, e in zip(observed, expected, strict=True):
        if e > 0:
            total += (o - e) * (o - e) / e
        elif o > 0:
            total += float("inf")
    return total


def _monte_carlo_uniformity_pvalue(
    observed: list[int],
    expected_probs: list[float],
    n_total: int,
    seed: int | None,
    n_sim: int = 10_000,
) -> tuple[float, float]:
    """Calcula el p-valor por Monte Carlo para prueba de uniformidad.

    Returns:
        (p_value, observed_chi2_stat)
    """
    rng = np.random.RandomState(seed)
    total_prob = sum(expected_probs)
    norm_probs = [p / total_prob for p in expected_probs] if total_prob > 0 else expected_probs
    expected_counts = np.array([p * n_total for p in norm_probs])
    observed_chi2 = _chi2_statistic(observed, expected_counts.tolist())

    count_exceed = 0
    for _ in range(n_sim):
        simulated = rng.multinomial(n_total, norm_probs)
        sim_expected = np.array([p * n_total for p in expected_probs])
        sim_chi2 = _chi2_statistic(simulated.tolist(), sim_expected.tolist())
        if sim_chi2 >= observed_chi2:
            count_exceed += 1

    p_value = (count_exceed + 1) / (n_sim + 1)
    return p_value, observed_chi2


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
    if len(counts) != len(expected_probs):
        raise ValueError("counts y expected_probs deben tener la misma longitud")

    n_total = sum(counts)
    if n_total == 0:
        return TestResult(
            stat=0.0,
            p_value=1.0,
            effect_size=0.0,
            method_used="monte_carlo",
            n=0,
            min_expected=0.0,
        )

    expected = [p * n_total for p in expected_probs]
    min_expected = min(expected) if expected else 0.0

    # --- filtrar celdas con esperado > 0 para decidir método ---
    if method == "auto":
        positive_expected = [e for e in expected if e > 0]
        if len(positive_expected) < 2 or all(e >= 5.0 for e in positive_expected):
            method = "chisquare"
        else:
            method = "monte_carlo"

    if method == "chisquare":
        # Si algún observación cae en celda con esperado=0, el modelo
        # se rechaza inmediatamente (chi² diverge).
        zero_expected_nonzero_observed = any(
            e == 0 and c > 0 for e, c in zip(expected, counts, strict=False)
        )
        if zero_expected_nonzero_observed:
            max_v = math.sqrt(len(counts) - 1) if len(counts) > 1 else 0.0
            return TestResult(
                stat=float("inf"),
                p_value=0.0,
                effect_size=max_v,
                method_used="chisquare",
                n=n_total,
                min_expected=min_expected,
            )

        # scipy chisquare falla con esperados=0 → usamos solo las celdas con esperado>0
        non_zero_mask = [e > 0 for e in expected]
        filtered_counts = [c for c, m in zip(counts, non_zero_mask, strict=True) if m]
        filtered_expected = [e for e, m in zip(expected, non_zero_mask, strict=True) if m]
        if sum(filtered_expected) <= 0 or len(filtered_counts) < 2 or sum(filtered_counts) == 0:
            return TestResult(
                stat=0.0,
                p_value=1.0,
                effect_size=0.0,
                method_used="chisquare",
                n=n_total,
                min_expected=min_expected,
            )
        result = chisquare(f_obs=filtered_counts, f_exp=filtered_expected)
        chi2_stat = float(result.statistic)
        p_value = float(result.pvalue)
        effect = _compute_cramers_v(chi2_stat, n_total, len(counts))
        return TestResult(
            stat=chi2_stat,
            p_value=p_value,
            effect_size=effect,
            method_used="chisquare",
            n=n_total,
            min_expected=min_expected,
        )

    if method == "monte_carlo":
        if sum(expected_probs) <= 0:
            return TestResult(
                stat=0.0,
                p_value=1.0,
                effect_size=0.0,
                method_used="monte_carlo",
                n=n_total,
                min_expected=min_expected,
            )
        p_value, chi2_stat = _monte_carlo_uniformity_pvalue(counts, expected_probs, n_total, seed)
        effect = _compute_cramers_v(chi2_stat, n_total, len(counts))
        return TestResult(
            stat=chi2_stat,
            p_value=p_value,
            effect_size=effect,
            method_used="monte_carlo",
            n=n_total,
            min_expected=min_expected,
        )

    raise ValueError(f"Método desconocido: {method}")


def _build_contingency_table(
    pairs: list[tuple[int, int]],
) -> tuple[dict[tuple[int, int], int], int, list[int], list[int], list[int], list[int]]:
    """Construye la tabla de contingencia a partir de pares.

    Returns:
        (table, n, sorted_rows, sorted_cols, row_totals, col_totals)
    """
    row_values: set[int] = set()
    col_values: set[int] = set()
    table: dict[tuple[int, int], int] = {}

    for r, c in pairs:
        row_values.add(r)
        col_values.add(c)
        key = (r, c)
        table[key] = table.get(key, 0) + 1

    n = len(pairs)
    sorted_rows = sorted(row_values)
    sorted_cols = sorted(col_values)

    row_totals = [sum(table.get((rv, cv), 0) for cv in sorted_cols) for rv in sorted_rows]
    col_totals = [sum(table.get((rv, cv), 0) for rv in sorted_rows) for cv in sorted_cols]

    return table, n, sorted_rows, sorted_cols, row_totals, col_totals


def _g_statistic(
    table: dict[tuple[int, int], int],
    n: int,
    sorted_rows: list[int],
    sorted_cols: list[int],
    row_totals: list[int],
    col_totals: list[int],
) -> float:
    """Calcula el estadístico G (log-likelihood ratio)."""
    g = 0.0
    for i, rv in enumerate(sorted_rows):
        for j, cv in enumerate(sorted_cols):
            observed = table.get((rv, cv), 0)
            if observed > 0:
                expected = (row_totals[i] * col_totals[j]) / n if n > 0 else 0.0
                if expected > 0:
                    g += 2.0 * observed * math.log(observed / expected)
    return g


def _g_test_pvalue(g: float, df: int) -> float:
    """p-valor del G-test a partir de la distribución chi²."""
    if df <= 0:
        return 1.0
    return float(1.0 - chi2.cdf(g, df))


def _monte_carlo_independence_pvalue(
    pairs: list[tuple[int, int]],
    observed_g: float,
    seed: int | None,
    sorted_rows: list[int],
    sorted_cols: list[int],
    n_sim: int = 10_000,
) -> float:
    """p-valor por Monte Carlo para prueba de independencia."""
    rng = np.random.RandomState(seed)
    stat2_vals = [p[1] for p in pairs]
    stat2_arr = np.array(stat2_vals)

    count_exceed = 0
    for _ in range(n_sim):
        rng.shuffle(stat2_arr)
        shuffled_pairs = [(pairs[i][0], int(stat2_arr[i])) for i in range(len(pairs))]
        sim_table, _, _, _, sim_row_totals, sim_col_totals = _build_contingency_table(
            shuffled_pairs
        )
        sim_g = _g_statistic(
            sim_table,
            len(pairs),
            sorted_rows,
            sorted_cols,
            sim_row_totals,
            sim_col_totals,
        )
        if sim_g >= observed_g:
            count_exceed += 1

    return (count_exceed + 1) / (n_sim + 1)


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
    n = len(pairs)
    if n == 0:
        return TestResult(
            stat=0.0,
            p_value=1.0,
            effect_size=0.0,
            method_used="g_test",
            n=0,
            warnings=[
                "comparaciones múltiples: si ejecutas varias pruebas de "
                "independencia (Att/Def, Att/HP, Def/HP), considera la "
                "corrección de Holm para controlar la tasa de error familiar."
            ],
        )

    table, n_obs, sorted_rows, sorted_cols, row_totals, col_totals = _build_contingency_table(pairs)

    if method == "auto":
        has_small_expected = False
        for i in range(len(sorted_rows)):
            for j in range(len(sorted_cols)):
                expected = (row_totals[i] * col_totals[j]) / n_obs if n_obs > 0 else 0.0
                if 0 < expected < 5.0:
                    has_small_expected = True
                    break
        method = "monte_carlo" if has_small_expected else "g_test"

    observed_g = _g_statistic(table, n_obs, sorted_rows, sorted_cols, row_totals, col_totals)
    df = (len(sorted_rows) - 1) * (len(sorted_cols) - 1)

    if method == "g_test":
        p_value = _g_test_pvalue(observed_g, df)
        method_used = "g_test"
    elif method == "monte_carlo":
        p_value = _monte_carlo_independence_pvalue(
            pairs,
            observed_g,
            seed,
            sorted_rows,
            sorted_cols,
        )
        method_used = "monte_carlo"
    else:
        raise ValueError(f"Método desconocido: {method}")

    cramers_v = _compute_cramers_v(observed_g, n_obs, min(len(sorted_rows), len(sorted_cols)))

    return TestResult(
        stat=observed_g,
        p_value=p_value,
        effect_size=cramers_v,
        method_used=method_used,
        n=n_obs,
        warnings=[
            "comparaciones múltiples: si ejecutas varias pruebas de "
            "independencia (Att/Def, Att/HP, Def/HP), considera la "
            "corrección de Holm para controlar la tasa de error familiar."
        ],
    )


def min_sample_for(metric: str) -> int:
    """Umbral mínimo de observaciones requerido para una métrica.

    Por debajo del umbral, la inferencia no se muestra y se reemplaza por
    "muestra insuficiente".

    Args:
        metric: Identificador de la métrica ("hundo_rate", "uniformity", etc.).

    Returns:
        Número mínimo de observaciones.
    """
    thresholds: dict[str, int] = {
        "hundo_rate": 50,
        "stat_uniformity": 100,
        "sum_uniformity": 100,
        "independence": 100,
    }
    return thresholds.get(metric, 30)
