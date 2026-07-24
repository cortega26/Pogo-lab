"""Paridad de datos de combate entre `dps_data` y la tabla canónica (Plan 046).

Procedencia: `engine.types.TYPE_CHART` es la fuente única designada por el
plan 046 (internamente consistente, 18x18 completa). Este test compara
exhaustivamente las 324 celdas contra lo que expone `engine.dps_data`, que
hasta ahora mantenía una tabla duplicada con divergencias reales (ver
spec.md §3.1 para el listado exacto de las 11 diferencias encontradas por
comparación programática en esta sesión — no se afirma verificación externa).
"""

import pytest

from engine.dps_data import COMBAT_DATA_VERSION, type_multiplier
from engine.types import PokemonType, type_effectiveness

ALL_TYPE_VALUES = [t.value for t in PokemonType]


class TestCombatDataVersion:
    """El snapshot es un identificador opaco, no un rótulo de versión oficial."""

    def test_is_a_non_empty_opaque_string(self):
        assert isinstance(COMBAT_DATA_VERSION, str)
        assert COMBAT_DATA_VERSION.strip() != ""

    def test_does_not_claim_an_official_game_version(self):
        """No debe parecer un rótulo tipo 'v0.295+' que implique verificación
        externa no realizada (regla de procedencia, spec.md §0)."""
        assert not COMBAT_DATA_VERSION.startswith("v")


class TestCombatDataParity:
    """Las 324 celdas de dps_data.type_multiplier deben igualar a engine.types."""

    @pytest.mark.parametrize("defend", ALL_TYPE_VALUES)
    @pytest.mark.parametrize("attack", ALL_TYPE_VALUES)
    def test_dps_data_matches_canonical_chart(self, attack, defend):
        canonical = type_effectiveness(PokemonType(attack), PokemonType(defend))
        actual = type_multiplier(attack, defend, None)
        assert actual == pytest.approx(canonical, abs=1e-9), (
            f"{attack}->{defend}: dps_data={actual} canónico(types.py)={canonical}"
        )


class TestCombatDataSemanticFixes:
    """Las 3 diferencias semánticas encontradas (no solo de redondeo)."""

    def test_poison_vs_grass_is_super_effective(self):
        """Poison ataca súper efectivo a Grass; dps_data lo omitía (quedaba neutro)."""
        assert type_multiplier("poison", "grass", None) == pytest.approx(1.6)

    def test_rock_vs_water_is_neutral(self):
        """Rock no es resistido por Water; dps_data lo marcaba 0.625 sin base real."""
        assert type_multiplier("rock", "water", None) == pytest.approx(1.0)

    def test_rock_vs_grass_is_neutral(self):
        """Rock no es resistido por Grass; dps_data lo marcaba 0.625 sin base real."""
        assert type_multiplier("rock", "grass", None) == pytest.approx(1.0)


class TestCombatDataPrecisionFixes:
    """Las 8 diferencias de precisión (0.39 aproximado vs 0.390625 exacto)."""

    @pytest.mark.parametrize(
        ("attack", "defend"),
        [
            ("dragon", "fairy"),
            ("electric", "ground"),
            ("fighting", "ghost"),
            ("ghost", "normal"),
            ("ground", "flying"),
            ("normal", "ghost"),
            ("poison", "steel"),
            ("psychic", "dark"),
        ],
    )
    def test_immune_pairs_use_exact_double_resist(self, attack, defend):
        assert type_multiplier(attack, defend, None) == pytest.approx(0.390625, abs=1e-9)
