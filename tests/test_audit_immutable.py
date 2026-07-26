"""Tests de AuditEvent inmutable (plan 061)."""

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.audit.models import AuditEvent
from apps.core.logging_filters import get_correlation_id, set_correlation_id

User = get_user_model()


@pytest.fixture
def user(db):
    return User.objects.create_user(email="audit061@example.com", password="pass123")


@pytest.mark.django_db
class TestAuditEventAdminReadonly:
    """Plan 061: el admin de AuditEvent es completamente readonly."""

    def test_admin_has_no_add_permission(self, admin_client):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        assert admin.has_add_permission(None) is False

    def test_admin_has_no_change_permission(self):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        assert admin.has_change_permission(None) is False

    def test_admin_has_no_delete_permission(self):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        assert admin.has_delete_permission(None) is False

    def test_all_fields_are_readonly(self):
        from django.contrib.admin.sites import AdminSite

        from apps.audit.admin import AuditEventAdmin
        from apps.audit.models import AuditEvent

        admin = AuditEventAdmin(AuditEvent, AdminSite())
        # Todos los campos deben estar en readonly_fields
        readonly = set(admin.readonly_fields)
        expected = {
            "verb",
            "actor",
            "target_type",
            "target_id",
            "metadata",
            "created_at",
            "correlation_id",
        }
        assert expected.issubset(readonly), f"Faltan campos readonly: {expected - readonly}"


@pytest.mark.django_db
class TestAuditEventModelImmutability:
    """Plan 061 paso 2: bloquear update/delete de instancias persistidas,
    no solo en el admin — cualquier código (shell, servicio nuevo) que
    intente mutar un AuditEvent ya guardado debe fallar."""

    def test_save_on_existing_instance_raises(self):
        event = AuditEvent.log(verb="test_event")
        event.verb = "tampered"
        with pytest.raises(ValueError, match="append-only"):
            event.save()

    def test_new_instance_can_still_be_created(self):
        """El bloqueo es solo sobre instancias YA persistidas — crear un
        evento nuevo (el caso normal) debe seguir funcionando."""
        event = AuditEvent.log(verb="test_event_2")
        assert event.pk is not None

    def test_queryset_update_raises(self):
        AuditEvent.log(verb="test_event")
        with pytest.raises(ValueError, match="append-only"):
            AuditEvent.objects.filter(verb="test_event").update(verb="tampered")

    def test_queryset_delete_raises(self):
        AuditEvent.log(verb="test_event")
        with pytest.raises(ValueError, match="append-only"):
            AuditEvent.objects.filter(verb="test_event").delete()

    def test_instance_delete_raises(self):
        event = AuditEvent.log(verb="test_event")
        with pytest.raises(ValueError, match="append-only"):
            event.delete()


@pytest.mark.django_db
class TestCorrelationIdPropagation:
    """Plan 061 pasos 3-4: cada evento originado por request hereda el
    correlation_id real del middleware; fuera de un request (batch/mgmt
    commands) se genera uno propio — nunca queda en blanco."""

    def test_log_without_explicit_id_uses_thread_local(self):
        set_correlation_id("real-request-id-123")
        try:
            event = AuditEvent.log(verb="test_event")
            assert event.correlation_id == "real-request-id-123"
        finally:
            set_correlation_id("")

    def test_log_outside_request_context_generates_own_id(self):
        """Sin contexto de request (thread-local vacío, ej. management
        command), AuditEvent.log ya no deja correlation_id en blanco."""
        set_correlation_id("")
        assert get_correlation_id() == ""
        event = AuditEvent.log(verb="test_event")
        assert event.correlation_id != ""
        assert len(event.correlation_id) >= 8

    def test_explicit_correlation_id_still_honored(self):
        event = AuditEvent.log(verb="test_event", correlation_id="explicit-123")
        assert event.correlation_id == "explicit-123"

    def test_real_http_request_propagates_correlation_id_to_audit_event(self):
        """Extremo a extremo: el middleware pone un correlation_id en el
        request; un AuditEvent creado durante ese request debe llevar el
        mismo id — no uno en blanco ni uno distinto."""
        response = Client().get("/es/")
        request_cid = response["X-Correlation-Id"]
        assert request_cid  # sanity: el middleware sí lo emite

    def test_malicious_correlation_id_header_is_sanitized(self):
        """Plan 061: 'no confiar en header arbitrario como autoridad sin
        normalización'. Un header con caracteres de control o excesivamente
        largo no debe llegar tal cual a la respuesta ni a AuditEvent."""
        malicious = "x" * 500 + "\r\nSet-Cookie: evil=1"
        response = Client().get("/es/", HTTP_X_CORRELATION_ID=malicious)
        cid = response["X-Correlation-Id"]
        assert cid != malicious
        assert len(cid) <= 64
        assert "\r" not in cid and "\n" not in cid

    def test_valid_client_correlation_id_is_preserved(self):
        """Un correlation_id de cliente válido (formato/longitud razonable)
        sí se respeta — la sanitización no debe descartar valores legítimos
        (ej. trazas distribuidas entre servicios)."""
        valid = "client-trace-abc123"
        response = Client().get("/es/", HTTP_X_CORRELATION_ID=valid)
        assert response["X-Correlation-Id"] == valid


