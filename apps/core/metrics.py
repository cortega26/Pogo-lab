"""Métricas de producto básicas sin PII."""

from django.contrib.auth import get_user_model

from apps.contributions.models import DatasetVersion
from apps.trades.models import TradeObservation


def product_metrics() -> dict:
    """Devuelve métricas agregadas del producto (sin PII)."""
    user_model = get_user_model()
    return {
        "total_users": user_model.objects.filter(is_active=True).count(),
        "total_observations": TradeObservation.objects.count(),
        "valid_observations": TradeObservation.objects.filter(state="valid").count(),
        "latest_dataset_version": (
            DatasetVersion.objects.order_by("-number").values_list("number", flat=True).first()
        ),
    }
