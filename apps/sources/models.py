from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class SourceReference(TimestampedModel):
    title = models.CharField(max_length=256)
    url = models.URLField(max_length=512, null=True, blank=True)
    source_type = models.CharField(
        max_length=32,
        choices=[
            ("oficial", _("Oficial")),
            ("community_research", _("Investigación comunitaria")),
            ("datamining", _("Datamining")),
            ("inference", _("Inferencia")),
            ("internal_hypothesis", _("Hipótesis interna")),
        ],
    )
    author_org = models.CharField(max_length=128, null=True, blank=True)
    published_at = models.DateTimeField(null=True, blank=True)
    retrieved_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=32,
        default="vigente",
        choices=[
            ("vigente", _("Vigente")),
            ("en_revision", _("En revisión")),
            ("obsoleta", _("Obsoleta")),
            ("contradicha", _("Contradicha")),
        ],
    )
    effective_from = models.DateTimeField(null=True, blank=True)
    effective_to = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("referencia de fuente")
        verbose_name_plural = _("referencias de fuente")
        indexes: ClassVar = [
            models.Index(fields=["source_type"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return self.title


class SourceClaim(TimestampedModel):
    source = models.ForeignKey(SourceReference, on_delete=models.CASCADE, related_name="claims")
    ruleset = models.ForeignKey(
        "mechanics.MechanicRuleSet",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claims",
    )
    parameter = models.ForeignKey(
        "mechanics.RuleParameter",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="claims",
    )
    scope = models.CharField(max_length=128, null=True, blank=True)
    quote_summary = models.TextField(null=True, blank=True)
    confidence_level = models.CharField(
        max_length=32,
        default="medium",
        choices=[
            ("high", _("Alto")),
            ("medium", _("Medio")),
            ("low", _("Bajo")),
            ("hypothetical", _("Hipotético")),
        ],
    )

    class Meta:
        verbose_name = _("afirmación citada")
        verbose_name_plural = _("afirmaciones citadas")
        indexes: ClassVar = [
            models.Index(fields=["source"]),
            models.Index(fields=["ruleset"]),
            models.Index(fields=["parameter"]),
        ]

    def __str__(self):
        return f"Claim: {self.scope or self.quote_summary or ''} — {self.source.title}"
