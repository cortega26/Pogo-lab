"""Tests de integracion para apps/trades — servicio + vistas + CSV + dashboard."""

import json
from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model

from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter
from apps.trades.models import TradeObservation, TradeSession
from apps.trades.services import (
    _compute_dedup_hash,
    _determine_state,
    _sanitize_csv_cell,
    bulk_create_observations,
    dashboard_stats,
    export_csv,
    import_csv,
    parse_csv_row,
    register_observation,
)

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
def user():
    return User.objects.create_user(email="test@example.com", password="pass123")


@pytest.fixture
def user2():
    return User.objects.create_user(email="other@example.com", password="pass123")


class TestRegisterObservation:
    @pytest.mark.django_db
    def test_valid_observation(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
            species="Mewtwo",
        )
        assert obs.state == "valid"
        assert obs.is_lucky is True
        assert obs.atk == 12
        assert obs.iv_def == 15
        assert obs.hp == 13

    @pytest.mark.django_db
    def test_excluded_iv_out_of_range(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=15,
            def_=15,
            hp=20,
        )
        assert obs.state == "excluded"
        assert "fuera de rango" in obs.exclusion_reason

    @pytest.mark.django_db
    def test_suspicious_below_floor(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="lucky",
            atk=11,
            def_=15,
            hp=15,
        )
        assert obs.state == "suspicious"
        assert "Inconsistente con el piso" in obs.exclusion_reason
        assert "f=12" in obs.exclusion_reason

    @pytest.mark.django_db
    def test_duplicate_detected(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
            species="Pikachu",
        )
        obs2 = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
            species="Pikachu",
        )
        assert obs2.state == "duplicate"

    @pytest.mark.django_db
    def test_non_duplicate_different_day(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
        )
        obs2 = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 18),
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
        )
        assert obs2.state == "valid"

    @pytest.mark.django_db
    def test_non_duplicate_different_owner(self, user, user2):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
        )
        obs2 = register_observation(
            owner_id=user2.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
        )
        assert obs2.state == "valid"

    @pytest.mark.django_db
    def test_is_lucky_derived_from_trade_type(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="lucky_guaranteed",
            atk=12,
            def_=15,
            hp=13,
        )
        assert obs.is_lucky is True
        assert obs.trade_type == "lucky_guaranteed"

    @pytest.mark.django_db
    def test_ruleset_assigned(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
        )
        assert obs.ruleset is not None
        assert obs.ruleset.version == 1

    @pytest.mark.django_db
    def test_register_observation_rejects_bad_friendship(self, user):
        with pytest.raises(ValueError, match="friendship_level inválido"):
            register_observation(
                owner_id=user.pk,
                observed_at=_utc(2026, 7, 17),
                friendship_level="lolz",
                trade_type="normal",
                atk=10,
                def_=10,
                hp=10,
            )
        assert TradeObservation.objects.count() == 0

    @pytest.mark.django_db
    def test_register_observation_rejects_bad_trade_type(self, user):
        with pytest.raises(ValueError, match="trade_type inválido"):
            register_observation(
                owner_id=user.pk,
                observed_at=_utc(2026, 7, 17),
                friendship_level="good",
                trade_type="bogus",
                atk=10,
                def_=10,
                hp=10,
            )
        assert TradeObservation.objects.count() == 0

    @pytest.mark.django_db
    def test_explicit_state_not_overridden(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
            state="draft",
        )
        assert obs.state == "draft"


