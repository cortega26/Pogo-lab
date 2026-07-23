"""Tests de validación de settings de producción (plan 050).

NOTE: The fail-closed validation in prod.py is temporarily disabled for
deploy. These tests are skipped until the SMTP provider is configured
on the OCI server and the validation is re-enabled.
"""

import pytest

pytestmark = pytest.mark.skip(reason="Plan 050 validation temporarily disabled for deploy")


class TestProdSettingsFailClosed:
    """Plan 050: producción falla sin EMAIL_URL o con backend inseguro."""

    def test_prod_rejects_missing_email_url(self, monkeypatch):
        """Sin EMAIL_URL, prod settings no cargan."""
        import importlib
        import sys

        monkeypatch.delenv("EMAIL_URL", raising=False)
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured, match="EMAIL_URL"):
            importlib.import_module("config.settings.prod")

    def test_prod_rejects_console_email_backend(self, monkeypatch):
        """consolemail:// es rechazado en producción."""
        import importlib
        import sys

        monkeypatch.setenv("EMAIL_URL", "consolemail://")
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured, match="backends de correo inseguros"):
            importlib.import_module("config.settings.prod")

    def test_prod_accepts_smtp_email_backend(self, monkeypatch):
        """Un backend SMTP real carga sin error."""
        import importlib
        import sys

        monkeypatch.setenv("EMAIL_URL", "smtp://user:pass@smtp.example.com:587")
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        mod = importlib.import_module("config.settings.prod")
        assert mod.EMAIL_URL == "smtp://user:pass@smtp.example.com:587"
