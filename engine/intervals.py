"""Intervalos de confianza y credibilidad para proporciones.

Por defecto: Wilson (buena cobertura con n pequeño y p extrema).
Disponible: Clopper-Pearson exacto, Beta-Binomial creíble (v1.1).
Descartado: Wald (cobertura pésima con p≈0 y n chico).
"""


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
    ...


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
    ...


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
    ...
