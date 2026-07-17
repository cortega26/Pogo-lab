"""Tests para las vistas de exportación y eliminación de cuenta."""

import json
from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.analysis.models import AnalysisRun
from apps.audit.models import AuditEvent
from apps.contributions.models import DataContributionConsent, DatasetVersion
from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter
from apps.trades.models import TradeObservation, TradeSession

User = get_user_model()


def _utc(year, month, day):
    return datetime(year, month, day, tzinfo=UTC)


@pytest.fixture(autouse=True)
def _seeded_mechanic(db):
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
        is_published=True,
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


@pytest.fixture
def user(db):
    return User.objects.create_user(email="test@example.com", password="pass123")


@pytest.fixture
def user2(db):
    return User.objects.create_user(email="other@example.com", password="pass123")


@pytest.fixture
def client():
    return Client()


def _create_observation(user, atk=12, iv_def=14, hp=13, state="valid", notes=""):
    obs = TradeObservation.objects.create(
        owner=user,
        observed_at=_utc(2026, 7, 17),
        friendship_level="best",
        trade_type="lucky",
        is_lucky=True,
        atk=atk,
        iv_def=iv_def,
        hp=hp,
        species="Mewtwo",
        state=state,
        notes=notes,
        dedup_hash=f"hash_{user.pk}_{atk}",
    )
    return obs


def _create_session(user, label="Sesión test"):
    return TradeSession.objects.create(
        owner=user,
        started_at=_utc(2026, 7, 16),
        label=label,
    )


# ── EXPORT ──────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_export_includes_only_own_data(user, user2):
    from apps.accounts.views import _build_export_payload

    obs1 = _create_observation(user, atk=12)
    obs2 = _create_observation(user2, atk=13)
    session1 = _create_session(user, label="A")
    session2 = _create_session(user2, label="B")

    payload = _build_export_payload(user)

    obs_ids = {o["id"] for o in payload["observations"]}
    session_ids = {s["id"] for s in payload["sessions"]}

    assert obs1.pk in obs_ids
    assert obs2.pk not in obs_ids
    assert session1.pk in session_ids
    assert session2.pk not in session_ids


@pytest.mark.django_db
def test_export_excludes_notes(user):
    from apps.accounts.views import _build_export_payload

    _create_observation(user, notes="nota privada con PII")

    payload = _build_export_payload(user)

    exported = payload["observations"][0]
    assert "notes" not in exported, "El campo notes no debe aparecer en el export"


@pytest.mark.django_db
def test_export_view_get_shows_page(client, user):
    client.force_login(user)
    response = client.get("/es/cuenta/exportar/")
    assert response.status_code == 200
    assert "accounts/export.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_export_view_post_downloads_json(client, user):
    client.force_login(user)
    _create_observation(user)
    _create_session(user)

    response = client.post("/es/cuenta/exportar/")
    assert response.status_code == 200
    assert response["Content-Type"] == "application/json"
    assert "attachment" in response.get("Content-Disposition", "")

    data = json.loads(response.content)
    assert len(data["observations"]) == 1
    assert len(data["sessions"]) == 1
    assert "notes" not in data["observations"][0]


@pytest.mark.django_db
def test_export_creates_audit_event(client, user):
    client.force_login(user)

    client.post("/es/cuenta/exportar/")

    event = AuditEvent.objects.filter(verb="account_data_exported").first()
    assert event is not None
    assert event.actor == user
    assert event.target_id == user.pk


@pytest.mark.django_db
def test_export_requires_login(client):
    response = client.get("/es/cuenta/exportar/")
    assert response.status_code == 302  # redirect to login


# ── DELETE ───────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_delete_removes_pii_from_db(client, user):
    client.force_login(user)

    obs1 = _create_observation(user, atk=12, notes="nota PII")
    obs2 = _create_observation(user, atk=13, notes="otra nota PII")
    session = _create_session(user)
    email_original = user.email

    response = client.post("/es/cuenta/eliminar/")
    assert response.status_code == 200
    assert "accounts/delete_done.html" in [t.name for t in response.templates]

    # Las observaciones deben estar borradas de la BD
    assert not TradeObservation.objects.filter(pk=obs1.pk).exists()
    assert not TradeObservation.objects.filter(pk=obs2.pk).exists()
    assert not TradeSession.objects.filter(pk=session.pk).exists()

    # El email original no debe existir
    assert not User.objects.filter(email=email_original).exists()

    # El perfil debe estar eliminado
    user.refresh_from_db()
    with pytest.raises(User.profile.RelatedObjectDoesNotExist):
        _ = user.profile


@pytest.mark.django_db
def test_delete_removes_all_observations_including_deleted(client, user):
    """Todas las observaciones del usuario se borran físicamente, incluidas las soft-deleted."""
    client.force_login(user)

    obs_deleted = _create_observation(user, atk=12, state="deleted")
    obs_valid = _create_observation(user, atk=13, state="valid")

    client.post("/es/cuenta/eliminar/")

    assert not TradeObservation.objects.filter(pk=obs_deleted.pk).exists()
    assert not TradeObservation.objects.filter(pk=obs_valid.pk).exists()


