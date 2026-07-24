"""Breakpoints PvE (CALC007) — niveles donde el daño de un ataque rápido aumenta.

Procedencia: comunidad (GamePress / PvPoke, alta confianza).
Fórmula PvE: Damage = floor(0.5 * Power * ATK / DEF * STAB * Effectiveness * Weather * Friendship) + 1
El breakpoint es el nivel más bajo donde el daño aumenta en 1 punto.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from engine.dps_data import FAST_MOVES, FastMove
from engine.dps_data import SPECIES as DPS_SPECIES
from engine.stats import CPM_TABLE, cpm_for_level

_MIN_TABLE_LEVEL = min(CPM_TABLE)
_MAX_TABLE_LEVEL = max(CPM_TABLE)


@dataclass(frozen=True)
class Breakpoint:
    """Un breakpoint: nivel donde el daño del fast move aumenta."""

    level: float
    damage: int
    atk_effective: float


def _pve_damage(
    power: int,
    atk_effective: float,
    def_effective: float,
    stab: float = 1.0,
    effectiveness: float = 1.0,
    weather: float = 1.0,
    friendship: float = 1.0,
) -> int:
    """Daño PvE por golpe de fast move (FOR010).

    Damage = floor(0.5 * Power * Atk / Def * STAB * Eff * Weather * Friend) + 1
    """
    raw = (
        0.5 * power * (atk_effective / def_effective) * stab * effectiveness * weather * friendship
    )
    return max(1, math.floor(raw) + 1)


def find_breakpoints(
    species_key: str,
    fast_move_key: str,
    iv_atk: int,
    defender_def: float,
    *,
    defender_type1: str = "normal",
    defender_type2: str | None = None,
    weather_boosted: bool = False,
    friendship_level: str = "none",
    min_level: float = 20.0,
    max_level: float = 50.0,
    max_results: int = 20,
) -> list[Breakpoint]:
    """Encuentra los breakpoints de un fast move PvE.

    Args:
        species_key: Clave de la especie en dps_data.SPECIES (ej. "machamp").
        fast_move_key: Clave del fast move en dps_data.FAST_MOVES (ej. "counter").
        iv_atk: IV de ataque del Pokémon (0-15).
        defender_def: Defensa efectiva del defensor (BOSS_DEFENSE = 200 por defecto).
        defender_type1: Tipo primario del defensor.
        defender_type2: Tipo secundario del defensor.
        weather_boosted: Si el ataque está potenciado por clima (×1.2).
        friendship_level: "none", "good", "great", "ultra", "best" (+0/3/5/7/10 % daño).
        min_level: Nivel mínimo a considerar.
        max_level: Nivel máximo.
        max_results: Máximo de breakpoints a devolver.

    Returns:
        Lista de Breakpoint ordenada por nivel ascendente.
    """
    species = DPS_SPECIES.get(species_key)
    if species is None:
        raise ValueError(f"Especie '{species_key}' no encontrada.")

    move = FAST_MOVES.get(fast_move_key)
    if move is None:
        raise ValueError(f"Fast move '{fast_move_key}' no encontrado.")

    if not (0 <= iv_atk <= 15):
        raise ValueError(f"iv_atk debe estar entre 0 y 15 (recibido: {iv_atk}).")

    if not math.isfinite(defender_def) or defender_def <= 0:
        raise ValueError(
            f"defender_def debe ser un número finito mayor que 0 (recibido: {defender_def})."
        )

    if min_level > max_level:
        raise ValueError(
            f"nivel: min_level ({min_level}) no puede ser mayor que max_level ({max_level})."
        )
    if max_level < _MIN_TABLE_LEVEL or min_level > _MAX_TABLE_LEVEL:
        raise ValueError(
            f"nivel: el rango [{min_level}, {max_level}] no intersecta la tabla CPM "
            f"([{_MIN_TABLE_LEVEL}, {_MAX_TABLE_LEVEL}])."
        )

    from engine.dps_data import type_multiplier as tm

    base_atk = species.stats.atk
    move_type = move.type
    species_types = [species.type1]
    if species.type2:
        species_types.append(species.type2)

    stab = 1.2 if move_type in species_types else 1.0
    effectiveness = tm(move_type, defender_type1, defender_type2)
    weather = 1.2 if weather_boosted else 1.0

    friend_map = {"good": 1.03, "great": 1.05, "ultra": 1.07, "best": 1.10}
    friendship = friend_map.get(friendship_level, 1.0)

    all_levels = []
    lv = 1.0
    while lv <= max_level + 0.01:
        all_levels.append(lv)
        lv += 0.5

    breakpoints: list[Breakpoint] = []
    prev_damage = -1

    for level in all_levels:
        if level < min_level:
            continue
        try:
            cpm = cpm_for_level(level)
        except ValueError:
            continue

        atk_eff = (base_atk + iv_atk) * cpm
        damage = _pve_damage(
            move.power,
            atk_eff,
            defender_def,
            stab=stab,
            effectiveness=effectiveness,
            weather=weather,
            friendship=friendship,
        )

        if damage > prev_damage and prev_damage >= 0:
            breakpoints.append(
                Breakpoint(level=level, damage=damage, atk_effective=round(atk_eff, 1))
            )
            if len(breakpoints) >= max_results:
                break

        prev_damage = damage

    return breakpoints


def get_fast_moves_for_species(species_key: str) -> list[tuple[str, FastMove]]:
    """Devuelve los fast moves para el selector de una especie.

    Plan 047: no hay en este repo un learnset verificado (qué fast moves
    aprende realmente cada especie en el juego), así que se devuelve
    honestamente el catálogo completo de `FAST_MOVES` en vez de aparentar
    un filtro que no está respaldado por datos reales. La UI que consume
    esta función debe avisar de esta limitación (ver `breakpoints_page.html`).

    Args:
        species_key: Clave de la especie.

    Returns:
        Lista de (key, FastMove) — vacía si la especie no existe.
    """
    if species_key not in DPS_SPECIES:
        return []

    return sorted(FAST_MOVES.items(), key=lambda x: x[1].name)
