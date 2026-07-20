from django.urls import path

from . import views

urlpatterns = [
    path("", views.calculator_view, name="calculator"),
    path("cp/", views.cp_calculator_view, name="cp_calculator"),
    path("costos/", views.cost_calculator_view, name="cost_calculator"),
    path("pvp/", views.pvp_ranker_view, name="pvp_ranker"),
    path("captura/", views.catch_calculator_view, name="catch_calculator"),
    path("tipos/", views.type_calculator_view, name="type_calculator"),
    path("shiny/", views.shiny_calculator_view, name="shiny_calculator"),
    path("shadow/", views.shadow_calculator_view, name="shadow_calculator"),
    path("breakpoints/", views.breakpoints_view, name="breakpoints_view"),
]
