"""Sitemaps del proyecto — multilenguaje (es/en) con hreflang.

Genera URLs para cada idioma usando i18n_patterns.
"""

from django.contrib import sitemaps
from django.urls import reverse

from apps.content.models import ContentPage
from engine.dps_data import ALL_TYPES


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap para vistas estaticas (sin objeto asociado)."""

    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return [
            "calculator",
            "cp_calculator",
            "cost_calculator",
            "pvp_ranker",
            "catch_calculator",
            "type_calculator",
            "shiny_calculator",
            "shadow_calculator",
            "dps_browser",
        ]

    def location(self, item):
        return reverse(item)


class ContentPageSitemap(sitemaps.Sitemap):
    """Sitemap para paginas de contenido en cada idioma."""

    priority = 0.6
    changefreq = "monthly"

    def items(self):
        return ContentPage.objects.filter(status="published")

    def lastmod(self, obj: ContentPage):
        return obj.updated_at


class DpsTypeSitemap(sitemaps.Sitemap):
    """Sitemap para paginas de ranking DPS por tipo."""

    priority = 0.7
    changefreq = "weekly"

    def items(self):
        return ALL_TYPES

    def location(self, item):
        return reverse("dps_by_type", args=[item])


sitemaps_dict = {
    "static": StaticViewSitemap,
    "content": ContentPageSitemap,
    "dps_types": DpsTypeSitemap,
}
