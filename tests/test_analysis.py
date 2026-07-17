"""Tests para apps/analysis — servicios y modelo.

Verifica:
  - Solo observaciones state="valid" entran en el análisis.
  - Separación Lucky/normal y por ruleset.
  - Reproducibilidad: mismo seed → mismo AnalysisResult.
"""

from datetime import UTC, datetime

import pytest
from django.contrib.auth import get_user_model

from apps.analysis.services import run_personal_analysis
from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter

User = get_user_model()


@pytest.fixture
def user(db):  # noqa: ARG001
    return User.objects.create_user(email="test@example.com", password="pass")


@pytest.fixture(autouse=True)
def mechanics(db):  # noqa: ARG001
    mechanic = Mechanic.objects.create(
        slug="iv-en-intercambios",
        key="trade_iv",
        name="IV en intercambios",
        status="active",
    )
    rs = MechanicRuleSet.objects.create(
        mechanic=mechanic,
        version=1,
        name="Ruleset test",
        effective_from=datetime(2026, 1, 1, tzinfo=UTC),
        is_published=True,
    )
    for pd in [
        {"key": "floor.friendship.good", "value": 1, "data_type": "integer"},
        {"key": "floor.friendship.great", "value": 2, "data_type": "integer"},
        {"key": "floor.friendship.ultra", "value": 3, "data_type": "integer"},
        {"key": "floor.friendship.best", "value": 5, "data_type": "integer"},
        {"key": "floor.lucky", "value": 12, "data_type": "integer"},
    ]:
        RuleParameter.objects.create(ruleset=rs, **pd)
    return mechanic


def _create_observation(
    user,
    state="valid",
    is_lucky=True,
    atk=12,
    def_=13,
    hp=14,
    friendship_level="best",
    trade_type="lucky",
    ruleset=None,
):
    from apps.trades.models import TradeObservation

    return TradeObservation.objects.create(
        owner=user,
        observed_at=datetime(2026, 7, 17, tzinfo=UTC),
        friendship_level=friendship_level,
        trade_type=trade_type,
        is_lucky=is_lucky,
        atk=atk,
        iv_def=def_,
        hp=hp,
        state=state,
        ruleset=ruleset,
    )


@pytest.mark.django_db
class TestRunPersonalAnalysis:
    def test_only_valid_observations_analyzed(self, user):
        """Solo observaciones state="valid" entran en el análisis."""
        _create_observation(user, state="valid", atk=12, def_=13, hp=14)
        _create_observation(user, state="excluded", atk=20, def_=20, hp=20)
        _create_observation(user, state="suspicious", atk=5, def_=5, hp=5)
        _create_observation(user, state="duplicate", atk=10, def_=10, hp=10)
        _create_observation(user, state="deleted", atk=15, def_=15, hp=15)

        run = run_personal_analysis(user.pk)
        results = run.results.all()

        for result in results:
            # El payload.n debe ser 1 (solo la observación valid)
            if result.metric_key.startswith("hundo_rate"):
                assert result.payload["n"] == 1, (
                    f"Esperado n=1 (solo valid), obtenido n={result.payload['n']}"
                )

    def test_separates_lucky_and_normal(self, user):
        """Lucky y normal generan resultados separados."""
        _create_observation(user, is_lucky=True, trade_type="lucky", atk=12, def_=13, hp=14)
        _create_observation(
            user, is_lucky=False, trade_type="normal", friendship_level="good", atk=5, def_=5, hp=5
        )

        run = run_personal_analysis(user.pk)
        keys = [r.metric_key for r in run.results.all()]

        # Debe haber resultados para Lucky y Normal
        lucky_keys = [k for k in keys if "lucky" in k.lower()]
        normal_keys = [k for k in keys if "normal" in k.lower()]
        assert len(lucky_keys) > 0, "Faltan resultados Lucky"
        assert len(normal_keys) > 0, "Faltan resultados Normal"

        # Verificar que no estén mezclados
        for k in lucky_keys:
            assert "normal" not in k.lower()

    def test_reproducibility_same_seed(self, user):
        """Mismo seed produce el mismo AnalysisResult."""
        _create_observation(user, atk=12, def_=13, hp=14)

        run1 = run_personal_analysis(user.pk, seed=42)
        run2 = run_personal_analysis(user.pk, seed=42)

        results1 = {r.metric_key: r.payload for r in run1.results.all()}
        results2 = {r.metric_key: r.payload for r in run2.results.all()}

        assert results1.keys() == results2.keys()
        for key in results1:
            assert results1[key] == results2[key], f"Divergencia en {key}"

    def test_different_seeds_may_differ_in_mc(self, user):
        """Semillas distintas pueden producir p-valores distintos en MC."""
        _create_observation(user, atk=12, def_=13, hp=14)

        run = run_personal_analysis(user.pk, seed=12345)
        assert run.random_seed == 12345

    def test_analysis_run_has_metadata(self, user):
        """AnalysisRun incluye metadata de reproducibilidad."""
        _create_observation(user, atk=12, def_=13, hp=14)

        run = run_personal_analysis(user.pk, seed=777)
        assert run.algorithm_version != ""
        assert run.random_seed == 777

    def test_insufficient_sample_flag(self, user):
        """n < min_sample → insufficient_sample=True en payload."""
        _create_observation(user, atk=12, def_=13, hp=14)

        run = run_personal_analysis(user.pk)
        hundo_results = run.results.filter(metric_key__startswith="hundo_rate")
        for r in hundo_results:
            assert r.payload["n"] < 50
            assert r.payload.get("insufficient_sample") is True

    def test_mixed_states_excluded_from_count(self, user):
        """Observaciones non-valid no afectan los conteos."""
        _create_observation(user, state="valid", atk=15, def_=15, hp=15)
        _create_observation(user, state="excluded", atk=15, def_=15, hp=15)
        _create_observation(user, state="excluded", atk=15, def_=15, hp=15)

        run = run_personal_analysis(user.pk)
        for r in run.results.all():
            if r.metric_key.startswith("hundo_rate"):
                assert r.payload["n"] == 1, (
                    f"Debería haber solo 1 observación (valid), hay {r.payload['n']}"
                )

    def test_best_normal_uses_ruleset_floor_not_hardcoded(self, user):
        """Regresión M5-2: normal best-friends usa el piso del ruleset (5), no 1.

        Antes se hardcodeaba f=1 → soporte de uniformidad [1,15] → falsa anomalía
        (ceros en IV 1-4, imposibles bajo piso 5). Con el piso correcto (5) el
        soporte es [5,15] y la hipótesis nula del binomial es p_hundo(5)=1/1331.
        """
        import random as _random

        from engine.probability import p_hundo

        # Adjuntar el ruleset publicado a las observaciones (como hace M4 en
        # producción) para ejercitar floor_for_ruleset, no solo el fallback.
        rs = MechanicRuleSet.objects.get(mechanic__key="trade_iv", is_published=True)

        rng = _random.Random(0)
        for _ in range(60):  # >= min_sample("hundo_rate")=50
            _create_observation(
                user,
                is_lucky=False,
                trade_type="normal",
                friendship_level="best",
                atk=rng.randint(5, 15),
                def_=rng.randint(5, 15),
                hp=rng.randint(5, 15),
                ruleset=rs,
            )

        run = run_personal_analysis(user.pk, seed=42)
        results = {r.metric_key: r.payload for r in run.results.all()}

        hundo = next(p for k, p in results.items() if k.startswith("hundo_rate-normal-best"))
        assert hundo["floor"] == 5, f"Piso debe leerse del ruleset (5), no hardcodeado: {hundo}"
        assert hundo["p0"] == pytest.approx(float(p_hundo(5)))
        assert hundo["p0"] != pytest.approx(float(p_hundo(1)))  # NO el piso hardcodeado

        stat = next(
            p for k, p in results.items() if k.startswith("stat_uniformity_atk-normal-best")
        )
        assert min(stat["values"]) == 5  # soporte [5,15], no [1,15] → sin falsa anomalía