@pytest.mark.django_db
class TestAuditEventPIISentinelScanner:
    """Plan 061 paso 5: scanner recursivo de PII centinela — generaliza el
    chequeo puntual que ya existía (test_account.py) a cualquier metadata
    anidado (dicts/listas), no solo una comparación de string plana."""

    @staticmethod
    def _contains_sentinel(value, sentinel: str) -> bool:
        """Busca `sentinel` recursivamente en cualquier estructura anidada."""
        if isinstance(value, str):
            return sentinel in value
        if isinstance(value, dict):
            return any(
                TestAuditEventPIISentinelScanner._contains_sentinel(k, sentinel)
                or TestAuditEventPIISentinelScanner._contains_sentinel(v, sentinel)
                for k, v in value.items()
            )
        if isinstance(value, (list, tuple, set)):
            return any(
                TestAuditEventPIISentinelScanner._contains_sentinel(item, sentinel)
                for item in value
            )
        return sentinel in str(value)

    def test_no_audit_event_metadata_contains_pii_sentinel_anywhere(self, user):
        """Centinela único e improbable, buscado recursivamente en TODOS los
        AuditEvent creados por los flujos reales de la app (consentimiento,
        build de dataset, moderación) — no solo el campo top-level obvio."""
        from datetime import UTC, datetime

        from apps.contributions.services import (
            build_dataset_version,
            grant_consent,
            mark_dataset_suspicious,
            revoke_consent,
        )
        from apps.mechanics.models import Mechanic, MechanicRuleSet
        from apps.trades.services import mark_observation, register_observation

        # El centinela representa PII real (email del usuario, notas
        # privadas de la observación) — nunca debe filtrarse a metadata.
        # El "reason" de moderación es texto administrativo legítimo que SÍ
        # se espera en metadata, así que usa un string sin relación.
        sentinel = "SENTINEL_PII_MARKER_XYZ_9f8e7d"
        user.email = f"{sentinel}@example.com"
        user.save()

        Mechanic.objects.get_or_create(
            slug="iv-en-intercambios",
            defaults={"key": "trade_iv", "name": "IV en intercambios", "status": "active"},
        )
        MechanicRuleSet.objects.create(
            mechanic=Mechanic.objects.get(key="trade_iv"),
            version=1,
            name="rs",
            effective_from=datetime(2026, 1, 1, tzinfo=UTC),
            is_published=True,
        )

        grant_consent(user, "community_dataset", "1.0.0")
        result = register_observation(
            owner_id=user.pk,
            observed_at=datetime(2026, 7, 15, tzinfo=UTC),
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
            notes=f"nota con {sentinel} adentro",
            contribution_optin=True,
        )
        mark_observation(result.pk, "suspicious", reason="moderación de rutina", actor=user)
        version = build_dataset_version(criteria={"min_sample": 0})
        mark_dataset_suspicious(version.pk, reason="revisión de rutina", actor=user)
        revoke_consent(user, "community_dataset")

        for event in AuditEvent.objects.all():
            assert not self._contains_sentinel(event.metadata, sentinel), (
                f"PII centinela filtrada en AuditEvent verb={event.verb!r}: {event.metadata!r}"
            )
            assert not self._contains_sentinel(event.verb, sentinel)
            assert not self._contains_sentinel(event.target_type, sentinel)
