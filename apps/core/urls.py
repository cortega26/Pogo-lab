from django.urls import path

from . import legal_views, views

urlpatterns = [
    path("", views.healthz, name="healthz"),
    path("healthz.json", views.healthz_json, name="healthz_json"),
    path("aviso-legal/", legal_views.disclaimer, name="disclaimer"),
    path("privacidad/", legal_views.privacy, name="privacy"),
    path("terminos/", legal_views.tos, name="tos"),
]
