from typing import ClassVar

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel
from apps.mechanics.models import MechanicRuleSet


class TradeSession(TimestampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trade_sessions",
    )
    started_at = models.DateTimeField()
    label = models.CharField(max_length=255, blank=True, default="")
    default_friendship = models.CharField(
        max_length=16,
        choices=[
            ("good", _("Good Friends")),
            ("great", _("Great Friends")),
            ("ultra", _("Ultra Friends")),
            ("best", _("Best Friends")),
        ],
        default="good",
    )
    default_trade_type = models.CharField(
        max_length=24,
        choices=[
            ("normal", _("Normal")),
            ("lucky", _("Lucky")),
            ("lucky_guaranteed", _("Lucky garantizado")),
        ],
        default="normal",
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("sesión de intercambios")
        verbose_name_plural = _("sesiones de intercambios")
        ordering = ("-started_at",)

    def __str__(self):
        return self.label or f"Sesión del {self.started_at:%Y-%m-%d %H:%M}"


class TradeObservation(TimestampedModel):
    SESSION_STATE_CHOICES = (
        ("draft", _("Borrador")),
        ("valid", _("Válido")),
        ("excluded", _("Excluido")),
        ("suspicious", _("Sospechoso")),
        ("duplicate", _("Duplicado")),
        ("deleted", _("Eliminado")),
    )
    FRIENDSHIP_CHOICES = (
        ("good", _("Good Friends")),
        ("great", _("Great Friends")),
        ("ultra", _("Ultra Friends")),
        ("best", _("Best Friends")),
    )
    TRADE_TYPE_CHOICES = (
        ("normal", _("Normal")),
        ("lucky", _("Lucky")),
        ("lucky_guaranteed", _("Lucky garantizado")),
    )
    INPUT_METHOD_CHOICES = (
        ("manual", _("Manual")),
        ("batch", _("Por lotes")),
        ("csv", _("CSV")),
    )

    session = models.ForeignKey(
        TradeSession,
        on_delete=models.CASCADE,
        related_name="observations",
        null=True,
        blank=True,
    )
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="trade_observations",
    )
    observed_at = models.DateTimeField()
    tz_offset = models.IntegerField(null=True, blank=True)
    friendship_level = models.CharField(max_length=16, choices=FRIENDSHIP_CHOICES)
    trade_type = models.CharField(max_length=24, choices=TRADE_TYPE_CHOICES)
    is_lucky = models.BooleanField(
        default=False,
        help_text=_("DERIVADO: True si trade_type es lucky o lucky_guaranteed"),
    )
    lucky_guaranteed = models.BooleanField(null=True, blank=True)
    atk = models.IntegerField()
    iv_def = models.IntegerField(db_column="def", verbose_name="Def")
    hp = models.IntegerField()
    species = models.CharField(max_length=128, blank=True, default="")
    special_trade = models.BooleanField(null=True, blank=True)
    oldest_age_bucket = models.CharField(max_length=32, blank=True, default="")
    event_context = models.CharField(max_length=64, blank=True, default="")
    app_version = models.CharField(max_length=32, blank=True, default="")
    input_method = models.CharField(max_length=16, choices=INPUT_METHOD_CHOICES, default="manual")
    ruleset = models.ForeignKey(
        MechanicRuleSet,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations",
    )
    state = models.CharField(
        max_length=16,
        choices=SESSION_STATE_CHOICES,
        default="draft",
    )
    exclusion_reason = models.TextField(blank=True, default="")
    contribution_optin = models.BooleanField(default=False)
    dedup_hash = models.CharField(max_length=64, blank=True, default="", db_index=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("observación de intercambio")
        verbose_name_plural = _("observaciones de intercambios")
        indexes: ClassVar = [
            models.Index(
                fields=["owner", "is_lucky", "ruleset", "observed_at"],
                name="trade_obs_owner_lucky_ruleset",
            ),
            models.Index(fields=["dedup_hash"], name="trade_obs_dedup_hash"),
        ]

    def __str__(self):
        return (
            f"Obs #{self.pk} ({self.get_friendship_level_display()}, "
            f"{self.get_trade_type_display()}, "
            f"{self.atk}/{self.iv_def}/{self.hp})"
        )
