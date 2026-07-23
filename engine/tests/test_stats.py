"""Tests de engine/stats.py — CP, HP, CPM table.

Fixtures calculadas a mano con la fórmula FOR006/FOR007 y CPM table verificada.
Los valores de referencia provienen de:
  - Mewtwo L40 15/15/15: CP=4178, HP=180 (valor comunitario consolidado)
  - Pikachu L15 10/10/10: CP=368, HP=62 (verificado en Gate 0)
  - Dragonite L40 15/15/15: CP=3792, HP=176 (valor comunitario consolidado)
  - Medicham L50 15/15/15: CP=1618 (Game Master; la conversión MSG→GO da ~1986, errónea)
"""

from dataclasses import FrozenInstanceError

import pytest

from engine.stats import (
    CPM_TABLE,
    MEWTWO,
    PIKACHU,
    compute_cp_hp,
    cp,
    cpm_for_level,
    effective_stat,
    hp,
)


class TestCpMultiplierTable:
    """La tabla CPM contiene valores verificados por la comunidad."""

    def test_table_has_110_levels(self):
        """110 niveles (1.0 a 55.0 en incrementos de 0.5)."""
        assert len(CPM_TABLE) == 109

    def test_table_is_monotonic(self):
        """CPM crece con el nivel."""
        levels = sorted(CPM_TABLE.keys())
        for i in range(1, len(levels)):
            assert CPM_TABLE[levels[i]] > CPM_TABLE[levels[i - 1]]

    def test_key_levels_have_known_values(self):
        """Valores en niveles de referencia verificados contra la comunidad."""
        assert CPM_TABLE[1.0] == pytest.approx(0.094)
        assert CPM_TABLE[20.0] == pytest.approx(0.59740001)
        assert CPM_TABLE[40.0] == pytest.approx(0.79030001)
        assert CPM_TABLE[50.0] == pytest.approx(0.84030002)

    def test_cpm_for_level_returns_correct_value(self):
        assert cpm_for_level(40.0) == pytest.approx(0.79030001)

    def test_cpm_for_unknown_level_raises_value_error(self):
        with pytest.raises(ValueError):
            cpm_for_level(99.0)


class TestEffectiveStat:
    """effective_stat = (base + iv) * cpm."""

    def test_mewtwo_atk_l40_perfect(self):
        """Mewtwo L40 15 ATK: (300 + 15) * 0.79030001 = 248.9445..."""
        result = effective_stat(300, 15, 0.79030001)
        assert result == pytest.approx(248.94450315)

    def test_pikachu_atk_l15_10iv(self):
        """Pikachu L15 10 ATK: (112 + 10) * 0.51739395 = 63.122..."""
        result = effective_stat(112, 10, 0.51739395)
        assert result == pytest.approx(63.12206190)


class TestCpFormula:
    """CP = max(10, floor(Atk_eff * sqrt(Def_eff) * sqrt(Stam_eff) * CPM² / 10))."""

    def test_mewtwo_l40_perfect(self):
        """Mewtwo L40 15/15/15 → CP=4178 (valor comunitario consolidado).

        Cálculo:
          Atk_eff = 300+15 = 315
          Def_eff = 182+15 = 197
          Stam_eff = 214+15 = 229
          sqrt(197) ≈ 14.0357, sqrt(229) ≈ 15.1327
          CPM² = 0.79030001² ≈ 0.624574
          raw = 315 * 14.0357 * 15.1327 * 0.624574 / 10
              ≈ 41780.84 / 10 = 4178.084
          floor = 4178
        """
        result = cp(300, 182, 214, 15, 15, 15, 0.79030001)
        assert result == 4178

    def test_pikachu_l15_10_10_10(self):
        """Pikachu L15 10/10/10 → CP=368 (verificado en Gate 0).

        Cálculo:
          Atk_eff = 112+10 = 122
          Def_eff = 95+10 = 105
          Stam_eff = 111+10 = 121
          sqrt(105) ≈ 10.2470, sqrt(121) = 11
          CPM = 0.51739395, CPM² ≈ 0.267697
          raw = 122 * 10.2470 * 11 * 0.267697 / 10
              ≈ 3682.04 / 10 = 368.20
          floor = 368
        """
        result = cp(112, 95, 111, 10, 10, 10, 0.51739395)
        assert result == 368

    def test_dragonite_l40_perfect(self):
        """Dragonite L40 15/15/15 → CP=3792.

        Cálculo:
          Atk_eff = 263+15 = 278
          Def_eff = 198+15 = 213
          Stam_eff = 209+15 = 224
          sqrt(213) ≈ 14.5945, sqrt(224) ≈ 14.9666
          CPM² = 0.79030001² ≈ 0.624574
          raw = 278 * 14.5945 * 14.9666 * 0.624574 / 10
              ≈ 37926.85 / 10 = 3792.685
          floor = 3792
        """
        result = cp(263, 198, 209, 15, 15, 15, 0.79030001)
        assert result == 3792

    def test_medicham_l50_perfect(self):
        """Medicham L50 15/15/15 → CP=1618 (Game Master; MSG→GO da ~1986, errónea).

        Cálculo:
          Atk_eff = 121+15 = 136
          Def_eff = 152+15 = 167
          Stam_eff = 155+15 = 170
          sqrt(167) ≈ 12.9228, sqrt(170) ≈ 13.0384
          CPM = 0.84030002, CPM² ≈ 0.706104
          raw = 136 * 12.9228 * 13.0384 * 0.706104 / 10
              ≈ 16180.44 / 10 = 1618.044
          floor = 1618
        """
        result = cp(121, 152, 155, 15, 15, 15, 0.84030002)
        assert result == 1618

    def test_minimum_cp_is_10(self):
        """Incluso con stats mínimas, el CP nunca baja de 10."""
        result = cp(1, 1, 1, 0, 0, 0, 0.094)
        assert result == 10

    def test_cp_monotonic_in_iv(self):
        """A mayor IV, mayor o igual CP (para una misma especie y nivel)."""
        cpm = 0.79030001
        cp_low = cp(300, 182, 214, 10, 10, 10, cpm)
        cp_high = cp(300, 182, 214, 15, 15, 15, cpm)
        assert cp_high > cp_low

    def test_cp_monotonic_in_level(self):
        """A mayor nivel, mayor o igual CP (para los mismos IVs)."""
        cp_l20 = cp(300, 182, 214, 15, 15, 15, 0.59740001)
        cp_l40 = cp(300, 182, 214, 15, 15, 15, 0.79030001)
        assert cp_l40 > cp_l20


