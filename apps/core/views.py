from django.db import connections
from django.db.utils import OperationalError
from django.http import JsonResponse
from django.shortcuts import render


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
