from django.urls import URLPattern, URLResolver, path

from . import views

app_name = "contributions"

urlpatterns: list[URLPattern | URLResolver] = [
    path("consentir/", views.grant_consent_view, name="grant"),
    path("revocar/", views.revoke_consent_view, name="revoke"),
]
