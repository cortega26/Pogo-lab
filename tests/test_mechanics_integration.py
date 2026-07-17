"""Tests de integración para apps/mechanics y apps/sources."""

from datetime import UTC, datetime

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.db.models import Q

from apps.mechanics.models import Mechanic, MechanicRuleSet, RuleParameter
from apps.sources.models import SourceClaim, SourceReference


def _utc(year, month, day):
    return datetime(year, month, day, tzinfo=UTC)


@pytest.fixture
def trade_mechanic():
    return Mechanic.objects.create(
        slug="iv-en-intercambios",
        key="trade_iv",
        name="IV en intercambios",
        status="active",
    )


@pytest.fixture
def draft_ruleset(trade_mechanic):
    return MechanicRuleSet.objects.create(
        mechanic=trade_mechanic,
        version=1,
        name="Ruleset de prueba",
        effective_from=_utc(2026, 1, 1),
        is_published=False,
    )


@pytest.fixture
def published_ruleset(trade_mechanic):
    rs = MechanicRuleSet.objects.create(
        mechanic=trade_mechanic,
        version=1,
        name="Ruleset publicado",
        effective_from=_utc(2026, 1, 1),
        is_published=True,
    )
    params = [
        RuleParameter(ruleset=rs, key="floor.friendship.good", value=1, data_type="integer"),
        RuleParameter(ruleset=rs, key="floor.friendship.great", value=2, data_type="integer"),
        RuleParameter(ruleset=rs, key="floor.friendship.ultra", value=3, data_type="integer"),
        RuleParameter(ruleset=rs, key="floor.friendship.best", value=5, data_type="integer"),
        RuleParameter(ruleset=rs, key="floor.lucky", value=12, data_type="integer"),
    ]
    RuleParameter.objects.bulk_create(params)
    return rs


@pytest.mark.django_db
class TestMechanicRuleSet:
    def test_create_ruleset(self, trade_mechanic):
        rs = MechanicRuleSet.objects.create(
            mechanic=trade_mechanic,
            version=1,
            name="v1",
            effective_from=_utc(2026, 1, 1),
            is_published=False,
        )
        assert rs.version == 1
        assert not rs.is_published

    def test_unique_constraint_mechanic_version(self, trade_mechanic):
        MechanicRuleSet.objects.create(
            mechanic=trade_mechanic,
            version=1,
            name="v1",
            effective_from=_utc(2026, 1, 1),
        )
        with pytest.raises(IntegrityError):
            MechanicRuleSet.objects.create(
                mechanic=trade_mechanic,
                version=1,
                name="v1-dupe",
                effective_from=_utc(2026, 1, 1),
            )

    def test_publish_fails_without_parameters(self, draft_ruleset):
        with pytest.raises(ValidationError):
            draft_ruleset.publish(None)

    def test_publish_succeeds_with_valid_params(self, trade_mechanic):
        rs = MechanicRuleSet.objects.create(
            mechanic=trade_mechanic,
            version=2,
            name="v2",
            effective_from=_utc(2026, 1, 1),
        )
        params = [
            RuleParameter(ruleset=rs, key="floor.friendship.good", value=1, data_type="integer"),
            RuleParameter(ruleset=rs, key="floor.friendship.great", value=2, data_type="integer"),
            RuleParameter(ruleset=rs, key="floor.friendship.ultra", value=3, data_type="integer"),
            RuleParameter(ruleset=rs, key="floor.friendship.best", value=5, data_type="integer"),
            RuleParameter(ruleset=rs, key="floor.lucky", value=12, data_type="integer"),
        ]
        RuleParameter.objects.bulk_create(params)
        rs.publish(None)
        rs.refresh_from_db()
        assert rs.is_published

    def test_cannot_edit_published_ruleset(self, published_ruleset):
        published_ruleset.name = "Intento de editar nombre"
        with pytest.raises(ValidationError, match="No se puede editar un ruleset ya publicado"):
            published_ruleset.save()

    def test_effective_to_must_be_after_from(self, trade_mechanic):
        with pytest.raises(ValidationError):
            MechanicRuleSet.objects.create(
                mechanic=trade_mechanic,
                version=1,
                name="bad",
                effective_from=_utc(2026, 6, 1),
                effective_to=_utc(2026, 1, 1),
            )

    def test_resolve_active_by_datetime(self, trade_mechanic):
        MechanicRuleSet.objects.create(
            mechanic=trade_mechanic,
            version=1,
            name="old",
            effective_from=_utc(2026, 1, 1),
            effective_to=_utc(2026, 6, 30),
            is_published=True,
        )
        MechanicRuleSet.objects.create(
            mechanic=trade_mechanic,
            version=2,
            name="current",
            effective_from=_utc(2026, 7, 1),
            effective_to=None,
            is_published=True,
        )
        MechanicRuleSet.objects.create(
            mechanic=trade_mechanic,
            version=3,
            name="future",
            effective_from=_utc(2027, 1, 1),
            effective_to=None,
            is_published=True,
        )
        now = _utc(2026, 10, 1)
        active = (
            MechanicRuleSet.objects.filter(
                mechanic=trade_mechanic,
                is_published=True,
                effective_from__lte=now,
            )
            .filter(
                Q(effective_to__isnull=True) | Q(effective_to__gt=now),
            )
            .order_by("-version")
            .first()
        )
        assert active is not None
        assert active.version == 2

    def test_no_active_ruleset_outside_range(self, trade_mechanic):
        MechanicRuleSet.objects.create(
            mechanic=trade_mechanic,
            version=1,
            name="old",
            effective_from=_utc(2026, 1, 1),
            effective_to=_utc(2026, 6, 30),
            is_published=True,
        )
        active = (
            MechanicRuleSet.objects.filter(
                mechanic=trade_mechanic,
                is_published=True,
                effective_from__lte=_utc(2026, 12, 1),
            )
            .filter(
                Q(effective_to__isnull=True) | Q(effective_to__gt=_utc(2026, 12, 1)),
            )
            .first()
        )
        assert active is None


