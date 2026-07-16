"""Modelo teórico de probabilidad para intercambios de IV en Pokémon GO.

Modelo: re-roll uniforme en [f, 15], sin clamping ni pico en el piso.
Independencia Att/Def/HP tratada como supuesto (S3) — la parte empírica lo prueba.
"""

import math
from fractions import Fraction
from itertools import product


def possible_values(f: int) -> int:
    """Número de valores posibles para un stat dado un piso `f`.

    k = 16 - f  (para 0 <= f <= 15).
    """
    return 16 - f


def p_specific_iv(f: int) -> Fraction:
    """Probabilidad de un valor concreto de IV (>= f) en un stat.

    P = 1/k, donde k = 16 - f.
    """
    k = possible_values(f)
    return Fraction(1, k)


def p_stat_at_least(f: int, t: int) -> Fraction:
    """Probabilidad de que un stat individual sea >= t, dado piso f.

    Si t <= f, P = 1 (todos los valores estan en [f,15], luego >= f >= t).
    Si t > 15, P = 0. En otro caso P = (16 - t) / k.
    """
    if t <= f:
        return Fraction(1, 1)
    if t > 15:
        return Fraction(0, 1)
    k = possible_values(f)
    n_above = 16 - t
    return Fraction(n_above, k)


def p_hundo(f: int) -> Fraction:
    """Probabilidad de hundo (15/15/15) con piso f.

    P = (1/k)^3, donde k = 16 - f. Asume independencia Att/Def/HP (S3).
    """
    k = possible_values(f)
    return Fraction(1, k**3)


def iv_sum_distribution(f: int) -> dict[int, Fraction]:
    """Distribucion de la suma de IV (Att+Def+HP) como convolucion de tres uniformes [f, 15].

    Soporte: [3f, 45]. Sigma = 1 exacto.
    """
    k = possible_values(f)
    values = list(range(f, 16))
    total = Fraction(0)
    dist: dict[int, Fraction] = {}
    for a, b, c in product(values, repeat=3):
        s = a + b + c
        dist[s] = dist.get(s, Fraction(0)) + Fraction(1, 1)
        total += Fraction(1, 1)
    denom = Fraction(k**3, 1)
    return {s: count / denom for s, count in dist.items()}


def p_sum_at_least(f: int, s: int) -> Fraction:
    """Probabilidad de que la suma de IV sea >= s, dado piso f.

    Cola de `iv_sum_distribution`.
    """
    dist = iv_sum_distribution(f)
    total = Fraction(0, 1)
    for sum_val, prob in dist.items():
        if sum_val >= s:
            total += prob
    return total


def p_at_least_one(p: float, n: int) -> float:
    """Probabilidad de al menos un exito en n intentos independientes.

    P = 1 - (1 - p)^n.
    """
    return 1.0 - (1.0 - p) ** n


def p_zero(p: float, n: int) -> float:
    """Probabilidad de cero exitos en n intentos.

    P = (1 - p)^n.
    """
    return (1.0 - p) ** n


def expected_successes(p: float, n: int) -> float:
    """Numero esperado de exitos en n intentos.

    E = n * p.
    """
    return n * p


def outcome_distribution(p: float, n: int) -> list[float]:
    """Distribucion binomial del numero de exitos en n intentos.

    Devuelve probabilidades P(X=i) para i = 0..n.
    """
    result: list[float] = []
    for k in range(n + 1):
        prob = math.comb(n, k) * (p**k) * ((1.0 - p) ** (n - k))
        result.append(prob)
    return result


def trades_for_confidence(p: float, c: float) -> int:
    """Menor numero de intercambios n tal que P(al menos 1 exito) >= c.

    n = ceil(ln(1 - c) / ln(1 - p)).  Usa un epsilon para compensar
    errores de redondeo de coma flotante cuando el cociente cae justo
    por debajo de un entero.
    """
    if p >= 1.0:
        return 1
    if p <= 0.0 or c <= 0.0:
        return 0
    if c >= 1.0:
        c = 1.0 - 1e-15
    ratio = math.log(1.0 - c) / math.log(1.0 - p)
    n = math.ceil(ratio - 1e-12)
    return max(n, 0)


def per_trade_success_prob(f: int, target: dict) -> float:
    """Probabilidad de exito por intercambio segun el objetivo del usuario.

    `target` especifica tipo de objetivo:
      - {"kind": "hundo"}
      - {"kind": "stat_min", "threshold": t}
      - {"kind": "sum_min", "threshold": s}

    El piso `f` proviene del RuleParameter (no del codigo).
    """
    kind = target["kind"]
    if kind == "hundo":
        return float(p_hundo(f))
    if kind == "stat_min":
        return float(p_stat_at_least(f, int(target["threshold"])))
    if kind == "sum_min":
        return float(p_sum_at_least(f, int(target["threshold"])))
    raise ValueError(f"Tipo de objetivo desconocido: {kind}")
