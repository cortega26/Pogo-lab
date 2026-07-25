"""Tests de sad path (entradas inválidas) para todas las calculadoras.

Cada calculadora debe devolver 200 con mensaje de error, nunca 500.
"""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client
from hypothesis import HealthCheck, given, settings
from hypothesis import strategies as st

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    user_model = get_user_model()
    return user_model.objects.create_user(email="sad@example.com", password="pass123")


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
        """Plan 053 (revisión de Fase 4): el iv_atk crudo debe rechazarse
        con error, no sustituirse en silencio por el default (10) antes de
        validar — antes se revalidaba el default ya calculado, no el input."""
        r = Client().post("/es/calculadora/cp/", {"species": "pikachu", "iv_atk": "abc"})
        assert r.status_code == 200
        assert r.context["error"] is not None

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

    def test_infinite_to_level_does_not_500(self):
        """Plan 053: to_level=inf crasheaba con OverflowError sin capturar
        (round((inf-1)*2) no puede convertirse a entero)."""
        r = Client().post("/es/calculadora/costos/", {"from_level": "20", "to_level": "inf"})
        assert r.status_code == 200
        assert "Error" in r.content.decode()

    def test_nan_from_level_does_not_500(self):
        r = Client().post("/es/calculadora/costos/", {"from_level": "nan", "to_level": "40"})
        assert r.status_code == 200
        assert "Error" in r.content.decode()


class TestSadPathPvP:
    def test_get(self):
        assert Client().get("/es/calculadora/pvp/").status_code == 200

    def test_bad_species(self):
        r = Client().post("/es/calculadora/pvp/", {"species": "zzz_nonexistent", "league": "1500"})
        assert r.status_code < 500

    def test_empty(self):
        assert Client().post("/es/calculadora/pvp/", {}).status_code == 200

    def test_ranking_shows_migration_note_and_hp_column(self):
        """Plan 048: el ranking corregido debe avisar al usuario final que el
        orden puede diferir de cálculos anteriores (no solo documentación
        interna en spec.md), y exponer el HP entero real por spread."""
        r = Client().post("/es/calculadora/pvp/", {"species": "medicham", "league": "1500"})
        content = r.content.decode()
        assert "2026-07-24" in content
        assert "HP" in content


class TestSadPathCatch:
    def test_get(self):
        assert Client().get("/es/calculadora/captura/").status_code == 200

    def test_bad_species(self):
        r = Client().post("/es/calculadora/captura/", {"species": "zzz", "level": "15.0"})
        assert r.status_code < 500

    def test_empty(self):
        assert Client().post("/es/calculadora/captura/", {}).status_code == 200

    def test_nan_ball_multiplier_is_rejected_not_silently_computed(self):
        """Plan 053: ball/berry/throw/medal sin validar podían producir un
        multiplicador NaN sin crashear, mostrando "nan%" de probabilidad de
        captura al usuario en vez de rechazar la entrada."""
        r = Client().post(
            "/es/calculadora/captura/", {"species": "charmander", "level": "15", "ball": "nan"}
        )
        assert r.status_code == 200
        assert "Error" in r.content.decode()


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

    def test_rate_one_with_negative_n_does_not_500(self):
        """Plan 053: p_at_least_one(1.0, n<0) = 0.0**(negativo) -> ZeroDivisionError
        sin capturar. rate=1.0 y n negativo no deben llegar al engine."""
        r = Client().post("/es/calculadora/shiny/", {"rate": "1.0", "n": "-1"})
        assert r.status_code == 200
        assert "Error" in r.content.decode()

    def test_non_numeric_n_is_rejected_not_silently_defaulted(self):
        """Plan 053 (revisión de Fase 4): n="abc" debe rechazarse con error,
        no sustituirse en silencio por el default (100) antes de validar."""
        r = Client().post("/es/calculadora/shiny/", {"rate": "0.002", "n": "abc"})
        assert r.status_code == 200
        assert r.context["error"] is not None


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
        """Plan 053: antes se aceptaba en silencio un IV fuera de [0,15] y se
        mostraba un CP/HP calculado con ese valor inválido como si fuera
        real. Ahora debe rechazarse con un error, no solo evitar el 500."""
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
        assert r.status_code == 200
        assert "Error" in r.content.decode()

    def test_non_numeric_iv_is_rejected_not_silently_defaulted(self):
        """Plan 053 (revisión de Fase 4): iv_atk="abc" debe rechazarse con
        error, no sustituirse en silencio por el default (15) antes de
        validar."""
        r = Client().post(
            "/es/calculadora/shadow/",
            {"species": "machamp", "level": "40.0", "iv_atk": "abc"},
        )
        assert r.status_code == 200
        assert r.context["error"] is not None

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


