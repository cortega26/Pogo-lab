"""Vistas de la app DPS."""

from django.http import Http404
from django.shortcuts import render

from engine.dps import (
    compute_best_moveset,
)
from engine.dps_data import (
    ALL_TYPES,
    CHARGE_MOVES,
    FAST_MOVES,
    SPECIES,
)

from .services import (
    get_move_list,
    get_type_attackers_filtered_sorted,
    get_type_effectiveness,
    get_type_move_effectiveness,
    get_type_stats,
)


def _parse_level(raw: str | None, default: int = 40) -> int:
    try:
        return int(raw) if raw not in (None, "") else default
    except (ValueError, TypeError):
        return default


def dps_browser(request):
    attack_type = request.GET.get("tipo", "")
    sort_by = request.GET.get("sort", "dps")
    level = _parse_level(request.GET.get("level"), 40)
    search_q = request.GET.get("q", "").strip().lower()

    type_stats = get_type_stats()
    effectiveness = {}
    move_effectiveness = []
    attackers = []

    if attack_type and attack_type in ALL_TYPES:
        attackers = get_type_attackers_filtered_sorted(
            attack_type,
            sort_by=sort_by,
            type_filter=None,
            level=level,
        )
        if search_q:
            attackers = [a for a in attackers if search_q in a["species"]["name"].lower()]
        effectiveness_raw = get_type_effectiveness(attack_type)
        move_effectiveness = get_type_move_effectiveness(attack_type)
        effectiveness = {e["type"]: e["mult"] for e in effectiveness_raw}

    context = {
        "attack_type": attack_type if attack_type in ALL_TYPES else "",
        "attack_type_name": attack_type.capitalize() if attack_type else "",
        "type_stats": type_stats,
        "attackers": attackers,
        "sort_by": sort_by,
        "type_filter": "",
        "effectiveness": effectiveness,
        "move_effectiveness": move_effectiveness,
        "level": level,
        "search_q": request.GET.get("q", ""),
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "dps/_ranking.html", context)
    return render(request, "dps/page.html", context)


def dps_by_type(request, tipo: str):
    tipo_lower = tipo.lower()
    if tipo_lower not in ALL_TYPES:
        raise Http404()

    level = _parse_level(request.GET.get("level"), 40)
    sort_by = request.GET.get("sort", "dps")
    type_filter = request.GET.get("type_filter", "")
    search_q = request.GET.get("q", "").strip().lower()

    attackers = get_type_attackers_filtered_sorted(
        tipo_lower,
        sort_by=sort_by,
        type_filter=type_filter or None,
        level=level,
    )
    if search_q:
        attackers = [a for a in attackers if search_q in a["species"]["name"].lower()]

    type_stats = get_type_stats()
    effectiveness_raw = get_type_effectiveness(tipo_lower)
    move_effectiveness = get_type_move_effectiveness(tipo_lower)
    effectiveness = {e["type"]: e["mult"] for e in effectiveness_raw}

    context = {
        "attack_type": tipo_lower,
        "attack_type_name": tipo_lower.capitalize(),
        "type_stats": type_stats,
        "attackers": attackers,
        "sort_by": sort_by,
        "type_filter": type_filter,
        "effectiveness": effectiveness,
        "move_effectiveness": move_effectiveness,
        "level": level,
        "search_q": request.GET.get("q", ""),
    }

    if request.headers.get("HX-Request") == "true":
        return render(request, "dps/_ranking.html", context)
    return render(request, "dps/page.html", context)


def move_browser(request):
    moves = get_move_list()
    sort = request.GET.get("sort", "dps")
    kind_filter = request.GET.get("kind", "")

    if kind_filter == "fast":
        moves = [m for m in moves if m["kind"] == "fast"]
    elif kind_filter == "charge":
        moves = [m for m in moves if m["kind"] == "charge"]

    if sort == "name":
        moves.sort(key=lambda m: m["name"])
    elif sort == "power":
        moves.sort(key=lambda m: m["power"], reverse=True)
    elif sort == "duration":
        moves.sort(key=lambda m: m["duration_s"])
    elif sort == "type":
        moves.sort(key=lambda m: m["type"])
    else:
        moves.sort(key=lambda m: m["dps"], reverse=True)

    context = {
        "moves": moves,
        "sort": sort,
        "kind_filter": kind_filter,
        "pagina_titulo": "Explorador de movimientos",
    }
    return render(request, "dps/moves.html", context)


def pokemon_compare(request):
    a_key = request.GET.get("a", "").strip().lower()
    b_key = request.GET.get("b", "").strip().lower()
    level = _parse_level(request.GET.get("level"), 40)

    def build(species_key: str) -> dict | None:
        if species_key not in SPECIES:
            return None
        dr = compute_best_moveset(species_key, level=level)
        if dr is None:
            return None
        species = SPECIES[species_key]
        return {
            "species_key": species_key,
            "name": species.name,
            "type1": species.type1,
            "type2": species.type2,
            "dex": species.dex,
            "atk": species.stats.atk,
            "def_": species.stats.def_,
            "sta": species.stats.sta,
            "fast_move": FAST_MOVES.get(dr.fast_move_key),
            "charge_move": CHARGE_MOVES.get(dr.charge_move_key),
            "dps": dr.cycle_dps,
            "tdo": dr.tdo,
            "edps": dr.edps,
            "hp": dr.hp,
            "fast_dps": dr.fast_dps,
            "charge_dps": dr.charge_dps,
            "stab": dr.stab,
        }

    left = build(a_key) if a_key else None
    right = build(b_key) if b_key else None

    context = {
        "left": left,
        "right": right,
        "level": level,
        "pagina_titulo": "Comparar Pokémon",
    }
    return render(request, "dps/compare.html", context)