@pytest.mark.django_db
class TestAnalysisView:
    def test_empty_dataset_renders(self, user):
        """Usuario sin observaciones ve mensaje amigable."""
        client = _client(user)
        resp = client.get("/es/analisis/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Registra intercambios" in content

    def test_with_observations_renders(self, user):
        """Usuario con observaciones ve resultados."""
        _create_observation(user, atk=12, def_=15, hp=13)
        _create_observation(
            user, is_lucky=False, trade_type="normal", friendship_level="good", atk=5, def_=5, hp=5
        )

        client = _client(user)
        resp = client.get("/es/analisis/")
        assert resp.status_code == 200
        content = resp.content.decode()
        assert "Observaciones" in content
        assert "lucky" in content.lower()
        assert "normal" in content.lower()

    def test_unauthenticated_redirects(self):
        """Usuario no autenticado es redirigido a login."""
        from django.test import Client

        client = Client()
        resp = client.get("/es/analisis/")
        assert resp.status_code == 302


def _client(user):
    from django.test import Client

    c = Client()
    c.force_login(user)
    return c


@pytest.mark.django_db
class TestPooledFloorPerRulesetVersion:
    """Regresión M6-1: el agregado pooled resuelve el piso del ruleset_version
    del grupo (floor_for_ruleset), no del ruleset vigente."""

    def test_floor_read_from_group_version_not_active(self):
        from apps.analysis.services import compute_pooled_statistics

        # La fixture autouse crea v1 (best=5, vigente). Añadimos v2 (best=7,
        # con fecha futura → NO vigente): si el agregado usara el ruleset activo,
        # el grupo de v2 tomaría 5; con el fix toma 7 (su propia versión).
        mech = Mechanic.objects.get(key="trade_iv")
        rs2 = MechanicRuleSet.objects.create(
            mechanic=mech,
            version=2,
            name="v2",
            effective_from=datetime(2027, 1, 1, tzinfo=UTC),
            is_published=True,
        )
        for key, value in [("floor.friendship.best", 7), ("floor.lucky", 12)]:
            RuleParameter.objects.create(ruleset=rs2, key=key, value=value, data_type="integer")

        def _row(version):
            return {
                "atk": 10,
                "def": 10,
                "hp": 10,
                "friendship_level": "best",
                "trade_type": "normal",
                "is_lucky": False,
                "ruleset_version": version,
                "observed_month": "2026-01",
            }

        result = compute_pooled_statistics([_row(1), _row(2)])
        floors = {g["ruleset_version"]: g["floor"] for g in result}
        assert floors[1] == 5, "v1 debe usar su propio piso (5)"
        assert floors[2] == 7, "v2 debe usar SU piso (7), no el del ruleset vigente"
