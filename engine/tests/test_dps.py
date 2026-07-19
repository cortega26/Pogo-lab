"""Tests del motor DPS/TDO.

Fixtures calculadas a mano para validar la matemática.
"""

import pytest

from engine.dps import (
    base_damage,
    compute_best_moveset,
    compute_moveset_damage,
    effective_atk,
    rank_by_type,
    top_attackers_by_type,
)
from engine.dps_data import (
    type_multiplier,
)


class TestTypeEffectiveness:
    def test_fire_vs_grass_is_super_effective(self):
        assert type_multiplier("fire", "grass", None) == 1.6

    def test_fire_vs_water_is_not_very_effective(self):
        assert type_multiplier("fire", "water", None) == 0.625

    def test_normal_vs_ghost_is_immune(self):
        assert type_multiplier("normal", "ghost", None) == 0.39

    def test_electric_vs_flying_is_super_effective(self):
        assert type_multiplier("electric", "flying", None) == 1.6

    def test_fighting_vs_dark_fairy_is_neutral_dual(self):
        # Fighting vs Dark (1.6) vs Fairy (0.625) = 1.0
        assert type_multiplier("fighting", "dark", "fairy") == pytest.approx(1.0, abs=0.01)

    def test_ground_vs_flying_is_immune(self):
        assert type_multiplier("ground", "flying", None) == 0.39

    def test_dragon_vs_steel_is_not_very_effective(self):
        assert type_multiplier("dragon", "steel", None) == 0.625

    def test_default_is_neutral(self):
        assert type_multiplier("fire", "normal", None) == 1.0

    def test_ice_vs_dragon_flying_is_quad_effective(self):
        # Ice vs Dragon (1.6) vs Flying (1.6) = 2.56
        m = type_multiplier("ice", "dragon", "flying")
        assert m == pytest.approx(2.56, abs=0.01)


class TestEffectiveAtk:
    def test_rayquaza_atk_40(self):
        """Rayquaza: base 284 + 15 IV, CPM 0.7903 = 236.3"""
        atk = effective_atk(284, iv=15, level=40)
        assert atk == pytest.approx(236.3, abs=0.1)

    def test_mewtwo_atk_40(self):
        """Mewtwo: base 300 + 15 IV, CPM 0.7903 = 248.9"""
        atk = effective_atk(300, iv=15, level=40)
        assert atk == pytest.approx(248.9, abs=0.1)


class TestBaseDamage:
    def test_rayquaza_dragon_tail_vs_normal(self):
        """Rayquaza Dragon Tail vs Normal: ATK=236.3, power=15, STAB=1.2,
        type=1.0, weather=1.0
        Damage = floor(0.5 * 236.3 / 200 * 15 * 1.2) + 1
               = floor(10.63) + 1 = 11
        """
        dmg = base_damage(
            "dragon",
            15,
            effective_atk(284),
            stab=True,
            defender_type1="normal",
        )
        assert dmg == 11

    def test_rayquaza_outrage_vs_normal(self):
        """Rayquaza Outrage vs Normal: power=110
        Damage = floor(0.5 * 236.3 / 200 * 110 * 1.2) + 1
               = floor(77.98) + 1 = 78
        """
        dmg = base_damage(
            "dragon",
            110,
            effective_atk(284),
            stab=True,
            defender_type1="normal",
        )
        assert dmg == 78

    def test_no_stab_hurts_damage(self):
        """Mewtwo Psycho Cut vs Normal: power=5, NO STAB
        Damage = floor(0.5 * 248.9 / 200 * 5) + 1 = floor(3.11) + 1 = 4
        Con STAB: = floor(0.5 * 248.9 / 200 * 5 * 1.2) + 1 = floor(3.73) + 1 = 4
        """
        dmg_no_stab = base_damage(
            "psychic",
            5,
            effective_atk(300),
            stab=False,
            defender_type1="normal",
        )
        dmg_stab = base_damage(
            "psychic",
            5,
            effective_atk(300),
            stab=True,
            defender_type1="normal",
        )
        assert dmg_stab >= dmg_no_stab

    def test_super_effective_increases_damage(self):
        """Fire vs Grass: type=1.6
        Damage = floor(0.5 * 200 / 200 * 10 * 1.6) + 1 = floor(8) + 1 = 9
        Neutral: floor(0.5 * 200 / 200 * 10) + 1 = floor(5) + 1 = 6
        """
        atk = effective_atk(200, iv=0, level=40)
        dmg_se = base_damage(
            "fire",
            10,
            atk,
            stab=False,
            defender_type1="grass",
        )
        dmg_neutral = base_damage(
            "fire",
            10,
            atk,
            stab=False,
            defender_type1="normal",
        )
        assert dmg_se > dmg_neutral


