"""Vistas de apps/trades.

Requieren autenticacion (login_required). El owner es siempre request.user.
"""

import datetime
import json

from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import TradeSession
from .services import (
    bulk_create_observations,
    dashboard_stats,
    export_csv,
    import_csv,
    register_observation,
)


@login_required
def session_list(request: HttpRequest) -> HttpResponse:
    owner_id = request.user.pk
    assert owner_id is not None
    sessions_qs = TradeSession.objects.filter(owner_id=owner_id).order_by("-started_at")
    paginator = Paginator(sessions_qs, 25)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(request, "trades/session_list.html", {"page_obj": page_obj})


@login_required
def session_create(request: HttpRequest) -> HttpResponse:
    if request.method == "POST":
        label = request.POST.get("label", "")
        default_friendship = request.POST.get("default_friendship", "good")
        default_trade_type = request.POST.get("default_trade_type", "normal")

        owner_id = request.user.pk
        assert owner_id is not None
        session = TradeSession.objects.create(
            owner_id=owner_id,
            started_at=timezone.now(),
            label=label,
            default_friendship=default_friendship,
            default_trade_type=default_trade_type,
        )
        return render(request, "trades/_session_row.html", {"session": session})

    return render(request, "trades/session_create.html")


@login_required
def session_detail(request: HttpRequest, session_id: int) -> HttpResponse:
    session = get_object_or_404(TradeSession, pk=session_id, owner=request.user)
    observations_qs = session.observations.select_related("ruleset").order_by("-observed_at")
    paginator = Paginator(observations_qs, 50)
    page_number = request.GET.get("page", 1)
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        "trades/session_detail.html",
        {"session": session, "page_obj": page_obj, "observations": page_obj},
    )


@login_required
def observation_create(request: HttpRequest) -> HttpResponse:
    """Entrada rapida movil: formulario con teclado numerico y guardar y siguiente."""
    if request.method == "POST":
        owner_id = request.user.pk
        assert owner_id is not None

        try:
            observed_at_str = request.POST.get("observed_at", "")
            if observed_at_str:
                observed_at = datetime.datetime.fromisoformat(observed_at_str)
            else:
                observed_at = datetime.datetime.now(tz=datetime.UTC)

            friendship_level = request.POST.get("friendship_level", "good")
            trade_type = request.POST.get("trade_type", "normal")
            atk = int(request.POST.get("atk", 0))
            def_ = int(request.POST.get("def", 0))
            hp = int(request.POST.get("hp", 0))
            species = request.POST.get("species", "")

            profile = getattr(request.user, "profile", None)
            contribution_optin = profile is not None and profile.default_contribution_optin

            obs = register_observation(
                owner_id=owner_id,
                observed_at=observed_at,
                friendship_level=friendship_level,
                trade_type=trade_type,
                atk=atk,
                def_=def_,
                hp=hp,
                species=species,
                input_method="manual",
                contribution_optin=contribution_optin,
            )
        except (ValueError, TypeError) as exc:
            ctx = {"error": str(exc) or "Datos inválidos"}
            if request.headers.get("HX-Request"):
                return render(request, "trades/observation_create.html", ctx, status=200)
            return render(request, "trades/observation_create.html", ctx, status=400)

        if request.headers.get("HX-Request"):
            return render(request, "trades/_observation_row.html", {"obs": obs})

        return render(
            request,
            "trades/observation_create.html",
            {"saved": True, "obs": obs},
        )

    return render(request, "trades/observation_create.html")


MAX_BULK_ITEMS = 500


