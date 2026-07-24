from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .base import *

DEBUG = env.bool("DEBUG", default=False)

SECURE_SSL_REDIRECT = env.bool("SECURE_SSL_REDIRECT", default=True)
SESSION_COOKIE_SECURE = env.bool("SESSION_COOKIE_SECURE", default=True)
CSRF_COOKIE_SECURE = env.bool("CSRF_COOKIE_SECURE", default=True)
CSRF_COOKIE_HTTPONLY = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")
RATELIMIT_IP_META_KEY = "HTTP_X_REAL_IP"

# allauth rate limiting (login/verify) usa este header para identificar al cliente.
# Debe coincidir con el header que nginx envía tras set_real_ip_from (X-Real-IP).
# Sin esto, allauth cae a REMOTE_ADDR (127.0.0.1 tras el proxy) y todos los
# usuarios comparten un mismo bucket de rate limit.
# Nota: allauth prefix es ALLAUTH_ (ver allauth.app_settings.AppSettings.prefix).
ALLAUTH_TRUSTED_CLIENT_IP_HEADER = "X-Real-IP"

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_ratelimit",
        "TIMEOUT": 300,
    }
}

ACCOUNT_EMAIL_VERIFICATION = "mandatory"

# Beta cerrada activa en producción: signup solo por invitación.
INVITATION_ONLY = env.bool("INVITATION_ONLY", default=True)

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="carlos@tooltician.com")

CSRF_TRUSTED_ORIGINS = env.list(
    "CSRF_TRUSTED_ORIGINS",
    default=[
        "https://pogo-lab.tooltician.com",
        "https://www.pogo-lab.tooltician.com",
    ],
)
SECURE_REFERRER_POLICY = "strict-origin-when-cross-origin"
SECURE_CONTENT_TYPE_NOSNIFF = True

# Plan 050: fail-closed email validation. Producción exige un proveedor SMTP real
# (Brevo por defecto). console/locmem/dummy/file NO son válidos en producción.
EMAIL_URL = env("EMAIL_URL", default="")
if not EMAIL_URL:
    raise ImproperlyConfigured(
        "Producción exige EMAIL_URL (backend de correo transaccional). "
        "Consola/locmem/dummy NO son válidos para producción."
    )
# Validación por esquema (no por substring) para evitar falsos positivos
# cuando un host legítimo contiene una subcadena como "locmem".
_email_scheme = urlparse(EMAIL_URL).scheme.lower().split("+", 1)[0]
_insecure_schemes = {"console", "consolemail", "locmem", "dummy", "file", ""}
if _email_scheme in _insecure_schemes:
    raise ImproperlyConfigured(
        f"Producción no permite backends de correo inseguros (esquema "
        f"'{_email_scheme}'). Define un proveedor SMTP real en EMAIL_URL "
        f"(smtp://, smtps://, smtp+tls:// o smtp+ssl://)."
    )

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {
            "()": "apps.core.logging_filters.CorrelationIdFilter",
        },
    },
    "formatters": {
        "json": {
            "format": "{levelname} {asctime} {module} [{correlation_id}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "json",
            "filters": ["correlation_id"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "WARNING",
    },
}
