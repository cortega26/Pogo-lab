"""Modelo de DPS (Damage Per Second) y TDO (Total Damage Output) para Pokémon GO.

Fórmulas basadas en el datamining de la Game Master v0.295+:

  Damage = floor(0.5 * ATK / DEF * Power * STAB * Type * Weather) + 1
  ATK = (base_atk + 15) * CPM(level)
  DPS_cycle = Cycle_Damage / Cycle_Duration_s
  TDO = Damage_per_cycle * floor(HP / Damage_received_per_cycle)

Supuestos:
  - S1: Atacante nivel 40 con IVs 15/15/15 (CPM = 0.790300).
  - S2: Defensa estandarizada del jefe en 200 (sin type advantage defensivo).
  - S3: Sin clima (Weather = 1.0).
  - S4: Ciclo de energía: fast moves hasta cargar la charge move.
  - S5: STAB = 1.2 si el tipo del move coincide con algún tipo del Pokémon.
  - S6: Sin daño de reserva ni escudos (PvE).
  - S7: La defensa del atacante NO se usa para su propio daño.
"""

import math
from dataclasses import dataclass

from .dps_data import (
    BEST_MOVESETS,
    CHARGE_MOVES,
    FAST_MOVES,
    SPECIES,
    type_multiplier,
)

CPM_40: float = 0.790300
BOSS_DEFENSE: float = 200.0
TDO_NORMALIZER: float = 1000.0
STAB_BONUS: float = 1.2
RELOBBY_S: float = 10.0
BOSS_DPT: float = 50.0


@dataclass(frozen=True)
class DamageResult:
    fast_damage: float
    fast_dps: float
    charge_damage: float
    charge_dps: float
    cycle_dps: float
    tdo: float
    edps: float
    cycle_duration_s: float
    fast_move_key: str
    charge_move_key: str
    stab: bool
    type_effectiveness: float
    hp: float
    level: int


CPM_VALUES: dict[int, float] = {
    1: 0.094000,
    5: 0.290249,
    10: 0.422500,
    15: 0.517394,
    20: 0.597400,
    25: 0.667934,
    30: 0.731700,
    35: 0.761684,
    40: 0.790300,
    45: 0.819300,
    50: 0.845299,
}


def _cp_multiplier(level: int) -> float:
    if level in CPM_VALUES:
        return CPM_VALUES[level]
    sorted_levels = sorted(CPM_VALUES.keys())
    for i in range(len(sorted_levels) - 1):
        if sorted_levels[i] <= level <= sorted_levels[i + 1]:
            lo, hi = sorted_levels[i], sorted_levels[i + 1]
            t = (level - lo) / (hi - lo) if hi != lo else 0
            return CPM_VALUES[lo] + t * (CPM_VALUES[hi] - CPM_VALUES[lo])
    return CPM_40


def effective_atk(base_atk: int, iv: int = 15, level: int = 40) -> float:
    return (base_atk + iv) * _cp_multiplier(level)


def base_damage(
    attack_type: str,
    move_power: int,
    atk: float,
    defender_def: float = BOSS_DEFENSE,
    stab: bool = False,
    weather: float = 1.0,
    defender_type1: str = "normal",
    defender_type2: str | None = None,
) -> float:
    t_mult = type_multiplier(attack_type, defender_type1, defender_type2)
    stab_m = STAB_BONUS if stab else 1.0
    raw = 0.5 * atk / defender_def * move_power * stab_m * t_mult * weather
    return math.floor(raw) + 1


def _has_stab(pokemon_types: list[str], move_type: str) -> bool:
    return move_type in pokemon_types


def _hp(base_sta: int, iv: int = 15, level: int = 40) -> float:
    return (base_sta + iv) * _cp_multiplier(level)


def compute_edps(
    cycle_dps: float, hp: float, relobby_s: float = RELOBBY_S, boss_dpt: float = BOSS_DPT
) -> float:
    survival_time = hp / boss_dpt * 100
    total_damage = cycle_dps * survival_time
    total_time = survival_time + relobby_s
    return total_damage / total_time if total_time > 0 else 0


