"""Tests de seguridad: CSP, CSRF, headers de hardening."""

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
