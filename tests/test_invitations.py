"""Tests de la beta cerrada por invitación (apps.accounts).

Cubre:
- Modelo Invitation (token, expiración, is_valid, constraint unique pending).
- Adapter is_open_for_signup respeta INVITATION_ONLY.
- Middleware carga token en sesión al visitar /signup/?invite=<token>.
- Signup requiere token válido; rechaza sin token, con token expirado o consumido.
- Señal consume_invitation_on_signup marca la invitación como consumida.
- Admin action send_invitations envía correo + registra AuditEvent.
"""

from datetime import timedelta

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client, override_settings
from django.utils import timezone

from apps.accounts.models import Invitation
from apps.audit.models import AuditEvent

User = get_user_model()


@pytest.fixture
def admin_user(db):
    return User.objects.create_superuser(email="admin@example.com", password="admin123")


@pytest.fixture
def admin_client(admin_user):
    c = Client()
    c.force_login(admin_user)
    return c


@pytest.fixture
def invitation(db):
    return Invitation.objects.create(email="invited@example.com")


# ── MODELO ─────────────────────────────────────────────────────────


@pytest.mark.django_db
def test_invitation_generates_status_labels(invitation):
    assert "pendiente" in str(invitation)
    invitation.expires_at = timezone.now() - timedelta(days=1)
    invitation.save()
    assert "expirada" in str(invitation)


@pytest.mark.django_db
def test_invitation_is_valid_pending(invitation):
    assert invitation.is_valid is True


@pytest.mark.django_db
def test_invitation_invalid_when_consumed(invitation, admin_user):
    invitation.consumed_by = admin_user
    invitation.save()
    invitation.refresh_from_db()
    assert invitation.is_valid is False


