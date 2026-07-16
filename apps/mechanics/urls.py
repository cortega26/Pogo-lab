from django.urls import path

from . import views

urlpatterns = [
    path("", views.mechanic_list, name="mechanic_list"),
    path("<slug:slug>/", views.mechanic_detail, name="mechanic_detail"),
]
