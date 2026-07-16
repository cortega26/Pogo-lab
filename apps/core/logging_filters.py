import logging
import threading

_thread_local = threading.local()


def set_correlation_id(value: str):
    _thread_local.correlation_id = value


def get_correlation_id() -> str:
    return getattr(_thread_local, "correlation_id", "")


class CorrelationIdFilter(logging.Filter):
    def filter(self, record):
        record.correlation_id = get_correlation_id()
        return True
