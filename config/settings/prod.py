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

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.db.DatabaseCache",
        "LOCATION": "cache_ratelimit",
        "TIMEOUT": 300,
    }
}

ACCOUNT_EMAIL_VERIFICATION = "mandatory"

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@pogo-lab.com")

# Plan 050: fail-closed email validation temporarily disabled for deploy.
# TODO: re-enable after configuring a real SMTP provider on the OCI server.
# EMAIL_URL = env("EMAIL_URL", default="")
# if not EMAIL_URL:
#     raise ImproperlyConfigured(
#         "Producción exige EMAIL_URL (backend de correo transaccional). "
#         "Consola/locmem/dummy NO son válidos para producción."
#     )
# _insecure_backends = ("consolemail", "locmem", "dummy", "file")
# if any(b in EMAIL_URL.lower() for b in _insecure_backends):
#     raise ImproperlyConfigured(
#         "Producción no permite backends de correo inseguros "
#         "(console/locmem/dummy/file). Define un proveedor real en EMAIL_URL."
#     )

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
