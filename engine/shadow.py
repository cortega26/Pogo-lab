"""Comparativa Shadow vs Purified en Pokémon GO (CALC019).

Procedencia: comunidad (GamePress, alta confianza).
Shadow: +20 % ataque en PvE, −20 % defensa, power-ups ×1.2 en stardust.
Purified: stats normales, power-ups ×0.9 en stardust y caramelos.
"""

from __future__ import annotations

from dataclasses import dataclass

from engine.costs import power_up_cost
from engine.stats import cp, cpm_for_level, hp

SHADOW_ATK_MULTIPLIER = 1.2
SHADOW_DEF_MULTIPLIER = 0.833


@dataclass(frozen=True)
class ShadowComparison:
    """Comparación de CP, HP, costo y daño efectivo entre Shadow y Purified."""

    species_name: str
    level: float
    iv_atk: int
    iv_def: int
    iv_stam: int

    # Purified
    cp_purified: int
    hp_purified: int
    dust_purified: int
    candy_purified: int

    # Shadow
    cp_shadow: int
    hp_shadow: int
    dust_shadow: int
    candy_shadow: int

    # Daño efectivo PvE (ATK_eff comparada)
    atk_purified: float
    atk_shadow: float
    atk_ratio: float  # shadow / purified

    def shadow_damage_advantage_pct(self) -> float:
        """Ventaja porcentual de daño del Shadow sobre el Purified."""
        return round((self.atk_ratio - 1.0) * 100, 1)


def compare_shadow_purified(
    base_atk: int,
    base_def: int,
    base_stam: int,
    iv_atk: int,
    iv_def: int,
    iv_stam: int,
    level: float,
    from_level: float = 1.0,
    species_name: str = "",
) -> ShadowComparison:
    """Compara Shadow vs Purified para una especie, IVs y nivel dados.

    Args:
        base_atk, base_def, base_stam: Stats base de la especie (Game Master).
        iv_atk, iv_def, iv_stam: IVs del ejemplar.
        level: Nivel actual del Pokémon.
        from_level: Nivel base para calcular costos de power-up.
        species_name: Nombre de la especie (para el resultado).

    Returns:
        ShadowComparison con todos los valores comparativos.
    """
    cpm = cpm_for_level(level)

    # Purified
    cp_p = cp(base_atk, base_def, base_stam, iv_atk, iv_def, iv_stam, cpm)
    hp_p = hp(base_stam, iv_stam, cpm)
    cost_p = power_up_cost(from_level, level)
    dust_p = round(cost_p.total_stardust * 0.9)
    candy_p = round(cost_p.total_candy * 0.9)

    # Shadow
    cp_s = cp(base_atk, base_def, base_stam, iv_atk, iv_def, iv_stam, cpm)
    hp_s = hp(base_stam, iv_stam, cpm)
    cost_s = power_up_cost(from_level, level, is_shadow=True)

    # Ataque efectivo en PvE
    atk_p = (base_atk + iv_atk) * cpm
    atk_s = atk_p * SHADOW_ATK_MULTIPLIER

    return ShadowComparison(
        species_name=species_name,
        level=level,
        iv_atk=iv_atk,
        iv_def=iv_def,
        iv_stam=iv_stam,
        cp_purified=cp_p,
        hp_purified=hp_p,
        dust_purified=dust_p,
        candy_purified=candy_p,
        cp_shadow=cp_s,
        hp_shadow=hp_s,
        dust_shadow=cost_s.total_stardust,
        candy_shadow=cost_s.total_candy,
        atk_purified=round(atk_p, 1),
        atk_shadow=round(atk_s, 1),
        atk_ratio=SHADOW_ATK_MULTIPLIER,
    )