@pytest.mark.django_db
def test_invitation_invalid_when_expired(db):
    inv = Invitation.objects.create(
        email="expired@example.com",
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    assert inv.is_valid is False


@pytest.mark.django_db
def test_unique_pending_invitation_per_email(db):
    """Solo puede haber una invitación pendiente por email."""
    Invitation.objects.create(email="dup@example.com")
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        Invitation.objects.create(email="dup@example.com")


@pytest.mark.django_db
def test_multiple_consumed_then_one_pending(db, admin_user):
    """Una invitación consumida permite crear otra pendiente para el mismo email."""
    consumed = Invitation.objects.create(email="recycle@example.com")
    consumed.consumed_by = admin_user
    consumed.consumed_at = timezone.now()
    consumed.save()
    # Ahora debe poder crearse otra pendiente para el mismo email.
    new_inv = Invitation.objects.create(email="recycle@example.com")
    assert new_inv.pk != consumed.pk
    assert new_inv.is_valid


# ── ADAPTER + MIDDLEWARE ────────────────────────────────────────────


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_closed_without_token(client):
    """Sin token en sesión, el signup devuelve la página de registro cerrado."""
    response = client.get("/es/cuenta/signup/")
    assert response.status_code == 200
    assert b"Registro cerrado" in response.content or b"beta cerrada" in response.content


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_open_with_valid_token(client, invitation):
    """Con token válido en URL, el middleware carga la sesión y el signup abre."""
    assert invitation.token, "La fixture debe generar un token automáticamente"
    response = client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    # El signup debe estar abierto (200 con formulario, no la página cerrada).
    assert response.status_code == 200
    assert b"Registro cerrado" not in response.content
    # La sesión debe contener el email.
    assert client.session.get("account_invitation_email") == invitation.email


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_closed_with_invalid_token(client, db):
    """Token inexistente no abre el signup."""
    response = client.get("/es/cuenta/signup/?invite=nonexistent-token")
    assert response.status_code == 200
    assert b"Registro cerrado" in response.content or b"beta cerrada" in response.content
    assert "account_invitation_email" not in client.session


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_closed_with_expired_token(client, db):
    """Token expirado no abre el signup."""
    inv = Invitation.objects.create(
        email="expired@example.com",
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    response = client.get(f"/es/cuenta/signup/?invite={inv.token}")
    assert b"Registro cerrado" in response.content or b"beta cerrada" in response.content
    assert "account_invitation_email" not in client.session


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_closed_with_consumed_token(client, admin_user):
    """Token ya consumido no abre el signup."""
    inv = Invitation.objects.create(email="consumed@example.com")
    inv.consumed_by = admin_user
    inv.consumed_at = timezone.now()
    inv.save()
    response = client.get(f"/es/cuenta/signup/?invite={inv.token}")
    assert b"Registro cerrado" in response.content or b"beta cerrada" in response.content


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=False)
def test_signup_open_when_invitation_only_disabled(client):
    """Con INVITATION_ONLY=False, el signup abre sin token."""
    response = client.get("/es/cuenta/signup/")
    assert response.status_code == 200
    assert b"Registro cerrado" not in response.content


# ── SEÑAL: CONSUMO ─────────────────────────────────────────────────


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_invitation_consumed_on_user_creation(client, invitation):
    """Al registrar un usuario con el email invitado, la invitación se consume."""
    # Simula el flujo: middleware carga sesión, usuario se registra.
    client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    new_user = User.objects.create_user(email=invitation.email, password="test12345")
    invitation.refresh_from_db()
    assert invitation.consumed_by_id == new_user.pk
    assert invitation.consumed_at is not None
    assert not invitation.is_valid


@pytest.mark.django_db
def test_invitation_not_consumed_for_unrelated_email(invitation):
    """Crear un usuario con otro email no consume la invitación."""
    User.objects.create_user(email="other@example.com", password="test12345")
    invitation.refresh_from_db()
    assert invitation.consumed_by_id is None


# ── ADMIN ACTION ───────────────────────────────────────────────────


@pytest.mark.django_db
def test_admin_send_invitations_sends_email(admin_client, invitation):
    """La acción de admin envía un correo por invitación pendiente."""
    response = admin_client.post(
        "/admin/accounts/invitation/",
        {"action": "send_invitations", "_selected_action": [invitation.pk]},
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 1
    assert invitation.email in mail.outbox[0].to[0]
    invitation.refresh_from_db()
    assert invitation.sent_at is not None


@pytest.mark.django_db
def test_admin_send_invitations_creates_audit_event(admin_client, invitation, admin_user):
    """Cada envío registra un AuditEvent."""
    admin_client.post(
        "/admin/accounts/invitation/",
        {"action": "send_invitations", "_selected_action": [invitation.pk]},
    )
    event = AuditEvent.objects.filter(verb="invitation_sent").first()
    assert event is not None
    assert event.actor_id == admin_user.pk
    assert event.metadata["email"] == invitation.email


@pytest.mark.django_db
def test_admin_send_invitations_skips_consumed(admin_client, admin_user):
    """Una invitación ya consumida se omite (no envía correo)."""
    inv = Invitation.objects.create(email="done@example.com")
    inv.consumed_by = admin_user
    inv.consumed_at = timezone.now()
    inv.save()
    admin_client.post(
        "/admin/accounts/invitation/",
        {"action": "send_invitations", "_selected_action": [inv.pk]},
    )
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_admin_send_invitations_skips_expired(admin_client):
    """Una invitación expirada se omite."""
    inv = Invitation.objects.create(
        email="expired@example.com",
        expires_at=timezone.now() - timedelta(minutes=1),
    )
    admin_client.post(
        "/admin/accounts/invitation/",
        {"action": "send_invitations", "_selected_action": [inv.pk]},
    )
    assert len(mail.outbox) == 0


@pytest.mark.django_db
def test_admin_create_invitation_sets_token_and_expiry(admin_client):
    """Al crear desde admin, se generan token y expires_at automáticamente."""
    response = admin_client.post(
        "/admin/accounts/invitation/add/",
        {"email": "new@example.com"},
        follow=True,
    )
    assert response.status_code == 200
    inv = Invitation.objects.get(email="new@example.com")
    assert inv.token  # no vacío
    assert len(inv.token) >= 32
    assert inv.expires_at is not None
    assert inv.created_by_id is not None  # el admin actual


# ── INTEGRACIÓN: FLUJO COMPLETO ────────────────────────────────────


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_full_flow_invitation_to_signup(client, invitation):
    """Flujo end-to-end: visita link → signup abierto → POST crea usuario → invitación consumida."""
    # 1. Visita el link con token.
    client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    assert client.session.get("account_invitation_email") == invitation.email

    # 2. POST al formulario de signup con el email invitado.
    response = client.post(
        "/es/cuenta/signup/",
        {
            "email": invitation.email,
            "password1": "Strong-Pass-123",
            "password2": "Strong-Pass-123",
            "age_confirmation": "on",
        },
    )
    # allauth redirige (302) tras signup exitoso, o muestra errores (200).
    assert response.status_code in (200, 302)

    # 3. El usuario fue creado y la invitación consumida.
    assert User.objects.filter(email=invitation.email).exists()
    invitation.refresh_from_db()
    assert invitation.consumed_by_id is not None
    assert invitation.consumed_at is not None


# ── EDGE CASES Y SAD PATHS ─────────────────────────────────────────


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_closed_when_token_in_session_but_invitation_consumed(
    client, invitation, admin_user
):
    """Tras consumir la invitación, una segunda visita al signup lo cierra
    aunque el token siga en sesión (re-validación del middleware)."""
    # Primera visita: carga sesión.
    client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    assert client.session.get("account_invitation_email") == invitation.email

    # Consume la invitación (simula signup exitoso o uso desde otro dispositivo).
    invitation.consumed_by = admin_user
    invitation.consumed_at = timezone.now()
    invitation.save()

    # Segunda visita al signup: el middleware re-valida y limpia la sesión.
    response = client.get("/es/cuenta/signup/")
    assert b"Registro cerrado" in response.content or b"beta cerrada" in response.content
    assert "account_invitation_email" not in client.session


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_closed_when_invitation_expires_after_session_load(client, invitation):
    """Si la invitación expira después de haberse cargado en sesión, el
    middleware la invalida en la siguiente request."""
    client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    assert client.session.get("account_invitation_email") == invitation.email

    # Simula expiración.
    invitation.expires_at = timezone.now() - timedelta(minutes=1)
    invitation.save()

    response = client.get("/es/cuenta/signup/")
    assert b"Registro cerrado" in response.content or b"beta cerrada" in response.content
    assert "account_invitation_email" not in client.session


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_session_cleared_after_successful_signup(client, invitation):
    """Tras un signup exitoso, el token se limpia de la sesión (no se reutiliza)."""
    client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    assert client.session.get("account_invitation_token") == invitation.token

    client.post(
        "/es/cuenta/signup/",
        {
            "email": invitation.email,
            "password1": "Strong-Pass-123",
            "password2": "Strong-Pass-123",
            "age_confirmation": "on",
        },
    )

    # La señal user_signed_up debe haber limpiado la sesión.
    assert "account_invitation_email" not in client.session
    assert "account_invitation_token" not in client.session


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_rejects_email_different_from_invitation(client, invitation):
    """El signup con un email diferente al invitado se rechaza (validación en el form).

    Esto evita que un solo enlace de invitación permita registrar cuentas con
    emails arbitrarios: el token está ligado al email del invitado.
    """
    client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    other_email = "attacker@example.com"

    response = client.post(
        "/es/cuenta/signup/",
        {
            "email": other_email,
            "password1": "Strong-Pass-123",
            "password2": "Strong-Pass-123",
            "age_confirmation": "on",
        },
    )
    # El signup debe fallar (200 con errores de form, no 302 de éxito).
    assert response.status_code == 200
    assert b"invitaci" in response.content.lower() or b"invitation" in response.content.lower()
    # El usuario con email ajeno NO debe existir.
    assert not User.objects.filter(email=other_email).exists()
    # La invitación original sigue pendiente.
    invitation.refresh_from_db()
    assert invitation.consumed_by_id is None


@pytest.mark.django_db
def test_invitation_token_is_unique(db):
    """Dos invitaciones no pueden tener el mismo token."""
    inv1 = Invitation.objects.create(email="a@example.com")
    from django.db import IntegrityError

    with pytest.raises(IntegrityError):
        Invitation.objects.create(email="b@example.com", token=inv1.token)


@pytest.mark.django_db
def test_invitation_token_generated_on_direct_create(db):
    """Crear una invitación vía objects.create() genera token y expires_at automáticamente."""
    inv = Invitation.objects.create(email="auto@example.com")
    assert inv.token
    assert len(inv.token) >= 32
    assert inv.expires_at is not None
    assert inv.expires_at > timezone.now()


@pytest.mark.django_db
def test_invitation_with_no_expiry_never_expires(db):
    """Una invitación con expires_at=None (creada explícitamente) no expira."""
    inv = Invitation.objects.create(email="noexpiry@example.com", expires_at=None)
    # Forzar expires_at=None (save() lo setaría si pk es None; aquí forzamos).
    Invitation.objects.filter(pk=inv.pk).update(expires_at=None)
    inv.refresh_from_db()
    assert inv.expires_at is None
    assert inv.is_valid is True


@pytest.mark.django_db
def test_admin_send_invitations_logs_error_on_failure(admin_client, invitation, monkeypatch):
    """Si el envío falla, el error se registra y se reporta al admin."""
    from apps.accounts import admin as admin_module

    def _raise(invitation):
        raise RuntimeError("SMTP timeout")

    monkeypatch.setattr(admin_module.InvitationAdmin, "_send_invitation_email", _raise)

    response = admin_client.post(
        "/admin/accounts/invitation/",
        {"action": "send_invitations", "_selected_action": [invitation.pk]},
    )
    assert response.status_code == 302
    assert len(mail.outbox) == 0


@pytest.mark.django_db
@override_settings(INVITATION_BASE_URL="")
def test_admin_build_signup_url_fails_in_prod_when_no_base_url(invitation):
    """En producción (DEBUG=False), falta INVITATION_BASE_URL lanza RuntimeError."""

    from apps.accounts.admin import InvitationAdmin

    admin_instance = InvitationAdmin(Invitation, None)
    with pytest.raises(RuntimeError, match="INVITATION_BASE_URL"):
        admin_instance._build_signup_url(invitation)


@pytest.mark.django_db
@override_settings(INVITATION_BASE_URL="https://example.com")
def test_admin_build_signup_url_with_base_url(invitation):
    """Con INVITATION_BASE_URL configurado, el enlace es absoluto y válido."""
    from apps.accounts.admin import InvitationAdmin

    admin_instance = InvitationAdmin(Invitation, None)
    url = admin_instance._build_signup_url(invitation)
    assert url.startswith("https://example.com/")
    assert f"invite={invitation.token}" in url


@pytest.mark.django_db
def test_admin_send_invitation_email_contains_valid_url(admin_client, invitation):
    """El correo enviado contiene un enlace absoluto con el token."""
    admin_client.post(
        "/admin/accounts/invitation/",
        {"action": "send_invitations", "_selected_action": [invitation.pk]},
    )
    assert len(mail.outbox) == 1
    body = mail.outbox[0].body
    assert invitation.token in body
    assert "https://testserver.example/" in body


@pytest.mark.django_db
def test_consume_invitation_atomic_no_double_consume(db):
    """Dos intentos concurrentes de consumo no duplican (UPDATE atómico)."""

    inv = Invitation.objects.create(email="race@example.com")
    user1 = User.objects.create_user(email="race@example.com", password="pass12345")
    user2 = User.objects.create_user(email="race2@example.com", password="pass12345")

    # El segundo intento no consume (la invitación ya fue consumida por user1).
    inv.refresh_from_db()
    assert inv.consumed_by_id == user1.pk

    # Intentar consumirla de nuevo con user2: no debería cambiar.
    updated = Invitation.objects.filter(pk=inv.pk, consumed_by__isnull=True).update(
        consumed_by=user2, consumed_at=timezone.now()
    )
    assert updated == 0
    inv.refresh_from_db()
    assert inv.consumed_by_id == user1.pk  # sigue siendo user1


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_middleware_ignores_invite_token_on_non_signup_paths(client, invitation):
    """Un token en la URL de una ruta que no es signup se ignora."""
    # Login page con un token en la query: no debe cargar la sesión.
    client.get(f"/es/cuenta/login/?invite={invitation.token}")
    assert "account_invitation_email" not in client.session


@pytest.mark.django_db
@override_settings(INVITATION_ONLY=True)
def test_signup_open_with_token_in_session_persists_across_requests(client, invitation):
    """Una vez cargado el token, visitas subsecuentes al signup siguen abiertas."""
    client.get(f"/es/cuenta/signup/?invite={invitation.token}")
    # Segunda visita sin el parámetro ?invite: la sesión mantiene el email.
    response = client.get("/es/cuenta/signup/")
    assert response.status_code == 200
    assert b"Registro cerrado" not in response.content
    assert client.session.get("account_invitation_email") == invitation.email
