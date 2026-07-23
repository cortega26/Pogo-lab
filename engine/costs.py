"""Costos de power-up (stardust, caramelos, caramelos XL).

Procedencia: comunidad (GamePress / PvPoke), verificada contra el juego.
Modelo: 4 power-ups (2 niveles) por escalón de costo.
Lucky: 50 % descuento en stardust. Shadow: 20 % recargo en stardust.
"""

from __future__ import annotations

from dataclasses import dataclass

# ─── Costos por power-up ─────────────────────────────────────────────────────
# Cada escalón cubre 4 power-ups (2 niveles).
# El array define (stardust, caramelos, caramelos_xl) por power-up.
# La secuencia se repite 4 veces para cada valor.

_DUST_TIERS: list[int] = [
    200,
    400,
    600,
    800,
    1000,
    1300,
    1600,
    1900,
    2200,
    2500,
    3000,
    3500,
    4000,
    4500,
    5000,
    6000,
    7000,
    8000,
    9000,
    10000,
    11000,
    12000,
    13000,
    14000,
    15000,
    17500,
    20000,
    22500,
    25000,
    30000,
]

_CANDY_TIERS: list[int] = [
    1,
    1,
    1,
    1,
    1,
    2,
    2,
    2,
    2,
    2,
    3,
    3,
    3,
    3,
    3,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    4,
    5,
    5,
    5,
    6,
]

_XL_TIERS: list[int] = [
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    0,
    1,
    1,
    1,
    2,
    2,
    2,
    3,
]

_POWERUPS_PER_TIER = 4

LUCKY_STARDUST_MULTIPLIER = 0.5
SHADOW_STARDUST_MULTIPLIER = 1.2


def _cost_for_powerup(pu_index: int) -> tuple[int, int, int]:
    """Costo para el power-up número `pu_index` (0-indexado).

    Args:
        pu_index: Índice del power-up (0 = L1.0→L1.5).

    Returns:
        (polvo, caramelos, caramelos_xl).
    """
    tier = pu_index // _POWERUPS_PER_TIER
    if tier >= len(_DUST_TIERS):
        return (30000, 6, 3)
    return (_DUST_TIERS[tier], _CANDY_TIERS[tier], _XL_TIERS[tier])


def _level_to_powerup_index(level: float) -> int:
    """Convierte un nivel a su índice de power-up (0-indexado).

    El nivel 1.0 corresponde al power-up 0 (no se ha aplicado ninguno).
    El nivel 1.5 corresponde a haber aplicado 1 power-up.
    """
    return round((level - 1.0) * 2)


@dataclass(frozen=True)
class PowerUpCost:
    """Resultado del cálculo de costo de power-ups."""

    total_stardust: int
    total_candy: int
    total_candy_xl: int
    power_ups: int
    from_level: float
    to_level: float


def power_up_cost(
    from_level: float,
    to_level: float,
    *,
    is_lucky: bool = False,
    is_shadow: bool = False,
) -> PowerUpCost:
    """Calcula el costo total de subir un Pokémon de `from_level` a `to_level`.

    Args:
        from_level: Nivel inicial (1.0 a 55.0, en incrementos de 0.5).
        to_level: Nivel objetivo (>= from_level).
        is_lucky: Si es True, aplica 50 % descuento en stardust.
        is_shadow: Si es True, aplica 20 % recargo en stardust.

    Returns:
        PowerUpCost con totales.

    Raises:
        ValueError: Si from_level > to_level.
    """
    if from_level > to_level:
        raise ValueError(f"from_level ({from_level}) no puede ser mayor que to_level ({to_level})")

    start_pu = _level_to_powerup_index(from_level)
    end_pu = _level_to_powerup_index(to_level)

    total_dust = 0
    total_candy = 0
    total_xl = 0

    for pu in range(start_pu, end_pu):
        d, c, x = _cost_for_powerup(pu)
        total_dust += d
        total_candy += c
        total_xl += x

    if is_lucky:
        total_dust = round(total_dust * LUCKY_STARDUST_MULTIPLIER)
    if is_shadow:
        total_dust = round(total_dust * SHADOW_STARDUST_MULTIPLIER)

    return PowerUpCost(
        total_stardust=total_dust,
        total_candy=total_candy,
        total_candy_xl=total_xl,
        power_ups=end_pu - start_pu,
        from_level=from_level,
        to_level=to_level,
    )


def power_ups_needed(from_level: float, to_level: float) -> int:
    """Número de power-ups (incrementos de 0.5 nivel) entre dos niveles."""
    return _level_to_powerup_index(to_level) - _level_to_powerup_index(from_level)
