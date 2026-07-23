from django.shortcuts import render

from engine.breakpoints import find_breakpoints
from engine.catch import catch_multiplier, catch_probability
from engine.costs import power_up_cost
from engine.dps_data import FAST_MOVES as FM
from engine.dps_data import SPECIES as DPS_SPECIES
from engine.probability import p_at_least_one, p_zero, trades_for_confidence
from engine.pvp_rank import top_spreads
from engine.shadow import compare_shadow_purified
from engine.stats import SPECIES_CHOICES, SPECIES_DB, compute_cp_hp
from engine.types import PokemonType, weaknesses

from .services import (
    CalcInput,
    compute_scenario_cached,
    decode_calc_share,
    decode_share_url,
    encode_calc_share,
    encode_share_url,
)

# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de IV (existente)
# ══════════════════════════════════════════════════════════════════════════════


def calculator_view(request):
    """Vista principal de la calculadora de IV en intercambios."""
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
    ("lucky_guaranteed", "Lucky garantizado (amigos 90 días+)"),
]

TARGET_CHOICES = [
    ("hundo", "Hundo (15/15/15)"),
    ("stat_min", "Stat individual >= X"),
    ("sum_min", "Suma de IV >= X"),
]


def _parse_int_in_range(raw, *, default, lo, hi, label):
    try:
        value = int(raw) if raw not in (None, "") else default
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} debe ser un número entero.") from exc
    if not lo <= value <= hi:
        raise ValueError(f"{label} debe estar entre {lo} y {hi}.")
    return value


def _parse_confidence(raw, *, default=0.5):
    try:
        value = float(raw) if raw not in (None, "") else default
    except (TypeError, ValueError) as exc:
        raise ValueError("La confianza debe ser un número.") from exc
    if not 0.0 < value < 1.0:
        raise ValueError("La confianza debe estar entre 0 y 1 (exclusivo).")
    return value


def _inputs_from_post(post):
    return CalcInput(
        friendship_level=post.get("friendship_level", "good"),
        trade_type=post.get("trade_type", "normal"),
        n=_parse_int_in_range(post.get("n"), default=1, lo=1, hi=1_000_000, label="n"),
        target_kind=post.get("target_kind", "hundo"),
        threshold=_int_or_none(post.get("threshold")),
        confidence=_parse_confidence(post.get("confidence")),
    )


def _int_or_none(val):
    if val is None or val.strip() == "":
        return None
    try:
        return int(val)
    except (ValueError, TypeError):
        return None


def _float_or(val, default):
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return default
    try:
        return float(val)
    except (ValueError, TypeError):
        return default


def _int_or_default(val, default=0):
    """Convierte a int de forma segura; si falla devuelve default."""
    if val is None or (isinstance(val, str) and val.strip() == ""):
        return default
    try:
        return int(val)
    except (ValueError, TypeError):
        return default


def _get_params(request, _calc_type, defaults):
    """Extrae params de POST, share URL o defaults."""
    if request.method == "POST":
        return dict(request.POST.items())
    if "share" in request.GET:
        try:
            _, params = decode_calc_share(request.GET["share"])
            return params
        except ValueError:
            pass
    return dict(defaults)


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de CP & Nivel
# ══════════════════════════════════════════════════════════════════════════════

LEVEL_CHOICES = [
    (f"{lv:.1f}", f"{lv:.1f}")
    for lv in [1.0, 5.0, 10.0, 15.0, 20.0, 25.0, 30.0, 35.0, 40.0, 45.0, 50.0]
]


