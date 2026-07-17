from django.urls import path

from . import views

app_name = "trades"

urlpatterns = [
    path("", views.session_list, name="session_list"),
    path("nueva/", views.session_create, name="session_create"),
    path("<int:session_id>/", views.session_detail, name="session_detail"),
    path("observar/", views.observation_create, name="observation_create"),
    path("lotes/", views.bulk_add, name="bulk_add"),
    path("csv/importar/", views.csv_import, name="csv_import"),
    path("csv/exportar/", views.csv_export, name="csv_export"),
    path("dashboard/", views.dashboard, name="dashboard"),
]
