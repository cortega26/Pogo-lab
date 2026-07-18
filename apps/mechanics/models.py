from typing import ClassVar

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class Mechanic(TimestampedModel):
    slug = models.SlugField(unique=True)
    key = models.CharField(max_length=64, unique=True, help_text=_("Código interno, ej. trade_iv"))
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True, default="")
    status = models.CharField(
        max_length=16,
        default="active",
        choices=[
            ("active", _("Activa")),
            ("deprecated", _("Deprecada")),
            ("experimental", _("Experimental")),
        ],
    )
    sort_order = models.IntegerField(default=0)
    current_ruleset = models.ForeignKey(
        "MechanicRuleSet",
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="+",
    )

    class Meta:
        verbose_name = _("mecánica")
        verbose_name_plural = _("mecánicas")
        ordering = ("sort_order", "slug")

    def __str__(self):
        return self.name


class MechanicRuleSet(TimestampedModel):
    mechanic = models.ForeignKey(Mechanic, on_delete=models.CASCADE, related_name="rulesets")
    version = models.IntegerField()
    name = models.CharField(max_length=128)
    effective_from = models.DateTimeField()
    effective_to = models.DateTimeField(null=True, blank=True)
    is_published = models.BooleanField(default=False)
    confidence_level = models.CharField(
        max_length=32,
        null=True,
        blank=True,
        choices=[
            ("high", _("Alto")),
            ("medium", _("Medio")),
            ("low", _("Bajo")),
            ("hypothetical", _("Hipotético")),
        ],
    )
    notes = models.TextField(blank=True, default="")

    class Meta:
        verbose_name = _("ruleset")
        verbose_name_plural = _("rulesets")
        constraints: ClassVar = [
            models.UniqueConstraint(
                fields=["mechanic", "version"], name="uq_ruleset_mechanic_version"
            ),
        ]
        indexes: ClassVar = [
            models.Index(fields=["effective_from"]),
            models.Index(fields=["effective_to"]),
        ]
        ordering = ("-version",)

    def __str__(self):
        return f"{self.mechanic.key} v{self.version} — {self.name}"

    def clean(self):
        if self.is_published and self.pk:
            original = MechanicRuleSet.objects.get(pk=self.pk)
            if original.is_published:
                raise ValidationError(_("No se puede editar un ruleset ya publicado."))
        if self.effective_to and self.effective_from and self.effective_to <= self.effective_from:
            raise ValidationError(_("effective_to debe ser posterior a effective_from."))

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def publish(self, _engine_ruleset: "MechanicRuleSet | None" = None) -> None:
        from engine.rulesets import validate_parameters

        params = list(self.parameters.all())
        errors = validate_parameters(self.mechanic.key, params)
        if errors:
            raise ValidationError({("Parámetros inválidos"): errors})
        self.is_published = True
        self.save(update_fields=["is_published", "updated_at"])


class RuleParameter(TimestampedModel):
    ruleset = models.ForeignKey(
        MechanicRuleSet, on_delete=models.CASCADE, related_name="parameters"
    )
    key = models.CharField(max_length=64)
    value = models.JSONField()
    data_type = models.CharField(
        max_length=32,
        default="integer",
        choices=[
            ("integer", _("Entero")),
            ("float", _("Decimal")),
            ("boolean", _("Booleano")),
            ("string", _("Texto")),
            ("json", _("JSON")),
        ],
    )
    unit = models.CharField(max_length=32, null=True, blank=True)

    class Meta:
        verbose_name = _("parámetro de ruleset")
        verbose_name_plural = _("parámetros de ruleset")
        indexes: ClassVar = [
            models.Index(fields=["key"]),
        ]

    def clean(self):
        if self.ruleset_id and self.ruleset.is_published:
            raise ValidationError(
                _(
                    "No se pueden modificar los parámetros de un ruleset ya publicado. "
                    "Crea una nueva versión del ruleset."
                )
            )

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        if self.ruleset_id and self.ruleset.is_published:
            raise ValidationError(
                _("No se pueden eliminar los parámetros de un ruleset publicado.")
            )
        return super().delete(*args, **kwargs)

    def __str__(self):
        return f"{self.key} = {self.value} ({self.data_type})"
