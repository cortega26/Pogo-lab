"""Vistas para gestión de consentimiento de contribución."""

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.decorators.http import require_POST
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


def _safe_referer(request: HttpRequest, default: str = "/") -> str:
    ref = request.META.get("HTTP_REFERER", "")
    if ref and url_has_allowed_host_and_scheme(
        url=ref,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return ref
    return default


@login_required
@require_POST
def grant_consent_view(request: HttpRequest) -> HttpResponse:
    if _is_rate_limited(request):
        return render(request, "core/429.html", status=429)
    DataContributionConsent.grant_consent(request.user, SCOPE, CONSENT_TEXT_VERSION)
    messages.success(request, _("Has dado tu consentimiento para contribuir."))
    return redirect(_safe_referer(request))


@login_required
@require_POST
def revoke_consent_view(request: HttpRequest) -> HttpResponse:
    if _is_rate_limited(request):
        return render(request, "core/429.html", status=429)
    DataContributionConsent.revoke_consent(request.user, SCOPE)
    messages.info(request, _("Has revocado tu consentimiento."))
    return redirect(_safe_referer(request))