class TestBulkCreate:
    @pytest.mark.django_db
    def test_bulk_create_valid(self, user):
        result = bulk_create_observations(
            [
                {
                    "owner_id": user.pk,
                    "observed_at": _utc(2026, 7, 17),
                    "friendship_level": "best",
                    "trade_type": "lucky",
                    "atk": 12,
                    "def_": 15,
                    "hp": 13,
                },
                {
                    "owner_id": user.pk,
                    "observed_at": _utc(2026, 7, 17),
                    "friendship_level": "good",
                    "trade_type": "normal",
                    "atk": 5,
                    "def_": 5,
                    "hp": 5,
                },
            ]
        )
        assert len(result) == 2
        assert result[0].state == "valid"
        assert result[1].state == "valid"

    @pytest.mark.django_db
    def test_bulk_create_mixed(self, user):
        result = bulk_create_observations(
            [
                {
                    "owner_id": user.pk,
                    "observed_at": _utc(2026, 7, 17),
                    "friendship_level": "best",
                    "trade_type": "lucky",
                    "atk": 12,
                    "def_": 15,
                    "hp": 13,
                },
                {
                    "owner_id": user.pk,
                    "observed_at": _utc(2026, 7, 17),
                    "friendship_level": "good",
                    "trade_type": "lucky",
                    "atk": 11,
                    "def_": 15,
                    "hp": 15,
                },
            ]
        )
        assert len(result) == 2
        assert result[0].state == "valid"
        assert result[1].state == "suspicious"

    @pytest.mark.django_db
    def test_bulk_create_rejects_and_rolls_back(self, user):
        with pytest.raises(ValueError, match="friendship_level inválido"):
            bulk_create_observations(
                [
                    {
                        "owner_id": user.pk,
                        "observed_at": _utc(2026, 7, 17),
                        "friendship_level": "best",
                        "trade_type": "lucky",
                        "atk": 12,
                        "def_": 15,
                        "hp": 13,
                    },
                    {
                        "owner_id": user.pk,
                        "observed_at": _utc(2026, 7, 18),
                        "friendship_level": "lolz",
                        "trade_type": "normal",
                        "atk": 5,
                        "def_": 5,
                        "hp": 5,
                    },
                ]
            )
        assert TradeObservation.objects.count() == 0

    @pytest.mark.django_db
    def test_bulk_create_atomic(self, user):
        r1 = bulk_create_observations(
            [
                {
                    "owner_id": user.pk,
                    "observed_at": _utc(2026, 7, 17),
                    "friendship_level": "good",
                    "trade_type": "normal",
                    "atk": 5,
                    "def_": 5,
                    "hp": 5,
                },
            ]
        )
        assert len(r1) == 1


class TestCSVImport:
    @pytest.mark.django_db
    def test_import_valid_csv(self, user):
        csv_content = (
            "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
            "2026-07-17T12:00:00+00:00,best,lucky,12,15,13,Mewtwo\n"
            "2026-07-17T12:05:00+00:00,good,normal,5,10,8,\n"
        )
        result = import_csv(csv_content, user.pk)
        assert result["total"] == 2
        assert result["valid_count"] == 2
        assert result["error_count"] == 0
        assert len(result["created"]) == 2

    @pytest.mark.django_db
    def test_import_csv_with_errors(self, user):
        csv_content = (
            "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
            "2026-07-17T12:00:00+00:00,best,lucky,12,15,13,Mewtwo\n"
            "invalid-date,good,normal,5,10,8,\n"
            "2026-07-17T12:10:00+00:00,bad_level,normal,5,5,5,\n"
        )
        result = import_csv(csv_content, user.pk)
        assert result["total"] == 3
        assert result["valid_count"] == 1
        assert result["error_count"] == 2

    @pytest.mark.django_db
    def test_import_csv_excluded_ivs(self, user):
        csv_content = (
            "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
            "2026-07-17T12:00:00+00:00,good,normal,15,15,20,\n"
        )
        result = import_csv(csv_content, user.pk)
        assert result["valid_count"] == 1
        assert result["created"][0].state == "excluded"

    @pytest.mark.django_db
    def test_import_csv_dedup(self, user):
        csv_content = (
            "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
            "2026-07-17T12:00:00+00:00,best,lucky,12,15,13,Mewtwo\n"
        )
        r1 = import_csv(csv_content, user.pk)
        assert r1["valid_count"] == 1
        r2 = import_csv(csv_content, user.pk)
        assert r2["valid_count"] == 1
        assert r2["created"][0].state == "duplicate"

    @pytest.mark.django_db
    def test_csv_utf8_bom_handling(self, user):
        csv_content = (
            "\ufeffobserved_at,friendship_level,trade_type,atk,def,hp,species\n"
            "2026-07-17T12:00:00+00:00,best,lucky,12,15,13,Mewtwo\n"
        )
        result = import_csv(csv_content, user.pk)
        assert result["valid_count"] == 1


