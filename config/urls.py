from django.conf.urls.i18n import i18n_patterns
from django.contrib import admin
from django.urls import URLPattern, URLResolver, include, path
from django.utils.translation import gettext_lazy as _

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
]

urlpatterns += i18n_patterns(
    path(_("cuenta/"), include("allauth.urls")),
    path(_("cuenta/"), include("apps.accounts.urls")),
    path("", include("apps.core.urls")),
    path(_("mecanicas/"), include("apps.mechanics.urls")),
    path(_("guias/"), include("apps.content.urls")),
)
