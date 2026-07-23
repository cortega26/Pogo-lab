"""Tests de engine/catch.py — probabilidad de captura.

Fixtures verificadas:
  Charmander (BCR=0.20) L15, modificadores estándar → ~55.9 %
  Legendary raid (BCR=0.02) L20, golden razz + curva → ~16.9 %
"""

import pytest

from engine.catch import (
    catch_multiplier,
    catch_probability,
    catch_probability_from_cpm,
)


class TestCatchMultiplier:
    def test_neutral_is_one(self):
        assert catch_multiplier() == 1.0

    def test_full_modifiers(self):
        m = catch_multiplier(
            ball=1.0,
            berry=1.5,
            curveball=1.7,
            throw=1.15,
            medal=1.3,
        )
        assert m == pytest.approx(3.81225)

    def test_legendary_raid_modifiers(self):
        m = catch_multiplier(
            ball=1.0,
            berry=2.5,
            curveball=1.7,
            throw=1.85,
            medal=1.4,
        )
        assert m == pytest.approx(11.0075)

    def test_master_ball_is_guaranteed(self):
        """Master Ball multiplier enorme, no hay probabilidad computable aquí."""
        m = catch_multiplier(ball=100.0)
        assert m > 1.0


class TestCatchProbability:
    def test_charmander_l15_standard(self):
        """Charmander BCR=0.20, L15, razz+curva+great+medal oro.

        CPM L15 = 0.51739395
        Multiplier = 1.0 * 1.5 * 1.7 * 1.15 * 1.3 = 3.81225
        P = 1 - (1 - 0.20/(2*0.51739395))^3.81225
          = 1 - (1 - 0.19327...)^3.81225
          = 1 - 0.80673^3.81225
          = 1 - 0.44111
          ≈ 0.55889
        """
        p = catch_probability(
            bcr=0.20,
            level=15.0,
            multiplier=catch_multiplier(berry=1.5, curveball=1.7, throw=1.15, medal=1.3),
        )
        assert p == pytest.approx(0.55889, abs=0.001)

    def test_legendary_raid_l20(self):
        """Legendary raid BCR=0.02, L20, golden razz+curva+excellent+medal platino.

        CPM L20 = 0.59740001
        Multiplier = 1.0 * 2.5 * 1.7 * 1.85 * 1.4 = 11.0075
        P = 1 - (1 - 0.02/(2*0.59740001))^11.0075
          = 1 - (1 - 0.016739...)^11.0075
          = 1 - 0.98326^11.0075
          ≈ 0.16912
        """
        p = catch_probability(
            bcr=0.02,
            level=20.0,
            multiplier=catch_multiplier(berry=2.5, curveball=1.7, throw=1.85, medal=1.4),
        )
        assert p == pytest.approx(0.16912, abs=0.001)

    def test_guaranteed_capture(self):
        """Con BCR muy alto y multiplicador enorme, P → 1.0."""
        p = catch_probability(bcr=1.0, level=1.0, multiplier=100.0)
        assert p == pytest.approx(1.0, abs=0.001)

    def test_impossible_capture(self):
        """BCR=0 da probabilidad 0."""
        p = catch_probability(bcr=0.0, level=20.0, multiplier=1.0)
        assert p == 0.0

    def test_probability_in_range(self):
        """La probabilidad siempre está en [0, 1]."""
        for bcr in [0.01, 0.1, 0.5, 0.9]:
            for level in [1.0, 10.0, 20.0, 30.0, 40.0]:
                p = catch_probability(bcr, level, 1.0)
                assert 0.0 <= p <= 1.0

    def test_higher_multiplier_gives_higher_probability(self):
        p1 = catch_probability(0.20, 15.0, 2.0)
        p2 = catch_probability(0.20, 15.0, 4.0)
        assert p2 > p1

    def test_higher_level_gives_lower_probability(self):
        p1 = catch_probability(0.20, 10.0, 1.0)
        p2 = catch_probability(0.20, 20.0, 1.0)
        assert p1 > p2


class TestCatchProbabilityFromCpm:
    def test_same_as_level_based(self):
        from engine.stats import cpm_for_level

        cpm = cpm_for_level(15.0)
        p1 = catch_probability(0.20, 15.0, 3.81225)
        p2 = catch_probability_from_cpm(0.20, cpm, 3.81225)
        assert p1 == pytest.approx(p2)
