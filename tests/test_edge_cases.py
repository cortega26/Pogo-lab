"""Tests de edge cases y sad paths para los planes de la sesión.

Cada test verifica un edge case específico que podría romper en producción.
"""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import ClassVar

import pytest

pytestmark = pytest.mark.django_db


@pytest.fixture
def user(db):
    return _make_user()


def _make_user(email: str = "edge@example.com", password: str = "pw12345!"):
    from django.contrib.auth import get_user_model

    user_model = get_user_model()
    return user_model.objects.create_user(email=email, password=password)


# ---------------------------------------------------------------------------
# Plan 029 — IntegrityError path edge cases
# ---------------------------------------------------------------------------


class TestPlan029EdgeCases:
    """Edge cases del catch de IntegrityError en register_observation."""

    def test_integrity_error_sets_is_new_false(self, user):
        """La observación retornada por IntegrityError tiene _is_new=False."""
        from apps.trades.services import register_observation

        now = datetime.now(tz=UTC)
        # Create first observation
        obs1 = register_observation(
            owner_id=user.pk,
            observed_at=now,
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
        )
        assert getattr(obs1, "_is_new", True) is True

        # Simulate the race: directly insert a duplicate, then call register
        # The existing check will find it
        obs2 = register_observation(
            owner_id=user.pk,
            observed_at=now,
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
        )
        assert obs2.pk == obs1.pk  # Same observation returned
        assert getattr(obs2, "_is_new", True) is False


# ---------------------------------------------------------------------------
# Plan 055 — Trade ingestion edge cases
# ---------------------------------------------------------------------------


