from .base import *

DEBUG = False

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "test_db.sqlite3",  # Base de datos en archivo para live_server.
    },
}

CACHES = {
    "default": {
        "BACKEND": "django.core.cache.backends.locmem.LocMemCache",
    },
}

PASSWORD_HASHERS = [
    "django.contrib.auth.hashers.MD5PasswordHasher",
]

EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

ACCOUNT_EMAIL_VERIFICATION = "none"

# En tests el registro por invitación está desactivado por defecto; cada test
# que lo necesite lo activa explícitamente con override_settings.
INVITATION_ONLY = False
INVITATION_EXPIRY_DAYS = 14
# Base URL para enlaces de invitación en tests (no se envía correo real).
INVITATION_BASE_URL = "https://testserver.example"

RATELIMIT_ENABLE = False

# CSP relajada para tests (admin inline scripts, htmx nonce, etc.)
CONTENT_SECURITY_POLICY = {
    "DIRECTIVES": {
        "default-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'", "data:"],
        "script-src": ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
        "style-src": ["'self'", "'unsafe-inline'"],
        "img-src": ["'self'", "data:"],
        "font-src": ["'self'"],
        "connect-src": ["'self'"],
        "base-uri": ["'self'"],
        "frame-ancestors": ["'self'"],
        "form-action": ["'self'"],
    },
}

STORAGES = {
    "staticfiles": {
        "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
    },
}
