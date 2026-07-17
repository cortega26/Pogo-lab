"""Vistas de allauth con rate limiting para login y registro."""

from allauth.account.views import LoginView, SignupView
from django.conf import settings
from django.shortcuts import render
from django_ratelimit.core import is_ratelimited


class RateLimitedLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "RATELIMIT_ENABLE", True) and is_ratelimited(
            request=request,
            group="account_login",
            key="ip",
            rate="5/m",
            method="POST",
            increment=True,
        ):
            return render(request, "core/429.html", status=429)
        return super().dispatch(request, *args, **kwargs)


class RateLimitedSignupView(SignupView):
    def dispatch(self, request, *args, **kwargs):
        if getattr(settings, "RATELIMIT_ENABLE", True) and is_ratelimited(
            request=request,
            group="account_signup",
            key="ip",
            rate="3/m",
            method="POST",
            increment=True,
        ):
            return render(request, "core/429.html", status=429)
        return super().dispatch(request, *args, **kwargs)
