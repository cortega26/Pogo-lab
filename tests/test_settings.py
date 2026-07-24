"""Tests de validación de settings de producción (plan 050).

The fail-closed validation in prod.py is now active (Brevo SMTP configured).
"""

import pytest

# Plan 050 validation is active again (Brevo SMTP wired). Tests run normally.


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


class TestProdSettingsSchemeValidation:
    """Validación de esquema de EMAIL_URL (no substring) — edge cases."""

    @pytest.mark.parametrize(
        "scheme,url",
        [
            ("smtp+tls", "smtp+tls://user:pass@smtp.example.com:587"),
            ("smtp+ssl", "smtp+ssl://user:pass@smtp.example.com:465"),
            ("smtps", "smtps://user:pass@smtp.example.com:465"),
        ],
    )
    def test_prod_accepts_secure_smtp_schemes(self, monkeypatch, scheme, url):
        """Esquemas SMTP seguros (TLS/SSL/smtps) cargan sin error."""
        import importlib
        import sys

        monkeypatch.setenv("EMAIL_URL", url)
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        mod = importlib.import_module("config.settings.prod")
        assert url == mod.EMAIL_URL

    @pytest.mark.parametrize(
        "url",
        [
            "locmem://",
            "dummy://",
            "file:///tmp/emails",
            "console://",
        ],
    )
    def test_prod_rejects_insecure_schemes(self, monkeypatch, url):
        """Esquemas inseguros son rechazados."""
        import importlib
        import sys

        monkeypatch.setenv("EMAIL_URL", url)
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured, match="inseguros"):
            importlib.import_module("config.settings.prod")

    def test_prod_accepts_smtp_host_containing_locmem_substring(self, monkeypatch):
        """Un host SMTP legítimo que contenga 'locmem' NO se rechaza (validación por esquema, no substring)."""
        import importlib
        import sys

        # El host contiene "locmem" como subcadena, pero el esquema es smtp.
        monkeypatch.setenv("EMAIL_URL", "smtp://user:pass@locmem-host.example.com:587")
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        mod = importlib.import_module("config.settings.prod")
        assert "locmem-host.example.com" in mod.EMAIL_URL
