"""Vistas para gestión de consentimiento de contribución."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect
from django.utils.translation import gettext_lazy as _

from .models import DataContributionConsent

CONSENT_TEXT_VERSION = "1.0.0"
SCOPE = "community_dataset"


@login_required
def grant_consent_view(request: HttpRequest) -> HttpResponse:
    DataContributionConsent.grant_consent(request.user, SCOPE, CONSENT_TEXT_VERSION)
    messages.success(request, _("Has dado tu consentimiento para contribuir."))
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def revoke_consent_view(request: HttpRequest) -> HttpResponse:
    DataContributionConsent.revoke_consent(request.user, SCOPE)
    messages.info(request, _("Has revocado tu consentimiento."))
    return redirect(request.META.get("HTTP_REFERER", "/"))
