from django.urls import path

from . import views

urlpatterns = [
    path("exportar/", views.export_data, name="account_export"),
    path("eliminar/", views.delete_account, name="account_delete"),
]