class TestCSVExport:
    @pytest.mark.django_db
    def test_export_empty(self, user):
        content = export_csv(user.pk)
        lines = content.strip().split("\n")
        assert len(lines) == 1
        assert "observed_at" in lines[0]

    @pytest.mark.django_db
    def test_export_with_data(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
            species="Mewtwo",
        )
        content = export_csv(user.pk)
        lines = content.strip().split("\n")
        assert len(lines) == 2
        assert "lucky" in lines[1]
        assert "Mewtwo" in lines[1]

    @pytest.mark.django_db
    def test_export_excludes_deleted(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=5,
            def_=5,
            hp=5,
            state="deleted",
        )
        content = export_csv(user.pk)
        lines = content.strip().split("\n")
        assert len(lines) == 1

    @pytest.mark.django_db
    def test_export_sanitizes_dangerous_cells(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
            species="=CMD()",
        )
        content = export_csv(user.pk)
        assert "'=CMD()" in content

    @pytest.mark.django_db
    def test_export_does_not_include_notes(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=5,
            def_=5,
            hp=5,
            notes="private_data",
        )
        content = export_csv(user.pk)
        assert "private_data" not in content
        assert "notes" not in content

    @pytest.mark.django_db
    def test_export_only_own_user(self, user, user2):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=5,
            def_=5,
            hp=5,
        )
        content = export_csv(user2.pk)
        lines = content.strip().split("\n")
        assert len(lines) == 1


class TestSanitizeCSVCell:
    def test_equal_sign_prefixed(self):
        assert _sanitize_csv_cell("=CMD()") == "'=CMD()"

    def test_plus_sign_prefixed(self):
        assert _sanitize_csv_cell("+1") == "'+1"

    def test_minus_sign_prefixed(self):
        assert _sanitize_csv_cell("-1") == "'-1"

    def test_at_sign_prefixed(self):
        assert _sanitize_csv_cell("@x") == "'@x"

    def test_tab_prefixed(self):
        assert _sanitize_csv_cell("\t") == "'\t"

    def test_normal_cell_unchanged(self):
        assert _sanitize_csv_cell("Mewtwo") == "Mewtwo"

    def test_empty_cell_unchanged(self):
        assert _sanitize_csv_cell("") == ""


class TestDashboard:
    @pytest.mark.django_db
    def test_dashboard_empty(self, user):
        stats = dashboard_stats(user.pk)
        assert stats["total"] == 0
        assert stats["lucky"] == 0
        assert stats["normal"] == 0

    @pytest.mark.django_db
    def test_dashboard_separates_lucky_normal(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
        )
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=5,
            def_=5,
            hp=5,
        )
        stats = dashboard_stats(user.pk)
        assert stats["total"] == 2
        assert stats["lucky"] == 1
        assert stats["normal"] == 1

    @pytest.mark.django_db
    def test_dashboard_excludes_deleted(self, user):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=5,
            def_=5,
            hp=5,
        )
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=10,
            def_=10,
            hp=10,
            state="deleted",
        )
        stats = dashboard_stats(user.pk)
        assert stats["total"] == 1

    @pytest.mark.django_db
    def test_dashboard_per_user(self, user, user2):
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=5,
            def_=5,
            hp=5,
        )
        stats_user2 = dashboard_stats(user2.pk)
        assert stats_user2["total"] == 0


