"""Matriz de efectividad de tipos en Pokémon GO.

Procedencia: oficial (mecánica heredada de los juegos principales).
18 tipos × 18 tipos. Los multiplicadores de GO difieren de MSG:
  - Súper efectivo: ×1.6
  - Doble súper efectivo: ×1.6² = ×2.56
  - Poco efectivo: ×0.625
  - Doble poco efectivo: ×0.625² = ×0.390625
  - Inmune: ×0.39 (en GO no hay inmunidad real, usa ×0.39)
"""

from __future__ import annotations

from enum import Enum


class PokemonType(Enum):
    NORMAL = "normal"
    FIRE = "fire"
    WATER = "water"
    ELECTRIC = "electric"
    GRASS = "grass"
    ICE = "ice"
    FIGHTING = "fighting"
    POISON = "poison"
    GROUND = "ground"
    FLYING = "flying"
    PSYCHIC = "psychic"
    BUG = "bug"
    ROCK = "rock"
    GHOST = "ghost"
    DRAGON = "dragon"
    DARK = "dark"
    STEEL = "steel"
    FAIRY = "fairy"


# ─── Constantes de efectividad en GO ─────────────────────────────────────────

SUPER_EFFECTIVE: float = 1.6
NOT_VERY_EFFECTIVE: float = 0.625
IMMUNE: float = 0.390625  # GO no tiene inmunidad real; usa doble resistencia


# ─── Matriz de efectividad ───────────────────────────────────────────────────
# TYPE_CHART[attacking][defending] = multiplicador en GO (1.0 = neutro).
# La diagonal siempre es 1.0.
# Fuente: mecánica oficial de Pokémon, adaptada a GO (FOR027).

_TYPE_CHART_DATA: dict[PokemonType, dict[PokemonType, float]] = {}

# Se construye línea por línea para claridad y verificación.

# Normal: inmune a Ghost, débil a Fighting/Rock/Steel (no en GO: normal es neutro contra todos excepto Ghost)
_TYPE_CHART_DATA[PokemonType.NORMAL] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.NORMAL][PokemonType.ROCK] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.NORMAL][PokemonType.STEEL] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.NORMAL][PokemonType.GHOST] = IMMUNE

# Fire
_TYPE_CHART_DATA[PokemonType.FIRE] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.GRASS] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.ICE] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.BUG] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.STEEL] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.FIRE] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.WATER] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.ROCK] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIRE][PokemonType.DRAGON] = NOT_VERY_EFFECTIVE

# Water
_TYPE_CHART_DATA[PokemonType.WATER] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.WATER][PokemonType.FIRE] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.WATER][PokemonType.GROUND] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.WATER][PokemonType.ROCK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.WATER][PokemonType.WATER] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.WATER][PokemonType.GRASS] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.WATER][PokemonType.DRAGON] = NOT_VERY_EFFECTIVE

# Electric
_TYPE_CHART_DATA[PokemonType.ELECTRIC] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.ELECTRIC][PokemonType.WATER] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ELECTRIC][PokemonType.FLYING] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ELECTRIC][PokemonType.ELECTRIC] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ELECTRIC][PokemonType.GRASS] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ELECTRIC][PokemonType.DRAGON] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ELECTRIC][PokemonType.GROUND] = IMMUNE

# Grass
_TYPE_CHART_DATA[PokemonType.GRASS] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.WATER] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.GROUND] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.ROCK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.FIRE] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.GRASS] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.POISON] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.FLYING] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.BUG] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.DRAGON] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GRASS][PokemonType.STEEL] = NOT_VERY_EFFECTIVE

# Ice
_TYPE_CHART_DATA[PokemonType.ICE] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.GRASS] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.GROUND] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.FLYING] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.DRAGON] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.FIRE] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.WATER] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.ICE] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ICE][PokemonType.STEEL] = NOT_VERY_EFFECTIVE

# Fighting
_TYPE_CHART_DATA[PokemonType.FIGHTING] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.NORMAL] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.ICE] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.ROCK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.DARK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.STEEL] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.POISON] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.FLYING] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.PSYCHIC] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.BUG] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.FAIRY] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FIGHTING][PokemonType.GHOST] = IMMUNE

# Poison
_TYPE_CHART_DATA[PokemonType.POISON] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.POISON][PokemonType.GRASS] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.POISON][PokemonType.FAIRY] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.POISON][PokemonType.POISON] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.POISON][PokemonType.GROUND] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.POISON][PokemonType.ROCK] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.POISON][PokemonType.GHOST] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.POISON][PokemonType.STEEL] = IMMUNE

# Ground
_TYPE_CHART_DATA[PokemonType.GROUND] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.FIRE] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.ELECTRIC] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.POISON] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.ROCK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.STEEL] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.GRASS] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.BUG] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GROUND][PokemonType.FLYING] = IMMUNE

