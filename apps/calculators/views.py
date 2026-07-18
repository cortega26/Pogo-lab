from django.shortcuts import render

from .services import CalcInput, compute_scenario_cached, decode_share_url, encode_share_url


def calculator_view(request):
    """Vista principal de la calculadora.

    GET sin parametros -> formulario vacio.
    GET con ?share=<encoded> -> decodifica, calcula y muestra resultados.
    POST con datos del formulario -> calcula y devuelve partial HTMX.
    """
    result = None
    share_url = None
    error = None

    if request.method == "POST":
        try:
            inputs = _inputs_from_post(request.POST)
            result = compute_scenario_cached(inputs)
            share_url = encode_share_url(inputs)
        except ValueError as exc:
            error = str(exc)
            if request.headers.get("HX-Request"):
                return render(
                    request,
                    "calculators/_result.html",
                    {"result": None, "error": error},
                )
        else:
            if request.headers.get("HX-Request"):
                return render(
                    request,
                    "calculators/_result.html",
                    {"result": result, "share_url": share_url},
                )
    elif "share" in request.GET:
        try:
            inputs = decode_share_url(request.GET["share"])
            result = compute_scenario_cached(inputs)
            share_url = request.GET["share"]
        except (ValueError, KeyError) as exc:
            error = str(exc)

    status = 400 if error else 200
    return render(
        request,
        "calculators/page.html",
        {
            "result": result,
            "share_url": share_url,
            "error": error,
            "friendship_choices": FRIENDSHIP_CHOICES,
            "trade_type_choices": TRADE_TYPE_CHOICES,
            "target_choices": TARGET_CHOICES,
        },
        status=status,
    )


FRIENDSHIP_CHOICES = [
    ("good", "Good"),
    ("great", "Great"),
    ("ultra", "Ultra"),
    ("best", "Best"),
]

TRADE_TYPE_CHOICES = [
    ("normal", "Normal"),
    ("lucky", "Lucky"),
    ("lucky_guaranteed", "Lucky garantizado (amigos 90 d\u00edas+)"),
]

TARGET_CHOICES = [
    ("hundo", "Hundo (15/15/15)"),
    ("stat_min", "Stat individual >= X"),
    ("sum_min", "Suma de IV >= X"),
]


def _parse_int_in_range(raw: str | None, *, default: int, lo: int, hi: int, label: str) -> int:
    try:
        value = int(raw) if raw not in (None, "") else default
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} debe ser un número entero.") from exc
    if not lo <= value <= hi:
        raise ValueError(f"{label} debe estar entre {lo} y {hi}.")
    return value


def _parse_confidence(raw: str | None, *, default: float = 0.5) -> float:
    try:
        value = float(raw) if raw not in (None, "") else default
    except (TypeError, ValueError) as exc:
        raise ValueError("La confianza debe ser un número.") from exc
    if not 0.0 < value < 1.0:
        raise ValueError("La confianza debe estar entre 0 y 1 (exclusivo).")
    return value


def _inputs_from_post(post) -> CalcInput:
    return CalcInput(
        friendship_level=post.get("friendship_level", "good"),
        trade_type=post.get("trade_type", "normal"),
        n=_parse_int_in_range(post.get("n"), default=1, lo=1, hi=1_000_000, label="n"),
        target_kind=post.get("target_kind", "hundo"),
        threshold=_int_or_none(post.get("threshold")),
        confidence=_parse_confidence(post.get("confidence")),
    )


def _int_or_none(val: str | None) -> int | None:
    if val is None or val.strip() == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