class TestTradeSession:
    @pytest.mark.django_db
    def test_create_session(self, user):
        session = TradeSession.objects.create(
            owner=user,
            started_at=_utc(2026, 7, 17),
            label="Sesion de prueba",
        )
        assert session.label == "Sesion de prueba"
        assert session.owner == user

    @pytest.mark.django_db
    def test_session_defaults(self, user):
        session = TradeSession.objects.create(
            owner=user,
            started_at=_utc(2026, 7, 17),
        )
        assert session.default_friendship == "good"
        assert session.default_trade_type == "normal"

    @pytest.mark.django_db
    def test_session_str_with_label(self, user):
        session = TradeSession.objects.create(
            owner=user,
            started_at=_utc(2026, 7, 17),
            label="Mi sesion",
        )
        assert str(session) == "Mi sesion"

    @pytest.mark.django_db
    def test_session_str_without_label(self, user):
        session = TradeSession.objects.create(
            owner=user,
            started_at=_utc(2026, 7, 17),
        )
        assert "Sesi" in str(session)
        assert "2026-07-17" in str(session)


class TestTradeObservationModel:
    @pytest.mark.django_db
    def test_iv_range_enforced_by_service(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="good",
            trade_type="normal",
            atk=15,
            def_=15,
            hp=20,
        )
        assert obs.state == "excluded"
        assert "fuera de rango" in obs.exclusion_reason

    @pytest.mark.django_db
    def test_observation_str(self, user):
        obs = register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
        )
        assert "Obs #" in str(obs)
        assert "Best" in str(obs) or "best" in str(obs)


class TestDedupHash:
    @pytest.mark.django_db
    def test_same_input_same_hash(self, user):
        h1 = _compute_dedup_hash(
            user.pk,
            _utc(2026, 7, 17),
            "best",
            "lucky",
            12,
            15,
            13,
            "Mewtwo",
        )
        h2 = _compute_dedup_hash(
            user.pk,
            _utc(2026, 7, 17),
            "best",
            "lucky",
            12,
            15,
            13,
            "Mewtwo",
        )
        assert h1 == h2

    @pytest.mark.django_db
    def test_different_day_different_hash(self, user):
        h1 = _compute_dedup_hash(
            user.pk,
            _utc(2026, 7, 17),
            "best",
            "lucky",
            12,
            15,
            13,
            "Mewtwo",
        )
        h2 = _compute_dedup_hash(
            user.pk,
            _utc(2026, 7, 18),
            "best",
            "lucky",
            12,
            15,
            13,
            "Mewtwo",
        )
        assert h1 != h2

    @pytest.mark.django_db
    def test_deterministic(self, user):
        h1 = _compute_dedup_hash(
            user.pk,
            _utc(2026, 7, 17),
            "best",
            "lucky",
            12,
            15,
            13,
            "Mewtwo",
        )
        h2 = _compute_dedup_hash(
            user.pk,
            _utc(2026, 7, 17),
            "best",
            "lucky",
            12,
            15,
            13,
            "Mewtwo",
        )
        assert h1 == h2


class TestDetermineState:
    @pytest.mark.django_db
    def test_range_excluded(self, user):
        state, _reason = _determine_state(
            20, 15, 15, "good", "normal", user.pk, _utc(2026, 7, 17), "", ""
        )
        assert state == "excluded"

    @pytest.mark.django_db
    def test_below_floor_suspicious(self, user):
        state, reason = _determine_state(
            11, 15, 15, "good", "lucky", user.pk, _utc(2026, 7, 17), "", ""
        )
        assert state == "suspicious"
        assert "f=12" in reason

    @pytest.mark.django_db
    def test_suspicious_no_ruleset_falls_back_to_f0(self, user):
        Mechanic.objects.filter(key="trade_iv").delete()
        state, reason = _determine_state(
            -1, 0, 0, "good", "normal", user.pk, _utc(2026, 7, 17), "", ""
        )
        assert state == "excluded"
        assert "fuera de rango" in reason

    @pytest.mark.django_db
    def test_valid_no_ruleset_does_not_raise(self, user):
        Mechanic.objects.filter(key="trade_iv").delete()
        state, _reason = _determine_state(
            0, 0, 0, "good", "normal", user.pk, _utc(2026, 7, 17), "", ""
        )
        assert state == "valid"