@login_required
def bulk_add(request: HttpRequest) -> HttpResponse:
    """Alta por lotes: varias observaciones en una operacion."""
    if request.method == "POST":
        owner_id = request.user.pk
        assert owner_id is not None

        raw = request.POST.get("observations_json", "[]")
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return render(
                request,
                "trades/bulk_add.html",
                {"error": "JSON invalido"},
            )

        if not isinstance(data, list):
            return render(
                request,
                "trades/bulk_add.html",
                {"error": "Se esperaba una lista de observaciones"},
                status=400,
            )

        if len(data) > MAX_BULK_ITEMS:
            return render(
                request,
                "trades/bulk_add.html",
                {"error": f"Máximo {MAX_BULK_ITEMS} observaciones por lote"},
                status=400,
            )

        observations = []
        for item in data:
            if not isinstance(item, dict):
                return render(
                    request,
                    "trades/bulk_add.html",
                    {"error": "Cada elemento debe ser un objeto JSON"},
                    status=400,
                )
            try:
                observed_at_str = item.get("observed_at", "")
                if observed_at_str:
                    observed_at = datetime.datetime.fromisoformat(observed_at_str)
                else:
                    observed_at = datetime.datetime.now(tz=datetime.UTC)

                observations.append(
                    {
                        "owner_id": owner_id,
                        "observed_at": observed_at,
                        "friendship_level": item.get("friendship_level", "good"),
                        "trade_type": item.get("trade_type", "normal"),
                        "atk": int(item.get("atk", 0)),
                        "def_": int(item.get("def", 0)),
                        "hp": int(item.get("hp", 0)),
                        "species": item.get("species", ""),
                        "input_method": "batch",
                    }
                )
            except (ValueError, TypeError) as exc:
                return render(
                    request,
                    "trades/bulk_add.html",
                    {"error": str(exc) or "Datos inválidos en un elemento"},
                    status=400,
                )

        created = bulk_create_observations(observations)
        created_new = [o for o in created if getattr(o, "_is_new", True)]
        duplicate_count = len(created) - len(created_new)
        return render(
            request,
            "trades/bulk_add.html",
            {
                "created_count": len(created_new),
                "duplicate_count": duplicate_count,
                "saved": True,
            },
        )

    return render(request, "trades/bulk_add.html")


@login_required
def csv_import(request: HttpRequest) -> HttpResponse:
    """Vista previa + import CSV.

    GET -> formulario de subida.
    POST -> parsea y muestra preview, o procesa si se confirma.
    """
    preview = None
    error = None

    if request.method == "POST":
        owner_id = request.user.pk
        assert owner_id is not None

        uploaded = request.FILES.get("csv_file")
        if uploaded is None:
            error = "Selecciona un archivo CSV"
        else:
            content_type = (getattr(uploaded, "content_type", None) or "").lower()
            if content_type and content_type not in (
                "text/csv",
                "text/plain",
                "application/vnd.ms-excel",
                "application/octet-stream",
            ):
                error = "Tipo de archivo no permitido. Sube un archivo CSV."
                return render(
                    request,
                    "trades/csv_import.html",
                    {"preview": preview, "error": error},
                )
            from apps.trades.services import MAX_CSV_BYTES

            if uploaded.size and uploaded.size > MAX_CSV_BYTES:
                error = f"El archivo excede el límite de {MAX_CSV_BYTES // 1024} KB."
                return render(
                    request,
                    "trades/csv_import.html",
                    {"preview": preview, "error": error},
                    status=413,
                )
            try:
                content = uploaded.read().decode("utf-8-sig")
            except UnicodeDecodeError:
                error = "El archivo no es un CSV de texto UTF-8 válido."
            else:
                if len(content) > MAX_CSV_BYTES:
                    error = f"El archivo excede el límite de {MAX_CSV_BYTES // 1024} KB."
                else:
                    result = import_csv(content, owner_id)
                    preview = result
                    if result["error_count"] == 0 and result["duplicate_count"] == 0:
                        error = f"Importados {result['created_count']} registros correctamente."
                    elif result["duplicate_count"] > 0:
                        error = (
                            f"Procesados {result['total']} filas. "
                            f"{result['created_count']} creadas, "
                            f"{result['duplicate_count']} duplicadas, "
                            f"{result['error_count']} errores."
                        )
                    else:
                        error_lines = "\n".join(result["errors"][:10])
                        error = (
                            f"Procesados {result['total']} filas. "
                            f"{result['created_count']} creadas, "
                            f"{result['error_count']} errores.\n"
                            f"Errores:\n{error_lines}"
                        )

    return render(
        request,
        "trades/csv_import.html",
        {"preview": preview, "error": error},
    )


@login_required
def csv_export(request: HttpRequest) -> HttpResponse:
    """Export CSV del usuario con anti spreadsheet-injection."""
    owner_id = request.user.pk
    assert owner_id is not None
    content = export_csv(owner_id)
    response = HttpResponse(content, content_type="text/csv; charset=utf-8")
    response["Content-Disposition"] = 'attachment; filename="observaciones.csv"'
    return response


@login_required
def dashboard(request: HttpRequest) -> HttpResponse:
    """Dashboard basico: totales Lucky vs normal."""
    owner_id = request.user.pk
    assert owner_id is not None
    stats = dashboard_stats(owner_id)
    return render(request, "trades/dashboard.html", {"stats": stats})
