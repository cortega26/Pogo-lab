import secrets
from typing import ClassVar

from django.conf import settings
from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager["User"]):
    """Manager del modelo User con email como identificador (sin username)."""

    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError("El email es obligatorio.")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Un superusuario debe tener is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Un superusuario debe tener is_superuser=True.")
        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Usuario con email como login (sin username). Custom desde el día 1 (§E / ADR-0008)."""

    username = None
    email = models.EmailField(_("dirección de email"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS: ClassVar[list[str]] = []

    objects = UserManager()

    def __str__(self):
        return self.email


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


class Invitation(models.Model):
    """Invitación a la beta cerrada.

    Una invitación se asocia a un email y se canjea una sola vez al registrarse
    el usuario invitado. El token es opaco (secrets.token_urlsafe) y se envía por
    correo transaccional (Brevo). No almacena PII más allá del email del invitado.
    """

    email = models.EmailField(_("email invitado"))
    token = models.CharField(
        _("token"),
        max_length=64,
        unique=True,
        db_index=True,
        default=secrets.token_urlsafe,
        editable=False,
    )
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations_created",
        verbose_name=_("creada por"),
    )
    consumed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="invitations_consumed",
        verbose_name=_("canjeada por"),
    )
    sent_at = models.DateTimeField(_("enviada el"), null=True, blank=True)
    consumed_at = models.DateTimeField(_("canjeada el"), null=True, blank=True)
    expires_at = models.DateTimeField(_("expira el"), null=True, blank=True)
    created_at = models.DateTimeField(_("creada el"), default=timezone.now)

    class Meta:
        verbose_name = _("invitación")
        verbose_name_plural = _("invitaciones")
        ordering = ("-created_at",)
        constraints: ClassVar[list] = [
            # Una invitación pendiente (no consumida) por email.
            models.UniqueConstraint(
                fields=["email"],
                condition=models.Q(consumed_by__isnull=True),
                name="unique_pending_invitation_per_email",
            ),
        ]

    def __str__(self):
        status = "pendiente"
        if self.consumed_by_id is not None:
            status = "consumada"
        elif self.expires_at and self.expires_at < timezone.now():
            status = "expirada"
        return f"Invitación a {self.email} ({status})"

    @property
    def is_valid(self) -> bool:
        """True si la invitación está pendiente y no ha expirado."""
        if self.consumed_by_id is not None:
            return False
        return not (self.expires_at is not None and self.expires_at < timezone.now())

    def save(self, *args, **kwargs):
        from datetime import timedelta

        if not self.token:
            self.token = secrets.token_urlsafe(32)
        if self.expires_at is None and not self.pk:
            expiry_days = getattr(settings, "INVITATION_EXPIRY_DAYS", 14)
            self.expires_at = timezone.now() + timedelta(days=expiry_days)
        super().save(*args, **kwargs)
