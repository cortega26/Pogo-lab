"""Modelos de auditoría y moderación.

AuditEvent: registro inmutable de eventos sensibles (consentimiento,
build de dataset, marcado de sospechosos). SIN PII en metadata.
"""

from typing import ClassVar

from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.logging_filters import get_correlation_id, sanitize_correlation_id
from apps.core.models import TimestampedModel

_APPEND_ONLY_ERROR = (
    "AuditEvent es append-only: no se puede modificar ni eliminar un evento existente."
)


class AuditEventQuerySet(models.QuerySet):
    """Plan 061: bloquea mutación/borrado en bloque (bypassea .save()/.delete()
    de instancias individuales)."""

    def update(self, **kwargs):  # noqa: ARG002
        raise ValueError(_APPEND_ONLY_ERROR)

    def delete(self):
        raise ValueError(_APPEND_ONLY_ERROR)


class AuditEventManager(models.Manager):
    def get_queryset(self):
        return AuditEventQuerySet(self.model, using=self._db)


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

    objects = AuditEventManager()

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

    def save(self, *args, **kwargs):
        """Plan 061: append-only. Un pk ya existente significa que esta
        instancia viene de la base de datos (o alguien la asignó a mano) —
        en cualquier caso, no se permite un UPDATE, solo el INSERT inicial."""
        if self.pk is not None:
            raise ValueError(_APPEND_ONLY_ERROR)
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):  # noqa: ARG002
        raise ValueError(_APPEND_ONLY_ERROR)

    @classmethod
    def log(
        cls,
        verb: str,
        actor=None,
        target_type: str = "",
        target_id: int | None = None,
        metadata: dict | None = None,
        correlation_id: str | None = None,
    ):
        """Crea un AuditEvent, heredando el correlation_id real del request
        en curso cuando no se pasa uno explícito (plan 061 pasos 3-4).

        Si no hay contexto de request (management commands, shell, tasks
        batch), se genera uno propio en vez de dejarlo en blanco. Cualquier
        valor (explícito o heredado) pasa por `sanitize_correlation_id`
        para no confiar ciegamente en un origen externo."""
        if correlation_id is None:
            correlation_id = get_correlation_id() or None
        correlation_id = sanitize_correlation_id(correlation_id)
        return cls.objects.create(
            actor=actor,
            verb=verb,
            target_type=target_type,
            target_id=target_id,
            metadata=metadata or {},
            correlation_id=correlation_id,
        )
