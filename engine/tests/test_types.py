"""Tests de engine/types.py — matriz de efectividad de tipos.

Fixtures verificadas contra la mecánica oficial de Pokémon GO:
  - Súper efectivo: ×1.6
  - Poco efectivo: ×0.625
  - Inmune (doble resistencia en GO): ×0.390625
  - Doble súper efectivo: ×2.56
  - Doble poco efectivo: ×0.390625
"""

import pytest

from engine.types import (
    IMMUNE,
    NOT_VERY_EFFECTIVE,
    SUPER_EFFECTIVE,
    TYPE_CHART,
    PokemonType,
    type_effectiveness,
    weaknesses,
)


class TestTypeChartSize:
    def test_all_18_types_present(self):
        assert len(TYPE_CHART) == 18

    def test_all_sub_charts_have_18_types(self):
        for atk_type, defenders in TYPE_CHART.items():
            assert len(defenders) == 18, f"{atk_type.value} no tiene 18 defensores"


class TestTypeEffectiveness:
    # Fixtures calculadas a mano contra la mecánica oficial

    def test_water_vs_fire(self):
        assert type_effectiveness(PokemonType.WATER, PokemonType.FIRE) == SUPER_EFFECTIVE

    def test_fire_vs_water(self):
        assert type_effectiveness(PokemonType.FIRE, PokemonType.WATER) == NOT_VERY_EFFECTIVE

    def test_electric_vs_water(self):
        assert type_effectiveness(PokemonType.ELECTRIC, PokemonType.WATER) == SUPER_EFFECTIVE

    def test_normal_vs_ghost(self):
        assert type_effectiveness(PokemonType.NORMAL, PokemonType.GHOST) == IMMUNE

    def test_ghost_vs_normal(self):
        assert type_effectiveness(PokemonType.GHOST, PokemonType.NORMAL) == IMMUNE

    def test_dragon_vs_dragon(self):
        assert type_effectiveness(PokemonType.DRAGON, PokemonType.DRAGON) == SUPER_EFFECTIVE

    def test_ground_vs_flying(self):
        assert type_effectiveness(PokemonType.GROUND, PokemonType.FLYING) == IMMUNE

    def test_fighting_vs_ghost(self):
        assert type_effectiveness(PokemonType.FIGHTING, PokemonType.GHOST) == IMMUNE

    def test_ice_vs_dragon(self):
        assert type_effectiveness(PokemonType.ICE, PokemonType.DRAGON) == SUPER_EFFECTIVE

    def test_neutral(self):
        assert type_effectiveness(PokemonType.NORMAL, PokemonType.WATER) == 1.0

    # Dual type
    def test_water_vs_ground_rock(self):
        """Water vs Ground/Rock: 1.6 × 1.6 = 2.56 (doble súper efectivo)."""
        eff = type_effectiveness(PokemonType.WATER, PokemonType.GROUND, PokemonType.ROCK)
        assert eff == pytest.approx(2.56)

    def test_grass_vs_water_ground(self):
        """Grass vs Water/Ground: 1.6 × 1.6 = 2.56."""
        eff = type_effectiveness(PokemonType.GRASS, PokemonType.WATER, PokemonType.GROUND)
        assert eff == pytest.approx(2.56)

    def test_normal_vs_ghost_dark(self):
        """Normal vs Ghost/Dark: 0.39 × 1.0 = 0.39."""
        eff = type_effectiveness(PokemonType.NORMAL, PokemonType.GHOST, PokemonType.DARK)
        assert eff == pytest.approx(IMMUNE)


class TestWeaknesses:
    def test_water_weak_to_electric_and_grass(self):
        w = weaknesses(PokemonType.WATER)
        assert w[PokemonType.ELECTRIC] == SUPER_EFFECTIVE
        assert w[PokemonType.GRASS] == SUPER_EFFECTIVE
        assert w[PokemonType.FIRE] == NOT_VERY_EFFECTIVE

    def test_dragon_flying_quad_weak_to_ice(self):
        """Dragon/Flying: Ice ×1.6 ×1.6 = ×2.56 (doble debilidad)."""
        w = weaknesses(PokemonType.DRAGON, PokemonType.FLYING)
        assert w[PokemonType.ICE] == pytest.approx(2.56)


class TestConstants:
    def test_super_effective_is_1_6(self):
        assert SUPER_EFFECTIVE == 1.6

    def test_not_very_effective_is_0_625(self):
        assert NOT_VERY_EFFECTIVE == 0.625

    def test_immune_is_double_resistance(self):
        assert pytest.approx(0.390625) == IMMUNE
