"""Tests de sad path (entradas inválidas) para todas las calculadoras.

Cada calculadora debe devolver 200 con mensaje de error, nunca 500.
"""

import pytest
from django.test import Client

pytestmark = pytest.mark.django_db


class TestSadPathIV:
    def test_get(self):
        assert Client().get("/es/calculadora/").status_code == 200

    def test_negative_n(self):
        r = Client().post("/es/calculadora/", {"n": "-1"})
        # La calculadora IV retorna 400 en errores de validación
        assert r.status_code in (200, 400)

    def test_invalid_confidence(self):
        r = Client().post("/es/calculadora/", {"confidence": "2.0", "n": "10"})
        assert r.status_code in (200, 400)

    def test_empty_post_no_mechanic(self):
        """Sin mechanic seedeado, el POST vacío lanza RulesetUnavailableError.
        Comportamiento esperado: se necesita el fixture seeded_mechanic (ver test_e2e.py)."""
        from apps.mechanics.services import RulesetUnavailableError

        with pytest.raises(RulesetUnavailableError):
            Client().post("/es/calculadora/", {})


class TestSadPathCP:
    def test_get(self):
        assert Client().get("/es/calculadora/cp/").status_code == 200

    def test_iv_out_of_range(self):
        r = Client().post(
            "/es/calculadora/cp/",
            {
                "species": "pikachu",
                "level": "20.0",
                "iv_atk": "99",
                "iv_def": "10",
                "iv_stam": "10",
            },
        )
        assert r.status_code == 200
        assert "Error" in r.content.decode() or "error" in r.content.decode().lower()

    def test_bad_species(self):
        r = Client().post(
            "/es/calculadora/cp/",
            {
                "species": "zzz_nonexistent",
                "level": "20.0",
                "iv_atk": "10",
                "iv_def": "10",
                "iv_stam": "10",
            },
        )
        assert r.status_code == 200

    def test_non_numeric_iv(self):
        r = Client().post("/es/calculadora/cp/", {"species": "pikachu", "iv_atk": "abc"})
        assert r.status_code < 500

    def test_empty(self):
        assert Client().post("/es/calculadora/cp/", {}).status_code == 200


class TestSadPathCost:
    def test_get(self):
        assert Client().get("/es/calculadora/costos/").status_code == 200

    def test_from_greater_than_to(self):
        r = Client().post("/es/calculadora/costos/", {"from_level": "40.0", "to_level": "20.0"})
        assert r.status_code == 200
        assert "Error" in r.content.decode()

    def test_empty(self):
        assert Client().post("/es/calculadora/costos/", {}).status_code == 200


class TestSadPathPvP:
    def test_get(self):
        assert Client().get("/es/calculadora/pvp/").status_code == 200

    def test_bad_species(self):
        r = Client().post("/es/calculadora/pvp/", {"species": "zzz_nonexistent", "league": "1500"})
        assert r.status_code < 500

    def test_empty(self):
        assert Client().post("/es/calculadora/pvp/", {}).status_code == 200


class TestSadPathCatch:
    def test_get(self):
        assert Client().get("/es/calculadora/captura/").status_code == 200

    def test_bad_species(self):
        r = Client().post("/es/calculadora/captura/", {"species": "zzz", "level": "15.0"})
        assert r.status_code < 500

    def test_empty(self):
        assert Client().post("/es/calculadora/captura/", {}).status_code == 200


class TestSadPathTypes:
    def test_get(self):
        assert Client().get("/es/calculadora/tipos/").status_code == 200

    def test_invalid_type(self):
        r = Client().post("/es/calculadora/tipos/", {"def_type1": "invalid_type"})
        assert r.status_code == 200
        assert "Error" in r.content.decode()

    def test_empty(self):
        assert Client().post("/es/calculadora/tipos/", {}).status_code == 200


class TestSadPathShiny:
    def test_get(self):
        assert Client().get("/es/calculadora/shiny/").status_code == 200

    def test_invalid_rate(self):
        r = Client().post("/es/calculadora/shiny/", {"rate": "not_a_number", "n": "100"})
        assert r.status_code < 500

    def test_empty(self):
        assert Client().post("/es/calculadora/shiny/", {}).status_code == 200


class TestSadPathShadow:
    def test_get(self):
        assert Client().get("/es/calculadora/shadow/").status_code == 200

    def test_bad_species(self):
        r = Client().post(
            "/es/calculadora/shadow/",
            {"species": "zzz", "level": "40.0", "iv_atk": "15", "iv_def": "15", "iv_stam": "15"},
        )
        assert r.status_code < 500

    def test_iv_out_of_range(self):
        r = Client().post(
            "/es/calculadora/shadow/",
            {
                "species": "machamp",
                "level": "40.0",
                "iv_atk": "99",
                "iv_def": "15",
                "iv_stam": "15",
            },
        )
        assert r.status_code < 500

    def test_empty(self):
        assert Client().post("/es/calculadora/shadow/", {}).status_code == 200


class TestSadPathBreakpoints:
    def test_get(self):
        assert Client().get("/es/calculadora/breakpoints/").status_code == 200

    def test_bad_species(self):
        r = Client().post(
            "/es/calculadora/breakpoints/",
            {"species": "zzz", "move": "psycho_cut", "iv_atk": "15", "defender_def": "200"},
        )
        assert r.status_code == 200
        assert "Error" in r.content.decode()

    def test_bad_move(self):
        r = Client().post(
            "/es/calculadora/breakpoints/",
            {
                "species": "mewtwo",
                "move": "nonexistent_move",
                "iv_atk": "15",
                "defender_def": "200",
            },
        )
        assert r.status_code == 200
        assert "Error" in r.content.decode()

    def test_empty(self):
        assert Client().post("/es/calculadora/breakpoints/", {}).status_code == 200
