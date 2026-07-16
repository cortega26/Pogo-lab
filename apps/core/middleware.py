import uuid

from django.utils.deprecation import MiddlewareMixin

from .logging_filters import set_correlation_id


class CorrelationIdMiddleware(MiddlewareMixin):
    def process_request(self, request):
        correlation_id = request.META.get("HTTP_X_CORRELATION_ID") or str(uuid.uuid4())
        request.correlation_id = correlation_id
        set_correlation_id(correlation_id)

    def process_response(self, request, response):
        correlation_id = getattr(request, "correlation_id", "")
        response["X-Correlation-Id"] = correlation_id
        return response
