from .base import *  # noqa: F403

DEBUG = False

SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_PROXY_SSL_HEADER = ("HTTP_X_FORWARDED_PROTO", "https")

ACCOUNT_EMAIL_VERIFICATION = "mandatory"

DEFAULT_FROM_EMAIL = env("DEFAULT_FROM_EMAIL", default="noreply@pogo-lab.com")

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
