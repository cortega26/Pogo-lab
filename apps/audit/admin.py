from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("verb", "actor", "target_type", "target_id", "created_at", "correlation_id")
    list_filter = ("verb", "target_type", "created_at")
    search_fields = ("verb", "target_type", "correlation_id")
    readonly_fields = ("created_at", "correlation_id")
