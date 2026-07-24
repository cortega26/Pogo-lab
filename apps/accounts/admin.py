from django.conf import settings
from django.contrib import admin, messages
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from .models import Invitation, User, UserProfile


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    ordering = ("email",)
    list_display = ("email", "is_staff", "is_active")
    list_filter = ("is_staff", "is_superuser", "is_active")
    search_fields = ("email",)
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        (_("Información personal"), {"fields": ("first_name", "last_name")}),
        (
            _("Permisos"),
            {"fields": ("is_active", "is_staff", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Fechas"), {"fields": ("last_login", "date_joined")}),
    )
    add_fieldsets = ((None, {"classes": ("wide",), "fields": ("email", "password1", "password2")}),)


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ("user", "locale", "country", "default_contribution_optin")
    search_fields = ("user__email",)


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ("email", "status", "created_at", "sent_at", "consumed_at", "expires_at")
    list_filter = ("consumed_by",)
    search_fields = ("email",)
    readonly_fields = ("token", "sent_at", "consumed_at", "consumed_by", "created_at")
    actions = ("send_invitations",)

    @admin.display(description=_("estado"))
    def status(self, obj):
        if obj.consumed_by_id is not None:
            return "✓ consumada"
        if obj.expires_at and obj.expires_at < timezone.now():
            return "✗ expirada"
        return "⏳ pendiente"

    def get_fields(self, request, obj=None):  # noqa: ARG002
        fields = ["email", "expires_at", "created_by"]
        if obj is not None:
            fields = [
                "email",
                "expires_at",
                "created_by",
                "token",
                "sent_at",
                "consumed_at",
                "consumed_by",
                "created_at",
            ]
        return fields

    def save_model(self, request, obj, form, change):
        if not change and obj.created_by_id is None:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)

    @admin.action(description=_("Enviar invitaciones por correo"))
    def send_invitations(self, request, queryset):
        import logging

        from apps.audit.models import AuditEvent

        logger = logging.getLogger(__name__)
        sent = 0
        skipped = 0
        errors = []
        for invitation in queryset:
            if not invitation.is_valid:
                skipped += 1
                continue
            try:
                self._send_invitation_email(invitation)
            except Exception as exc:
                skipped += 1
                errors.append(f"{invitation.email}: {exc!s}")
                logger.exception("Error enviando invitación a %s", invitation.email)
                continue
            invitation.sent_at = timezone.now()
            invitation.save(update_fields=["sent_at"])
            AuditEvent.log(
                verb="invitation_sent",
                actor=request.user,
                target_type="Invitation",
                target_id=invitation.pk,
                metadata={"email": invitation.email},
            )
            sent += 1
        msg = _("{sent} invitaciones enviadas, {skipped} omitidas.").format(
            sent=sent, skipped=skipped
        )
        if errors:
            msg += " " + _("Errores: ") + "; ".join(errors[:5])
            if len(errors) > 5:
                msg += f" (+{len(errors) - 5} más)"
        self.message_user(
            request,
            msg,
            level=messages.SUCCESS if sent else messages.WARNING,
        )

    def _send_invitation_email(self, invitation):
        signup_url = self._build_signup_url(invitation)
        context = {"invitation": invitation, "signup_url": signup_url}
        text_body = render_to_string("accounts/invitation_email.txt", context)
        send_mail(
            subject=_("Tu invitación a Pogo-lab"),
            message=text_body,
            from_email=getattr(settings, "DEFAULT_FROM_EMAIL", "noreply@tooltician.com"),
            recipient_list=[invitation.email],
            fail_silently=False,
        )

    def _build_signup_url(self, invitation):
        from urllib.parse import urlencode

        base = getattr(settings, "INVITATION_BASE_URL", "").strip()
        if not base:
            # En dev/test basta con ruta relativa; en prod debe configurarse.
            from django.conf import settings as dj_settings

            if not dj_settings.DEBUG:
                raise RuntimeError(
                    "INVITATION_BASE_URL debe configurarse en producción para "
                    "enviar enlaces de invitación válidos."
                )
            base = ""
        signup_path = reverse("account_signup")
        query = urlencode({"invite": invitation.token})
        return f"{base.rstrip('/')}{signup_path}?{query}"
