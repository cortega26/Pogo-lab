"""Tests para apps/audit — AuditEvent y moderación."""

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.trades.models import TradeObservation

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


class TestModeration:
    """Marcado de observaciones como sospechosas/duplicate."""

    @pytest.mark.django_db
    def test_mark_suspicious(self):
        user = User.objects.create_user(email="mod@test.com", password="pass123")
        obs = TradeObservation.objects.create(
            owner=user,
            observed_at="2026-07-15T00:00:00Z",
            friendship_level="best",
            trade_type="lucky",
            is_lucky=True,
            atk=15,
            iv_def=15,
            hp=15,
            state="valid",
        )

        obs.state = "suspicious"
        obs.save()

        obs.refresh_from_db()
        assert obs.state == "suspicious"

        AuditEvent.log(
            verb="observation_marked_suspicious",
            actor=user,
            target_type="TradeObservation",
            target_id=obs.pk,
            metadata={"reason": "Estadísticamente atípico"},
        )

    @pytest.mark.django_db
    def test_mark_dataset_suspicious(self):
        from apps.contributions.models import DatasetVersion

        version = DatasetVersion.objects.create(
            number=1,
            criteria={"min_sample": 30},
            row_count=100,
            checksum="abc123",
        )

        AuditEvent.log(
            verb="dataset_marked_suspicious",
            target_type="DatasetVersion",
            target_id=version.pk,
            metadata={"reason": "Sospecha de datos manipulados"},
        )

        events = AuditEvent.objects.filter(verb="dataset_marked_suspicious")
        assert events.count() == 1
