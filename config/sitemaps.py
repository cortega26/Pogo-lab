"""Sitemaps del proyecto — multilenguaje (es/en) con hreflang.

Genera URLs para cada idioma usando i18n_patterns.
"""

from django.contrib import sitemaps
from django.urls import reverse

from apps.content.models import ContentPage


class StaticViewSitemap(sitemaps.Sitemap):
    """Sitemap para vistas estaticas (sin objeto asociado)."""

    priority = 0.8
    changefreq = "weekly"

    def items(self):
        return ["calculator"]

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


sitemaps_dict = {
    "static": StaticViewSitemap,
    "content": ContentPageSitemap,
}
