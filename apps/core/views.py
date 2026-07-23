import json
import logging

from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt

logger = logging.getLogger(__name__)


def healthz(request):
    """Health check: verifica que la app y la DB responden."""
    db_ok = True
    try:
        connections["default"].cursor().execute("SELECT 1")
    except OperationalError:
        db_ok = False

    if not db_ok:
        return render(request, "core/healthz.html", {"db_ok": False})

    if request.GET.get("full"):
        return render(request, "core/healthz.html", {"db_ok": db_ok})

    return render(request, "core/healthz.html", {"db_ok": True})


MAX_CSP_REPORT_BYTES = 10_000


@csrf_exempt
def csp_report(request):
    """Collector de reportes CSP. Logea violaciones en producción."""
    if request.method != "POST":
        return JsonResponse({"error": "POST required"}, status=405)
    if request.body and len(request.body) > MAX_CSP_REPORT_BYTES:
        logger.info("CSP report body too large (%d bytes)", len(request.body))
        return JsonResponse({"status": "accepted"})
    try:
        report = json.loads(request.body)
        csp_data = report.get("csp-report", {}) if isinstance(report, dict) else {}
        sanitized = {
            "blocked": str(csp_data.get("blocked-uri", "unknown"))[:200]
            .replace("\n", " ")
            .replace("\r", " "),
            "directive": str(csp_data.get("effective-directive", "unknown"))[:100],
            "count": 1,
        }
        logger.info("CSP violation: %s", sanitized)
    except (json.JSONDecodeError, AttributeError):
        logger.info("CSP report with invalid body")
    return JsonResponse({"status": "accepted"})


def healthz_json(request):  # noqa: ARG001
    """Health check JSON para monitoreo automatizado."""
    db_ok = True
    try:
        connections["default"].cursor().execute("SELECT 1")
    except OperationalError:
        db_ok = False

    status_code = 200 if db_ok else 503
    return JsonResponse(
        {"status": "ok" if db_ok else "degraded", "db": "ok" if db_ok else "error"},
        status=status_code,
    )
