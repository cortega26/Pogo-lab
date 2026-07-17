"""Tests E2E con Playwright para la calculadora y trades."""

import pytest

pytestmark = [
    pytest.mark.skipif(True, reason="Playwright E2E requiere navegador instalado y servidor vivo"),
    pytest.mark.django_db,
]


@pytest.fixture(scope="module")
def _seeded_mechanic(django_db_blocker, django_db_used):  # noqa: ARG001
    """Seed de datos para E2E."""
    from datetime import UTC, datetime

    from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter

    with django_db_blocker.unblock():
        mechanic = Mechanic.objects.create(
            slug="iv-en-intercambios",
            key="trade_iv",
            name="IV en intercambios",
            status="active",
        )
        rs = MechanicRuleSet.objects.create(
            mechanic=mechanic,
            version=1,
            name="Ruleset E2E",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            is_published=True,
        )
        for pd in [
            {"key": "floor.friendship.good", "value": 1, "data_type": "integer"},
            {"key": "floor.friendship.great", "value": 2, "data_type": "integer"},
            {"key": "floor.friendship.ultra", "value": 3, "data_type": "integer"},
            {"key": "floor.friendship.best", "value": 5, "data_type": "integer"},
            {"key": "floor.lucky", "value": 12, "data_type": "integer"},
        ]:
            RuleParameter.objects.create(ruleset=rs, **pd)


@pytest.mark.skipif(True, reason="Requiere playwright install")
def test_calculator_flow(live_server, _seeded_mechanic):
    """Visitante calcula una probabilidad."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/es/calculadora/")

        page.select_option("#friendship_level", "best")
        page.select_option("#trade_type", "lucky")
        page.fill("#n", "10")
        page.select_option("#target_kind", "hundo")
        page.select_option("#confidence", "0.5")
        page.click("button[type=submit]")

        page.wait_for_selector("text=Resultados", timeout=5000)
        content = page.text_content("body")
        assert content is not None
        assert "Piso (f)" in content

        browser.close()


@pytest.mark.skipif(True, reason="Requiere playwright install")
def test_share_url_reproduces_calculation(live_server, _seeded_mechanic):
    """URL compartible reproduce el calculo."""
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/es/calculadora/")

        page.select_option("#friendship_level", "best")
        page.select_option("#trade_type", "lucky")
        page.fill("#n", "10")
        page.select_option("#target_kind", "hundo")
        page.select_option("#confidence", "0.5")
        page.click("button[type=submit]")

        page.wait_for_selector("text=Resultados", timeout=5000)
        share_input = page.locator("input[readonly]")
        share_url = share_input.input_value()
        assert "share=" in share_url

        page.goto(share_url)
        page.wait_for_selector("text=Resultados", timeout=5000)
        content = page.text_content("body")
        assert content is not None
        assert "Piso (f)" in content

        browser.close()


@pytest.mark.skipif(True, reason="Requiere playwright install")
def test_trade_session_flow(live_server, _seeded_mechanic):
    """Usuario registra una sesion de intercambios."""
    from django.contrib.auth import get_user_model
    from playwright.sync_api import sync_playwright

    user_model = get_user_model()
    user_model.objects.create_user(email="test@example.com", password="pass123")

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/cuenta/login/")
        page.fill("input[name=login]", "test@example.com")
        page.fill("input[name=password]", "pass123")
        page.click("button[type=submit]")

        page.goto(f"{live_server.url}/es/intercambios/")
        page.wait_for_selector("text=Sesiones de intercambios", timeout=5000)

        page.click("text=Nueva sesion")
        page.fill("input[name=label]", "Sesion E2E")
        page.click("button[type=submit]")

        content = page.text_content("body")
        assert content is not None
        assert "Sesion E2E" in content

        browser.close()


@pytest.mark.skipif(True, reason="Requiere playwright install")
def test_trade_dashboard_flow(live_server, _seeded_mechanic):
    """Usuario consulta su dashboard de intercambios."""
    from datetime import UTC, datetime

    from django.contrib.auth import get_user_model
    from playwright.sync_api import sync_playwright

    from apps.trades.services import register_observation

    user_model = get_user_model()
    user = user_model.objects.create_user(email="test@example.com", password="pass123")

    register_observation(
        owner_id=user.pk,
        observed_at=datetime(2026, 7, 17, tzinfo=UTC),
        friendship_level="best",
        trade_type="lucky",
        atk=12,
        def_=15,
        hp=13,
    )
    register_observation(
        owner_id=user.pk,
        observed_at=datetime(2026, 7, 17, tzinfo=UTC),
        friendship_level="good",
        trade_type="normal",
        atk=5,
        def_=5,
        hp=5,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/cuenta/login/")
        page.fill("input[name=login]", "test@example.com")
        page.fill("input[name=password]", "pass123")
        page.click("button[type=submit]")

        page.goto(f"{live_server.url}/es/intercambios/dashboard/")
        page.wait_for_selector("text=Dashboard de intercambios", timeout=5000)

        content = page.text_content("body")
        assert content is not None
        assert "2" in content
        assert "Lucky" in content
        assert "Normal" in content

        browser.close()
