from typing import ClassVar

from django.db import models
from django.utils.translation import gettext_lazy as _

from apps.core.models import TimestampedModel


class ContentPage(TimestampedModel):
    slug = models.SlugField(unique=True)
    mechanic = models.ForeignKey(
        "mechanics.Mechanic",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="content_pages",
    )
    page_type = models.CharField(
        max_length=32,
        choices=[
            ("mechanics", _("Mecánica")),
            ("guide", _("Guía")),
            ("methodology", _("Metodología")),
            ("legal", _("Legal")),
            ("landing", _("Portada")),
        ],
    )
    status = models.CharField(
        max_length=16,
        default="draft",
        choices=[
            ("draft", _("Borrador")),
            ("published", _("Publicado")),
            ("archived", _("Archivado")),
        ],
    )
    review_date = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = _("página de contenido")
        verbose_name_plural = _("páginas de contenido")

    def __str__(self):
        return self.slug


class ContentPageTranslation(TimestampedModel):
    page = models.ForeignKey(ContentPage, on_delete=models.CASCADE, related_name="translations")
    locale = models.CharField(max_length=10)
    title = models.CharField(max_length=256)
    body = models.TextField(help_text=_("Contenido renderizable (HTML)"))
    seo_title = models.CharField(max_length=128, null=True, blank=True)
    seo_description = models.CharField(max_length=320, null=True, blank=True)
    og_fields = models.JSONField(default=dict, blank=True)
    is_published = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("traducción de página")
        verbose_name_plural = _("traducciones de página")
        constraints: ClassVar = [
            models.UniqueConstraint(fields=["page", "locale"], name="uq_content_page_translation"),
        ]

    def __str__(self):
        return f"{self.page.slug} — {self.locale}"
