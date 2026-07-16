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
        inputs = _inputs_from_post(request.POST)
        result = compute_scenario_cached(inputs)
        share_url = encode_share_url(inputs)
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


def _inputs_from_post(post) -> CalcInput:
    return CalcInput(
        friendship_level=post.get("friendship_level", "good"),
        trade_type=post.get("trade_type", "normal"),
        n=int(post.get("n", 1)),
        target_kind=post.get("target_kind", "hundo"),
        threshold=_int_or_none(post.get("threshold")),
        confidence=float(post.get("confidence", 0.5)),
    )


def _int_or_none(val: str | None) -> int | None:
    if val is None or val.strip() == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None
