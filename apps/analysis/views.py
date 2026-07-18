"""Vistas para el panel de análisis personal.

SSR + HTMX. Chart.js autohospedado + tabla alternativa.
"""

import json

from django.contrib.auth.decorators import login_required
from django.shortcuts import render

from engine.decisions import AnalysisContext, evaluate

from .services import get_or_run_personal_analysis


@login_required
def analysis_dashboard(request):
    """Panel principal de análisis del usuario autenticado."""
    owner = request.user
    filters: dict = {}

    if request.GET.get("friendship_level"):
        filters["friendship_level"] = request.GET["friendship_level"]
    if request.GET.get("trade_type"):
        filters["trade_type"] = request.GET["trade_type"]

    run = get_or_run_personal_analysis(owner.pk, filters=filters)
    results = run.results.all()

    recs = []
    mixing = run.mixing_flags or {}
    for result in results:
        if result.metric_key.startswith("hundo_rate"):
            payload = result.payload
            ctx = _build_context(payload, mixing)
            if ctx is not None:
                recs = [
                    {
                        "rule_key": r.rule_key,
                        "rule_version": r.rule_version,
                        "message_key": r.message_key,
                        "severity": r.severity,
                        "params": r.params,
                    }
                    for r in evaluate(ctx)
                ]
            break

    chart_data = _prepare_chart_data(results)

    results_with_rows = [
        {
            "result": r,
            "distribution_rows": _zip_counts_values(r),
        }
        for r in results
    ]

    return render(
        request,
        "analysis/dashboard.html",
        {
            "run": run,
            "results_with_rows": results_with_rows,
            "recommendations": recs,
            "chart_data": json.dumps(chart_data),
            "has_results": results.exists(),
        },
    )


def _build_context(payload: dict, mixing: dict | None = None) -> AnalysisContext | None:
    """Construye AnalysisContext desde el payload de un resultado."""
    mixing = mixing or {}
    n = payload.get("n", 0)
    if n == 0:
        return None

    successes = payload.get("successes", 0)
    p0 = payload.get("p0", 0.0)
    p_value = payload.get("p_value", 1.0)
    effect_size = payload.get("effect_size")
    method_used = payload.get("method_used", "unknown")
    min_n = payload.get("min_sample", 30)

    return AnalysisContext(
        n=n,
        successes=successes,
        p0=p0,
        p_value=p_value,
        effect_size=effect_size,
        method_used=method_used,
        metric="hundo_rate",
        min_sample=min_n,
        has_mixed_lucky_normal=bool(mixing.get("has_mixed_lucky_normal")),
        has_mixed_rulesets=bool(mixing.get("has_mixed_rulesets")),
        has_mixed_periods=bool(mixing.get("has_mixed_periods")),
    )


def _prepare_chart_data(results) -> dict:
    """Prepara datos para gráficos Chart.js."""
    data: dict = {"distributions": []}

    for result in results:
        payload = result.payload
        if "counts" in payload and "values" in payload:
            data["distributions"].append(
                {
                    "metric_key": result.metric_key,
                    "labels": [str(v) for v in payload["values"]],
                    "counts": payload["counts"],
                    "n": payload.get("n", 0),
                }
            )

    return data


def _zip_counts_values(result) -> list[dict]:
    """Empareja values y counts para iterar en la plantilla."""
    payload = result.payload
    values: list = payload.get("values", [])
    counts: list = payload.get("counts", [])
    return [
        {"value": v, "count": counts[i] if i < len(counts) else 0} for i, v in enumerate(values)
    ]
