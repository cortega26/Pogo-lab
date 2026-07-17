from django.contrib import admin

from .models import ExperimentProtocol


@admin.register(ExperimentProtocol)
class ExperimentProtocolAdmin(admin.ModelAdmin):
    list_display = ("mechanic", "hypothesis", "status", "min_sample", "dataset_version")
    list_filter = ("status", "mechanic")
    search_fields = ("hypothesis",)
