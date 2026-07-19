from django.urls import path

from . import views

urlpatterns = [
    path("", views.dps_browser, name="dps_browser"),
    path("tipo/<str:tipo>/", views.dps_by_type, name="dps_by_type"),
    path("movimientos/", views.move_browser, name="dps_moves"),
    path("comparar/", views.pokemon_compare, name="dps_compare"),
]