class TestCSVParsingSadPaths:
    @pytest.mark.django_db
    def test_invalid_trade_type(self, user):
        result = parse_csv_row(
            {
                "observed_at": "2026-07-17T12:00:00+00:00",
                "friendship_level": "best",
                "trade_type": "invalid",
                "atk": "12",
                "def": "15",
                "hp": "13",
            },
            2,
            user.pk,
        )
        assert isinstance(result, str)
        assert "trade_type invalido" in result

    @pytest.mark.django_db
    def test_non_integer_ivs(self, user):
        result = parse_csv_row(
            {
                "observed_at": "2026-07-17T12:00:00+00:00",
                "friendship_level": "best",
                "trade_type": "lucky",
                "atk": "abc",
                "def": "15",
                "hp": "13",
            },
            3,
            user.pk,
        )
        assert isinstance(result, str)
        assert "IVs deben ser enteros" in result

    @pytest.mark.django_db
    def test_missing_date(self, user):
        result = parse_csv_row(
            {
                "observed_at": "",
                "friendship_level": "best",
                "trade_type": "lucky",
                "atk": "12",
                "def": "15",
                "hp": "13",
            },
            4,
            user.pk,
        )
        assert isinstance(result, str)
        assert "observed_at invalido" in result


class TestTradeViewsMalformedInput:
    @pytest.mark.django_db
    def test_observation_create_bad_date_returns_400_not_500(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/es/intercambios/observar/",
            {
                "observed_at": "not-a-date",
                "friendship_level": "best",
                "trade_type": "lucky",
                "atk": "12",
                "def": "15",
                "hp": "13",
            },
        )
        assert resp.status_code == 400
        assert TradeObservation.objects.count() == 0

    @pytest.mark.django_db
    def test_observation_create_non_numeric_iv_400(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/es/intercambios/observar/",
            {
                "friendship_level": "best",
                "trade_type": "lucky",
                "atk": "x",
                "def": "15",
                "hp": "13",
            },
        )
        assert resp.status_code == 400
        assert TradeObservation.objects.count() == 0

    @pytest.mark.django_db
    def test_bulk_add_non_list_json_400(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/es/intercambios/lotes/",
            {"observations_json": '{"a":1}'},
        )
        assert resp.status_code == 400
        assert "Se esperaba una lista" in resp.content.decode()
        assert TradeObservation.objects.count() == 0

    @pytest.mark.django_db
    def test_csv_import_binary_file_shows_error(self, client, user):
        import io

        client.force_login(user)
        resp = client.post(
            "/es/intercambios/csv/importar/",
            {"csv_file": io.BytesIO(b"\xff\xfe\x00")},
        )
        assert resp.status_code == 200
        assert "UTF-8" in resp.content.decode()
        assert TradeObservation.objects.count() == 0


