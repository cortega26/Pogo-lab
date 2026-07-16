from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.contrib.sitemaps import views as sitemaps_views
from django.urls import URLPattern, URLResolver, include, path
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView

from .sitemaps import sitemaps_dict

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    path(
        "robots.txt",
        TemplateView.as_view(template_name="robots.txt", content_type="text/plain"),
    ),
    path(
        "sitemap.xml",
        sitemaps_views.index,
        {"sitemaps": sitemaps_dict},
        name="sitemap-index",
    ),
    path(
        "sitemap-<section>.xml",
        sitemaps_views.sitemap,
        {"sitemaps": sitemaps_dict},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

urlpatterns += i18n_patterns(
    path(_("cuenta/"), include("allauth.urls")),
    path(_("cuenta/"), include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path(_("mecanicas/"), include("apps.mechanics.urls")),
    path(_("guias/"), include("apps.content.urls")),
    path(_("calculadora/"), include("apps.calculators.urls")),
)
