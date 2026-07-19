from django.contrib import admin

from .models import ContentPage, ContentPageTranslation


class ContentPageTranslationInline(admin.TabularInline):
    model = ContentPageTranslation
    extra = 1
    fields = ("locale", "title", "seo_title", "is_published")


@admin.register(ContentPage)
class ContentPageAdmin(admin.ModelAdmin):
    list_display = ("slug", "page_type", "status", "mechanic", "review_date")
    list_filter = ("page_type", "status")
    search_fields = ("slug",)
    prepopulated_fields = {"slug": ("page_type",)}
    inlines = [ContentPageTranslationInline]
    fieldsets = (
        (None, {"fields": ("slug", "page_type", "status")}),
        ("Relaciones", {"fields": ("mechanic",)}),
        ("Revisión", {"fields": ("review_date",)}),
    )


@admin.register(ContentPageTranslation)
class ContentPageTranslationAdmin(admin.ModelAdmin):
    list_display = ("page", "locale", "title", "is_published")
    list_filter = ("locale", "is_published")
    search_fields = ("title", "seo_title", "page__slug")
    fieldsets = (
        (None, {"fields": ("page", "locale")}),
        ("Contenido", {"fields": ("title", "body")}),
        ("SEO", {"fields": ("seo_title", "seo_description", "og_fields")}),
        ("Estado", {"fields": ("is_published",)}),
    )
