"""Tests del dashboard comunitario (apps/experiments)."""

from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model

from apps.contributions.models import DataContributionConsent
from apps.contributions.services import build_dataset_version
from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter
from apps.trades.models import TradeObservation

from ..models import ExperimentProtocol

User = get_user_model()
SCOPE = "community_dataset"
CONSENT_VERSION = "1.0.0"


def _utc(year, month, day, hour=0, minute=0, second=0):
    return datetime(year, month, day, hour, minute, second, tzinfo=UTC)


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
        RuleParameter.objects.create(ruleset=rs, key=key, value=value, data_type="integer")


@pytest.fixture
def user():
    return User.objects.create_user(email="expuser@test.com", password="pass123")


def _make_obs(user, atk=14, iv_def=13, hp=12, is_lucky=True, friendship_level="best"):
    ruleset = MechanicRuleSet.objects.filter(is_published=True).first()
    return TradeObservation.objects.create(
        owner=user,
        observed_at=_utc(2026, 7, 15),
        friendship_level=friendship_level,
        trade_type="lucky" if is_lucky else "normal",
        is_lucky=is_lucky,
        atk=atk,
        iv_def=iv_def,
        hp=hp,
        state="valid",
        contribution_optin=True,
        ruleset=ruleset,
    )


class TestExperimentProtocol:
    @pytest.mark.django_db
    def test_create_protocol(self):
        mechanic = Mechanic.objects.get(key="trade_iv")
        protocol = ExperimentProtocol.objects.create(
            mechanic=mechanic,
            hypothesis="El piso Lucky es f=12.",
            status="draft",
            min_sample=30,
        )
        assert protocol.pk is not None
        assert protocol.hypothesis == "El piso Lucky es f=12."

    @pytest.mark.django_db
    def test_protocol_with_dataset(self, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user)
        version = build_dataset_version(criteria={"min_sample": 1})

        mechanic = Mechanic.objects.get(key="trade_iv")
        protocol = ExperimentProtocol.objects.create(
            mechanic=mechanic,
            hypothesis="Dataset comunitario anonimizado funciona.",
            dataset_version=version,
        )
        assert protocol.dataset_version == version


class TestCommunityDashboardView:
    @pytest.mark.django_db
    def test_dashboard_empty_dataset(self, client):
        response = client.get("/es/comunidad/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Dataset" in content

    @pytest.mark.django_db
    def test_dashboard_with_data(self, client, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=15, iv_def=15, hp=15)
        build_dataset_version(criteria={"min_sample": 1})

        response = client.get("/es/comunidad/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "Total de observaciones" in content
        assert "Afortunados" in content
        assert "Advertencia sobre los datos" in content or "advertencia" in content.lower()

    @pytest.mark.django_db
    def test_dashboard_shows_bias_warning(self, client):
        response = client.get("/es/comunidad/")
        assert response.status_code == 200
        content = response.content.decode()
        assert "auto-selección" in content or "sesgo" in content.lower()

    @pytest.mark.django_db
    def test_dashboard_hides_below_threshold_dataset(self, client, user):
        """Regresión M6-2: un dataset sub-umbral (is_public=False) NO se muestra."""
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=15, iv_def=15, hp=15)
        version = build_dataset_version(criteria={"min_sample": 100})
        assert version.is_public is False

        response = client.get("/es/comunidad/")
        assert response.status_code == 200
        content = response.content.decode()
        # No expone los totales de un dataset que no alcanzó el umbral mínimo.
        assert "Total de observaciones" not in content

    @pytest.mark.django_db
    def test_download_disabled_by_default(self, client, user):
        DataContributionConsent.grant_consent(user, SCOPE, CONSENT_VERSION)
        _make_obs(user, atk=15, iv_def=15, hp=15)
        build_dataset_version(criteria={"min_sample": 1})

        response = client.get("/es/comunidad/")
        content = response.content.decode()
        assert "no está habilitada" in content or "revisión legal" in content
