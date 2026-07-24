from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Invitation, UserProfile

User = get_user_model()


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):  # noqa: ARG001
    if created:
        UserProfile.objects.get_or_create(user=instance)


@receiver(post_save, sender=User)
def consume_invitation_on_signup(sender, instance, created, **kwargs):  # noqa: ARG001
    """Marca la invitación como consumida cuando el usuario invitado se registra.

    Busca una invitación pendiente y válida para el email del nuevo usuario y la
    canjea atómicamente (UPDATE ... WHERE consumed_by IS NULL) para evitar
    carreras entre signups concurrentes con el mismo email.
    """
    if not created:
        return

    invitation = (
        Invitation.objects.filter(email=instance.email, consumed_by__isnull=True)
        .order_by("-created_at")
        .first()
    )
    if invitation is not None and invitation.is_valid:
        # UPDATE atómico: solo canjea si sigue pendiente. Si otra signup
        # concurrente la canjeó primero, no hace nada (affected_rows=0).
        updated = Invitation.objects.filter(pk=invitation.pk, consumed_by__isnull=True).update(
            consumed_by=instance, consumed_at=timezone.now()
        )
        if updated:
            invitation.refresh_from_db()


def _on_user_signed_up(sender, request, user, **kwargs):  # noqa: ARG001
    """Limpia la sesión de invitación tras un signup exitoso.

    Evita que el token quede en sesión y reabra el signup si el usuario
    cierra sesión e intenta registrarse de nuevo.
    """
    if request is None:
        return
    request.session.pop("account_invitation_email", None)
    request.session.pop("account_invitation_token", None)
    request.session.modified = True


# Registrar el receptor de la señal de allauth (importación diferida para
# evitar importar allauth antes de que apps esté listo).
from allauth.account.signals import user_signed_up  # noqa: E402

user_signed_up.connect(_on_user_signed_up)
