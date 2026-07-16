from django.contrib import admin

from .models import Mechanic, MechanicRuleSet, RuleParameter


class RuleParameterInline(admin.TabularInline):
    model = RuleParameter
    extra = 1


class MechanicRuleSetInline(admin.TabularInline):
    model = MechanicRuleSet
    extra = 0
    show_change_link = True
    fields = (
        "version",
        "name",
        "effective_from",
        "effective_to",
        "is_published",
        "confidence_level",
    )
    readonly_fields = ("is_published",)


@admin.register(Mechanic)
class MechanicAdmin(admin.ModelAdmin):
    list_display = ("key", "name", "status", "sort_order")
    list_editable = ("sort_order",)
    list_filter = ("status",)
    search_fields = ("key", "name", "slug")
    prepopulated_fields = {"slug": ("name",)}  # noqa: RUF012
    inlines = [MechanicRuleSetInline]  # noqa: RUF012


@admin.register(MechanicRuleSet)
class MechanicRuleSetAdmin(admin.ModelAdmin):
    list_display = (
        "mechanic",
        "version",
        "name",
        "effective_from",
        "effective_to",
        "is_published",
        "confidence_level",
    )
    list_filter = ("is_published", "mechanic", "confidence_level")
    search_fields = ("name", "mechanic__key")
    inlines = [RuleParameterInline]  # noqa: RUF012
    fieldsets = (
        (None, {"fields": ("mechanic", "version", "name")}),
        ("Fechas", {"fields": ("effective_from", "effective_to")}),
        ("Estado", {"fields": ("is_published", "confidence_level", "notes")}),
    )
    readonly_fields = ("is_published",)
    actions = ["publish_ruleset"]  # noqa: RUF012

    @admin.action(description="Publicar ruleset seleccionado (inmutable)")
    def publish_ruleset(self, request, queryset):
        count = 0
        for ruleset in queryset:
            if not ruleset.is_published:
                ruleset.publish(None)
                count += 1
        self.message_user(request, f"{count} ruleset(s) publicado(s).")


@admin.register(RuleParameter)
class RuleParameterAdmin(admin.ModelAdmin):
    list_display = ("ruleset", "key", "value", "data_type", "unit")
    list_filter = ("data_type", "ruleset__mechanic")
    search_fields = ("key", "ruleset__name")
