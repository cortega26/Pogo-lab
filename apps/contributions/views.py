"""Vistas para gestión de consentimiento de contribución."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.translation import gettext_lazy as _
from django_ratelimit.core import is_ratelimited

from .models import DataContributionConsent

CONSENT_TEXT_VERSION = "1.0.0"
SCOPE = "community_dataset"


def _is_rate_limited(request):
    """Comprueba rate limiting respetando RATELIMIT_ENABLE."""
    from django.conf import settings

    if not getattr(settings, "RATELIMIT_ENABLE", True):
        return False
    return is_ratelimited(
        request=request,
        group="contributions",
        key="user_or_ip",
        rate="10/m",
        method="POST",
        increment=True,
    )


@login_required
def grant_consent_view(request: HttpRequest) -> HttpResponse:
    if _is_rate_limited(request):
        return render(request, "core/429.html", status=429)
    DataContributionConsent.grant_consent(request.user, SCOPE, CONSENT_TEXT_VERSION)
    messages.success(request, _("Has dado tu consentimiento para contribuir."))
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def revoke_consent_view(request: HttpRequest) -> HttpResponse:
    if _is_rate_limited(request):
        return render(request, "core/429.html", status=429)
    DataContributionConsent.revoke_consent(request.user, SCOPE)
    messages.info(request, _("Has revocado tu consentimiento."))
    return redirect(request.META.get("HTTP_REFERER", "/"))
