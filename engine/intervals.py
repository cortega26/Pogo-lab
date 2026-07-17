"""Intervalos de confianza y credibilidad para proporciones.

Por defecto: Wilson (buena cobertura con n pequeño y p extrema).
Disponible: Clopper-Pearson exacto, Beta-Binomial creíble (v1.1).
Descartado: Wald (cobertura pésima con p≈0 y n chico).
"""

import math

from scipy.stats import beta as beta_dist
from scipy.stats import norm as norm_dist


def wilson_interval(successes: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Intervalo de Wilson para la proporción de éxitos.

    Por defecto en la UI. Siempre contenido en [0, 1].

    Args:
        successes: Número de éxitos observados.
        n: Número total de intentos.
        conf: Nivel de confianza (0 < conf < 1).

    Returns:
        (límite_inferior, límite_superior).
    """
    if n == 0:
        return (0.0, 1.0)
    if conf <= 0 or conf >= 1:
        raise ValueError("conf debe estar en (0, 1)")

    p_hat = successes / n
    z = norm_dist.ppf(1.0 - (1.0 - conf) / 2.0)
    z2 = z * z

    denominator = 1.0 + z2 / n
    center = (p_hat + z2 / (2.0 * n)) / denominator
    margin = (z / denominator) * math.sqrt(p_hat * (1.0 - p_hat) / n + z2 / (4.0 * n * n))

    lo = max(0.0, center - margin)
    hi = min(1.0, center + margin)
    return (lo, hi)


def clopper_pearson_interval(successes: int, n: int, conf: float = 0.95) -> tuple[float, float]:
    """Intervalo exacto de Clopper-Pearson (conservador).

    Basado en la distribución Beta (scipy.stats.beta.ppf).
    Disponible para modo "estricto".

    Args:
        successes: Número de éxitos observados.
        n: Número total de intentos.
        conf: Nivel de confianza (0 < conf < 1).

    Returns:
        (límite_inferior, límite_superior).
    """
    if n == 0:
        return (0.0, 1.0)
    if conf <= 0 or conf >= 1:
        raise ValueError("conf debe estar en (0, 1)")

    alpha = 1.0 - conf

    lo = 0.0 if successes == 0 else float(beta_dist.ppf(alpha / 2.0, successes, n - successes + 1))

    hi = (
        1.0
        if successes == n
        else float(beta_dist.ppf(1.0 - alpha / 2.0, successes + 1, n - successes))
    )

    return (lo, hi)


def beta_binomial_credible(
    successes: int,
    n: int,
    cred: float = 0.95,
    prior: tuple[float, float] = (1.0, 1.0),
) -> tuple[float, float]:
    """Intervalo creíble Beta-Binomial (opcional, v1.1).

    Para comunicar "compatible con" en muestras pequeñas. No se usa por defecto.

    Args:
        successes: Número de éxitos observados.
        n: Número total de intentos.
        cred: Nivel de credibilidad (0 < cred < 1).
        prior: (alpha, beta) del prior Beta.

    Returns:
        (límite_inferior, límite_superior).
    """
    if n == 0:
        return (0.0, 1.0)
    if cred <= 0 or cred >= 1:
        raise ValueError("cred debe estar en (0, 1)")

    alpha = 1.0 - cred
    prior_a, prior_b = prior
    post_a = prior_a + successes
    post_b = prior_b + n - successes

    lo = float(beta_dist.ppf(alpha / 2.0, post_a, post_b))
    hi = float(beta_dist.ppf(1.0 - alpha / 2.0, post_a, post_b))

    return (lo, hi)