@pytest.mark.django_db
class TestRuleParameter:
    def test_create_parameter(self, draft_ruleset):
        param = RuleParameter.objects.create(
            ruleset=draft_ruleset,
            key="floor.lucky",
            value=12,
            data_type="integer",
        )
        assert param.value == 12
        assert param.data_type == "integer"

    def test_json_value(self, draft_ruleset):
        param = RuleParameter.objects.create(
            ruleset=draft_ruleset,
            key="test.complex",
            value={"a": 1, "b": [2, 3]},
            data_type="json",
        )
        assert param.value["a"] == 1


@pytest.mark.django_db
class TestSourceReference:
    def test_create_source(self):
        src = SourceReference.objects.create(
            title="Test Source",
            url="https://example.com",
            source_type="community_research",
            status="vigente",
        )
        assert src.source_type == "community_research"

    def test_source_types(self):
        choices = SourceReference._meta.get_field("source_type").choices or ()
        for st, _label in choices:
            assert st in (
                "oficial",
                "community_research",
                "datamining",
                "inference",
                "internal_hypothesis",
            )


@pytest.mark.django_db
class TestSourceClaim:
    def test_create_claim(self, draft_ruleset):
        src = SourceReference.objects.create(
            title="Test",
            source_type="datamining",
            status="vigente",
        )
        claim = SourceClaim.objects.create(
            source=src,
            ruleset=draft_ruleset,
            scope="Test claim",
            quote_summary="Esto es una prueba.",
            confidence_level="high",
        )
        assert claim.confidence_level == "high"
        assert claim in list(draft_ruleset.claims.all())

    def test_claim_confidence_levels(self):
        choices = SourceClaim._meta.get_field("confidence_level").choices or ()
        for cl, _label in choices:
            assert cl in ("high", "medium", "low", "hypothetical")


@pytest.mark.django_db
class TestMechanicViews:
    def test_mechanic_list_empty(self, client):
        resp = client.get("/es/mecanicas/")
        assert resp.status_code == 200
        assert "No hay mecánicas" in resp.content.decode()

    def test_mechanic_detail_404_for_unknown(self, client):
        resp = client.get("/es/mecanicas/no-existe/")
        assert resp.status_code == 404

    def test_mechanic_detail_shows_ruleset(self, client, published_ruleset):  # noqa: ARG002
        resp = client.get("/es/mecanicas/iv-en-intercambios/")
        assert resp.status_code == 200
        html = resp.content.decode()
        assert "Reglas vigentes" in html
        assert "v1" in html
        assert "floor.friendship.good" in html