@pytest.mark.django_db
def test_delete_anonymizes_user(client, user):
    client.force_login(user)
    email_original = user.email

    client.post("/es/cuenta/eliminar/")

    user.refresh_from_db()
    assert user.email != email_original
    assert user.email.startswith("deleted_")
    assert user.email.endswith("@pogolab.local")
    assert not user.is_active


@pytest.mark.django_db
def test_delete_does_not_mutate_dataset_versions(client, user):
    client.force_login(user)

    ds = DatasetVersion.objects.create(
        number=1,
        criteria={"min_sample": 30},
        min_sample_met=True,
        row_count=50,
        checksum="abc123",
        is_public=True,
        pipeline_version="1.0.0",
    )
    ds_before = {
        "number": ds.number,
        "row_count": ds.row_count,
        "checksum": ds.checksum,
        "is_public": ds.is_public,
        "pipeline_version": ds.pipeline_version,
    }

    client.post("/es/cuenta/eliminar/")

    ds.refresh_from_db()
    assert ds.number == ds_before["number"]
    assert ds.row_count == ds_before["row_count"]
    assert ds.checksum == ds_before["checksum"]
    assert ds.is_public == ds_before["is_public"]
    assert ds.pipeline_version == ds_before["pipeline_version"]


@pytest.mark.django_db
def test_delete_audit_events_created(client, user):
    client.force_login(user)
    _create_observation(user, atk=12)
    _create_session(user)
    AnalysisRun.objects.create(owner=user)
    DataContributionConsent.objects.create(
        user=user,
        scope="community_dataset",
        consent_text_version="v1",
        is_active=True,
    )

    client.post("/es/cuenta/eliminar/")

    event = AuditEvent.objects.filter(verb="account_deleted").first()
    assert event is not None
    assert event.actor is None  # el actor queda anónimo porque el usuario se anonimiza
    assert event.target_id == user.pk
    stats = event.metadata["stats"]
    assert stats["observations_deleted"] >= 1
    assert stats["sessions_deleted"] >= 1
    assert stats["analysis_runs_deleted"] >= 1
    assert stats["consents_deleted"] >= 1
    assert stats["profile_deleted"] is True


@pytest.mark.django_db
def test_delete_requires_login(client):
    response = client.post("/es/cuenta/eliminar/")
    assert response.status_code == 302  # redirect to login


@pytest.mark.django_db
def test_delete_shows_confirmation_on_get(client, user):
    client.force_login(user)
    response = client.get("/es/cuenta/eliminar/")
    assert response.status_code == 200
    assert "accounts/delete.html" in [t.name for t in response.templates]


@pytest.mark.django_db
def test_delete_removes_consent_records(client, user):
    client.force_login(user)
    consent = DataContributionConsent.objects.create(
        user=user,
        scope="community_dataset",
        consent_text_version="v2",
        is_active=True,
    )

    client.post("/es/cuenta/eliminar/")

    assert not DataContributionConsent.objects.filter(pk=consent.pk).exists()


@pytest.mark.django_db
def test_delete_removes_analysis_runs(client, user):
    client.force_login(user)
    run = AnalysisRun.objects.create(owner=user)

    client.post("/es/cuenta/eliminar/")

    assert not AnalysisRun.objects.filter(pk=run.pk).exists()


@pytest.mark.django_db
def test_delete_only_affects_own_data(client, user, user2):
    client.force_login(user)

    obs_self = _create_observation(user, atk=12)
    obs_other = _create_observation(user2, atk=13)
    session_self = _create_session(user)
    session_other = _create_session(user2, label="Otro")

    client.post("/es/cuenta/eliminar/")

    # Los datos del usuario se borraron
    assert not TradeObservation.objects.filter(pk=obs_self.pk).exists()
    assert not TradeSession.objects.filter(pk=session_self.pk).exists()

    # Los datos del otro usuario permanecen intactos
    assert TradeObservation.objects.filter(pk=obs_other.pk).exists()
    assert TradeSession.objects.filter(pk=session_other.pk).exists()

    # El otro usuario sigue activo
    user2.refresh_from_db()
    assert user2.is_active


# ── PII EN AUDITORÍA (M7-1) ──────────────────────────────────────────


@pytest.mark.django_db
def test_delete_no_pii_in_audit_event(client, user):
    """El email centinela NO debe aparecer en AuditEvent.metadata tras el borrado."""
    client.force_login(user)
    email_original = user.email

    _create_observation(user, atk=12, notes="nota PII")
    AnalysisRun.objects.create(owner=user)
    DataContributionConsent.objects.create(
        user=user,
        scope="community_dataset",
        consent_text_version="v1",
        is_active=True,
    )

    client.post("/es/cuenta/eliminar/")

    events = AuditEvent.objects.filter(verb="account_deleted")
    assert events.exists(), "Debe existir al menos un AuditEvent de borrado"

    for event in events:
        metadata_str = str(event.metadata)
        assert email_original not in metadata_str, (
            f"El email {email_original} NO debe aparecer en AuditEvent.metadata: {metadata_str}"
        )

    # Verificar que el email tampoco está en forma de hash falso
    first_event = events.first()
    assert first_event is not None
    assert "original_email_hash" not in str(first_event.metadata)
