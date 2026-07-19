import uuid

from django import forms
from django.contrib.auth import get_user_model, logout
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import render
from django.utils import timezone

from apps.analysis.models import AnalysisRun
from apps.audit.models import AuditEvent
from apps.contributions.models import DataContributionConsent
from apps.trades.models import TradeObservation, TradeSession

User = get_user_model()


class DeleteAccountForm(forms.Form):
    password = forms.CharField(
        label="Contraseña",
        widget=forms.PasswordInput(
            attrs={
                "class": "block w-full rounded-lg border border-slate-300 bg-white px-3 py-2.5 text-sm placeholder-slate-400 transition-colors duration-150 focus:border-brand-500 focus:outline-none focus:ring-2 focus:ring-brand-500/20 dark:border-slate-600 dark:bg-slate-800 dark:text-slate-100 dark:placeholder-slate-500 dark:focus:border-brand-400"
            }
        ),
    )


def _build_export_payload(user):
    """Reúne todos los datos del usuario para exportar.

    No incluye el campo privado notes de TradeObservation.
    """
    observations = (
        TradeObservation.objects.filter(owner=user)
        .order_by("-observed_at")
        .values(
            "id",
            "session_id",
            "observed_at",
            "friendship_level",
            "trade_type",
            "is_lucky",
            "atk",
            "iv_def",
            "hp",
            "species",
            "special_trade",
            "oldest_age_bucket",
            "event_context",
            "app_version",
            "input_method",
            "state",
            "exclusion_reason",
            "contribution_optin",
            "dedup_hash",
        )
    )

    sessions = TradeSession.objects.filter(owner=user).order_by("-started_at").values()

    analysis_runs = AnalysisRun.objects.filter(owner=user).order_by("-created_at").values()

    consents = DataContributionConsent.objects.filter(user=user).values()

    try:
        profile = user.profile
        profile_data = {
            "locale": profile.locale,
            "country": profile.country,
            "default_contribution_optin": profile.default_contribution_optin,
            "display_prefs": profile.display_prefs,
        }
    except User.profile.RelatedObjectDoesNotExist:
        profile_data = {}

    return {
        "exported_at": timezone.now().isoformat(),
        "user_id": user.pk,
        "email": user.email,
        "observations": list(observations),
        "sessions": list(sessions),
        "analysis_runs": list(analysis_runs),
        "contribution_consents": list(consents),
        "profile": profile_data,
    }


@login_required
def export_data(request):
    """Exporta los datos del usuario en JSON.

    GET: muestra la página de confirmación.
    POST: genera y descarga el archivo JSON.
    """
    if request.method == "POST":
        payload = _build_export_payload(request.user)

        AuditEvent.log(
            verb="account_data_exported",
            actor=request.user,
            target_type="User",
            target_id=request.user.pk,
            metadata={"data_types": list(payload.keys())},
        )

        response = JsonResponse(payload, json_dumps_params={"ensure_ascii": False, "indent": 2})
        response["Content-Disposition"] = (
            f'attachment; filename="pogolab_export_{request.user.pk}.json"'
        )
        return response

    return render(request, "accounts/export.html")


@login_required
def delete_account(request):
    """Elimina la cuenta y anonimiza/borra datos asociados.

    GET: muestra la página de confirmación.
    POST: ejecuta la eliminación irreversible.
    """
    if request.method == "POST":
        form = DeleteAccountForm(request.POST)
        if not form.is_valid():
            return render(request, "accounts/delete.html", {"form": form}, status=400)

        if not request.user.check_password(form.cleaned_data["password"]):
            form.add_error("password", "Contraseña incorrecta.")
            return render(request, "accounts/delete.html", {"form": form}, status=400)

        user = request.user

        if not user.is_active:
            logout(request)
            return render(request, "accounts/delete_done.html")

        user_id = user.pk
        profile_deleted = True

        with transaction.atomic():
            # 1. Borrar observaciones
            obs_qs = TradeObservation.objects.filter(owner=user)
            obs_count = obs_qs.count()
            obs_pks = list(obs_qs.values_list("pk", flat=True))
            obs_qs.delete()

            # 2. Borrar sesiones
            session_qs = TradeSession.objects.filter(owner=user)
            session_count = session_qs.count()
            session_pks = list(session_qs.values_list("pk", flat=True))
            session_qs.delete()

            # 3. Borrar ejecuciones de análisis
            analysis_qs = AnalysisRun.objects.filter(owner=user)
            analysis_count = analysis_qs.count()
            analysis_pks = list(analysis_qs.values_list("pk", flat=True))
            analysis_qs.delete()

            # 4. Borrar consentimientos de contribución
            consent_qs = DataContributionConsent.objects.filter(user=user)
            consent_count = consent_qs.count()
            consent_pks = list(consent_qs.values_list("pk", flat=True))
            consent_qs.delete()

            # 5. Borrar perfil de usuario
            try:
                profile = user.profile
                profile_pk = profile.pk
                profile.delete()
            except User.profile.RelatedObjectDoesNotExist:
                profile_deleted = False
                profile_pk = None

            # 6. Anonimizar el usuario (preserva FK de AuditEvent)
            anonymized_email = f"deleted_{uuid.uuid4().hex}@pogolab.local"
            user.email = anonymized_email
            user.set_unusable_password()
            user.is_active = False
            user.save(update_fields=["email", "password", "is_active"])

        AuditEvent.log(
            verb="account_deleted",
            actor=None,
            target_type="User",
            target_id=user_id,
            metadata={
                "email_anonymized": True,
                "stats": {
                    "observations_deleted": obs_count,
                    "observation_pks": obs_pks,
                    "sessions_deleted": session_count,
                    "session_pks": session_pks,
                    "analysis_runs_deleted": analysis_count,
                    "analysis_pks": analysis_pks,
                    "consents_deleted": consent_count,
                    "consent_pks": consent_pks,
                    "profile_deleted": profile_deleted,
                    "profile_pk": profile_pk,
                },
            },
        )

        logout(request)
        return render(request, "accounts/delete_done.html")

    return render(request, "accounts/delete.html", {"form": DeleteAccountForm()})
