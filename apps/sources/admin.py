from django.contrib import admin

from .models import SourceClaim, SourceReference


class SourceClaimInline(admin.TabularInline):
    model = SourceClaim
    extra = 1
    fields = ("scope", "confidence_level", "parameter", "quote_summary")
    raw_id_fields = ("ruleset", "parameter")


@admin.register(SourceReference)
class SourceReferenceAdmin(admin.ModelAdmin):
    list_display = ("title", "source_type", "status", "author_org", "published_at")
    list_filter = ("source_type", "status")
    search_fields = ("title", "author_org", "notes")
    inlines = [SourceClaimInline]
    fieldsets = (
        (None, {"fields": ("title", "url")}),
        ("Tipo y autoría", {"fields": ("source_type", "author_org")}),
        ("Fechas", {"fields": ("published_at", "retrieved_at")}),
        ("Vigencia", {"fields": ("status", "effective_from", "effective_to")}),
        ("Notas", {"fields": ("notes",)}),
    )


@admin.register(SourceClaim)
class SourceClaimAdmin(admin.ModelAdmin):
    list_display = ("source", "scope", "confidence_level", "ruleset")
    list_filter = ("confidence_level", "source__source_type")
    search_fields = ("scope", "quote_summary", "source__title")
    raw_id_fields = ("source", "ruleset", "parameter")