def compute_moveset_damage(
    species_key: str,
    fast_key: str,
    charge_key: str,
    level: int = 40,
    defender_type1: str = "normal",
    defender_type2: str | None = None,
    defender_def: float = BOSS_DEFENSE,
) -> DamageResult:
    species = SPECIES[species_key]
    fast = FAST_MOVES[fast_key]
    charge = CHARGE_MOVES[charge_key]

    atk = effective_atk(species.stats.atk, iv=15, level=level)
    pokemon_types = [t for t in [species.type1, species.type2] if t]

    stab_fast = _has_stab(pokemon_types, fast.type)
    stab_charge = _has_stab(pokemon_types, charge.type)

    fast_dmg = base_damage(
        fast.type,
        fast.power,
        atk,
        defender_def,
        stab=stab_fast,
        defender_type1=defender_type1,
        defender_type2=defender_type2,
    )
    charge_dmg = base_damage(
        charge.type,
        charge.power,
        atk,
        defender_def,
        stab=stab_charge,
        defender_type1=defender_type1,
        defender_type2=defender_type2,
    )

    fast_dur_s = fast.duration_ticks * 0.5
    charge_dur_s = charge.duration_ticks * 0.5

    fast_dps = fast_dmg / fast_dur_s if fast_dur_s > 0 else 0
    charge_dps = charge_dmg / charge_dur_s if charge_dur_s > 0 else 0

    if fast.energy_gain <= 0:
        fast_per_cycle = 1
    else:
        fast_per_cycle = max(1, math.ceil(charge.energy_cost / fast.energy_gain))

    cycle_damage = fast_per_cycle * fast_dmg + charge_dmg
    cycle_duration = fast_per_cycle * fast_dur_s + charge_dur_s
    cycle_dps = cycle_damage / cycle_duration if cycle_duration > 0 else 0

    hp = _hp(species.stats.sta, level=level)
    tdo = cycle_dps * hp / TDO_NORMALIZER
    edps = compute_edps(cycle_dps, hp)

    return DamageResult(
        fast_damage=fast_dmg,
        fast_dps=round(fast_dps, 2),
        charge_damage=charge_dmg,
        charge_dps=round(charge_dps, 2),
        cycle_dps=round(cycle_dps, 2),
        tdo=round(tdo, 2),
        edps=round(edps, 2),
        cycle_duration_s=round(cycle_duration, 2),
        fast_move_key=fast_key,
        charge_move_key=charge_key,
        stab=stab_fast or stab_charge,
        type_effectiveness=type_multiplier(fast.type, defender_type1, defender_type2),
        hp=round(hp, 1),
        level=level,
    )


def compute_best_moveset(
    species_key: str,
    level: int = 40,
    defender_type1: str = "normal",
    defender_type2: str | None = None,
) -> DamageResult | None:
    if species_key not in BEST_MOVESETS:
        return None
    if species_key not in SPECIES:
        return None
    fast_key, charge_key = BEST_MOVESETS[species_key]
    if fast_key not in FAST_MOVES or charge_key not in CHARGE_MOVES:
        return None
    return compute_moveset_damage(
        species_key,
        fast_key,
        charge_key,
        level=level,
        defender_type1=defender_type1,
        defender_type2=defender_type2,
    )


def rank_by_type(
    target_type: str,
    level: int = 40,
    min_cycle_dps: float = 0,
) -> list[tuple[str, DamageResult]]:
    results: list[tuple[str, DamageResult]] = []
    for species_key in SPECIES:
        if species_key not in BEST_MOVESETS:
            continue
        result = compute_best_moveset(
            species_key,
            level=level,
            defender_type1=target_type,
        )
        if result is None:
            continue
        if result.cycle_dps < min_cycle_dps:
            continue
        results.append((species_key, result))

    results.sort(key=lambda x: x[1].cycle_dps, reverse=True)
    return results


def top_attackers_by_type(
    target_type: str,
    limit: int = 10,
    level: int = 40,
) -> list[tuple[str, DamageResult]]:
    ranked = rank_by_type(target_type, level=level)
    return ranked[:limit]


def compute_best_movesets_multi(
    species_keys: list[str],
    level: int = 40,
    defender_type1: str = "normal",
) -> list[tuple[str, DamageResult | None]]:
    results: list[tuple[str, DamageResult | None]] = []
    for key in species_keys:
        result = compute_best_moveset(key, level=level, defender_type1=defender_type1)
        results.append((key, result))
    return results
