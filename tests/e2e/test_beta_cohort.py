"""Pruebas E2E locales para los controles previos de la cohorte beta."""

import logging

import pytest
from django.contrib.auth import get_user_model
from django.test import Client

from apps.accounts.models import Invitation
from apps.audit.models import AuditEvent

User = get_user_model()


@pytest.mark.django_db
def test_admin_invitation_delivery_keeps_pii_out_of_audit_messages_and_logs(caplog):
    """El envío exitoso no propaga el email centinela fuera del correo."""
    sentinel = "beta-pii-sentinel-7f8b2@example.invalid"
    admin = User.objects.create_superuser(email="admin@example.com", password="admin123")
    invitation = Invitation.objects.create(email=sentinel)
    client = Client()
    client.force_login(admin)

    with caplog.at_level(logging.ERROR, logger="apps.accounts.admin"):
        post_response = client.post(
            "/admin/accounts/invitation/",
            {"action": "send_invitations", "_selected_action": [invitation.pk]},
        )
    response = client.get(post_response["Location"])

    event = AuditEvent.objects.get(verb="invitation_sent")
    rendered_messages = " ".join(str(message) for message in response.context["messages"])
    captured_logs = " ".join(record.getMessage() for record in caplog.records)

    assert event.target_type == "Invitation"
    assert event.target_id == invitation.pk
    assert event.actor_id == admin.pk
    assert event.correlation_id == post_response["X-Correlation-Id"]
    assert sentinel not in str(event.metadata)
    assert sentinel not in rendered_messages
    assert sentinel not in captured_logs


@pytest.mark.django_db
def test_admin_invitation_delivery_failure_keeps_pii_out_of_messages_and_logs(caplog, monkeypatch):
    """Un error de proveedor no filtra email ni detalle sensible al operador."""
    sentinel = "beta-error-sentinel-4c1a9@example.invalid"
    admin = User.objects.create_superuser(email="admin@example.com", password="admin123")
    invitation = Invitation.objects.create(email=sentinel)
    client = Client()
    client.force_login(admin)

    from apps.accounts.admin import InvitationAdmin

    def fail_send(_self, _invitation):
        raise RuntimeError(f"provider rejected {sentinel}")

    monkeypatch.setattr(InvitationAdmin, "_send_invitation_email", fail_send)

    with caplog.at_level(logging.ERROR, logger="apps.accounts.admin"):
        post_response = client.post(
            "/admin/accounts/invitation/",
            {"action": "send_invitations", "_selected_action": [invitation.pk]},
        )
    response = client.get(post_response["Location"])

    rendered_messages = " ".join(str(message) for message in response.context["messages"])
    captured_logs = " ".join(record.getMessage() for record in caplog.records)

    assert sentinel not in rendered_messages
    assert sentinel not in captured_logs
    assert str(invitation.pk) in rendered_messages
    assert str(invitation.pk) in captured_logs
    assert not AuditEvent.objects.filter(verb="invitation_sent").exists()
    invitation.refresh_from_db()
    assert invitation.sent_at is None
