"""Modelos para el dashboard comunitario y experimentos.

ExperimentProtocol: protocolo de experimento con hipótesis, método y dataset asociado.
"""

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.contributions.models import DatasetVersion
from apps.core.models import TimestampedModel
from apps.mechanics.models import Mechanic


class ExperimentProtocol(TimestampedModel):
    STATUS_CHOICES = (
        ("draft", _("Borrador")),
        ("published", _("Publicado")),
        ("retracted", _("Retractado")),
    )

    mechanic = models.ForeignKey(
        Mechanic,
        on_delete=models.CASCADE,
        related_name="experiments",
    )
    hypothesis = models.TextField()
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="draft")
    min_sample = models.PositiveIntegerField(default=30)
    method_notes = models.TextField(blank=True, default="")
    dataset_version = models.ForeignKey(
        DatasetVersion,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="experiments",
    )

    class Meta:
        verbose_name = _("protocolo de experimento")
        verbose_name_plural = _("protocolos de experimento")
        ordering = ("-created_at",)

    def __str__(self):
        return f"Exp {self.mechanic.key}: {self.hypothesis[:60]}"
