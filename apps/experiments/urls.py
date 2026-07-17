from django.urls import URLPattern, URLResolver, path

from . import views

app_name = "experiments"

urlpatterns: list[URLPattern | URLResolver] = [
    path("", views.community_dashboard, name="community_dashboard"),
]
