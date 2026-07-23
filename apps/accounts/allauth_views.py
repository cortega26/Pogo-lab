"""Vistas de allauth con rate limiting para login y registro."""

from allauth.account.views import LoginView, SignupView
from django.shortcuts import render
from django_ratelimit.core import is_ratelimited

from apps.core.ratelimit import client_ip_key


class RateLimitedLoginView(LoginView):
    def dispatch(self, request, *args, **kwargs):
        if is_ratelimited(
            request=request,
            group="account_login",
            key=client_ip_key,
            rate="5/m",
            method="POST",
            increment=True,
        ):
            return render(request, "core/429.html", status=429)
        return super().dispatch(request, *args, **kwargs)


class RateLimitedSignupView(SignupView):
    def dispatch(self, request, *args, **kwargs):
        if is_ratelimited(
            request=request,
            group="account_signup",
            key=client_ip_key,
            rate="3/m",
            method="POST",
            increment=True,
        ):
            return render(request, "core/429.html", status=429)
        return super().dispatch(request, *args, **kwargs)