def cp_calculator_view(request):
    params = _get_params(request, "cp", {})
    ctx = _cp_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("cp", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_cp_result.html", ctx)
    return render(request, "calculators/cp_page.html", ctx)


def _cp_result(params):
    error = None
    result = None
    species_id = params.get("species", "pikachu")
    level = _float_or(params.get("level"), 20.0)
    iv_atk = _int_or_default(params.get("iv_atk"), 10)
    iv_def = _int_or_default(params.get("iv_def"), 10)
    iv_stam = _int_or_default(params.get("iv_stam"), 10)

    if params:
        try:
            iv_atk = _parse_int_in_range(str(iv_atk), default=10, lo=0, hi=15, label="IV Ataque")
            iv_def = _parse_int_in_range(str(iv_def), default=10, lo=0, hi=15, label="IV Defensa")
            iv_stam = _parse_int_in_range(str(iv_stam), default=10, lo=0, hi=15, label="IV Stamina")

            species = SPECIES_DB.get(species_id, SPECIES_DB["pikachu"])
            cp_val, hp_val = compute_cp_hp(
                species.base_atk,
                species.base_def,
                species.base_stam,
                iv_atk,
                iv_def,
                iv_stam,
                level,
            )

            result = {
                "species": species_id,
                "level": level,
                "iv_atk": iv_atk,
                "iv_def": iv_def,
                "iv_stam": iv_stam,
                "cp": cp_val,
                "hp": hp_val,
                "atk_eff": species.base_atk + iv_atk,
                "def_eff": species.base_def + iv_def,
                "stam_eff": species.base_stam + iv_stam,
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    return {
        "error": error,
        "result": result,
        "species_choices": SPECIES_CHOICES,
        "level_choices": LEVEL_CHOICES,
        "species_id": species_id,
        "level": level,
        "iv_atk": iv_atk,
        "iv_def": iv_def,
        "iv_stam": iv_stam,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de Costo de Power-Up
# ══════════════════════════════════════════════════════════════════════════════


def cost_calculator_view(request):
    params = _get_params(request, "cost", {})
    ctx = _cost_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("cost", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_cost_result.html", ctx)
    return render(request, "calculators/cost_page.html", ctx)


def _cost_result(params):
    error = None
    result = None
    from_level = _float_or(params.get("from_level"), 20.0)
    to_level = _float_or(params.get("to_level"), 40.0)
    is_lucky = params.get("is_lucky", "") in ("1", "true", "True")
    is_shadow = params.get("is_shadow", "") in ("1", "true", "True")

    if params:
        try:
            cost = power_up_cost(from_level, to_level, is_lucky=is_lucky, is_shadow=is_shadow)
            result = {
                "from_level": from_level,
                "to_level": to_level,
                "total_stardust": cost.total_stardust,
                "total_candy": cost.total_candy,
                "total_candy_xl": cost.total_candy_xl,
                "power_ups": cost.power_ups,
                "is_lucky": is_lucky,
                "is_shadow": is_shadow,
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    return {
        "error": error,
        "result": result,
        "level_choices": LEVEL_CHOICES,
        "from_level": from_level,
        "to_level": to_level,
        "is_lucky": is_lucky,
        "is_shadow": is_shadow,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de PvP IV Ranker
# ══════════════════════════════════════════════════════════════════════════════

LEAGUE_CHOICES = [
    ("1500", "Great League (1500 CP)"),
    ("2500", "Ultra League (2500 CP)"),
    ("10000", "Master League (sin límite)"),
]


def pvp_ranker_view(request):
    params = _get_params(request, "pvp", {})
    ctx = _pvp_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("pvp", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_pvp_result.html", ctx)
    return render(request, "calculators/pvp_page.html", ctx)


def _pvp_result(params):
    error = None
    result = None
    species_id = params.get("species", "medicham")
    league_cap = _int_or_default(params.get("league"), 1500)

    if params:
        try:
            species = SPECIES_DB.get(species_id, SPECIES_DB["medicham"])
            ranking = top_spreads(
                species.base_atk,
                species.base_def,
                species.base_stam,
                max_cp=league_cap,
                n=25,
            )
            result = {
                "species": species_id,
                "league": league_cap,
                "league_name": dict(LEAGUE_CHOICES).get(str(league_cap), ""),
                "spreads": [
                    {
                        "rank": i + 1,
                        "atk": s.atk_iv,
                        "def": s.def_iv,
                        "stam": s.stam_iv,
                        "level": f"{s.level:.1f}",
                        "cp": s.cp_value,
                        "stat_product": s.stat_product,
                    }
                    for i, s in enumerate(ranking)
                ],
                "total_ranked": len(ranking),
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    return {
        "error": error,
        "result": result,
        "species_choices": SPECIES_CHOICES,
        "league_choices": LEAGUE_CHOICES,
        "species_id": species_id,
        "league_cap": league_cap,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de Captura
# ══════════════════════════════════════════════════════════════════════════════

BALL_CHOICES = [
    ("1.0", "Poké Ball"),
    ("1.5", "Super Ball"),
    ("2.0", "Ultra Ball"),
]

BERRY_CHOICES = [
    ("1.0", "Sin baya"),
    ("1.5", "Baya Frambu"),
    ("2.5", "Baya Frambu Dorada"),
]

THROW_CHOICES = [
    ("1.0", "Normal"),
    ("1.15", "Nice"),
    ("1.5", "Great"),
    ("1.85", "Excellent"),
]

MEDAL_CHOICES = [
    ("1.0", "Sin medalla"),
    ("1.1", "Bronce"),
    ("1.2", "Plata"),
    ("1.3", "Oro"),
    ("1.4", "Platino"),
]


def catch_calculator_view(request):
    params = _get_params(request, "catch", {})
    ctx = _catch_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("catch", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_catch_result.html", ctx)
    return render(request, "calculators/catch_page.html", ctx)


def _catch_result(params):
    error = None
    result = None
    species_id = params.get("species", "charmander")
    level = _float_or(params.get("level"), 15.0)
    ball = _float_or(params.get("ball"), 1.0)
    berry = _float_or(params.get("berry"), 1.5)
    curveball = 1.7 if params.get("curveball", "") in ("1", "true") else 1.0
    throw = _float_or(params.get("throw"), 1.15)
    medal = _float_or(params.get("medal"), 1.3)

    if params:
        try:
            mult = catch_multiplier(
                ball=ball, berry=berry, curveball=curveball, throw=throw, medal=medal
            )
            from engine.catch import get_bcr

            bcr = get_bcr(species_id)
            if species_id == "mewtwo":
                level = 20.0

            prob = catch_probability(bcr=bcr, level=level, multiplier=mult)

            result = {
                "species": species_id,
                "bcr": bcr,
                "level": level,
                "ball": ball,
                "berry": berry,
                "curveball": curveball,
                "throw": throw,
                "medal": medal,
                "multiplier": round(mult, 4),
                "probability": round(prob * 100, 2),
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    return {
        "error": error,
        "result": result,
        "species_choices": SPECIES_CHOICES,
        "level_choices": LEVEL_CHOICES,
        "ball_choices": BALL_CHOICES,
        "berry_choices": BERRY_CHOICES,
        "throw_choices": THROW_CHOICES,
        "medal_choices": MEDAL_CHOICES,
        "species_id": species_id,
        "level": level,
        "ball": ball,
        "berry": berry,
        "curveball": curveball,
        "throw": throw,
        "medal": medal,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de Tipos
# ══════════════════════════════════════════════════════════════════════════════

TYPE_CHOICES = [(t.value, t.value.capitalize()) for t in PokemonType]

EFFECTIVENESS_LABELS = {
    2.56: "2.56× (doble súper efectivo)",
    1.6: "1.6× (súper efectivo)",
    1.0: "1× (neutro)",
    0.625: "0.625× (poco efectivo)",
    0.390625: "0.39× (doble resistencia)",
}


def type_calculator_view(request):
    params = _get_params(request, "types", {})
    ctx = _type_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("types", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_type_result.html", ctx)
    return render(request, "calculators/type_page.html", ctx)


def _type_result(params):
    error = None
    result = None
    def1 = params.get("def_type1", "dragon")
    def2 = params.get("def_type2", "") or None

    if params:
        try:
            t1 = PokemonType(def1)
            t2 = PokemonType(def2) if def2 else None
            w = weaknesses(t1, t2)

            result = {
                "def_type1": def1,
                "def_type2": def2,
                "weaknesses": [
                    {
                        "type": atk.value,
                        "effectiveness": eff,
                        "label": _eff_label(eff),
                    }
                    for atk, eff in sorted(w.items(), key=lambda x: -x[1])
                ],
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    return {
        "error": error,
        "result": result,
        "type_choices": TYPE_CHOICES,
        "def_type1": def1,
        "def_type2": def2,
    }


def _eff_label(eff):
    for threshold, label in sorted(EFFECTIVENESS_LABELS.items(), reverse=True):
        if abs(eff - threshold) < 0.001:
            return label
    return f"{eff:.3f}×"


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de Shiny (CALC014) — reutiliza engine/probability
# ══════════════════════════════════════════════════════════════════════════════

SHINY_RATES = [
    ("0.002", "1/500 — Estándar"),
    ("0.008", "1/125 — Permaboost"),
    ("0.02", "1/50 — Día de Comunidad"),
    ("0.05", "1/20 — Legendario shiny"),
    ("0.1", "1/10 — Evento especial"),
]


def shiny_calculator_view(request):
    params = _get_params(request, "shiny", {})
    ctx = _shiny_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("shiny", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_shiny_result.html", ctx)
    return render(request, "calculators/shiny_page.html", ctx)


def _shiny_result(params):
    error = None
    result = None
    rate = _float_or(params.get("rate"), 0.002)
    n_encounters = _int_or_default(params.get("n"), 100)
    confidence = _float_or(params.get("confidence"), 0.95)

    if params:
        try:
            p = p_at_least_one(rate, n_encounters)
            p0 = p_zero(rate, n_encounters)
            for_conf = trades_for_confidence(rate, confidence)
            expected = n_encounters * rate

            result = {
                "rate": rate,
                "rate_label": dict(SHINY_RATES).get(f"{rate:.3f}", ""),
                "n": n_encounters,
                "confidence": confidence,
                "probability": round(p * 100, 2),
                "p_zero": round(p0 * 100, 2),
                "expected_shinies": round(expected, 1),
                "encounters_for_confidence": for_conf,
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    return {
        "error": error,
        "result": result,
        "rate_choices": SHINY_RATES,
        "confidence_choices": CONFIDENCE_CHOICES,
        "rate": rate,
        "n": n_encounters,
        "confidence": confidence,
    }


CONFIDENCE_CHOICES = [
    ("0.5", "50%"),
    ("0.75", "75%"),
    ("0.9", "90%"),
    ("0.95", "95%"),
    ("0.99", "99%"),
]


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora Shadow vs Purified (CALC019)
# ══════════════════════════════════════════════════════════════════════════════


def shadow_calculator_view(request):
    params = _get_params(request, "shadow", {})
    ctx = _shadow_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("shadow", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_shadow_result.html", ctx)
    return render(request, "calculators/shadow_page.html", ctx)


def _shadow_result(params):
    error = None
    result = None
    species_id = params.get("species", "machamp")
    level = _float_or(params.get("level"), 40.0)
    iv_atk = _int_or_default(params.get("iv_atk"), 15)
    iv_def = _int_or_default(params.get("iv_def"), 15)
    iv_stam = _int_or_default(params.get("iv_stam"), 15)

    if params:
        try:
            species = SPECIES_DB.get(species_id, SPECIES_DB["machamp"])
            r = compare_shadow_purified(
                species.base_atk,
                species.base_def,
                species.base_stam,
                iv_atk,
                iv_def,
                iv_stam,
                level,
                from_level=1.0,
                species_name=species_id,
            )
            result = {
                "species": species_id,
                "level": level,
                "iv_atk": r.iv_atk,
                "iv_def": r.iv_def,
                "iv_stam": r.iv_stam,
                "cp": r.cp_purified,
                "hp": r.hp_purified,
                "atk_purified": r.atk_purified,
                "atk_shadow": r.atk_shadow,
                "atk_ratio": r.atk_ratio,
                "damage_advantage": r.shadow_damage_advantage_pct(),
                "dust_purified": r.dust_purified,
                "dust_shadow": r.dust_shadow,
                "candy_purified": r.candy_purified,
                "candy_shadow": r.candy_shadow,
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    return {
        "error": error,
        "result": result,
        "species_choices": SPECIES_CHOICES,
        "level_choices": LEVEL_CHOICES,
        "species_id": species_id,
        "level": level,
        "iv_atk": iv_atk,
        "iv_def": iv_def,
        "iv_stam": iv_stam,
    }


# ══════════════════════════════════════════════════════════════════════════════
# Calculadora de Breakpoints PvE (CALC007)
# ══════════════════════════════════════════════════════════════════════════════


def breakpoints_view(request):
    params = _get_params(request, "breakpoints", {})
    ctx = _breakpoints_result(params)
    if params:
        ctx["share_url"] = encode_calc_share("breakpoints", params)
    if isinstance(ctx, dict) and request.headers.get("HX-Request"):
        return render(request, "calculators/_breakpoints_result.html", ctx)
    return render(request, "calculators/breakpoints_page.html", ctx)


def _breakpoints_result(params):
    error = None
    result = None
    species_id = params.get("species", "mewtwo")
    move_key = params.get("move", "psycho_cut")
    iv_atk = _int_or_default(params.get("iv_atk"), 15)
    defender_def = _float_or(params.get("defender_def"), 200.0)
    weather = params.get("weather", "") in ("1", "true")

    if params:
        try:
            bps = find_breakpoints(
                species_id,
                move_key,
                iv_atk,
                defender_def,
                weather_boosted=weather,
                max_results=15,
            )
            result = {
                "species": species_id,
                "move": move_key,
                "iv_atk": iv_atk,
                "defender_def": int(defender_def),
                "weather": weather,
                "breakpoints": [
                    {"level": f"{b.level:.1f}", "damage": b.damage, "atk": b.atk_effective}
                    for b in bps
                ],
            }
        except (ValueError, KeyError) as exc:
            error = str(exc)

    move_choices = _move_choices_for(species_id)

    return {
        "error": error,
        "result": result,
        "species_choices": SPECIES_CHOICES,
        "move_choices": move_choices or [("psycho_cut", "Psycho Cut")],
        "species_id": species_id,
        "move_key": move_key,
        "iv_atk": iv_atk,
        "defender_def": defender_def,
        "weather": weather,
    }


def _move_choices_for(species_key):
    sp = DPS_SPECIES.get(species_key)
    if sp is None:
        return []
    choices = []
    for key, move in FM.items():
        choices.append((key, f"{move.name} ({move.type})"))
    return sorted(choices, key=lambda x: x[1])
