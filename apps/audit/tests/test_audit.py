"""Tests para apps/audit — AuditEvent y moderación."""

import pytest
from django.contrib.auth import get_user_model

from apps.audit.models import AuditEvent
from apps.audit.services import mark_dataset_suspicious, mark_observation
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
    """Marcado de observaciones como sospechosas/duplicate usando servicios de moderación."""

    @pytest.mark.django_db
    def test_mark_observation_suspicious(self):
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

        mark_observation(obs.pk, "suspicious", reason="Estadísticamente atípico", actor=user)

        obs.refresh_from_db()
        assert obs.state == "suspicious"
        assert obs.exclusion_reason == "Estadísticamente atípico"

        events = AuditEvent.objects.filter(verb="observation_marked_suspicious")
        assert events.count() == 1
        assert events[0].actor == user

    @pytest.mark.django_db
    def test_mark_observation_duplicate(self):
        user = User.objects.create_user(email="dup@test.com", password="pass123")
        obs = TradeObservation.objects.create(
            owner=user,
            observed_at="2026-07-15T00:00:00Z",
            friendship_level="good",
            trade_type="normal",
            is_lucky=False,
            atk=10,
            iv_def=10,
            hp=10,
            state="valid",
        )

        mark_observation(obs.pk, "duplicate", reason="Hash duplicado", actor=user)

        obs.refresh_from_db()
        assert obs.state == "duplicate"

        events = AuditEvent.objects.filter(verb="observation_marked_duplicate")
        assert events.count() == 1

    @pytest.mark.django_db
    def test_mark_dataset_suspicious(self):
        from apps.contributions.models import DatasetVersion

        version = DatasetVersion.objects.create(
            number=1,
            criteria={"min_sample": 30},
            row_count=100,
            checksum="abc123",
            is_public=True,
            publication_status="public",
        )

        user = User.objects.create_user(email="auditor@test.com", password="pass123")
        mark_dataset_suspicious(version.pk, reason="Sospecha de datos manipulados", actor=user)

        version.refresh_from_db()
        assert version.publication_status == "quarantined"
        assert version.is_public is False
        assert version.moderation_reason == "Sospecha de datos manipulados"
        assert version.moderated_at is not None

        events = AuditEvent.objects.filter(verb="dataset_marked_suspicious")
        assert events.count() == 1
        assert events[0].actor == user
        assert events[0].metadata.get("reason") == "Sospecha de datos manipulados"
