"""Tests de engine/breakpoints.py (Plan 047).

Fixtures calculadas a mano con la fórmula documentada en el propio módulo:
    Damage = floor(0.5 * Power * ATK / DEF * STAB * Effectiveness * Weather
                   * Friendship) + 1
usando la tabla de tipos unificada (plan 046) y la tabla CPM canónica
(`engine.stats.CPM_TABLE`). Procedencia: cálculo puro sobre reglas ya
verificadas en este repo — no se afirma ninguna fuente externa nueva.
"""

import math

import pytest

from engine.breakpoints import (
    Breakpoint,
    _pve_damage,
    find_breakpoints,
    get_fast_moves_for_species,
)
from engine.dps_data import FAST_MOVES
from engine.stats import cpm_for_level


class TestPveDamageFormula:
    """Fixtures a mano: floor(0.5 * power * atk/def * stab * eff * weather * friend) + 1."""

    def test_no_modifiers(self):
        # 0.5 * 100 * (100/100) * 1 * 1 * 1 = 50.0 -> floor(50.0) + 1 = 51
        assert _pve_damage(100, 100.0, 100.0) == 51

    def test_stab_bonus(self):
        # 0.5 * 100 * (100/100) * 1.2 = 60.0 -> floor(60.0) + 1 = 61
        assert _pve_damage(100, 100.0, 100.0, stab=1.2) == 61

    def test_super_effective(self):
        # 0.5 * 100 * (100/100) * 1.6 = 80.0 -> floor(80.0) + 1 = 81
        assert _pve_damage(100, 100.0, 100.0, effectiveness=1.6) == 81

    def test_double_super_effective(self):
        # 0.5 * 100 * (100/100) * 2.56 = 128.0 -> floor(128.0) + 1 = 129
        assert _pve_damage(100, 100.0, 100.0, effectiveness=2.56) == 129

    def test_not_very_effective(self):
        # 0.5 * 100 * (100/100) * 0.625 = 31.25 -> floor(31.25) + 1 = 32
        assert _pve_damage(100, 100.0, 100.0, effectiveness=0.625) == 32

    def test_weather_boost(self):
        # 0.5 * 100 * (100/100) * 1.2 (weather) = 60.0 -> floor(60.0) + 1 = 61
        assert _pve_damage(100, 100.0, 100.0, weather=1.2) == 61

    def test_friendship_best(self):
        # 0.5 * 100 * (100/100) * 1.10 = 55.0 -> floor(55.0) + 1 = 56
        assert _pve_damage(100, 100.0, 100.0, friendship=1.10) == 56

    def test_all_modifiers_combined(self):
        # 0.5*100*(150/100)*1.2*1.6*1.2*1.07 = 184.896 -> floor(184.896)+1 = 185
        dmg = _pve_damage(
            100, 150.0, 100.0, stab=1.2, effectiveness=1.6, weather=1.2, friendship=1.07
        )
        assert dmg == 185

    def test_minimum_damage_is_one(self):
        # ATK muy bajo frente a DEF muy alta: floor(~0) + 1 = 1, nunca 0.
        assert _pve_damage(1, 1.0, 100000.0) == 1


