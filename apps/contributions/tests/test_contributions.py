"""Tests de integración para apps/contributions.

PR-17: consentimiento + build + anonimización.
Verifica invariantes de privacidad, inclusión AND, revocación e idempotencia.
"""

import json
from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.urls import reverse

from apps.accounts.models import UserProfile
from apps.contributions.models import DataContributionConsent, DatasetVersion
from apps.contributions.services import (
    aggregate_community_distribution,
    build_dataset_version,
)
from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter
from apps.trades.models import TradeObservation

User = get_user_model()

SCOPE = "community_dataset"
CONSENT_VERSION = "1.0.0"


def _utc(year, month, day, hour=0, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _seeded_mechanic(db):
    """Crea la mecánica trade_iv y un ruleset publicado (necesario para FK en obs)."""
    Mechanic.objects.create(
        slug="iv-en-intercambios",
        key="trade_iv",
        name="IV en intercambios",
        status="active",
    )
    rs = MechanicRuleSet.objects.create(
        mechanic=Mechanic.objects.get(key="trade_iv"),
        version=1,
        name="Ruleset de prueba",
        effective_from=_utc(2026, 1, 1),
        is_published=False,
    )
    for key, value in [
        ("floor.friendship.good", 1),
        ("floor.friendship.great", 2),
        ("floor.friendship.ultra", 3),
        ("floor.friendship.best", 5),
        ("floor.lucky", 12),
    ]:
        RuleParameter.objects.create(
            ruleset=rs,
            key=key,
            value=value,
            data_type="integer",
        )
    rs.is_published = True
    rs.save(update_fields=["is_published", "updated_at"])


@pytest.fixture
def user():
    return User.objects.create_user(email="contributor@test.com", password="pass123")


@pytest.fixture
def user2():
    return User.objects.create_user(email="other@test.com", password="pass123")


def _make_obs(
    user,
    state="valid",
    contribution_optin=True,
    atk=14,
    iv_def=13,
    hp=12,
    friendship_level="best",
    trade_type="lucky",
    is_lucky=True,
    observed_at=None,
    notes="",
):
    ruleset = MechanicRuleSet.objects.filter(is_published=True).first()
    if observed_at is None:
        observed_at = _utc(2026, 7, 15, 12, 30, 45)
    return TradeObservation.objects.create(
        owner=user,
        observed_at=observed_at,
        friendship_level=friendship_level,
        trade_type=trade_type,
        is_lucky=is_lucky,
        atk=atk,
        iv_def=iv_def,
        hp=hp,
        state=state,
        contribution_optin=contribution_optin,
        ruleset=ruleset,
        notes=notes,
    )


class TestDataContributionConsent:
    @pytest.mark.django_db
    def test_grant_consent_creates_active(self, user):
        c = DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        assert c.is_active is True
        assert c.granted_at is not None
        assert c.revoked_at is None
        assert c.consent_text_version == CONSENT_VERSION

    @pytest.mark.django_db
    def test_revoke_consent_sets_inactive(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        c = DataContributionConsent.revoke_consent(user, SCOPE)
        assert c is not None
        assert c.is_active is False
        assert c.revoked_at is not None

    @pytest.mark.django_db
    def test_regrant_after_revoke(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        DataContributionConsent.revoke_consent(user, SCOPE)
        c = DataContributionConsent.grant_consent(user, SCOPE, "2.0.0")
        assert c.is_active is True
        assert c.revoked_at is None
        assert c.consent_text_version == "2.0.0"

    @pytest.mark.django_db
    def test_revoke_nonexistent_returns_none(self, user):
        c = DataContributionConsent.revoke_consent(user, SCOPE)
        assert c is None

    @pytest.mark.django_db
    def test_grant_idempotent_does_not_reset(self, user):
        c1 = DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        first_granted = c1.granted_at
        c2 = DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        assert c2.pk == c1.pk
        assert c2.granted_at == first_granted

    @pytest.mark.django_db
    def test_active_with_revoked_date_clean_error(self, user):
        c = DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        c.revoked_at = _utc(2026, 7, 15)
        c.is_active = True
        with pytest.raises(ValidationError):
            c.save()

    @pytest.mark.django_db
    def test_revoked_before_granted_clean_error(self, user):
        c = DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        c.revoked_at = c.granted_at
        with pytest.raises(ValidationError):
            c.clean()

    @pytest.mark.django_db
    def test_grant_creates_audit_event(self, user):
        from apps.audit.models import AuditEvent

        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        events = AuditEvent.objects.filter(verb="consent_granted", actor=user)
        assert events.count() == 1
        assert events[0].metadata == {"scope": "community_dataset", "text_version": "1.0.0"}

    @pytest.mark.django_db
    def test_revoke_creates_audit_event(self, user):
        from apps.audit.models import AuditEvent

        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        DataContributionConsent.revoke_consent(user, SCOPE)
        events = AuditEvent.objects.filter(verb="consent_revoked", actor=user)
        assert events.count() == 1

    @pytest.mark.django_db
    def test_audit_metadata_has_no_pii_from_consent(self, user):
        from apps.audit.models import AuditEvent

        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        event = AuditEvent.objects.filter(verb="consent_granted").first()
        assert event is not None
        metadata_str = str(event.metadata)
        assert user.email not in metadata_str


def _serialize_version(version):
    """Serializa el dataset version para inspección de PII."""
    snapshot = {
        "number": version.number,
        "built_at": version.built_at.isoformat(),
        "criteria": version.criteria,
        "min_sample_met": version.min_sample_met,
        "row_count": version.row_count,
        "checksum": version.checksum,
        "is_public": version.is_public,
        "pipeline_version": version.pipeline_version,
    }
    rows = getattr(version, "rows_cache", [])
    return json.dumps({"snapshot": snapshot, "rows": rows}, default=str)


class TestAnonymizationPII:
    """El test de M6: verifica ausencia de PII sobre bytes reales."""

    @pytest.mark.django_db
    def test_sentinel_pii_not_in_serialized(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        user.email = "sentinel_pii_email_abc123@example.com"
        user.save()
        _make_obs(
            user,
            notes="SENTINEL_NOTE_XYZ_UNIQUE",
            observed_at=_utc(2026, 3, 15, 9, 25, 33),
        )

        version = build_dataset_version(criteria={"min_sample": 1})

        serialized = _serialize_version(version)
        serialized_lower = serialized.lower()

        forbidden = [
            "SENTINEL_NOTE_XYZ_UNIQUE",
            "sentinel_pii_email_abc123",
            "owner_id",
            "dedup_hash",
        ]

        for forbidden_str in forbidden:
            assert forbidden_str.lower() not in serialized_lower, (
                f"Fuga de PII detectada: '{forbidden_str}' encontrada en "
                f"el contenido serializado del dataset."
            )

        assert "09:25" not in serialized, "El timestamp exacto apareció en el dataset."

        for row in getattr(version, "rows_cache", []):
            assert "notes" not in row
            assert "owner" not in row
            assert "owner_id" not in row
            assert "dedup_hash" not in row
            assert "country" not in row
            assert "observed_at" not in row

    @pytest.mark.django_db
    def test_no_notes_in_anonymized_rows(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, notes="una nota cualquiera", atk=13, iv_def=14, hp=10)

        version = build_dataset_version(criteria={"min_sample": 1})

        for row in getattr(version, "rows_cache", []):
            assert "notes" not in row, f"Campo 'notes' encontrado en fila anonimizada: {row}"

    @pytest.mark.django_db
    def test_no_owner_id_in_rows(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user)

        version = build_dataset_version(criteria={"min_sample": 1})

        for row in getattr(version, "rows_cache", []):
            assert "owner" not in row
            assert "owner_id" not in row
            assert "user" not in row
            assert "user_id" not in row
            assert "email" not in str(row).lower()

    @pytest.mark.django_db
    def test_no_country_per_row(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        profile, _created = UserProfile.objects.get_or_create(user=user)
        profile.country = "AR"
        profile.save()
        _make_obs(user)

        version = build_dataset_version(criteria={"min_sample": 1})

        serialized = _serialize_version(version)
        assert '"AR"' not in serialized
        assert "'AR'" not in serialized

    @pytest.mark.django_db
    def test_month_bucket_not_timestamp(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, observed_at=_utc(2026, 5, 18, 14, 22, 55))

        version = build_dataset_version(criteria={"min_sample": 1})

        for row in getattr(version, "rows_cache", []):
            assert row["observed_month"] == "2026-05"
            assert "14:22" not in str(row)
            assert "55" not in str(row.get("observed_at", ""))


class TestInclusionAND:
    """Verifica que la inclusión es AND compuesto de los tres criterios."""

    @pytest.mark.django_db
    def test_all_conditions_met_included(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user)

        version = build_dataset_version(criteria={"min_sample": 1})

        assert version.row_count >= 1

    @pytest.mark.django_db
    def test_state_not_valid_excluded(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, state="suspicious")

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0

    @pytest.mark.django_db
    def test_state_excluded_excluded(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, state="excluded")

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0

    @pytest.mark.django_db
    def test_state_draft_excluded(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, state="draft")

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0

    @pytest.mark.django_db
    def test_no_optin_excluded(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, contribution_optin=False)

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0

    @pytest.mark.django_db
    def test_no_consent_excluded(self, user):
        _make_obs(user, contribution_optin=True)

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0

    @pytest.mark.django_db
    def test_consent_revoked_excluded(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user)
        DataContributionConsent.revoke_consent(user, SCOPE)

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0

    @pytest.mark.django_db
    def test_trampa_valid_state_required(self, user):
        """Caso trampa: usuario consentido y opt-in pero observación 'suspicious'."""
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, state="suspicious", contribution_optin=True)

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0, (
            "Una observación 'suspicious' no debería incluirse aunque el usuario "
            "tenga consentimiento y opt-in."
        )

    @pytest.mark.django_db
    def test_trampa_excluded_state(self, user):
        """Caso trampa: usuario consentido y opt-in pero observación 'excluded'."""
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, state="excluded", contribution_optin=True)

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.row_count == 0


class TestRevocationVsImmutability:
    """La revocación excluye de builds futuros, NUNCA muta snapshots ya construidos."""

    @pytest.mark.django_db
    def test_v1_untouched_after_revoke(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=15, iv_def=15, hp=15)

        v1 = build_dataset_version(criteria={"min_sample": 1})
        assert v1.row_count == 1

        v1_checksum = v1.checksum
        v1_row_count = v1.row_count

        DataContributionConsent.revoke_consent(user, SCOPE)

        v1_refreshed = DatasetVersion.objects.get(pk=v1.pk)
        assert v1_refreshed.checksum == v1_checksum
        assert v1_refreshed.row_count == v1_row_count

        v2 = build_dataset_version(criteria={"min_sample": 1})
        assert v2.row_count == 0
        assert v2.pk != v1.pk
        assert v2.checksum != v1_checksum

    @pytest.mark.django_db
    def test_editing_built_version_raises(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user)

        v1 = build_dataset_version(criteria={"min_sample": 1})

        # Flags operativos (is_public, min_sample_met) sí se permiten
        v1.is_public = True
        v1.save()
        v1.refresh_from_db()
        assert v1.is_public is True

        # Editar campos de contenido sigue bloqueado
        v1.row_count = 999
        with pytest.raises(ValidationError, match="ya construida"):
            v1.save()


class TestIdempotencia:
    """Dos builds de las mismas entradas deben dar el mismo checksum."""

    @pytest.mark.django_db
    def test_same_input_same_checksum(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=10, iv_def=11, hp=12, observed_at=_utc(2026, 1, 1, 12, 0, 0))

        v1 = build_dataset_version(pipeline_version="1.0.0")
        v2 = build_dataset_version(pipeline_version="1.0.0")

        assert v1.checksum == v2.checksum
        assert v1.row_count == v2.row_count

    @pytest.mark.django_db
    def test_different_pipeline_version_different_checksum(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, observed_at=_utc(2026, 1, 1, 12, 0, 0))

        v1 = build_dataset_version(pipeline_version="1.0.0")
        v2 = build_dataset_version(pipeline_version="2.0.0")

        assert v1.checksum != v2.checksum

    @pytest.mark.django_db
    def test_different_observations_different_checksum(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=10, iv_def=11, hp=12, observed_at=_utc(2026, 1, 1, 12, 0, 0))
        v1 = build_dataset_version(pipeline_version="1.0.0")

        _make_obs(user, atk=13, iv_def=14, hp=15, observed_at=_utc(2026, 2, 1, 12, 0, 0))
        v2 = build_dataset_version(pipeline_version="1.0.0")

        assert v1.checksum != v2.checksum


class TestMinSample:
    @pytest.mark.django_db
    def test_min_sample_not_met(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=10, iv_def=11, hp=12)

        version = build_dataset_version(criteria={"min_sample": 100})
        assert version.min_sample_met is False
        assert version.is_public is False

    @pytest.mark.django_db
    def test_min_sample_met(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        for i in range(50):
            _make_obs(
                user,
                atk=min(i % 16, 15),
                iv_def=min((i + 5) % 16, 15),
                hp=min((i + 10) % 16, 15),
            )

        version = build_dataset_version(criteria={"min_sample": 30})
        assert version.min_sample_met is True
        assert version.is_public is True
        assert version.row_count == 50

    @pytest.mark.django_db
    def test_build_creates_audit_event(self, user):
        from apps.audit.models import AuditEvent

        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=10, iv_def=11, hp=12)

        version = build_dataset_version(criteria={"min_sample": 1})

        events = AuditEvent.objects.filter(verb="dataset_built", target_id=version.pk)
        assert events.count() == 1
        assert events[0].metadata["row_count"] == 1


class TestDatasetVersionImmutability:
    @pytest.mark.django_db
    def test_cannot_edit_built_version(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=10, iv_def=11, hp=12)

        v = build_dataset_version()
        # Should have a checksum after build
        assert v.checksum != ""

        v.criteria = {"min_sample": 999}
        with pytest.raises(ValidationError, match="ya construida"):
            v.save()

    @pytest.mark.django_db
    def test_can_create_new_version_instead(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=10, iv_def=11, hp=12)

        v1 = build_dataset_version(criteria={"min_sample": 1})
        v2 = build_dataset_version(criteria={"min_sample": 100})

        assert v1.pk != v2.pk
        assert v2.number == v1.number + 1


class TestAggregateCommunityDistribution:
    @pytest.mark.django_db
    def test_aggregate_groups_by_lucky_and_friendship(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=14, iv_def=13, hp=12, is_lucky=True, friendship_level="best")
        _make_obs(user, atk=5, iv_def=6, hp=7, is_lucky=False, friendship_level="good")
        _make_obs(user, atk=8, iv_def=9, hp=10, is_lucky=False, friendship_level="good")

        version = build_dataset_version(criteria={"min_sample": 1})
        result = aggregate_community_distribution(version)

        groups_by_key = {(g["is_lucky"], g["friendship_level"]) for g in result}
        assert (True, "best") in groups_by_key
        assert (False, "good") in groups_by_key

    @pytest.mark.django_db
    def test_aggregate_hundo_count(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=15, iv_def=15, hp=15, is_lucky=True, friendship_level="best")
        _make_obs(user, atk=14, iv_def=15, hp=15, is_lucky=True, friendship_level="best")

        version = build_dataset_version(criteria={"min_sample": 1})
        result = aggregate_community_distribution(version)

        lucky_group = [g for g in result if g["is_lucky"]]
        assert len(lucky_group) == 1
        assert lucky_group[0]["n"] == 2
        assert lucky_group[0]["hundo_analysis"]["successes"] == 1
        assert "sum_analysis" in lucky_group[0], "Pooled debe exponer sum_analysis (paridad M5)"

    @pytest.mark.django_db
    def test_empty_dataset_returns_empty_list(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)

        version = build_dataset_version(criteria={"min_sample": 1})

        # row_count is 0 because no observations were seeded in this test
        if version.row_count == 0:
            result = aggregate_community_distribution(version)
            assert result == []


class TestManagementCommand:
    @pytest.mark.django_db
    def test_build_command_idempotent(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=10, iv_def=11, hp=12, observed_at=_utc(2026, 1, 1, 12, 0, 0))

        from django.core.management import call_command

        call_command("build_dataset", min_sample=1, pipeline_version="1.0.0")
        v1 = DatasetVersion.objects.order_by("-number").first()
        assert v1 is not None

        call_command("build_dataset", min_sample=1, pipeline_version="1.0.0")
        v2 = DatasetVersion.objects.order_by("-number").first()
        assert v2 is not None
        assert v2.number == v1.number + 1
        assert v2.checksum == v1.checksum
        assert v2.row_count == v1.row_count


class TestAggregationFromDB:
    """Verifica que aggregate_community_distribution funciona con versiones cargadas de BD."""

    @pytest.mark.django_db
    def test_aggregation_from_db_loaded_version(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=15, iv_def=15, hp=15, is_lucky=True, friendship_level="best")
        _make_obs(user, atk=12, iv_def=13, hp=14, is_lucky=True, friendship_level="best")

        version = build_dataset_version(criteria={"min_sample": 1})
        assert version.anonymized_rows is not None
        assert len(version.anonymized_rows) == 2

        db_version = DatasetVersion.objects.get(pk=version.pk)
        assert not hasattr(db_version, "rows_cache") or not getattr(db_version, "rows_cache", None)

        result = aggregate_community_distribution(db_version)
        assert len(result) == 1
        assert result[0]["n"] == 2
        assert result[0]["hundo_analysis"]["successes"] == 1
        assert "sum_analysis" in result[0], "Pooled desde BD debe exponer sum_analysis (paridad M5)"


class TestConsentViews:
    @pytest.mark.django_db
    def test_grant_view_redirects(self, client, user):
        client.force_login(user)
        response = client.post("/es/contribuciones/consentir/")
        assert response.status_code == 302

        consent = DataContributionConsent.objects.filter(user=user, scope=SCOPE).first()
        assert consent is not None
        assert consent.is_active is True

    @pytest.mark.django_db
    def test_revoke_view_redirects(self, client, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        client.force_login(user)
        response = client.post("/es/contribuciones/revocar/")
        assert response.status_code == 302

        consent = DataContributionConsent.objects.get(user=user, scope=SCOPE)
        assert consent.is_active is False

    @pytest.mark.django_db
    def test_consent_views_require_login(self, client):
        response = client.get("/es/contribuciones/consentir/")
        assert response.status_code == 302
        assert "login" in response.url

    @pytest.mark.django_db
    def test_grant_consent_rejects_get(self, client, user):
        client.force_login(user)
        response = client.get(reverse("contributions:grant"))
        assert response.status_code == 405
        assert not DataContributionConsent.objects.filter(user=user, scope=SCOPE).exists()

    @pytest.mark.django_db
    def test_revoke_consent_rejects_get(self, client, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        client.force_login(user)
        response = client.get(reverse("contributions:revoke"))
        assert response.status_code == 405
        consent = DataContributionConsent.objects.get(user=user, scope=SCOPE)
        assert consent.is_active is True

    @pytest.mark.django_db
    def test_consent_redirect_ignores_external_referer(self, client, user):
        client.force_login(user)
        response = client.post(
            reverse("contributions:grant"),
            HTTP_REFERER="https://evil.example.com/steal",
        )
        assert response.status_code == 302
        assert response.url == "/"