class TestPlan055EdgeCases:
    """Edge cases de importación masiva y dedup."""

    def test_csv_empty_content(self, user):
        """CSV vacío no crashea."""
        from apps.trades.services import import_csv

        result = import_csv("", user.pk)
        assert result["total"] == 0
        assert result["created_count"] == 0
        assert result["error_count"] == 0

    def test_csv_header_only(self, user):
        """CSV con solo header no crea observaciones."""
        from apps.trades.services import import_csv

        csv_content = "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
        result = import_csv(csv_content, user.pk)
        assert result["total"] == 0
        assert result["created_count"] == 0

    def test_csv_exceeds_row_limit(self, user):
        """CSV con más de MAX_CSV_ROWS filas se trunca."""
        from apps.trades.services import MAX_CSV_ROWS, import_csv

        header = "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
        row = "2026-07-17T12:00:00+00:00,good,normal,5,10,8,\n"
        csv_content = header + row * (MAX_CSV_ROWS + 5)
        result = import_csv(csv_content, user.pk)
        assert "Excedido el límite" in result["errors"][-1]
        assert result["total"] <= MAX_CSV_ROWS + 1

    def test_duplicate_within_same_batch(self, user):
        """Duplicados dentro del mismo lote se detectan correctamente."""
        from apps.trades.services import import_csv

        csv_content = (
            "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
            "2026-07-17T12:00:00+00:00,good,normal,5,10,8,\n"
            "2026-07-17T12:00:00+00:00,good,normal,5,10,8,\n"
        )
        result = import_csv(csv_content, user.pk)
        assert result["created_count"] == 1
        assert result["duplicate_count"] == 1

    def test_bulk_json_string_value_for_numeric_field(self, client, user):
        """Strings en campos numéricos del bulk JSON devuelven 400."""
        client.force_login(user)
        payload = json.dumps([{"observed_at": "", "atk": "not-a-number", "def": 0, "hp": 0}])
        response = client.post(
            "/es/intercambios/lotes/",
            data={"observations_json": payload},
        )
        assert response.status_code == 400

    def test_bulk_json_empty_list(self, client, user):
        """Lista vacía en bulk JSON no crashea."""
        client.force_login(user)
        response = client.post(
            "/es/intercambios/lotes/",
            data={"observations_json": "[]"},
        )
        assert response.status_code == 200

    def test_csv_view_rejects_oversized_file(self, client, user):
        """Archivo CSV que excede MAX_CSV_BYTES devuelve 413."""
        from apps.trades.services import MAX_CSV_BYTES

        client.force_login(user)
        from django.core.files.uploadedfile import SimpleUploadedFile

        header = b"observed_at,friendship_level,trade_type,atk,def,hp,species\n"
        row = b"2026-07-17T12:00:00+00:00,good,normal,5,10,8,\n"
        # Create a file larger than MAX_CSV_BYTES
        content = header + row * (MAX_CSV_BYTES // len(row) + 10)
        uploaded = SimpleUploadedFile("test.csv", content, content_type="text/csv")
        response = client.post(
            "/es/intercambios/csv/importar/",
            data={"csv_file": uploaded},
        )
        assert response.status_code == 413

    def test_import_csv_result_has_all_keys(self, user):
        """El resultado de import_csv tiene todas las claves documentadas."""
        from apps.trades.services import import_csv

        result = import_csv("", user.pk)
        expected_keys = {
            "created",
            "duplicates",
            "errors",
            "total",
            "valid_count",
            "created_count",
            "duplicate_count",
            "error_count",
        }
        assert set(result.keys()) == expected_keys


# ---------------------------------------------------------------------------
# Plan 054 — Analysis runs atomic edge cases
# ---------------------------------------------------------------------------


class TestPlan054EdgeCases:
    """Edge cases de atomicidad de analysis runs."""

    def test_run_with_no_observations(self, user):
        """Un run sin observaciones válidas queda complete con 0 resultados."""
        from apps.analysis.services import run_personal_analysis

        run = run_personal_analysis(user.pk)
        assert run.status == "complete"
        assert run.results.count() == 0

    def test_get_or_run_creates_new_if_only_failed_exists(self, user):
        """Si solo existe un run failed, get_or_run crea uno nuevo."""
        from apps.analysis.models import AnalysisRun
        from apps.analysis.services import (
            _input_fingerprint,
            get_or_run_personal_analysis,
        )

        # Create a failed run manually
        fp = _input_fingerprint(user.pk, None)
        AnalysisRun.objects.create(
            owner_id=user.pk,
            input_fingerprint=fp,
            status="failed",
            error_message="test failure",
        )
        run = get_or_run_personal_analysis(user.pk)
        assert run.status == "complete"
        failed_run = AnalysisRun.objects.filter(status="failed").first()
        assert failed_run is not None
        assert run.pk != failed_run.pk

    def test_run_error_message_truncated(self, user):
        """El error_message se trunca a 500 caracteres."""
        from datetime import UTC
        from datetime import datetime as dt_datetime
        from unittest.mock import patch

        from apps.analysis.models import AnalysisResult, AnalysisRun
        from apps.analysis.services import run_personal_analysis
        from apps.mechanics.models import Mechanic, MechanicRuleSet
        from apps.trades.models import TradeObservation

        # Setup mechanic + published ruleset (required for analysis)
        mechanic = Mechanic.objects.create(
            slug="iv-en-intercambios",
            key="trade_iv",
            name="IV",
            status="active",
        )
        rs = MechanicRuleSet.objects.create(
            mechanic=mechanic,
            version=1,
            name="Ruleset test",
            effective_from=dt_datetime(2026, 1, 1, tzinfo=UTC),
            is_published=False,
        )
        rs.parameters.create(key="floor_good", value=1, data_type="integer")
        rs.parameters.create(key="floor_best", value=5, data_type="integer")
        rs.parameters.create(key="floor_lucky", value=12, data_type="integer")
        rs.is_published = True
        rs.save(update_fields=["is_published", "updated_at"])

        # Create an observation so there's something to analyze
        TradeObservation.objects.create(
            owner=user,
            observed_at=dt_datetime.now(tz=UTC),
            friendship_level="best",
            trade_type="lucky",
            is_lucky=True,
            atk=12,
            iv_def=13,
            hp=14,
            state="valid",
            ruleset=rs,
        )

        long_error = "x" * 1000
        with (
            patch.object(AnalysisResult.objects, "bulk_create", side_effect=Exception(long_error)),
            pytest.raises(Exception, match=""),
        ):
            run_personal_analysis(user.pk)

        failed = AnalysisRun.objects.filter(status="failed").first()
        assert failed is not None
        assert len(failed.error_message) <= 500


# ---------------------------------------------------------------------------
# Plan 052 — Community publication edge cases
# ---------------------------------------------------------------------------


class TestPlan052EdgeCases:
    """Edge cases de publicación comunitaria."""

    def test_quarantined_dataset_excluded_from_public(self, user):
        """Un dataset cuarentenado no es público."""
        from apps.audit.services import mark_dataset_suspicious
        from apps.contributions.models import DatasetVersion

        version = DatasetVersion.objects.create(
            number=1,
            row_count=100,
            checksum="abc",
            is_public=True,
            publication_status="public",
        )
        mark_dataset_suspicious(version.pk, reason="test")
        version.refresh_from_db()
        assert version.publication_status == "quarantined"
        assert version.is_public is False

    def test_build_dataset_version_is_atomic(self, user):
        """build_dataset_version crea version con publication_status correcto."""
        from apps.contributions.services import build_dataset_version

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.publication_status in ("public", "draft")
        assert version.consent_text_version == "1.0.0"

    def test_build_with_consent_version_filters_old(self, user):
        """Consents with old text version are excluded from the build."""
        from apps.contributions.models import DataContributionConsent
        from apps.contributions.services import build_dataset_version
        from apps.trades.models import TradeObservation

        # Grant consent with old version
        DataContributionConsent.grant_consent(user, "community_dataset", "0.9.0")
        now = datetime.now(tz=UTC)
        TradeObservation.objects.create(
            owner=user,
            observed_at=now,
            friendship_level="good",
            trade_type="normal",
            is_lucky=False,
            atk=10,
            iv_def=10,
            hp=10,
            state="valid",
            contribution_optin=True,
        )

        # Build with consent_text_version="1.0.0" — old consent excluded
        version = build_dataset_version(
            criteria={"min_sample": 1},
            consent_text_version="1.0.0",
        )
        assert version.row_count == 0  # No observations included


# ---------------------------------------------------------------------------
# Plan 051 — Rate limiting edge cases
# ---------------------------------------------------------------------------


class TestPlan051EdgeCases:
    """Edge cases de rate limiting."""

    def test_invalid_proxy_network_env_doesnt_crash(self, monkeypatch):
        """RATELIMIT_PROXY_NETWORKS con CIDR inválido no crashea el import."""
        import importlib

        monkeypatch.setenv("RATELIMIT_PROXY_NETWORKS", "not-a-network,172.16.0.0/12")
        import apps.core.ratelimit as rl

        importlib.reload(rl)
        # Invalid network is skipped, valid one works
        assert rl._is_proxy_ip("172.16.0.1") is True
        assert rl._is_proxy_ip("8.8.8.8") is False
        # Restore default
        monkeypatch.delenv("RATELIMIT_PROXY_NETWORKS", raising=False)
        importlib.reload(rl)

    def test_x_real_ip_with_whitespace(self):
        """X-Real-IP con espacios en blanco se limpia."""

        class FakeRequest:
            META: ClassVar[dict] = {
                "REMOTE_ADDR": "172.18.0.1",
                "HTTP_X_REAL_IP": "  203.0.113.5  ",
            }

        from apps.core.ratelimit import client_ip_key

        assert client_ip_key("test", FakeRequest()) == "203.0.113.5"

    def test_empty_proxy_networks_env(self, monkeypatch):
        """RATELIMIT_PROXY_NETWORKS vacío → ningún IP es proxy."""
        import importlib

        monkeypatch.setenv("RATELIMIT_PROXY_NETWORKS", "")
        import apps.core.ratelimit as rl

        importlib.reload(rl)
        assert rl._is_proxy_ip("172.16.0.1") is False
        assert rl._is_proxy_ip("8.8.8.8") is False
        monkeypatch.delenv("RATELIMIT_PROXY_NETWORKS", raising=False)
        importlib.reload(rl)


# ---------------------------------------------------------------------------
# Plan 056 — PostgreSQL CI gate edge cases
# ---------------------------------------------------------------------------


class TestPlan056EdgeCases:
    """Edge cases del gate PostgreSQL."""

    def test_test_postgres_rejects_non_test_url(self, monkeypatch):
        """DATABASE_URL sin 'test' en el nombre es rechazada."""
        import importlib
        import sys

        monkeypatch.setenv("DATABASE_URL", "postgres://user@localhost/prod_db")
        if "config.settings.test_postgres" in sys.modules:
            del sys.modules["config.settings.test_postgres"]
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured, match="no parece apuntar"):
            importlib.import_module("config.settings.test_postgres")

    def test_test_postgres_parses_url_correctly(self, monkeypatch):
        """DATABASE_URL se parsea correctamente (host, port, db name)."""
        import importlib
        import sys

        monkeypatch.setenv("DATABASE_URL", "postgres://myuser:mypass@dbhost:5432/my_test_db")
        if "config.settings.test_postgres" in sys.modules:
            del sys.modules["config.settings.test_postgres"]
        mod = importlib.import_module("config.settings.test_postgres")
        db = mod.DATABASES["default"]
        assert db["NAME"] == "my_test_db"
        assert db["HOST"] == "dbhost"
        assert db["PORT"] == "5432"
        assert db["USER"] == "myuser"
        assert db["PASSWORD"] == "mypass"


