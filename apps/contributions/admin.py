from django.contrib import admin

from .models import DataContributionConsent, DatasetVersion


@admin.register(DataContributionConsent)
class DataContributionConsentAdmin(admin.ModelAdmin):
    list_display = ("user", "scope", "is_active", "granted_at", "revoked_at")
    list_filter = ("scope", "is_active")
    search_fields = ("user__email",)
    readonly_fields = ("granted_at", "revoked_at")


@admin.register(DatasetVersion)
class DatasetVersionAdmin(admin.ModelAdmin):
    list_display = ("number", "built_at", "row_count", "min_sample_met", "is_public", "checksum")
    list_filter = ("min_sample_met", "is_public")
    readonly_fields = ("number", "built_at", "checksum", "row_count")
