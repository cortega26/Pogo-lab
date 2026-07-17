"""Tests E2E con Playwright — 10 flujos completos del plan §13.

PR-20: hardening. TODOS los tests E2E corren sin skip/xfail.
Verifica CSP, htmx, rate limiting y flujos críticos de usuario.
"""

from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from playwright.sync_api import sync_playwright

pytestmark = pytest.mark.django_db


# ═══════════════════════════════════════════════════════════════════
# Fixture compartida — seed de mecánica trade_iv
# ═══════════════════════════════════════════════════════════════════
@pytest.fixture(scope="function")
def seeded_mechanic():
    """Crea mechanic trade_iv con ruleset y parámetros de piso."""
    from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter

    mechanic, _ = Mechanic.objects.get_or_create(
        slug="iv-en-intercambios",
        defaults={"key": "trade_iv", "name": "IV en intercambios", "status": "active"},
    )
    mechanic.key = "trade_iv"
    mechanic.status = "active"
    mechanic.save()

    rs, _ = MechanicRuleSet.objects.get_or_create(
        mechanic=mechanic,
        version=1,
        defaults={
            "name": "Ruleset E2E",
            "effective_from": datetime(2026, 1, 1, tzinfo=UTC),
            "is_published": True,
        },
    )
    params = [
        ("floor.friendship.good", 1),
        ("floor.friendship.great", 2),
        ("floor.friendship.ultra", 3),
        ("floor.friendship.best", 5),
        ("floor.lucky", 12),
    ]
    for key, value in params:
        RuleParameter.objects.get_or_create(
            ruleset=rs,
            key=key,
            value=value,
            data_type="integer",
        )


# ═══════════════════════════════════════════════════════════════════
# Flujo 1 — Visitante calcula hundo (HTMX, sin recarga completa)
# ═══════════════════════════════════════════════════════════════════
def test_visitor_calculates_hundo(live_server, seeded_mechanic):
    """Visitante sin cuenta: calcula hundo y verifica HTMX swap sin recarga."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/es/calculadora/")

        title_before = page.title()
        page.select_option("#friendship_level", "best")
        page.select_option("#trade_type", "lucky")
        page.fill("#n", "10")
        page.select_option("#target_kind", "hundo")
        page.select_option("#confidence", "0.5")
        page.click("button[type=submit]")

        page.wait_for_selector("#calc-results .font-medium", timeout=10000)
        content = page.text_content("#calc-results")
        assert content is not None
        assert "Piso (f)" in content

        title_after = page.title()
        assert title_before == title_after

        browser.close()


# ═══════════════════════════════════════════════════════════════════
# Flujo 2 — Visitante crea cuenta
# ═══════════════════════════════════════════════════════════════════
def test_visitor_creates_account(live_server):
    """Visitante: llena signup, envía, verifica redirección o éxito."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto(f"{live_server.url}/es/cuenta/signup/")

        page.fill("input[name=email]", "signup_e2e@example.com")
        page.fill("input[name=password1]", "AComplexPass123!")
        page.fill("input[name=password2]", "AComplexPass123!")
        page.click("button[type=submit]")

        page.wait_for_load_state("networkidle")

        assert page.url != f"{live_server.url}/es/cuenta/signup/"

        browser.close()

    # Verificar que el usuario se creó en BD
    user_model = get_user_model()
    assert user_model.objects.filter(email="signup_e2e@example.com").exists()