class TestHpFormula:
    """HP = max(10, floor(Stam_eff * CPM))."""

    def test_mewtwo_l40_perfect(self):
        """Mewtwo L40 15 stam: floor((214+15) * 0.79030001) = floor(180.978) = 180."""
        result = hp(214, 15, 0.79030001)
        assert result == 180

    def test_pikachu_l15_10_stam(self):
        """Pikachu L15 10 stam: floor((111+10) * 0.51739395) = floor(62.60) = 62."""
        result = hp(111, 10, 0.51739395)
        assert result == 62

    def test_minimum_hp_is_10(self):
        result = hp(10, 0, 0.094)
        assert result == 10

    def test_hp_monotonic_in_stam(self):
        hp_low = hp(214, 10, 0.79030001)
        hp_high = hp(214, 15, 0.79030001)
        assert hp_high > hp_low


class TestComputeCpHp:
    """Conveniencia: compute_cp_hp devuelve (CP, HP)."""

    def test_mewtwo_l40_perfect(self):
        cp_val, hp_val = compute_cp_hp(300, 182, 214, 15, 15, 15, 40.0)
        assert cp_val == 4178
        assert hp_val == 180

    def test_pikachu_l15_10_10_10(self):
        cp_val, hp_val = compute_cp_hp(112, 95, 111, 10, 10, 10, 15.0)
        assert cp_val == 368
        assert hp_val == 62

    def test_pikachu_l20_perfect(self):
        """Pikachu L20 15/15/15.

        Cálculo:
          Atk_eff = 112+15=127, Def_eff=95+15=110, Stam_eff=111+15=126
          sqrt(110)≈10.4881, sqrt(126)≈11.2250
          CPM=0.59740001, CPM²≈0.356887
          raw = 127 * 10.4881 * 11.2250 * 0.356887 / 10
              ≈ 5335.76/10 = 533.576
          floor = 533
        HP = floor(126 * 0.59740001) = floor(75.27) = 75
        """
        cp_val, hp_val = compute_cp_hp(112, 95, 111, 15, 15, 15, 20.0)
        assert cp_val == 533
        assert hp_val == 75


class TestSpeciesStats:
    """Los dataclasses SpeciesStats son inmutables y contienen valores del Game Master."""

    def test_mewtwo_is_nerfed(self):
        assert MEWTWO.nerf_applied is True
        assert MEWTWO.base_atk == 300  # nerfeado de 330

    def test_pikachu_base_def_is_95(self):
        """Gate 0: Pikachu Def base es 95, no 96 (error del research pack)."""
        assert PIKACHU.base_def == 95

    def test_species_are_immutable(self):
        with pytest.raises(FrozenInstanceError):
            MEWTWO.base_atk = 999  # type: ignore[misc]


class TestCpFormulaHypothesis:
    """Propiedades invariantes del cálculo de CP (property-based)."""

    @pytest.mark.parametrize(
        "base_atk,base_def,base_stam",
        [
            (300, 182, 214),  # Mewtwo
            (112, 95, 111),  # Pikachu
            (263, 198, 209),  # Dragonite
            (121, 152, 155),  # Medicham
        ],
    )
    def test_cp_never_negative(self, base_atk, base_def, base_stam):
        for iv in range(16):
            for level in [1.0, 10.0, 20.0, 30.0, 40.0, 50.0]:
                cpm = cpm_for_level(level)
                result = cp(base_atk, base_def, base_stam, iv, iv, iv, cpm)
                assert result >= 10

    @pytest.mark.parametrize(
        "base_atk,base_def,base_stam",
        [
            (300, 182, 214),
            (112, 95, 111),
            (263, 201, 209),
            (121, 152, 155),
        ],
    )
    def test_cp_hundo_is_max(self, base_atk, base_def, base_stam):
        """15/15/15 produce el CP máximo para una especie y nivel dados."""
        cpm = 0.79030001
        cp_max = cp(base_atk, base_def, base_stam, 15, 15, 15, cpm)
        cp_low = cp(base_atk, base_def, base_stam, 0, 0, 0, cpm)
        assert cp_max >= cp_low
