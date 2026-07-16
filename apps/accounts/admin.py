from django.contrib import admin

from .models import UserProfile


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "locale", "country", "default_contribution_optin")
    search_fields = ("user__email",)
