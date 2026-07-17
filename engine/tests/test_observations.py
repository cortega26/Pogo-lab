"""Tests del engine para validacion de observaciones.

Fixtures calculadas a mano + property-based.
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from engine.observations import ivs_consistent_with_floor


class TestIVsConsistentWithFloor:
    """Fixtures calculadas a mano."""

    def test_lucky_floor_12_all_above(self):
        """f=12, (12,15,13) -> True: todos en o sobre el piso."""
        assert ivs_consistent_with_floor(12, 12, 15, 13) is True

    def test_lucky_floor_12_one_below(self):
        """f=12, (11,15,15) -> False: atk=11 < 12."""
        assert ivs_consistent_with_floor(12, 11, 15, 15) is False

    def test_floor_1_all_at_floor(self):
        """f=1, (1,1,1) -> True: en el piso."""
        assert ivs_consistent_with_floor(1, 1, 1, 1) is True

    def test_floor_1_one_below(self):
        """f=1, (0,5,5) -> False: atk=0 < 1."""
        assert ivs_consistent_with_floor(1, 0, 5, 5) is False

    def test_floor_5_mixed(self):
        """f=5, (5,7,4) -> False: hp=4 < 5."""
        assert ivs_consistent_with_floor(5, 5, 7, 4) is False

    def test_floor_5_all_above(self):
        """f=5, (7,8,6) -> True."""
        assert ivs_consistent_with_floor(5, 7, 8, 6) is True

    def test_floor_0_all_above(self):
        """f=0, cualquier IV en [0,15] es consistente."""
        assert ivs_consistent_with_floor(0, 0, 0, 0) is True
        assert ivs_consistent_with_floor(0, 15, 15, 15) is True

    def test_floor_15_all_at_floor(self):
        """f=15, (15,15,15) -> True: hundo en Lucky."""
        assert ivs_consistent_with_floor(15, 15, 15, 15) is True

    def test_floor_15_one_below(self):
        """f=15, (14,15,15) -> False."""
        assert ivs_consistent_with_floor(15, 14, 15, 15) is False

    def test_def_below_floor(self):
        """def_ por debajo del piso."""
        assert ivs_consistent_with_floor(3, 5, 2, 5) is False

    def test_hp_below_floor(self):
        """hp por debajo del piso."""
        assert ivs_consistent_with_floor(3, 5, 5, 1) is False

    def test_all_below_floor(self):
        """Los tres stats por debajo del piso."""
        assert ivs_consistent_with_floor(10, 3, 4, 5) is False


class TestIVsConsistentWithFloorPropertyBased:
    """Property-based tests con Hypothesis."""

    @given(f=st.integers(min_value=0, max_value=15))
    @settings(max_examples=100)
    def test_floor_to_floor_is_always_consistent(self, f: int):
        """Para todo f, (f, f, f) siempre es True."""
        assert ivs_consistent_with_floor(f, f, f, f) is True

    @given(f=st.integers(min_value=1, max_value=15))
    @settings(max_examples=50)
    def test_below_floor_is_inconsistent(self, f: int):
        """Para f>0, un IV = f-1 es inconsistente."""
        assert ivs_consistent_with_floor(f, f - 1, f, f) is False
        assert ivs_consistent_with_floor(f, f, f - 1, f) is False
        assert ivs_consistent_with_floor(f, f, f, f - 1) is False

    @given(
        f=st.integers(min_value=0, max_value=15),
        a=st.integers(min_value=0, max_value=15),
        d=st.integers(min_value=0, max_value=15),
        h=st.integers(min_value=0, max_value=15),
    )
    @settings(max_examples=200)
    def test_result_matches_min_check(self, f: int, a: int, d: int, h: int):
        """El resultado booleano equivale a 'min(atk, def_, hp) >= f'."""
        expected = min(a, d, h) >= f
        assert ivs_consistent_with_floor(f, a, d, h) is expected