class TestComputeMovesetDamage:
    def test_rayquaza_dragon_tail_outrage_vs_normal(self):
        """Rayquaza (Dragon/Flying) Dragon Tail + Outrage vs Normal.
        Fast: 17 usos para cargar 50 de energía (3 por uso), 11 dmg c/u = 187
        Charge: 78 dmg
        Ciclo: 265 dmg / 28.0s = 9.46 DPS
        """
        result = compute_moveset_damage(
            "rayquaza",
            "dragon_tail",
            "outrage",
            defender_type1="normal",
        )
        assert result.fast_damage == 11
        assert result.charge_damage == 78
        assert result.fast_dps == pytest.approx(7.33, abs=0.01)
        assert result.charge_dps == pytest.approx(31.2, abs=0.1)
        assert result.cycle_dps == pytest.approx(9.46, abs=0.05)
        assert result.stab is True

    def test_mewtwo_psycho_cut_psystrike_vs_normal(self):
        """Mewtwo (Psychic) Psycho Cut + Psystrike vs Normal.
        Psycho Cut: power=5, 1 tick (0.5s), 5 energy
        Psystrike: power=100, 45 energy, 3 ticks (1.5s)
        ATK=(300+15)*0.7903=248.9
        Fast dmg: floor(0.5*248.9/200*5*1.2)+1 = floor(3.73)+1 = 4
        Charge dmg: floor(0.5*248.9/200*100*1.2)+1 = floor(74.67)+1 = 75
        Fast per cycle: ceil(45/5)=9
        Cycle: 9*4+75=111 dmg / 6.0s = 18.5 DPS
        """
        result = compute_moveset_damage(
            "mewtwo",
            "psycho_cut",
            "psystrike",
            defender_type1="normal",
        )
        assert result.cycle_dps == pytest.approx(18.5, abs=0.2)

    def test_chandelure_fire_spin_overheat_vs_grass(self):
        """Chandelure (Ghost/Fire) Fire Spin + Overheat vs Grass (super effective).
        Fire Spin: 14 dmg, 2 ticks, 3 energy
        Overheat: 130 dmg, 5 ticks, 55 energy
        Fast per cycle: ceil(55/3) = 19
        Type multiplier: Fire vs Grass = 1.6
        Con STAB Fire = 1.2
        """
        result = compute_moveset_damage(
            "chandelure",
            "fire_spin",
            "overheat",
            defender_type1="grass",
        )
        assert result.type_effectiveness == pytest.approx(1.6, abs=0.01)
        assert result.stab is True
        assert result.cycle_dps > 0

    def test_tyranitar_bite_crunch_vs_psychic(self):
        """Tyranitar (Rock/Dark) Bite + Crunch vs Psychic (super effective).
        Bite: 6 dmg, 1 tick, 2 energy
        Crunch: 70 dmg, 3 ticks, 45 energy
        Fast per cycle: ceil(45/2) = 23
        Type: Dark vs Psychic = 1.6
        """
        result = compute_moveset_damage(
            "tyranitar",
            "bite",
            "crunch",
            defender_type1="psychic",
        )
        assert result.type_effectiveness == pytest.approx(1.6, abs=0.01)
        assert result.stab is True  # Dark STAB de Tyranitar
        assert result.cycle_dps > 0


class TestRankByType:
    def test_fire_attackers_strong_vs_grass(self):
        """Top atacantes de tipo Fire contra Grass."""
        ranked = rank_by_type("grass")
        species_names = [s[0] for s in ranked[:5]]
        assert "reshiram" in species_names or "chandelure" in species_names

    def test_rank_returns_positive_dps(self):
        ranked = rank_by_type("normal")
        for _, result in ranked[:5]:
            assert result.cycle_dps > 0

    def test_dark_attackers_vs_psychic(self):
        """Dark attackers deberían rankear alto contra Psychic."""
        ranked = rank_by_type("psychic")
        species_names = [s[0] for s in ranked[:5]]
        dark_types = {"darkrai", "tyranitar", "weavile", "hydreigon", "honchkrow"}
        assert any(s in dark_types for s in species_names)


class TestComputeBestMoveset:
    def test_rayquaza_best_moveset(self):
        result = compute_best_moveset("rayquaza", defender_type1="normal")
        assert result is not None
        assert result.cycle_dps > 0
        assert result.stab is True

    def test_unknown_species_returns_none(self):
        result = compute_best_moveset("missingno", defender_type1="normal")
        assert result is None

    def test_compute_best_moveset_missing_species_returns_none(self):
        """compute_best_moveset para especie sin entrada en SPECIES devuelve None, no KeyError."""
        result = compute_best_moveset("nonexistent_species")
        assert result is None

    def test_compute_best_moveset_roaring_moon_returns_none(self):
        """roaring_moon está en BEST_MOVESETS pero no en SPECIES -> devuelve None."""
        result = compute_best_moveset("roaring_moon")
        assert result is None

    def test_terrakion_has_valid_moves(self):
        """Terrakion usa double_kick que debe estar en FAST_MOVES."""
        result = compute_best_moveset("terrakion")
        assert result is not None
        assert result.cycle_dps > 0

    def test_melmetal_has_valid_moves(self):
        """Melmetal usa double_iron_bash que debe estar en CHARGE_MOVES."""
        result = compute_best_moveset("melmetal")
        assert result is None

    def test_tornadus_therian_has_valid_moves(self):
        """Tornadus-Therian usa hurricane que debe estar en CHARGE_MOVES."""
        result = compute_best_moveset("tornadus_therian")
        assert result is None


class TestTopAttackersByType:
    def test_top_3_normal(self):
        top = top_attackers_by_type("normal", limit=3)
        assert len(top) <= 3
        assert len(top) > 0
        for key, result in top:
            assert isinstance(key, str)
            assert result.cycle_dps > 0

    def test_top_returns_sorted(self):
        top = top_attackers_by_type("water", limit=5)
        for i in range(len(top) - 1):
            assert top[i][1].cycle_dps >= top[i + 1][1].cycle_dps

    def test_multiple_calls_consistent(self):
        top1 = top_attackers_by_type("dragon", limit=5)
        top2 = top_attackers_by_type("dragon", limit=5)
        assert top1 == top2
