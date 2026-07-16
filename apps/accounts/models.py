from django.conf import settings
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="profile",
    )
    locale = models.CharField(max_length=10, default="es")
    country = models.CharField(max_length=2, blank=True, default="")
    default_contribution_optin = models.BooleanField(default=False)
    display_prefs = models.JSONField(default=dict, blank=True)

    class Meta:
        verbose_name = "perfil de usuario"
        verbose_name_plural = "perfiles de usuario"

    def __str__(self):
        return f"Perfil de {self.user.email}"