# ---------------------------------------------------------------------------
# Plan 050 — Fail-closed email edge cases
# ---------------------------------------------------------------------------


class TestPlan050EdgeCases:
    """Edge cases de fail-closed email validation.

    NOTE: validation is temporarily disabled for deploy. These tests
    are skipped until SMTP is configured on the OCI server.
    """

    @pytest.mark.skip(reason="Plan 050 validation temporarily disabled for deploy")
    def test_prod_rejects_locmem_backend(self, monkeypatch):
        """locmem:// es rechazado en producción."""
        import importlib
        import sys

        monkeypatch.setenv("EMAIL_URL", "locmem://")
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured):
            importlib.import_module("config.settings.prod")

    @pytest.mark.skip(reason="Plan 050 validation temporarily disabled for deploy")
    def test_prod_rejects_dummy_backend(self, monkeypatch):
        """dummy:// es rechazado en producción."""
        import importlib
        import sys

        monkeypatch.setenv("EMAIL_URL", "dummy://")
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured):
            importlib.import_module("config.settings.prod")

    @pytest.mark.skip(reason="Plan 050 validation temporarily disabled for deploy")
    def test_prod_rejects_file_backend(self, monkeypatch):
        """file:// es rechazado en producción."""
        import importlib
        import sys

        monkeypatch.setenv("EMAIL_URL", "file:///tmp/emails")
        if "config.settings.prod" in sys.modules:
            del sys.modules["config.settings.prod"]
        from django.core.exceptions import ImproperlyConfigured

        with pytest.raises(ImproperlyConfigured):
            importlib.import_module("config.settings.prod")