# Flying
_TYPE_CHART_DATA[PokemonType.FLYING] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.FLYING][PokemonType.GRASS] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FLYING][PokemonType.FIGHTING] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FLYING][PokemonType.BUG] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FLYING][PokemonType.ELECTRIC] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FLYING][PokemonType.ROCK] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FLYING][PokemonType.STEEL] = NOT_VERY_EFFECTIVE

# Psychic
_TYPE_CHART_DATA[PokemonType.PSYCHIC] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.PSYCHIC][PokemonType.FIGHTING] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.PSYCHIC][PokemonType.POISON] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.PSYCHIC][PokemonType.PSYCHIC] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.PSYCHIC][PokemonType.STEEL] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.PSYCHIC][PokemonType.DARK] = IMMUNE

# Bug
_TYPE_CHART_DATA[PokemonType.BUG] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.GRASS] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.PSYCHIC] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.DARK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.FIRE] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.FIGHTING] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.POISON] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.FLYING] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.GHOST] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.STEEL] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.BUG][PokemonType.FAIRY] = NOT_VERY_EFFECTIVE

# Rock
_TYPE_CHART_DATA[PokemonType.ROCK] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.ROCK][PokemonType.FIRE] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ROCK][PokemonType.ICE] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ROCK][PokemonType.FLYING] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ROCK][PokemonType.BUG] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ROCK][PokemonType.FIGHTING] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ROCK][PokemonType.GROUND] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.ROCK][PokemonType.STEEL] = NOT_VERY_EFFECTIVE

# Ghost
_TYPE_CHART_DATA[PokemonType.GHOST] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.GHOST][PokemonType.PSYCHIC] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GHOST][PokemonType.GHOST] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GHOST][PokemonType.DARK] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.GHOST][PokemonType.NORMAL] = IMMUNE

# Dragon
_TYPE_CHART_DATA[PokemonType.DRAGON] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.DRAGON][PokemonType.DRAGON] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.DRAGON][PokemonType.STEEL] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.DRAGON][PokemonType.FAIRY] = IMMUNE

# Dark
_TYPE_CHART_DATA[PokemonType.DARK] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.DARK][PokemonType.PSYCHIC] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.DARK][PokemonType.GHOST] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.DARK][PokemonType.FIGHTING] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.DARK][PokemonType.DARK] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.DARK][PokemonType.FAIRY] = NOT_VERY_EFFECTIVE

# Steel
_TYPE_CHART_DATA[PokemonType.STEEL] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.STEEL][PokemonType.ICE] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.STEEL][PokemonType.ROCK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.STEEL][PokemonType.FAIRY] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.STEEL][PokemonType.FIRE] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.STEEL][PokemonType.WATER] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.STEEL][PokemonType.ELECTRIC] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.STEEL][PokemonType.STEEL] = NOT_VERY_EFFECTIVE

# Fairy
_TYPE_CHART_DATA[PokemonType.FAIRY] = dict.fromkeys(PokemonType, 1.0)
_TYPE_CHART_DATA[PokemonType.FAIRY][PokemonType.FIGHTING] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FAIRY][PokemonType.DRAGON] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FAIRY][PokemonType.DARK] = SUPER_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FAIRY][PokemonType.FIRE] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FAIRY][PokemonType.POISON] = NOT_VERY_EFFECTIVE
_TYPE_CHART_DATA[PokemonType.FAIRY][PokemonType.STEEL] = NOT_VERY_EFFECTIVE

# La matriz construida es inmutable: TYPE_CHART
TYPE_CHART: dict[PokemonType, dict[PokemonType, float]] = _TYPE_CHART_DATA


def type_effectiveness(
    attacking: PokemonType,
    defending1: PokemonType,
    defending2: PokemonType | None = None,
) -> float:
    """Efectividad de un ataque de `attacking` contra el defensor.

    Si el defensor tiene dos tipos, se multiplican ambas efectividades.
    En GO: súper efectivo = ×1.6, poco efectivo = ×0.625, inmune = ×0.390625.

    Args:
        attacking: Tipo del movimiento atacante.
        defending1: Tipo primario del defensor.
        defending2: Tipo secundario del defensor (opcional).

    Returns:
        Multiplicador de efectividad total.
    """
    effectiveness = TYPE_CHART[attacking][defending1]
    if defending2 is not None:
        effectiveness *= TYPE_CHART[attacking][defending2]
    return effectiveness


def weaknesses(defending1: PokemonType, defending2: PokemonType | None = None) -> dict[PokemonType, float]:
    """Debilidades y resistencias de una combinación de tipos defensivos.

    Args:
        defending1: Tipo primario.
        defending2: Tipo secundario (opcional).

    Returns:
        Diccionario {tipo_atacante: multiplicador}.
    """
    result: dict[PokemonType, float] = {}
    for atk_type in PokemonType:
        eff = type_effectiveness(atk_type, defending1, defending2)
        result[atk_type] = eff
    return result
