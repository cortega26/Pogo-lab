"""Tests para apps/audit — AuditEvent (modelo/sink).

Plan 060: apps.audit ya no tiene services.py — mark_observation vive en
apps.trades.services (ver tests/test_trades.py::TestMarkObservation) y
mark_dataset_suspicious en apps.contributions.services (ver
apps/contributions/tests/test_contributions.py::TestMarkDatasetSuspicious).
apps.audit queda como sink puro: solo el modelo AuditEvent, consultable
por cualquier app, sin lógica de moderación propia ni dependencias hacia
apps de dominio."""

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent

User = get_user_model()


class TestAuditEvent:
    @pytest.mark.django_db
    def test_create_audit_event(self):
        user = User.objects.create_user(email="audit@test.com", password="pass123")
        event = AuditEvent.log(
            verb="consent_granted",
            actor=user,
            target_type="DataContributionConsent",
            target_id=1,
            metadata={"scope": "community_dataset", "text_version": "1.0.0"},
            correlation_id="abc-123",
        )
        assert event.pk is not None
        assert event.verb == "consent_granted"
        assert event.actor == user
        assert event.correlation_id == "abc-123"

    @pytest.mark.django_db
    def test_audit_event_without_actor(self):
        event = AuditEvent.log(
            verb="dataset_built",
            target_type="DatasetVersion",
            target_id=5,
            metadata={"row_count": 100},
        )
        assert event.actor is None
        assert event.target_id == 5

    @pytest.mark.django_db
    def test_audit_metadata_no_pii(self):
        """El metadata del AuditEvent nunca debe contener PII."""
        user = User.objects.create_user(email="sentinel_audit@example.com", password="pass123")
        event = AuditEvent.log(
            verb="consent_revoked",
            actor=user,
            metadata={
                "scope": "community_dataset",
            },
        )

        # Verifica que el metadata NO contenga PII del actor
        metadata_str = str(event.metadata)
        assert user.email not in metadata_str
        assert "sentinel" not in metadata_str

    @pytest.mark.django_db
    def test_audit_ordering(self):
        user = User.objects.create_user(email="order@test.com", password="pass123")
        AuditEvent.log(verb="event_1", actor=user)
        e2 = AuditEvent.log(verb="event_2", actor=user)

        events = list(AuditEvent.objects.all())
        assert events[0].pk == e2.pk
