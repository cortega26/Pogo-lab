from dataclasses import dataclass
from urllib.parse import urlparse

from django.db import models
from django.shortcuts import get_object_or_404, render
from django.utils import timezone
from django.utils.translation import get_language

from apps.content.models import ContentPageTranslation

from .models import Mechanic, MechanicRuleSet


@dataclass(frozen=True)
class MechanicCard:
    mechanic: Mechanic
    translation: ContentPageTranslation


@dataclass(frozen=True)
class EvidenceItem:
    summary: str | None
    source_label: str
    source_url: str | None
    source_type: str
    confidence: str
    parameter_key: str | None


def _published_translation(slug: str, locale: str) -> ContentPageTranslation:
    return get_object_or_404(
        ContentPageTranslation.objects.select_related("page"),
        page__slug=slug,
        page__page_type="mechanics",
        page__status="published",
        locale=locale,
        is_published=True,
    )


def _source_label(source) -> str:
    """Return a locale-neutral public label without leaking canonical Spanish prose."""

    if source.url:
        hostname = urlparse(source.url).hostname
        if hostname:
            return hostname.removeprefix("www.")
    return str(source.get_source_type_display())


def _evidence_items(ruleset: MechanicRuleSet | None, locale: str) -> list[EvidenceItem]:
    if ruleset is None:
        return []

    items: list[EvidenceItem] = []
    for claim in ruleset.claims.select_related("source", "parameter").all():
        is_canonical_spanish = locale.split("-", 1)[0] == "es"
        items.append(
            EvidenceItem(
                summary=claim.quote_summary if is_canonical_spanish else None,
                source_label=(
                    claim.source.title
                    if is_canonical_spanish
                    else _source_label(claim.source)
                ),
                source_url=claim.source.url,
                source_type=str(claim.source.get_source_type_display()),
                confidence=str(claim.get_confidence_level_display()),
                parameter_key=claim.parameter.key if claim.parameter else None,
            )
        )
    return items


def mechanic_list(request):
    locale = get_language() or "es"
    mechanics = list(Mechanic.objects.filter(status="active").order_by("sort_order"))
    translations = {
        translation.page.slug: translation
        for translation in ContentPageTranslation.objects.select_related("page").filter(
            page__slug__in=[mechanic.slug for mechanic in mechanics],
            page__page_type="mechanics",
            page__status="published",
            locale=locale,
            is_published=True,
        )
    }
    cards = [
        MechanicCard(mechanic=mechanic, translation=translations[mechanic.slug])
        for mechanic in mechanics
        if mechanic.slug in translations
    ]
    return render(request, "mechanics/list.html", {"mechanic_cards": cards})


def mechanic_detail(request, slug):
    locale = get_language() or "es"
    mechanic = get_object_or_404(Mechanic, slug=slug, status="active")
    translation = _published_translation(slug, locale)

    now = timezone.now()
    ruleset = (
        MechanicRuleSet.objects.filter(
            mechanic=mechanic,
            is_published=True,
            effective_from__lte=now,
        )
        .filter(
            models.Q(effective_to__isnull=True) | models.Q(effective_to__gt=now),
        )
        .order_by("-version")
        .first()
    )
    return render(
        request,
        "mechanics/detail.html",
        {
            "mechanic": mechanic,
            "translation": translation,
            "ruleset": ruleset,
            "evidence_items": _evidence_items(ruleset, locale),
        },
    )
