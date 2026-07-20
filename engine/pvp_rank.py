"""Stat Product y ranking de IV para PvP.

Procedencia: comunidad (PvPoke, alta confianza).
Stat Product = ATK_eff * DEF_eff * STAM_eff (a un nivel dado).
Para ranking, se generan las 4096 combinaciones de IV (0-15 cada stat)
y se ordenan por stat product descendente, respetando el cap de CP de la liga.

Regla: a igual stat product, gana el que tiene menor ATK (optimización PvP clásica).
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product

from engine.stats import CPM_TABLE, cp


@dataclass(frozen=True, order=True)
class IVSpread:
    """Combinación de IVs con su stat product a un nivel dado."""

    atk_iv: int
    def_iv: int
    stam_iv: int
    level: float
    cp_value: int
    stat_product: int

    @property
    def hp(self) -> int:
        """HP calculado en este nivel con estos IVs."""
        return 0  # se completa en el constructor


def stat_product(
    base_atk: int,
    base_def: int,
    base_stam: int,
    iv_atk: int,
    iv_def: int,
    iv_stam: int,
    cpm: float,
) -> int:
    """Stat Product entero: floor(ATK_eff * DEF_eff * STAM_eff * CPM³).

    Se usa floor porque los stats se truncan en el juego en cada paso.
    En la práctica: se multiplican las stats efectivas reales.

    Args:
        base_atk, base_def, base_stam: Stats base de la especie.
        iv_atk, iv_def, iv_stam: IVs individuales (0-15).
        cpm: CpMultiplier del nivel.

    Returns:
        Stat product como entero.
    """
    atk_val = (base_atk + iv_atk) * cpm
    def_val = (base_def + iv_def) * cpm
    stam_val = (base_stam + iv_stam) * cpm
    return int(atk_val * def_val * stam_val)


def generate_all_ivs() -> list[tuple[int, int, int]]:
    """Genera las 4096 combinaciones de IV (0-15 cada stat)."""
    return [(a, d, s) for a in range(16) for d in range(16) for s in range(16)]


def rank_for_league(
    base_atk: int,
    base_def: int,
    base_stam: int,
    max_cp: int,
    *,
    level_cap: float = 50.0,
    min_level: float = 1.0,
) -> list[IVSpread]:
    """Rankea las 4096 combinaciones de IV para una liga con cap de CP.

    Para cada combinación de IV, busca el nivel más alto posible (en pasos de 0.5)
    que NO exceda max_cp, calcula el stat product, y ordena por:
      1. Stat product descendente.
      2. A igual stat product, menor atk_iv primero (prioriza bulk sobre ataque).

    Args:
        base_atk, base_def, base_stam: Stats base de la especie.
        max_cp: Cap de CP de la liga (1500, 2500, o 0 para sin límite).
        level_cap: Nivel máximo permitido (default 50.0).
        min_level: Nivel mínimo (default 1.0).

    Returns:
        Lista de IVSpread ordenada del mejor (#1) al peor (#4096).
    """
    levels = sorted(CPM_TABLE.keys())
    # Filtrar niveles dentro del rango permitido
    valid_levels = [lv for lv in levels if min_level <= lv <= level_cap]

    results: list[IVSpread] = []

    for atk_iv, def_iv, stam_iv in product(range(16), repeat=3):
        best_level = min_level
        best_cp = 0
        best_sp = 0

        # Buscar el mejor nivel para esta combinación de IV
        for lv in valid_levels:
            cpm_val = CPM_TABLE[lv]
            cp_val = cp(base_atk, base_def, base_stam, atk_iv, def_iv, stam_iv, cpm_val)

            if cp_val > max_cp:
                break  # niveles posteriores solo darán CP más alto

            best_level = lv
            best_cp = cp_val
            best_sp = stat_product(base_atk, base_def, base_stam, atk_iv, def_iv, stam_iv, cpm_val)

        if best_cp > 0:
            results.append(IVSpread(
                atk_iv=atk_iv,
                def_iv=def_iv,
                stam_iv=stam_iv,
                level=best_level,
                cp_value=best_cp,
                stat_product=best_sp,
            ))

    # Ordenar: mayor stat product primero, a igual SP menor atk_iv primero
    results.sort(key=lambda s: (-s.stat_product, s.atk_iv))

    return results


def iv_rank_percent(
    base_atk: int,
    base_def: int,
    base_stam: int,
    iv_atk: int,
    iv_def: int,
    iv_stam: int,
    max_cp: int,
    *,
    level_cap: float = 50.0,
) -> float:
    """Percentil de una combinación de IVs específica (0.0 = mejor, 100.0 = peor).

    Args:
        base_atk, base_def, base_stam: Estadísticas base.
        iv_atk, iv_def, iv_stam: IVs a evaluar.
        max_cp: Cap de CP de la liga.
        level_cap: Nivel máximo.

    Returns:
        Percentil (0.0 = rank #1, 99.9 = casi peor).
    """
    ranking = rank_for_league(base_atk, base_def, base_stam, max_cp, level_cap=level_cap)

    for i, spread in enumerate(ranking):
        if spread.atk_iv == iv_atk and spread.def_iv == iv_def and spread.stam_iv == iv_stam:
            return (i / (len(ranking) - 1)) * 100.0

    return 100.0  # no encontrado (no debería ocurrir)


def top_spreads(
    base_atk: int,
    base_def: int,
    base_stam: int,
    max_cp: int,
    n: int = 10,
    *,
    level_cap: float = 50.0,
) -> list[IVSpread]:
    """Devuelve los mejores N spreads de IV para una liga.

    Args:
        base_atk, base_def, base_stam: Estadísticas base.
        max_cp: Cap de CP de la liga.
        n: Número de resultados a devolver.
        level_cap: Nivel máximo.

    Returns:
        Los N mejores IVSpread.
    """
    ranking = rank_for_league(base_atk, base_def, base_stam, max_cp, level_cap=level_cap)
    return ranking[:n]