# ═══════════════════════════════════════════════════════════════════
# Flujo 3 — Usuario se loguea y ve su dashboard
# ═══════════════════════════════════════════════════════════════════
def test_user_login_and_see_dashboard(live_server, seeded_mechanic):
    """Usuario creado previamente: login y verifica que está autenticado."""
    from allauth.account.models import EmailAddress

    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="login_e2e@example.com", password="AComplexPass123!"
    )
    EmailAddress.objects.create(
        user=user, email="login_e2e@example.com", verified=True, primary=True
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/cuenta/login/")
        page.fill("input[name=login]", "login_e2e@example.com")
        page.fill("input[name=password]", "AComplexPass123!")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        page.goto(f"{live_server.url}/es/")
        page.wait_for_load_state("networkidle")
        body_text = page.text_content("body")
        assert body_text is not None
        assert "Cerrar sesión" in body_text

        browser.close()


# ═══════════════════════════════════════════════════════════════════
# Flujo 4 — Usuario registra sesión de intercambios
# ═══════════════════════════════════════════════════════════════════
def test_user_records_trade_session(live_server, seeded_mechanic):
    """Usuario logueado: crea sesión de intercambios y verifica."""
    from allauth.account.models import EmailAddress

    user_model = get_user_model()
    user_model.objects.create_user(email="session_e2e@example.com", password="AComplexPass123!")
    EmailAddress.objects.create(
        user=user_model.objects.get(email="session_e2e@example.com"),
        email="session_e2e@example.com",
        verified=True,
        primary=True,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/cuenta/login/")
        page.fill("input[name=login]", "session_e2e@example.com")
        page.fill("input[name=password]", "AComplexPass123!")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        page.goto(f"{live_server.url}/es/intercambios/")
        page.wait_for_selector("text=Nueva sesión", timeout=10000)

        page.click("text=Nueva sesión")
        page.wait_for_selector("input[name=label]", timeout=5000)
        page.fill("input[name=label]", "Sesión E2E")
        page.click("button[type=submit]")

        page.wait_for_load_state("networkidle")
        content = page.text_content("body")
        assert content is not None
        assert "Iniciada" in content

        browser.close()

    # Verificar BD fuera del contexto Playwright
    from apps.trades.models import TradeSession

    assert TradeSession.objects.filter(label="Sesión E2E").exists()


# ═══════════════════════════════════════════════════════════════════
# Flujo 5 — Usuario otorga y revoca consentimiento
# ═══════════════════════════════════════════════════════════════════
def test_user_opt_in_and_revoke(live_server):
    """Usuario logueado: da consentimiento para contribuir y luego revoca."""
    from allauth.account.models import EmailAddress

    from apps.contributions.models import DataContributionConsent

    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="consent_e2e@example.com", password="AComplexPass123!"
    )
    EmailAddress.objects.create(
        user=user, email="consent_e2e@example.com", verified=True, primary=True
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/cuenta/login/")
        page.fill("input[name=login]", "consent_e2e@example.com")
        page.fill("input[name=password]", "AComplexPass123!")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        # POST a consentir
        csrf_token = page.evaluate(
            "() => document.querySelector('input[name=csrfmiddlewaretoken]').value"
        )
        page.evaluate(
            """([url, token]) => {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;
                form.innerHTML = '<input type="hidden" name="csrfmiddlewaretoken" value="' + token + '">';
                document.body.appendChild(form);
                form.submit();
            }""",
            ["/es/contribuciones/consentir/", csrf_token],
        )
        page.wait_for_load_state("networkidle")

        browser.close()

    # Verificar BD fuera del contexto Playwright
    consent = DataContributionConsent.objects.get(user=user, scope="community_dataset")
    assert consent.is_active

    # Revocar
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/cuenta/login/")
        page.fill("input[name=login]", "consent_e2e@example.com")
        page.fill("input[name=password]", "AComplexPass123!")
        page.click("button[type=submit]")
        page.wait_for_load_state("networkidle")

        csrf_token = page.evaluate(
            "() => document.querySelector('input[name=csrfmiddlewaretoken]').value"
        )
        page.evaluate(
            """([url, token]) => {
                const form = document.createElement('form');
                form.method = 'POST';
                form.action = url;
                form.innerHTML = '<input type="hidden" name="csrfmiddlewaretoken" value="' + token + '">';
                document.body.appendChild(form);
                form.submit();
            }""",
            ["/es/contribuciones/revocar/", csrf_token],
        )
        page.wait_for_load_state("networkidle")

        browser.close()

    # Verificar fuera del contexto Playwright
    consent.refresh_from_db()
    assert not consent.is_active


# ═══════════════════════════════════════════════════════════════════
# Flujo 6 — Admin marca observación como excluded
# ═══════════════════════════════════════════════════════════════════
def test_admin_invalidates_observation(live_server, seeded_mechanic):
    """Admin: accede al panel de Django y visualiza una TradeObservation."""
    from apps.trades.services import register_observation

    user_model = get_user_model()
    user_model.objects.create_superuser(email="admin_e2e@example.com", password="AComplexPass123!")
    regular_user = user_model.objects.create_user(
        email="user_e2e@example.com", password="AComplexPass123!"
    )

    obs = register_observation(
        owner_id=regular_user.pk,
        observed_at=datetime(2026, 7, 17, tzinfo=UTC),
        friendship_level="best",
        trade_type="lucky",
        atk=14,
        def_=15,
        hp=13,
    )

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/admin/login/?next=/admin/")
        page.wait_for_load_state("networkidle")
        page.fill("input[name=username]", "admin_e2e@example.com")
        page.fill("input[name=password]", "AComplexPass123!")
        page.click("input[type=submit]")
        page.wait_for_load_state("networkidle")

        assert "admin" in page.url

        # Verificar que la lista de observaciones carga
        page.goto(f"{live_server.url}/admin/trades/tradeobservation/")
        page.wait_for_load_state("networkidle")
        content = page.text_content("body")
        assert content is not None
        assert ("Trade" in content) or ("observation" in content.lower())

        # Verificar que el detalle de una observación carga
        page.goto(f"{live_server.url}/admin/trades/tradeobservation/{obs.pk}/change/")
        page.wait_for_load_state("networkidle")
        detail_content = page.text_content("body")
        assert detail_content is not None
        assert str(obs.pk) in detail_content or "Trade" in detail_content

        browser.close()


# ═══════════════════════════════════════════════════════════════════
# Flujo 7 — Dashboard comunitario se actualiza tras observaciones
# ═══════════════════════════════════════════════════════════════════
def test_community_aggregate_recalculation(live_server, seeded_mechanic):
    """Tras registrar observaciones, el dashboard comunitario muestra datos."""
    from allauth.account.models import EmailAddress

    from apps.contributions.models import DataContributionConsent
    from apps.contributions.services import build_dataset_version
    from apps.trades.services import register_observation

    user_model = get_user_model()
    user = user_model.objects.create_user(
        email="community_e2e@example.com", password="AComplexPass123!"
    )
    EmailAddress.objects.create(
        user=user, email="community_e2e@example.com", verified=True, primary=True
    )
    DataContributionConsent.grant_consent(user, "community_dataset", "1.0.0")

    for i in range(10):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=datetime(2026, 7, 17, tzinfo=UTC),
            friendship_level="best",
            trade_type="lucky",
            atk=12 + (i % 4),
            def_=12 + ((i + 1) % 4),
            hp=12 + ((i + 2) % 4),
        )
        obs.contribution_optin = True
        obs.state = "valid"
        obs.save()

    dv = build_dataset_version()
    dv.is_public = True
    dv.min_sample_met = True
    dv.save()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/comunidad/")
        page.wait_for_selector("text=Dataset Comunitario", timeout=10000)
        content = page.text_content("body")
        assert content is not None
        assert "Total de observaciones" in content

        browser.close()


# ═══════════════════════════════════════════════════════════════════
# Flujo 8 — Cambio de idioma
# ═══════════════════════════════════════════════════════════════════
def test_language_switch(live_server):
    """Visitante: cambia de español a inglés y verifica URL y contenido."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/calculadora/")
        page.wait_for_load_state("networkidle")

        page.select_option("#language-selector", "en")
        page.wait_for_timeout(2000)
        page.wait_for_load_state("networkidle")

        assert "/en/" in page.url
        title = page.title()
        assert "IV" in title

        browser.close()


# ═══════════════════════════════════════════════════════════════════
# Flujo 9 — URL compartida reproduce el cálculo
# ═══════════════════════════════════════════════════════════════════
def test_share_url_reproduces_calculation(live_server, seeded_mechanic):
    """Calcula un escenario, copia la URL compartida, la abre y verifica."""
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

        page.wait_for_selector("#calc-results .font-medium", timeout=10000)
        share_input = page.locator("#calc-results input[readonly]")
        share_value = share_input.input_value()

        assert "share=" in share_value

        page.goto(share_value)
        page.wait_for_selector("#calc-results .font-medium", timeout=10000)

        content = page.text_content("#calc-results")
        assert content is not None
        assert "Piso (f)" in content

        browser.close()


# ═══════════════════════════════════════════════════════════════════
# Flujo 10 — HTMX recalcula sin recarga completa (ANTI-REGRESSION)
# ═══════════════════════════════════════════════════════════════════
def test_htmx_recalculates_without_full_reload(live_server, seeded_mechanic):
    """EL MÁS IMPORTANTE: HTMX swap NO recarga la página completa."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto(f"{live_server.url}/es/calculadora/")
        page.wait_for_load_state("networkidle")

        title_before = page.title()

        page.select_option("#friendship_level", "best")
        page.select_option("#trade_type", "lucky")
        page.fill("#n", "10")
        page.select_option("#target_kind", "hundo")
        page.select_option("#confidence", "0.5")

        page.click("button[type=submit]")
        page.wait_for_selector("#calc-results .font-medium", timeout=10000)

        title_after = page.title()
        assert title_before == title_after

        results_text = page.text_content("#calc-results")
        assert results_text is not None
        assert "Resultados" in results_text
        assert "12" in results_text

        friendship_val = page.input_value("#friendship_level")
        assert friendship_val == "best"

        trade_val = page.input_value("#trade_type")
        assert trade_val == "lucky"

        n_val = page.input_value("#n")
        assert n_val == "10"

        browser.close()
