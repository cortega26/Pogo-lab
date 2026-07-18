"""Modelos para el análisis estadístico de observaciones de intercambios.

Reproducibilidad: cada AnalysisRun fija dataset_version, ruleset_version,
algorithm_version, random_seed y code_sha para poder re-ejecutar y obtener
exactamente el mismo resultado.
"""

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class AnalysisRun(TimestampedModel):
    owner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="analysis_runs",
        null=True,
        blank=True,
    )
    filters = models.JSONField(default=dict, blank=True)
    ruleset_version = models.CharField(max_length=32, blank=True, default="")
    algorithm_version = models.CharField(max_length=32, blank=True, default="")
    method_params = models.JSONField(default=dict, blank=True)
    random_seed = models.IntegerField(null=True, blank=True)
    code_sha = models.CharField(max_length=64, blank=True, default="")
    input_fingerprint = models.CharField(max_length=64, blank=True, default="", db_index=True)
    mixing_flags = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = _("ejecución de análisis")
        verbose_name_plural = _("ejecuciones de análisis")
        ordering = ("-created_at",)

    def __str__(self):
        return f"AnalysisRun #{self.pk} ({self.created_at:%Y-%m-%d %H:%M})"


class AnalysisResult(TimestampedModel):
    run = models.ForeignKey(
        AnalysisRun,
        on_delete=models.CASCADE,
        related_name="results",
    )
    metric_key = models.CharField(max_length=64)
    payload = models.JSONField(default=dict)

    class Meta:
        verbose_name = _("resultado de análisis")
        verbose_name_plural = _("resultados de análisis")
        ordering = ("metric_key",)

    def __str__(self):
        return f"Result {self.metric_key} (run #{self.run_id})"
