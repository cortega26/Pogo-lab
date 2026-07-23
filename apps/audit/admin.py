from django.contrib import admin

from .models import AuditEvent


@admin.register(AuditEvent)
class AuditEventAdmin(admin.ModelAdmin):
    list_display = ("verb", "actor", "target_type", "target_id", "created_at", "correlation_id")
    list_filter = ("verb", "target_type", "created_at")
    search_fields = ("verb", "target_type", "correlation_id")
    readonly_fields = (
        "verb",
        "actor",
        "target_type",
        "target_id",
        "metadata",
        "created_at",
        "correlation_id",
    )

    def has_add_permission(self, request):  # noqa: ARG002
        return False

    def has_change_permission(self, request, obj=None):  # noqa: ARG002
        return False

    def has_delete_permission(self, request, obj=None):  # noqa: ARG002
        return False
