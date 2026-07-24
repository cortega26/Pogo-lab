"""Adapter de allauth para beta cerrada por invitación.

Cuando INVITATION_ONLY=True:
- El registro queda cerrado salvo que la sesión contenga un email de invitación
  válido (cargado por InvitationGateMiddleware al visitar /signup/?invite=<token>).
- El email del signup debe coincidir con el email de la invitación; cualquier
  otro email se rechaza con ValidationError en clean_email (evita que un solo
  enlace de invitación permita registrar cuentas con emails arbitrarios).
"""

from allauth.account.adapter import DefaultAccountAdapter
from allauth.core import context
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.translation import gettext_lazy as _


class InvitationAdapter(DefaultAccountAdapter):
    def is_open_for_signup(self, request):
        if not getattr(settings, "INVITATION_ONLY", False):
            return super().is_open_for_signup(request)
        # Beta cerrada: solo si la sesión ya validó un token de invitación.
        return bool(request.session.get("account_invitation_email"))

    def clean_email(self, email):
        email = super().clean_email(email)
        if not getattr(settings, "INVITATION_ONLY", False):
            return email
        # En beta cerrada, el email debe coincidir con el de la invitación.
        # allauth.core.context.request es un thread-local con la request actual.
        request = context.request
        if request is None:
            return email
        invited_email = request.session.get("account_invitation_email")
        if invited_email and email.lower() != invited_email.lower():
            raise ValidationError(
                _(
                    "Este enlace de invitación es para %(invited)s. "
                    "Usa el email que recibió la invitación."
                ),
                params={"invited": invited_email},
            )
        return email