class TestCrossCalculatorShareURL:
    """Plan 053: _get_params descartaba el calc_type devuelto por
    decode_calc_share, así que una share URL de una calculadora se
    aceptaba en cualquier otra (cálculo cruzado)."""

    def test_pvp_share_url_is_ignored_by_cp_calculator(self):
        """El selector de especie de la calculadora CP siempre lista todas
        las especies (incluida Medicham) como <option>, así que se verifica
        el contexto real (qué especie quedó seleccionada), no un substring
        en el HTML completo."""
        from apps.calculators.services import encode_calc_share

        pvp_share = encode_calc_share("pvp", {"species": "medicham", "league": "1500"})
        r = Client().get(f"/es/calculadora/cp/?share={pvp_share}")
        assert r.status_code == 200
        assert r.context["species_id"] != "medicham"
        assert r.context["result"] is None


_SUSPICIOUS_VALUES = st.one_of(
    st.just("nan"),
    st.just("inf"),
    st.just("-inf"),
    st.just("Infinity"),
    st.just(""),
    st.just("0"),
    st.just("-1"),
    st.just("abc"),
    st.just("15; DROP TABLE x"),
    st.integers(min_value=-(10**9), max_value=10**9).map(str),
)

# (url, campo) para cada calculadora; cubre los campos numéricos de entrada
# de las 8 calculadoras (plan 053, paso 5: fuzzing genérico).
_CALCULATOR_NUMERIC_FIELDS = [
    ("/es/calculadora/costos/", "from_level"),
    ("/es/calculadora/costos/", "to_level"),
    ("/es/calculadora/captura/", "ball"),
    ("/es/calculadora/captura/", "berry"),
    ("/es/calculadora/captura/", "throw"),
    ("/es/calculadora/captura/", "medal"),
    ("/es/calculadora/captura/", "level"),
    ("/es/calculadora/shiny/", "rate"),
    ("/es/calculadora/shiny/", "n"),
    ("/es/calculadora/shiny/", "confidence"),
    ("/es/calculadora/shadow/", "level"),
    ("/es/calculadora/shadow/", "iv_atk"),
    ("/es/calculadora/shadow/", "iv_def"),
    ("/es/calculadora/shadow/", "iv_stam"),
    ("/es/calculadora/breakpoints/", "iv_atk"),
    ("/es/calculadora/breakpoints/", "defender_def"),
    ("/es/calculadora/cp/", "level"),
    ("/es/calculadora/cp/", "iv_atk"),
    ("/es/calculadora/pvp/", "league"),
]


class TestCalculatorFuzzing:
    """Plan 053, paso 5: fuzzing genérico sobre todas las calculadoras.

    Ninguna combinación de (endpoint, campo numérico, valor sospechoso)
    debe producir un 500 — nan/inf/enteros extremos deben rechazarse con
    un error controlado, nunca llegar sin validar al engine."""

    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture], deadline=None)
    @given(value=_SUSPICIOUS_VALUES, endpoint=st.sampled_from(_CALCULATOR_NUMERIC_FIELDS))
    def test_no_500_for_any_suspicious_value_in_any_calculator(self, value, endpoint):
        url, field = endpoint
        r = Client().post(url, {field: value})
        assert r.status_code < 500, f"{url} con {field}={value!r} devolvió {r.status_code}"


class TestBulkAddSadPath:
    """Plan 055: inputs estructuralmente inválidos devuelven 4xx."""

    def test_bulk_with_null_item(self, client, user):
        """[null] en JSON no produce 500."""
        client.force_login(user)
        r = client.post(
            "/es/intercambios/lotes/",
            data={"observations_json": "[null]"},
        )
        assert r.status_code == 400

    def test_bulk_with_non_dict_item(self, client, user):
        """[42] en JSON no produce 500."""
        client.force_login(user)
        r = client.post(
            "/es/intercambios/lotes/",
            data={"observations_json": "[42]"},
        )
        assert r.status_code == 400
