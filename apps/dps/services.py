"""Servicios de la app DPS: orquestan la lógica entre engine y vistas."""

from engine.dps import (
    DamageResult,
    rank_by_type,
)
from engine.dps_data import (
    ALL_TYPES,
    CHARGE_MOVES,
    EFFECTIVENESS,
    FAST_MOVES,
    SPECIES,
    TYPE_COLORS,
    PokemonType,
    type_multiplier,
)


def _type_color(tipo: str) -> str:
    try:
        return TYPE_COLORS[PokemonType(tipo)]
    except (ValueError, KeyError):
        return "#888888"


def get_type_stats(tipo: str | None = None) -> list[dict]:
    if tipo:
        ranked = rank_by_type(tipo, level=40)
        color = _type_color(tipo)
        return [
            {
                "key": tipo,
                "name": tipo.capitalize(),
                "color": color,
                "count": len(ranked),
            }
        ]
    types: list[dict] = []
    for t in sorted(ALL_TYPES):
        ranked = rank_by_type(t, level=40)
        types.append(
            {
                "key": t,
                "name": t.capitalize(),
                "color": _type_color(t),
                "count": len(ranked),
            }
        )
    return types


def _build_string_type_colors():
    return {pt.value: color for pt, color in TYPE_COLORS.items()}


_STR_TYPE_COLORS = _build_string_type_colors()


def get_type_color(tipo: str) -> str:
    return _STR_TYPE_COLORS.get(tipo, "#888888")


def _build_attackers(
    ranked: list[tuple[str, DamageResult]],
    level: int = 40,
    tipo: str | None = None,
) -> list[dict]:
    attackers = []
    defender_type1 = tipo if tipo else "normal"
    for species_key, dr in ranked:
        species = SPECIES[species_key]
        fast = FAST_MOVES.get(dr.fast_move_key)
        charge = CHARGE_MOVES.get(dr.charge_move_key)
        types = [species.type1]
        if species.type2:
            types.append(species.type2)
        attackers.append(
            {
                "species": {
                    "key": species_key,
                    "dex": species.dex,
                    "name": species.name,
                    "type1": species.type1,
                    "type2": species.type2,
                    "stats": species.stats,
                },
                "fast_move": fast,
                "charge_move": charge,
                "cycle_dps": dr.cycle_dps,
                "tdo": dr.tdo,
                "edps": dr.edps,
                "stab": dr.stab,
                "level": level,
                "target_type": defender_type1,
                "types": types,
            }
        )
    return attackers


def get_type_attackers(tipo: str, limit: int = 10, level: int = 40) -> list[dict]:
    ranked = rank_by_type(tipo, level=level)
    ranked = ranked[:limit]
    return _build_attackers(ranked, level=level, tipo=tipo)


def get_type_attackers_filtered_sorted(
    tipo: str,
    sort_by: str = "dps",
    type_filter: str | None = None,
    level: int = 40,
) -> list[dict]:
    ranked = rank_by_type(tipo, level=level)
    attackers = _build_attackers(ranked, level=level, tipo=tipo)

    if type_filter:
        attackers = [
            a for a in attackers if type_filter in {a["species"]["type1"], a["species"]["type2"]}
        ]

    if sort_by == "tdo":
        attackers.sort(key=lambda a: a["tdo"], reverse=True)
    elif sort_by == "name":
        attackers.sort(key=lambda a: a["species"]["name"])
    elif sort_by == "edps":
        attackers.sort(key=lambda a: a["edps"], reverse=True)
    else:
        attackers.sort(key=lambda a: a["cycle_dps"], reverse=True)

    return attackers


def get_all_types() -> list[str]:
    return sorted(ALL_TYPES)


def get_type_effectiveness(tipo: str) -> list[dict]:
    results: list[dict] = []
    for (atk, dfn), mult in EFFECTIVENESS.items():
        if atk == tipo and mult != 1.0:
            color = _type_color(dfn)
            results.append({"type": dfn, "mult": mult, "color": color})
    results.sort(key=lambda x: x["type"])
    return results


def get_type_move_effectiveness(tipo: str) -> list[dict]:
    results: list[dict] = []
    for other in sorted(ALL_TYPES):
        mult = type_multiplier(tipo, other, None)
        color = _type_color(other)
        results.append({"type": other, "mult": mult, "color": color})
    return results


def get_move_list() -> list[dict]:
    moves: list[dict] = []
    for key, fm in FAST_MOVES.items():
        moves.append(
            {
                "key": key,
                "name": fm.name,
                "type": fm.type,
                "kind": "fast",
                "power": fm.power,
                "duration_ticks": fm.duration_ticks,
                "duration_s": fm.duration_ticks * 0.5,
                "energy_gain": fm.energy_gain,
                "energy_cost": 0,
                "dps": round(fm.power / max(fm.duration_ticks * 0.5, 0.1), 2)
                if fm.power > 0
                else 0,
                "eps": round(fm.energy_gain / max(fm.duration_ticks * 0.5, 0.1), 2)
                if fm.energy_gain > 0
                else 0,
            }
        )
    for key, cm in CHARGE_MOVES.items():
        duration = max(cm.duration_ticks * 0.5, 0.5)
        moves.append(
            {
                "key": key,
                "name": cm.name,
                "type": cm.type,
                "kind": "charge",
                "power": cm.power,
                "duration_ticks": cm.duration_ticks,
                "duration_s": round(duration, 1),
                "energy_gain": 0,
                "energy_cost": cm.energy_cost,
                "dps": round(cm.power / duration, 2) if cm.power > 0 else 0,
                "eps": 0,
                "dpe": round(cm.power / cm.energy_cost, 2) if cm.energy_cost > 0 else 0,
            }
        )
    moves.sort(key=lambda x: x["dps"], reverse=True)
    return moves
