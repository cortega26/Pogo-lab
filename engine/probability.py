"""Modelo teórico de probabilidad para intercambios de IV en Pokémon GO.

Modelo: re-roll uniforme en [f, 15], sin clamping ni pico en el piso.
Independencia Att/Def/HP tratada como supuesto (S3) — la parte empírica lo prueba.
"""

from fractions import Fraction


def possible_values(f: int) -> int:
    """Número de valores posibles para un stat dado un piso `f`.

    k = 16 - f  (para 0 <= f <= 15).
    """
    ...


def p_specific_iv(f: int) -> Fraction:
    """Probabilidad de un valor concreto de IV (≥ f) en un stat.

    P = 1/k, donde k = 16 - f.
    """
    ...


def p_stat_at_least(f: int, t: int) -> Fraction:
    """Probabilidad de que un stat individual sea ≥ t, dado piso f.

    Válido solo para t ≥ f. P = (16 - t) / k.
    """
    ...


def p_hundo(f: int) -> Fraction:
    """Probabilidad de hundo (15/15/15) con piso f.

    P = (1/k)^3, donde k = 16 - f. Asume independencia Att/Def/HP (S3).
    """
    ...


def iv_sum_distribution(f: int) -> dict[int, Fraction]:
    """Distribución de la suma de IV (Att+Def+HP) como convolución de tres uniformes [f, 15].

    Soporte: [3f, 45]. Σ = 1 exacto.
    """
    ...


def p_sum_at_least(f: int, s: int) -> Fraction:
    """Probabilidad de que la suma de IV sea ≥ s, dado piso f.

    Cola de `iv_sum_distribution`.
    """
    ...


def p_at_least_one(p: float, n: int) -> float:
    """Probabilidad de al menos un éxito en n intentos independientes.

    P = 1 - (1 - p)^n.
    """
    ...


def p_zero(p: float, n: int) -> float:
    """Probabilidad de cero éxitos en n intentos.

    P = (1 - p)^n.
    """
    ...


def expected_successes(p: float, n: int) -> float:
    """Número esperado de éxitos en n intentos.

    E = n * p.
    """
    ...


def outcome_distribution(p: float, n: int) -> list[float]:
    """Distribución binomial del número de éxitos en n intentos.

    Devuelve probabilidades P(X=i) para i = 0..n.
    """
    ...


def trades_for_confidence(p: float, c: float) -> int:
    """Menor número de intercambios n tal que P(al menos 1 éxito) ≥ c.

    n = ceil(ln(1 - c) / ln(1 - p)).
    """
    ...


def per_trade_success_prob(f: int, target: dict) -> float:
    """Probabilidad de éxito por intercambio según el objetivo del usuario.

    `target` especifica tipo de objetivo:
      - {"kind": "hundo"}
      - {"kind": "stat_min", "threshold": t}
      - {"kind": "sum_min", "threshold": s}

    El piso `f` proviene del RuleParameter (no del código).
    """
    ...
