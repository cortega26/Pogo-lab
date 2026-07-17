"""Tests de integracion para apps/calculators — servicio + URL compartible."""

import re
from datetime import UTC, datetime

import pytest

from apps.calculators.services import (
    CalcInput,
    CalcResult,
    _round,
    compute_scenario,
    compute_scenario_cached,
    decode_share_url,
    encode_share_url,
)
from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter


def _utc(year, month, day):
    return datetime(year, month, day, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _seeded_mechanic(db):  # noqa: ARG001
    """Crea la mecanica trade_iv con un ruleset publicado para tests de calculadora."""
    Mechanic.objects.create(
        slug="iv-en-intercambios",
        key="trade_iv",
        name="IV en intercambios",
        status="active",
    )
    rs = MechanicRuleSet.objects.create(
        mechanic=Mechanic.objects.get(key="trade_iv"),
        version=1,
        name="Ruleset de prueba",
        effective_from=_utc(2026, 1, 1),
        is_published=True,
    )
    params_data = [
        {"key": "floor.friendship.good", "value": 1, "data_type": "integer", "unit": "int"},
        {"key": "floor.friendship.great", "value": 2, "data_type": "integer", "unit": "int"},
        {"key": "floor.friendship.ultra", "value": 3, "data_type": "integer", "unit": "int"},
        {"key": "floor.friendship.best", "value": 5, "data_type": "integer", "unit": "int"},
        {"key": "floor.lucky", "value": 12, "data_type": "integer", "unit": "int"},
    ]
    for pd in params_data:
        RuleParameter.objects.create(ruleset=rs, **pd)


class TestCalcInput:
    def test_create_input(self):
        inputs = CalcInput(
            friendship_level="best",
            trade_type="lucky",
            n=10,
            target_kind="hundo",
        )
        assert inputs.friendship_level == "best"
        assert inputs.n == 10

    def test_defaults(self):
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="hundo",
        )
        assert inputs.threshold is None
        assert inputs.confidence == 0.5


class TestCalcResult:
    def test_default_assumptions_empty(self):
        result = CalcResult(
            p_per_trade=0.5,
            p_cumulative=0.9,
            expected_successes=5.0,
            p_zero=0.1,
            trades_for_confidence=10,
            floor=1,
            k=15,
            ruleset_version=1,
            algorithm_version="1.0.0",
        )
        assert result.assumptions == []
        assert result.params == {}


@pytest.mark.django_db
class TestComputeScenario:
    def test_hundo_normal(self):
        """Good friend, normal trade, hundo target, n=1."""
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="hundo",
        )
        result = compute_scenario(inputs)
        assert result.floor == 1
        assert result.k == 15
        assert result.p_per_trade == pytest.approx(1.0 / 3375.0, abs=1e-6)
        assert result.ruleset_version is not None

    def test_lucky_hundo(self):
        """Best friend, lucky, hundo target, n=10."""
        inputs = CalcInput(
            friendship_level="best",
            trade_type="lucky",
            n=10,
            target_kind="hundo",
        )
        result = compute_scenario(inputs)
        assert result.floor == 12
        assert result.k == 4
        assert result.p_per_trade == pytest.approx(1.0 / 64.0, abs=1e-6)
        assert result.trades_for_confidence == 45  # n para 50%

    def test_best_friends_hundo(self):
        """Best friend, normal, hundo -> f=5."""
        inputs = CalcInput(
            friendship_level="best",
            trade_type="normal",
            n=5,
            target_kind="hundo",
        )
        result = compute_scenario(inputs)
        assert result.floor == 5
        assert result.k == 11
        assert result.p_per_trade == pytest.approx(1.0 / 1331.0, abs=1e-6)

    def test_stat_min_target(self):
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="stat_min",
            threshold=15,
        )
        result = compute_scenario(inputs)
        assert result.floor == 1
        assert result.p_per_trade == pytest.approx(1.0 / 15.0, abs=1e-6)

    def test_sum_min_target(self):
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="sum_min",
            threshold=42,
        )
        result = compute_scenario(inputs)
        # f=1, k=15, suma minima 42/45
        assert result.floor == 1
        assert result.p_per_trade > 0

    def test_assumptions_included(self):
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="hundo",
        )
        result = compute_scenario(inputs)
        assert len(result.assumptions) == 3

    def test_lucky_assumptions(self):
        inputs = CalcInput(
            friendship_level="best",
            trade_type="lucky",
            n=1,
            target_kind="hundo",
        )
        result = compute_scenario(inputs)
        assert any("Lucky" in a for a in result.assumptions)
        assert result.algorithm_version == "1.0.0"

    def test_round_returns_float(self):
        assert isinstance(_round(0.123456789), float)
        assert _round(0.123456789) == 0.123457

    def test_floor_override_applied(self):
        """floor_override reemplaza el piso del ruleset."""
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="hundo",
            floor_override=12,
        )
        result = compute_scenario(inputs)
        assert result.floor == 12
        assert result.ruleset_version is None
        assert result.p_per_trade == pytest.approx(1.0 / 64.0, abs=1e-6)
        assert any("manual" in a for a in result.assumptions)

    def test_floor_override_assumptions_replace_ruleset_claim(self):
        """Con floor_override no se afirma 'datos comunitarios verificados'."""
        inputs = CalcInput(
            friendship_level="best",
            trade_type="lucky",
            n=10,
            target_kind="hundo",
            floor_override=15,
        )
        result = compute_scenario(inputs)
        assert not any("comunitarios" in a for a in result.assumptions)
        assert any("manual" in a for a in result.assumptions)

    def test_floor_override_in_share_url_roundtrip(self):
        """floor_override se preserva en la URL compartible."""
        original = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=10,
            target_kind="hundo",
            floor_override=12,
        )
        encoded = encode_share_url(original)
        decoded = decode_share_url(encoded)
        assert decoded.floor_override == 12
        result = compute_scenario(decoded)
        assert result.floor == 12