class TestTradeViews:
    @pytest.mark.django_db
    def test_session_list_requires_login(self, client):
        resp = client.get("/es/intercambios/")
        assert resp.status_code == 302

    @pytest.mark.django_db
    def test_session_list_logged_in(self, client, user):
        client.force_login(user)
        resp = client.get("/es/intercambios/")
        assert resp.status_code == 200

    @pytest.mark.django_db
    def test_observation_create_get(self, client, user):
        client.force_login(user)
        resp = client.get("/es/intercambios/observar/")
        assert resp.status_code == 200

    @pytest.mark.django_db
    def test_observation_create_post(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/es/intercambios/observar/",
            {
                "friendship_level": "best",
                "trade_type": "lucky",
                "atk": "12",
                "def": "15",
                "hp": "13",
                "species": "Mewtwo",
            },
        )
        assert resp.status_code == 200
        assert TradeObservation.objects.count() == 1

    @pytest.mark.django_db
    def test_dashboard_view(self, client, user):
        client.force_login(user)
        resp = client.get("/es/intercambios/dashboard/")
        assert resp.status_code == 200
        assert "0" in resp.content.decode()

    @pytest.mark.django_db
    def test_dashboard_with_data(self, client, user):
        client.force_login(user)
        register_observation(
            owner_id=user.pk,
            observed_at=_utc(2026, 7, 17),
            friendship_level="best",
            trade_type="lucky",
            atk=12,
            def_=15,
            hp=13,
        )
        resp = client.get("/es/intercambios/dashboard/")
        html = resp.content.decode()
        assert "1" in html

    @pytest.mark.django_db
    def test_csv_export_view(self, client, user):
        client.force_login(user)
        resp = client.get("/es/intercambios/csv/exportar/")
        assert resp.status_code == 200
        assert resp["Content-Type"] == "text/csv; charset=utf-8"
        assert "observaciones.csv" in resp["Content-Disposition"]

    @pytest.mark.django_db
    def test_csv_import_view_get(self, client, user):
        client.force_login(user)
        resp = client.get("/es/intercambios/csv/importar/")
        assert resp.status_code == 200

    @pytest.mark.django_db
    def test_csv_import_post(self, client, user):
        client.force_login(user)
        import io

        csv_content = (
            "observed_at,friendship_level,trade_type,atk,def,hp,species\n"
            "2026-07-17T12:00:00+00:00,best,lucky,12,15,13,Mewtwo\n"
        )
        resp = client.post(
            "/es/intercambios/csv/importar/",
            {"csv_file": io.BytesIO(csv_content.encode("utf-8"))},
        )
        assert resp.status_code == 200
        assert TradeObservation.objects.count() == 1

    @pytest.mark.django_db
    def test_bulk_add_get(self, client, user):
        client.force_login(user)
        resp = client.get("/es/intercambios/lotes/")
        assert resp.status_code == 200

    @pytest.mark.django_db
    def test_bulk_add_post(self, client, user):
        client.force_login(user)
        data = json.dumps(
            [
                {
                    "observed_at": "2026-07-17T12:00:00+00:00",
                    "friendship_level": "best",
                    "trade_type": "lucky",
                    "atk": 12,
                    "def": 15,
                    "hp": 13,
                    "species": "Mewtwo",
                },
            ]
        )
        resp = client.post(
            "/es/intercambios/lotes/",
            {"observations_json": data},
        )
        assert resp.status_code == 200
        assert TradeObservation.objects.count() == 1

    @pytest.mark.django_db
    def test_session_create(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/es/intercambios/nueva/",
            {"label": "Mi sesion", "default_friendship": "best", "default_trade_type": "lucky"},
        )
        assert resp.status_code == 200
        assert TradeSession.objects.count() == 1

    @pytest.mark.django_db
    def test_session_detail(self, client, user):
        client.force_login(user)
        session = TradeSession.objects.create(owner=user, started_at=_utc(2026, 7, 17))
        resp = client.get(f"/es/intercambios/{session.pk}/")
        assert resp.status_code == 200

    @pytest.mark.django_db
    def test_session_detail_not_owner(self, client, user, user2):
        client.force_login(user2)
        session = TradeSession.objects.create(owner=user, started_at=_utc(2026, 7, 17))
        resp = client.get(f"/es/intercambios/{session.pk}/")
        assert resp.status_code == 404

    @pytest.mark.django_db
    def test_htmx_observation_create(self, client, user):
        client.force_login(user)
        resp = client.post(
            "/es/intercambios/observar/",
            {
                "friendship_level": "best",
                "trade_type": "lucky",
                "atk": "12",
                "def": "15",
                "hp": "13",
            },
            HTTP_HX_REQUEST="true",
        )
        assert resp.status_code == 200
        assert "<html" not in resp.content.decode()
