"""Settings para tests sobre PostgreSQL 16.

Uso:
    DATABASE_URL=postgres://pogo:pogo@localhost:5433/pogo_test \
        uv run pytest -m postgres --settings=config.settings.test_postgres

Guard: la URL debe identificar inequívocamente una DB de test.
"""

import os
from urllib.parse import urlparse

from django.core.exceptions import ImproperlyConfigured

from .test import *  # noqa: F403

_database_url = os.environ.get("DATABASE_URL", "")
if not _database_url:
    raise ImproperlyConfigured(
        "test_postgres exige DATABASE_URL apuntando a una DB de test PostgreSQL."
    )
_test_markers = ("test", "pogo_test", "_test")
if not any(m in _database_url for m in _test_markers):
    raise ImproperlyConfigured(
        f"DATABASE_URL no parece apuntar a una DB de test: {_database_url}. "
        "Debe contener 'test' en el nombre."
    )

_parsed = urlparse(_database_url)
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": _parsed.path.lstrip("/") if _parsed.path else "pogo_test",
        "HOST": _parsed.hostname or "localhost",
        "PORT": str(_parsed.port or 5432),
        "USER": _parsed.username or "pogo",
        "PASSWORD": _parsed.password or "pogo",
    }
}