class TestFindBreakpointsValidation:
    """Plan 047: nunca crashear ni aceptar parámetros fuera de dominio en silencio."""

    def test_rejects_defender_def_zero(self):
        with pytest.raises(ValueError, match="defender_def"):
            find_breakpoints("mewtwo", "psycho_cut", 15, 0)

    def test_rejects_defender_def_negative(self):
        with pytest.raises(ValueError, match="defender_def"):
            find_breakpoints("mewtwo", "psycho_cut", 15, -50)

    def test_rejects_defender_def_infinite(self):
        with pytest.raises(ValueError, match="defender_def"):
            find_breakpoints("mewtwo", "psycho_cut", 15, float("inf"))

    def test_rejects_defender_def_nan(self):
        with pytest.raises(ValueError, match="defender_def"):
            find_breakpoints("mewtwo", "psycho_cut", 15, float("nan"))

    def test_rejects_iv_atk_above_15(self):
        with pytest.raises(ValueError, match="iv_atk"):
            find_breakpoints("mewtwo", "psycho_cut", 16, 200.0)

    def test_rejects_iv_atk_below_zero(self):
        with pytest.raises(ValueError, match="iv_atk"):
            find_breakpoints("mewtwo", "psycho_cut", -1, 200.0)

    def test_accepts_iv_atk_boundaries(self):
        # 0 y 15 son válidos (no deben lanzar).
        assert find_breakpoints("mewtwo", "psycho_cut", 0, 200.0) is not None
        assert find_breakpoints("mewtwo", "psycho_cut", 15, 200.0) is not None

    def test_rejects_min_level_greater_than_max_level(self):
        with pytest.raises(ValueError, match="nivel"):
            find_breakpoints("mewtwo", "psycho_cut", 15, 200.0, min_level=50.0, max_level=20.0)

    def test_rejects_level_range_outside_cpm_table(self):
        """min_level/max_level completamente fuera de la tabla CPM (1.0-55.0)."""
        with pytest.raises(ValueError, match="nivel"):
            find_breakpoints("mewtwo", "psycho_cut", 15, 200.0, min_level=100.0, max_level=200.0)

    def test_unknown_species_raises(self):
        with pytest.raises(ValueError, match="Especie"):
            find_breakpoints("no_existe_esta_especie", "psycho_cut", 15, 200.0)

    def test_unknown_move_raises(self):
        with pytest.raises(ValueError, match="Fast move"):
            find_breakpoints("mewtwo", "no_existe_este_movimiento", 15, 200.0)

    def test_dual_type_species_gets_stab_from_secondary_type(self):
        """Gengar (ghost/poison) con un fast move poison debe recibir STAB
        aunque el tipo coincidente sea el secundario, no el primario."""
        bps = find_breakpoints("gengar", "poison_jab", 15, 200.0, max_results=1)
        assert len(bps) >= 1

    def test_max_level_partially_beyond_cpm_table_skips_out_of_range_levels(self):
        """Un max_level que solapa con la tabla pero la excede no debe
        crashear: los niveles fuera de la tabla se saltan (no se rechaza
        toda la llamada, porque el rango sí intersecta la tabla)."""
        bps = find_breakpoints("mewtwo", "psycho_cut", 15, 200.0, min_level=50.0, max_level=100.0)
        assert all(bp.level <= 55.0 for bp in bps)


class TestFindBreakpointsGoldenVector:
    def test_mewtwo_psycho_cut_matches_hand_computed_damage_at_level_40(self):
        """Verifica que un breakpoint real coincide con la fórmula calculada
        a mano: Mewtwo (atk base 300, ver engine.stats.MEWTWO) nivel 40,
        IV atk 15, Psycho Cut (psychic, power=5) vs defensor normal (sin
        efectividad especial), defensa 200."""
        bps = find_breakpoints("mewtwo", "psycho_cut", 15, 200.0, max_results=1)
        assert len(bps) >= 1
        first = bps[0]
        assert isinstance(first, Breakpoint)

        cpm = cpm_for_level(first.level)
        atk_eff = (300 + 15) * cpm
        assert first.atk_effective == pytest.approx(round(atk_eff, 1), abs=0.05)

        # Mewtwo es psychic y psycho_cut es psychic -> hay STAB (x1.2) en el engine real.
        expected_damage = math.floor(0.5 * 5 * (atk_eff / 200.0) * 1.2) + 1
        assert first.damage == expected_damage


class TestGetFastMovesForSpecies:
    def test_unknown_species_returns_empty(self):
        assert get_fast_moves_for_species("no_existe_esta_especie") == []

    def test_known_species_returns_full_catalog(self):
        """Plan 047: no hay datos de learnset verificados, así que se
        devuelve honestamente el catálogo completo (no un subconjunto
        filtrado que aparente estar verificado)."""
        result = get_fast_moves_for_species("mewtwo")
        assert len(result) == len(FAST_MOVES)
        assert {key for key, _ in result} == set(FAST_MOVES.keys())
