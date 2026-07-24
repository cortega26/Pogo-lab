"""Middleware de beta cerrada: valida tokens de invitación en la URL de signup.

Flujo:
1. Admin crea Invitation + envía correo con link /cuenta/signup/?invite=<token>.
2. Invitado abre el link → este middleware valida el token y guarda el email en sesión.
3. El adapter allauth permite signup solo si la sesión tiene un email de invitación
   cuyo token sigue siendo válido (lo re-valida en cada request).
4. Al crearse el usuario (señal user_signed_up), la invitación se marca como
   consumida y la sesión se limpia para evitar reusar el token.

Rutas públicas (no afectadas): todo menos account_signup. En particular login,
logout, admin, healthz, legales y assets quedan accesibles sin invitación.
"""

from django.conf import settings
from django.urls import Resolver404, resolve

from .models import Invitation


class InvitationGateMiddleware:
    """Valida tokens de invitación en la URL de signup cuando INVITATION_ONLY=True."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, "INVITATION_ONLY", False):
            self._maybe_consume_token(request)
            self._revalidate_session_token(request)
        return self.get_response(request)

    def _maybe_consume_token(self, request):
        """Si la petición incluye ?invite=<token>, valida y carga en sesión."""
        token = request.GET.get("invite")
        if not token:
            return

        # Solo procesamos el token si la URL resuelve a la vista de signup.
        if not self._is_signup_url(request):
            return

        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            return

        if not invitation.is_valid:
            return

        # Guarda el email y token en sesión; el adapter lo usa para abrir el signup.
        request.session["account_invitation_email"] = invitation.email
        request.session["account_invitation_token"] = token
        request.session.modified = True

    def _revalidate_session_token(self, request):
        """Re-valida el token en sesión: si la invitación ya fue consumida o
        expiró, limpia la sesión para cerrar el signup."""
        token = request.session.get("account_invitation_token")
        if not token:
            return
        try:
            invitation = Invitation.objects.get(token=token)
        except Invitation.DoesNotExist:
            self._clear_session(request)
            return
        if not invitation.is_valid:
            self._clear_session(request)

    def _clear_session(self, request):
        """Limpia las claves de invitación de la sesión."""
        request.session.pop("account_invitation_email", None)
        request.session.pop("account_invitation_token", None)
        request.session.modified = True

    def _is_signup_url(self, request):
        """True si la request resuelve a la vista account_signup de allauth."""
        try:
            match = resolve(request.path)
        except Resolver404:
            return False
        return match.url_name == "account_signup"