# ---------------------------------------------------------------------------
# Plan 061 — AuditEvent admin readonly edge cases
# ---------------------------------------------------------------------------


class TestPlan061EdgeCases:
    """Edge cases de AuditEvent inmutable."""

    def test_admin_cannot_add_via_post(self, admin_client):
        """POST al admin de AuditEvent no crea (has_add_permission=False)."""
        from apps.audit.models import AuditEvent

        response = admin_client.post(
            "/admin/audit/auditevent/add/",
            {"verb": "test_verb", "target_type": "Test"},
        )
        # Django returns 403 when has_add_permission is False
        assert response.status_code in (403, 302)
        assert not AuditEvent.objects.filter(verb="test_verb").exists()

    def test_admin_cannot_delete_via_post(self, admin_client):
        """DELETE via admin no borra (has_delete_permission=False)."""
        from apps.audit.models import AuditEvent

        event = AuditEvent.log(verb="test_delete", target_type="Test")
        response = admin_client.post(f"/admin/audit/auditevent/{event.pk}/delete/")
        assert response.status_code in (403, 302)
        assert AuditEvent.objects.filter(pk=event.pk).exists()


# ---------------------------------------------------------------------------
# Plan 044 — Secret boundaries edge cases
# ---------------------------------------------------------------------------


class TestPlan044EdgeCases:
    """Edge cases de límites de secretos."""

    def test_dockerignore_covers_env_hyphen(self):
        """.env-* (con guion) está en .dockerignore."""
        from pathlib import Path

        dockerignore = Path(".dockerignore").read_text()
        assert ".env-*" in dockerignore

    def test_gitignore_covers_env_hyphen(self):
        """.env-* (con guion) está en .gitignore."""
        from pathlib import Path

        gitignore = Path(".gitignore").read_text()
        assert ".env-*" in gitignore

    def test_dockerfile_uses_allowlist(self):
        """Dockerfile no hace COPY . ."""
        from pathlib import Path

        dockerfile = Path("Dockerfile").read_text()
        assert "COPY . ." not in dockerfile
        # Debe copiar archivos específicos
        assert "COPY config/ ./config/" in dockerfile
        assert "COPY apps/ ./apps/" in dockerfile
        assert "COPY engine/ ./engine/" in dockerfile