class TestRulesetUnavailableError:
    @pytest.mark.django_db
    def test_resolve_floor_raises_without_mechanic(self):
        """Sin mecanica trade_iv, _resolve_floor lanza RulesetUnavailableError."""
        Mechanic.objects.filter(key="trade_iv").delete()
        from apps.calculators.services import RulesetUnavailableError, _resolve_floor

        with pytest.raises(RulesetUnavailableError):
            _resolve_floor("good", "normal")


@pytest.mark.django_db
class TestComputeScenarioCached:
    def test_returns_same_as_compute(self):
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="hundo",
        )
        result = compute_scenario_cached(inputs)
        expected = compute_scenario(inputs)
        assert result.p_per_trade == expected.p_per_trade
        assert result.ruleset_version == expected.ruleset_version

    def test_cache_hit_returns_same(self):
        inputs = CalcInput(
            friendship_level="best",
            trade_type="lucky",
            n=10,
            target_kind="hundo",
        )
        r1 = compute_scenario_cached(inputs)
        r2 = compute_scenario_cached(inputs)
        assert r1.p_per_trade == r2.p_per_trade


class TestShareURLRoundTrip:
    def test_encode_decode_roundtrip(self):
        original = CalcInput(
            friendship_level="best",
            trade_type="lucky",
            n=10,
            target_kind="hundo",
            confidence=0.9,
        )
        encoded = encode_share_url(original)
        decoded = decode_share_url(encoded)
        assert decoded == original

    def test_with_threshold(self):
        original = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=50,
            target_kind="stat_min",
            threshold=15,
            confidence=0.95,
        )
        encoded = encode_share_url(original)
        decoded = decode_share_url(encoded)
        assert decoded == original
        assert decoded.threshold == 15

    def test_invalid_string_raises(self):
        with pytest.raises(ValueError, match="URL de calculo invalida"):
            decode_share_url("not-valid-base64!!!")

    def test_unknown_version_raises(self):
        with pytest.raises(ValueError, match="Version de URL no soportada"):
            decode_share_url("eyJ2IjoiVk1VTFRJIiwidGVzdCI6MX0")

    def test_deterministic_encoding(self):
        inputs = CalcInput(
            friendship_level="good",
            trade_type="normal",
            n=1,
            target_kind="hundo",
        )
        e1 = encode_share_url(inputs)
        e2 = encode_share_url(inputs)
        assert e1 == e2


@pytest.mark.django_db
class TestCalculatorViews:
    def test_get_renders_form(self, client):
        resp = client.get("/es/calculadora/")
        assert resp.status_code == 200
        html = resp.content.decode()
        assert "Calculadora" in html
        assert 'hx-post="' in html or "csrfmiddlewaretoken" in html

    def test_post_returns_results(self, client):
        resp = client.post(
            "/es/calculadora/",
            {
                "friendship_level": "good",
                "trade_type": "normal",
                "n": "1",
                "target_kind": "hundo",
                "confidence": "0.5",
            },
        )
        assert resp.status_code == 200
        html = resp.content.decode()
        assert "Resultados" in html

    def test_post_with_threshold(self, client):
        resp = client.post(
            "/es/calculadora/",
            {
                "friendship_level": "best",
                "trade_type": "lucky",
                "n": "10",
                "target_kind": "stat_min",
                "threshold": "15",
                "confidence": "0.9",
            },
        )
        assert resp.status_code == 200

    def test_share_url_reproduces_calculation(self, client):
        """E2E reducido: URL compartible reproduce el calculo exacto."""
        post_resp = client.post(
            "/es/calculadora/",
            {
                "friendship_level": "best",
                "trade_type": "lucky",
                "n": "10",
                "target_kind": "hundo",
                "confidence": "0.5",
            },
        )
        assert post_resp.status_code == 200
        post_html = post_resp.content.decode()

        match = re.search(r"share=([a-zA-Z0-9_-]+)", post_html)
        assert match is not None, "No se encontro share URL en la respuesta"
        share_code = match.group(1)

        get_resp = client.get(f"/es/calculadora/?share={share_code}")
        assert get_resp.status_code == 200
        get_html = get_resp.content.decode()
        assert "Resultados" in get_html or "Piso (f)" in get_html

    def test_htmx_partial_returns_no_layout(self, client):
        resp = client.post(
            "/es/calculadora/",
            {
                "friendship_level": "good",
                "trade_type": "normal",
                "n": "1",
                "target_kind": "hundo",
            },
            HTTP_HX_REQUEST="true",
        )
        assert resp.status_code == 200
        html = resp.content.decode()
        assert "Resultados" in html
        assert "<html" not in html  # Es partial, no pagina completa
