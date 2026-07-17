from .base import *  # noqa: F403

DEBUG = True

ACCOUNT_EMAIL_VERIFICATION = "optional"

INSTALLED_APPS += [  # noqa: F405
    "django_extensions",
]

LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "correlation_id": {
            "()": "apps.core.logging_filters.CorrelationIdFilter",
        },
    },
    "formatters": {
        "verbose": {
            "format": "{levelname} {asctime} {module} [{correlation_id}] {message}",
            "style": "{",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "verbose",
            "filters": ["correlation_id"],
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}
