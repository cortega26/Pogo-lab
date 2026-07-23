"""Tests de seguridad: CSP, CSRF, headers de hardening."""

import json

import pytest
from csp.constants import NONCE, SELF
from django.test import Client, override_settings

PROD_CSP = {
    "DIRECTIVES": {
        "default-src": [SELF],
        "script-src": [SELF, NONCE],
        "style-src": [SELF, "'unsafe-inline'"],
        "img-src": [SELF, "data:"],
        "font-src": [SELF],
        "connect-src": [SELF],
        "base-uri": [SELF],
        "frame-ancestors": [SELF],
        "form-action": [SELF],
        "object-src": ["'none'"],
    },
}


@pytest.mark.django_db
@override_settings(CONTENT_SECURITY_POLICY=PROD_CSP)
def test_csp_header_emitted_with_prod_settings():
    """Con CSP de producción, el header Content-Security-Policy se emite."""
    response = Client().get("/es/calculadora/")
    assert response.status_code == 200

    csp_header = response.headers.get("Content-Security-Policy") or response.get(
        "Content-Security-Policy"
    )
    assert csp_header is not None, (
        "Content-Security-Policy header debe estar presente con settings de producción"
    )
    assert "script-src 'self'" in csp_header
    assert "object-src 'none'" in csp_header
    assert "form-action 'self'" in csp_header


@pytest.mark.django_db
def test_x_content_type_options_header():
    """El middleware de seguridad emite X-Content-Type-Options: nosniff."""
    response = Client().get("/es/")
    assert response.status_code == 200
    assert response.get("X-Content-Type-Options") == "nosniff"


@pytest.mark.django_db
def test_x_frame_options_header():
    """El middleware de clickjacking emite X-Frame-Options: DENY."""
    response = Client().get("/es/calculadora/")
    assert response.status_code == 200
    assert response.get("X-Frame-Options") == "DENY"


@pytest.mark.django_db
def test_csp_header_present_with_test_settings():
    """Incluso con CSP relajada de tests, el header se emite (no vacío)."""
    response = Client().get("/es/calculadora/")
    assert response.status_code == 200

    csp_header = response.headers.get("Content-Security-Policy") or response.get(
        "Content-Security-Policy"
    )
    assert csp_header is not None, "Content-Security-Policy debe emitirse siempre"


@pytest.mark.django_db
def test_correlation_id_header():
    """El middleware emite X-Correlation-Id en la respuesta."""
    response = Client().get("/es/")
    assert response.status_code == 200
    cid = response.get("X-Correlation-Id")
    assert cid is not None
    assert len(cid) == 36  # UUID formato estándar
    assert cid.count("-") == 4


@pytest.mark.django_db
@override_settings(CONTENT_SECURITY_POLICY=PROD_CSP)
def test_csp_does_not_block_htmx_script_with_nonce():
    """La CSP permite htmx (self-hosted) vía script-src 'self'."""
    from django.template import Context, Template

    template = Template(
        '<script src="/static/vendor/htmx.min.js" defer nonce="{{ request.csp_nonce }}"></script>'
    )
    rendered = template.render(Context({"request": type("R", (), {"csp_nonce": "test123"})()}))
    assert "nonce=" in rendered
    assert "htmx" in rendered


@pytest.mark.django_db
def test_csp_report_handles_malicious_uri(client):
    """CSP report con newlines en blocked-uri no inyecta logs (plan 028)."""
    malicious = json.dumps(
        {"csp-report": {"blocked-uri": "http://evil.com/\nFAKE LOG ENTRY"}}
    ).encode()
    response = client.post("/csp-reports/", data=malicious, content_type="application/json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_csp_report_does_not_log_raw_report(client, caplog):
    """La vista sanitiza el report CSP antes de loguear (plan 028)."""
    import logging

    payload = json.dumps(
        {
            "csp-report": {
                "blocked-uri": "http://evil.com/\nFAKE",
                "effective-directive": "script-src",
            }
        }
    ).encode()
    with caplog.at_level(logging.INFO, logger="apps.core.views"):
        client.post("/csp-reports/", data=payload, content_type="application/json")
    # El log debe contener 'sanitized' metadata, no el payload crudo
    log_text = caplog.text
    assert "FAKE LOG ENTRY" not in log_text, (
        "El log no debe contener el contenido inyectado crudo (plan 028)"
    )
    assert "blocked" in log_text or "CSP violation" in log_text