@pytest.mark.django_db
class TestContentPageViews:
    def test_content_page_404_for_unpublished(self, client):
        from apps.content.models import ContentPage

        ContentPage.objects.create(slug="borrador", page_type="guide", status="draft")
        resp = client.get("/es/guias/borrador/")
        assert resp.status_code == 404


@pytest.mark.django_db
class TestResolveTradeFloor:
    def test_resolve_with_published_ruleset(self, published_ruleset):  # noqa: ARG002
        from apps.mechanics.services import resolve_trade_floor

        floor, version = resolve_trade_floor("good", "normal")
        assert floor == 1
        assert version == 1

    def test_resolve_lucky_uses_lucky_floor(self, published_ruleset):  # noqa: ARG002
        from apps.mechanics.services import resolve_trade_floor

        floor, _version = resolve_trade_floor("best", "lucky")
        assert floor == 12

    def test_resolve_raises_without_ruleset(self, trade_mechanic):  # noqa: ARG002
        from apps.mechanics.services import RulesetUnavailableError, resolve_trade_floor

        with pytest.raises(RulesetUnavailableError):
            resolve_trade_floor("good", "normal")

    def test_resolve_raises_without_mechanic(self):
        from apps.mechanics.services import RulesetUnavailableError, resolve_trade_floor

        with pytest.raises(RulesetUnavailableError):
            resolve_trade_floor("good", "normal")

    def test_content_page_404_for_unpublished(self, client):
        from apps.content.models import ContentPage

        ContentPage.objects.create(slug="borrador", page_type="guide", status="draft")
        resp = client.get("/es/guias/borrador/")
        assert resp.status_code == 404

    def test_content_page_404_for_unknown(self, client):
        resp = client.get("/es/guias/no-existe/")
        assert resp.status_code == 404

    def test_content_page_renders_with_seo(self, client, seed_content_pages):  # noqa: ARG002
        resp = client.get("/es/guias/no-afiliacion/")
        assert resp.status_code == 200
        html = resp.content.decode()
        assert "No afiliación" in html
        assert "No afiliación — Pogo-lab" in html


@pytest.fixture
def seed_content_pages():
    """Crea páginas de contenido seed para tests de vistas."""
    from apps.content.models import ContentPage, ContentPageTranslation

    for slug, page_type, title_es, title_en in [
        ("no-afiliacion", "legal", "No afiliación", "No Affiliation"),
        ("iv-en-intercambios", "mechanics", "IV en intercambios", "IVs in Trades"),
    ]:
        page, _ = ContentPage.objects.update_or_create(
            slug=slug,
            defaults={"page_type": page_type, "status": "published"},
        )
        for locale, title in [("es", title_es), ("en", title_en)]:
            ContentPageTranslation.objects.update_or_create(
                page=page,
                locale=locale,
                defaults={"title": title, "body": f"<p>{title}</p>", "is_published": True},
            )


@pytest.mark.django_db
class TestContentModels:
    def test_content_page_creation(self):
        from apps.content.models import ContentPage, ContentPageTranslation

        page = ContentPage.objects.create(
            slug="test-page",
            page_type="guide",
            status="published",
        )
        trans = ContentPageTranslation.objects.create(
            page=page,
            locale="es",
            title="Página de prueba",
            body="<p>Contenido de prueba.</p>",
            seo_title="SEO Test",
            is_published=True,
        )
        assert str(trans) == "test-page — es"
        assert trans.seo_title == "SEO Test"

    def test_unique_page_locale(self):
        from apps.content.models import ContentPage, ContentPageTranslation

        page = ContentPage.objects.create(slug="unique-page", page_type="guide")
        ContentPageTranslation.objects.create(
            page=page,
            locale="es",
            title="ES",
            body="ES body",
            is_published=True,
        )
        with pytest.raises(IntegrityError):
            ContentPageTranslation.objects.create(
                page=page,
                locale="es",
                title="ES dupe",
                body="dup",
                is_published=True,
            )
