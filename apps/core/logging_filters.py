import logging
import re
import threading
import uuid

_thread_local = threading.local()

MAX_CORRELATION_ID_LENGTH = 64
_SAFE_CORRELATION_ID = re.compile(r"^[A-Za-z0-9_-]+$")


def set_correlation_id(value: str):
    _thread_local.correlation_id = value


def get_correlation_id() -> str:
    return getattr(_thread_local, "correlation_id", "")


def sanitize_correlation_id(value: str | None) -> str:
    """Normaliza un correlation_id de origen no confiable (ej. un header
    HTTP puesto por el cliente).

    Plan 061: "no confiar en header arbitrario como autoridad sin
    normalización". Si `value` no es una cadena corta con un charset
    seguro (alfanumérico, guion, guion bajo — sin saltos de línea ni otros
    caracteres de control que podrían usarse para inyección de headers o
    log injection), se descarta y se genera un id nuevo."""
    if value and len(value) <= MAX_CORRELATION_ID_LENGTH and _SAFE_CORRELATION_ID.match(value):
        return value
    return str(uuid.uuid4())


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True
