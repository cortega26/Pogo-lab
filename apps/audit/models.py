"""Modelos de auditoría y moderación.

AuditEvent: registro inmutable de eventos sensibles (consentimiento,
build de dataset, marcado de sospechosos). SIN PII en metadata.
"""

from typing import ClassVar

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class AuditEvent(TimestampedModel):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="audit_events",
    )
    verb = models.CharField(max_length=64)
    target_type = models.CharField(max_length=64, blank=True, default="")
    target_id = models.PositiveIntegerField(null=True, blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    correlation_id = models.CharField(max_length=64, blank=True, default="")

    class Meta:
        verbose_name = _("evento de auditoría")
        verbose_name_plural = _("eventos de auditoría")
        ordering = ("-created_at",)
        indexes: ClassVar = [
            models.Index(fields=["verb"]),
            models.Index(fields=["target_type", "target_id"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.verb} ({self.created_at:%Y-%m-%d %H:%M})"

    @classmethod
    def log(
        cls,
        verb: str,
        actor=None,
        target_type: str = "",
        target_id: int | None = None,
        metadata: dict | None = None,
        correlation_id: str = "",
    ):
        return cls.objects.create(
            actor=actor,
            verb=verb,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
            correlation_id=correlation_id,
        )
