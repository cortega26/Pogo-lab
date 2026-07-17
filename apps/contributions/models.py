"""Modelos para contribuciones comunitarias anonimizadas y consentidas.

DataContributionConsent: consentimiento explícito versionado y revocable.
DatasetVersion: snapshot inmutable de dataset público anonimizado.
"""

from typing import ClassVar

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class DataContributionConsent(TimestampedModel):
    SCOPE_CHOICES = (("community_dataset", _("Dataset comunitario")),)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="contribution_consents",
    )
    scope = models.CharField(max_length=64, choices=SCOPE_CHOICES)
    consent_text_version = models.CharField(max_length=32)
    granted_at = models.DateTimeField(null=True, blank=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("consentimiento de contribución")
        verbose_name_plural = _("consentimientos de contribución")
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["user", "scope"],
                name="uq_consent_user_scope",
            ),
        ]
        indexes: ClassVar = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["scope", "is_active"]),
        ]

    def __str__(self):
        return f"Consent {self.scope} — {self.user.email} ({'activo' if self.is_active else 'revocado'})"

    @classmethod
    def grant_consent(cls, user, scope: str, text_version: str):
        now = timezone.now()
        consent, created = cls.objects.get_or_create(
            user=user,
            scope=scope,
            defaults={
                "consent_text_version": text_version,
                "granted_at": now,
                "is_active": True,
            },
        )
        if not created and not consent.is_active:
            consent.consent_text_version = text_version
            consent.granted_at = now
            consent.revoked_at = None
            consent.is_active = True
            consent.save()
        return consent

    @classmethod
    def revoke_consent(cls, user, scope: str):
        try:
            consent = cls.objects.get(user=user, scope=scope)
        except cls.DoesNotExist:
            return None
        if consent.is_active:
            consent.is_active = False
            consent.revoked_at = timezone.now()
            consent.save()
        return consent

    def clean(self):
        if self.granted_at and self.revoked_at and self.revoked_at <= self.granted_at:
            raise ValidationError(
                _("La fecha de revocación debe ser posterior a la de otorgamiento.")
            )
        if self.is_active and self.revoked_at:
            raise ValidationError(_("Un consentimiento activo no puede tener fecha de revocación."))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)


def _default_criteria() -> dict:
    return {"min_sample": 30, "state_filter": "valid"}


class DatasetVersion(TimestampedModel):
    number = models.PositiveIntegerField(unique=True)
    built_at = models.DateTimeField(auto_now_add=True)
    criteria = models.JSONField(default=_default_criteria)
    min_sample_met = models.BooleanField(default=False)
    row_count = models.PositiveIntegerField(default=0)
    checksum = models.CharField(max_length=64, blank=True, default="")
    is_public = models.BooleanField(default=False)
    pipeline_version = models.CharField(max_length=32, blank=True, default="")
    anonymized_rows = models.JSONField(null=True, blank=True, default=None)

    class Meta:
        verbose_name = _("versión de dataset")
        verbose_name_plural = _("versiones de dataset")
        ordering = ("-number",)

    def __str__(self):
        return f"Dataset v{self.number} ({self.row_count} filas)"

    def clean(self):
        if self.pk:
            original = DatasetVersion.objects.get(pk=self.pk)
            if original.checksum:
                raise ValidationError(
                    _(
                        "No se puede editar una versión de dataset ya construida. "
                        "Para actualizar, crea una nueva versión."
                    )
                )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
