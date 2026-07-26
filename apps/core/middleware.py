from django.utils.deprecation import MiddlewareMixin

from .logging_filters import sanitize_correlation_id, set_correlation_id


class CorrelationIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # sanitize_correlation_id nunca confía en el header del cliente tal
        # cual: valida charset/longitud y genera uno nuevo si es inválido
        # (plan 061 — evita inyección de headers/logs vía X-Correlation-Id).
        correlation_id = sanitize_correlation_id(request.META.get("HTTP_X_CORRELATION_ID"))
        request.correlation_id = correlation_id
        set_correlation_id(correlation_id)

    def process_response(self, request, response):
        correlation_id = getattr(request, "correlation_id", "")
        response["X-Correlation-Id"] = correlation_id
        return response
