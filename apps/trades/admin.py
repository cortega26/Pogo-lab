from typing import ClassVar

from django.contrib import admin

from .models import TradeObservation, TradeSession


class TradeObservationInline(admin.TabularInline):
    model = TradeObservation
    extra = 0
    fields = (
        "observed_at",
        "friendship_level",
        "trade_type",
        "is_lucky",
        "atk",
        "iv_def",
        "hp",
        "state",
        "dedup_hash",
    )
    readonly_fields = ("is_lucky", "dedup_hash", "state")


@admin.register(TradeSession)
class TradeSessionAdmin(admin.ModelAdmin):
    list_display = ("owner", "label", "started_at", "default_friendship", "default_trade_type")
    list_filter = ("default_friendship", "default_trade_type")
    search_fields = ("owner__email", "label")
    inlines: ClassVar = [TradeObservationInline]


@admin.register(TradeObservation)
class TradeObservationAdmin(admin.ModelAdmin):
    list_display = (
        "owner",
        "observed_at",
        "friendship_level",
        "trade_type",
        "is_lucky",
        "atk",
        "iv_def",
        "hp",
        "state",
    )
    list_filter = ("state", "friendship_level", "trade_type", "is_lucky")
    search_fields = ("owner__email", "species")
    readonly_fields = ("is_lucky", "dedup_hash", "state")
