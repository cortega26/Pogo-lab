"""Modelos para recomendaciones deterministas y versionadas.

Cada recomendación es trazable a DecisionRule.key + version (Rule de oro 5).
Nunca se usa LLM en runtime.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.analysis.models import AnalysisRun
from apps.core.models import TimestampedModel


class DecisionRule(TimestampedModel):
    SEVERITY_CHOICES = (
        ("info", _("Informativo")),
        ("warning", _("Advertencia")),
        ("critical", _("Crítico")),
    )

    key = models.CharField(max_length=64, unique=True)
    version = models.CharField(max_length=16)
    condition_spec = models.JSONField(default=dict)
    message_key = models.CharField(max_length=128)
    severity = models.CharField(max_length=16, choices=SEVERITY_CHOICES, default="info")
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = _("regla de decisión")
        verbose_name_plural = _("reglas de decisión")
        ordering = ("key",)

    def __str__(self):
        return f"{self.key}@{self.version}"


class DecisionRecommendation(TimestampedModel):
    analysis_run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="recommendations",
        null=True,
        blank=True,
    )
    rule = models.ForeignKey(
        DecisionRule,
        on_delete=models.CASCADE,
        related_name="recommendations",
    )
    params = models.JSONField(default=dict)

    class Meta:
        verbose_name = _("recomendación")
        verbose_name_plural = _("recomendaciones")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Rec {self.rule.key} (run #{self.analysis_run_id})"
