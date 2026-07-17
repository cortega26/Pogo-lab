"""Vistas del dashboard comunitario.

Dashboard PÚBLICO (sin login) que muestra el dataset comunitario con:
- Métricas agregadas
- Advertencia de sesgo de selección
- Sin country por fila
- Descarga pública desactivada por defecto
"""

from typing import Any

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render

from apps.contributions.models import DatasetVersion
from apps.contributions.services import aggregate_community_distribution


def community_dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard comunitario público (solo lectura).

    Solo muestra datasets marcados `is_public` (es decir, con `min_sample_met`):
    honra el umbral mínimo como gate de exposición pública frente a la
    re-identificación con muestras pequeñas.
    """
    latest = DatasetVersion.objects.filter(is_public=True).order_by("-number").first()

    context: dict[str, Any] = {
        "dataset_version": latest,
        "can_download": False,
    }

    if latest is not None:
        aggregation = aggregate_community_distribution(latest)
        context["aggregation"] = aggregation

        build_date = latest.built_at
        context["build_date"] = build_date

        total_observations = sum(g["n"] for g in aggregation)
        context["total_observations"] = total_observations

        lucky_total = sum(g["n"] for g in aggregation if g["is_lucky"])
        normal_total = sum(g["n"] for g in aggregation if not g["is_lucky"])
        context["lucky_total"] = lucky_total
        context["normal_total"] = normal_total

        ruleset_versions = {g["ruleset_version"] for g in aggregation}
        context["ruleset_versions"] = sorted(ruleset_versions)

        if latest.min_sample_met and getattr(settings, "COMMUNITY_DATASET_DOWNLOAD_ENABLED", False):
            context["can_download"] = True

    return render(
        request,
        "experiments/dashboard.html",
        context,
    )
