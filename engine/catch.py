"""Probabilidad de captura en Pokémon GO.

Procedencia: comunidad (Silph Road / GamePress, alta confianza).
Fórmula FOR008: P = 1 - (1 - BCR / (2 * CPM))^Multiplier.
El multiplier es producto de: ball * berry * curveball * throw * medal.
"""

from __future__ import annotations

from engine.stats import cpm_for_level


def catch_multiplier(
    ball: float = 1.0,
    berry: float = 1.0,
    curveball: float = 1.0,
    throw: float = 1.0,
    medal: float = 1.0,
) -> float:
    """Multiplicador total de captura (producto de modificadores).

    Args:
        ball: Multiplicador de la Poké Ball (1.0=normal, 1.5=ultra, 2.0=master).
        berry: Multiplicador de la baya (1.0=sin baya, 1.5=razz, 2.5=golden razz).
        curveball: Multiplicador por lanzamiento curvo (1.0=recto, 1.7=curvo).
        throw: Multiplicador por precisión (1.0=sin bonus, 1.15=Nice, 1.5=Great, 1.85=Excellent).
               En realidad es continuo: throw = 2 - r, donde r∈[0.1, 1.0] es el radio del círculo.
        medal: Multiplicador por medalla de tipo (1.0=sin medalla, 1.1=bronce, 1.2=plata, 1.3=oro, 1.4=platino).

    Returns:
        Multiplicador total (producto de los cinco factores).
    """
    return ball * berry * curveball * throw * medal


def catch_probability(
    bcr: float,
    level: float,
    multiplier: float,
) -> float:
    """Probabilidad de captura por lanzamiento (FOR008).

    P = 1 - (1 - BCR / (2 * CPM))^multiplier

    Args:
        bcr: Base Catch Rate de la especie (0.0 a 1.0).
        level: Nivel del Pokémon salvaje (determina el CPM).
        multiplier: Multiplicador total (producto de ball*berry*curveball*throw*medal).

    Returns:
        Probabilidad de captura en [0, 1].
    """
    cpm = cpm_for_level(level)
    inner = bcr / (2.0 * cpm)
    return 1.0 - (1.0 - min(inner, 1.0)) ** multiplier


def catch_probability_from_cpm(
    bcr: float,
    cpm: float,
    multiplier: float,
) -> float:
    """Probabilidad de captura usando CPM directamente (sin lookup de nivel).

    Args:
        bcr: Base Catch Rate.
        cpm: CpMultiplier del nivel.
        multiplier: Multiplicador total.

    Returns:
        Probabilidad de captura en [0, 1].
    """
    inner = bcr / (2.0 * cpm)
    return 1.0 - (1.0 - min(inner, 1.0)) ** multiplier


# ─── BCR por especie (Base Catch Rate) ────────────────────────────────────────
# Procedencia: comunidad (GamePress), verificada por datamining.
# No listadas: default 0.20.

BCR_DB: dict[str, float] = {
    "bulbasaur": 0.20, "charmander": 0.20, "squirtle": 0.20,
    "pikachu": 0.20, "caterpie": 0.40, "weedle": 0.40, "pidgey": 0.40,
    "rattata": 0.40, "spearow": 0.40, "ekans": 0.40,
    "zubat": 0.40, "oddish": 0.40, "paras": 0.30,
    "venonat": 0.40, "diglett": 0.40, "meowth": 0.40,
    "psyduck": 0.40, "mankey": 0.40, "growlithe": 0.30,
    "poliwag": 0.40, "abra": 0.40, "machop": 0.40,
    "bellsprout": 0.40, "tentacool": 0.40, "geodude": 0.40,
    "ponyta": 0.30, "slowpoke": 0.40, "magnemite": 0.30,
    "gastly": 0.30, "drowzee": 0.40, "krabby": 0.40,
    "voltorb": 0.40, "exeggcute": 0.40, "cubone": 0.30,
    "koffing": 0.40, "rhyhorn": 0.40, "horsea": 0.40,
    "goldeen": 0.40, "staryu": 0.40, "scyther": 0.30,
    "pinsir": 0.30, "magikarp": 0.70, "eevee": 0.40,
    "porygon": 0.30, "omanyte": 0.30, "kabuto": 0.30,
    "dratini": 0.30, "snorlax": 0.05, "lapras": 0.05,
    "aerodactyl": 0.05, "chansey": 0.10, "onix": 0.20,
    "ditto": 0.20, "tangela": 0.30, "lickitung": 0.20,
    "chikorita": 0.20, "cyndaquil": 0.20, "totodile": 0.20,
    "treecko": 0.20, "torchic": 0.20, "mudkip": 0.20,
    "venusaur": 0.05, "charizard": 0.05, "blastoise": 0.05,
    "dragonite": 0.05, "tyranitar": 0.05, "metagross": 0.05,
    "gengar": 0.10, "alakazam": 0.10, "machamp": 0.10,
    "gyarados": 0.10, "blissey": 0.05,
    "mewtwo": 0.02, "articuno": 0.02, "zapdos": 0.02,
    "moltres": 0.02, "lugia": 0.02, "ho_oh": 0.02,
    "raikou": 0.02, "entei": 0.02, "suicune": 0.02,
    "kyogre": 0.02, "groudon": 0.02, "rayquaza": 0.02,
    "dialga": 0.02, "palkia": 0.02, "giratina": 0.02,
    "heatran": 0.02, "cresselia": 0.02, "darkrai": 0.02,
    "swampert": 0.05, "blaziken": 0.05, "sceptile": 0.05,
    "gardevoir": 0.05, "lucario": 0.05, "garchomp": 0.05,
    "umbreon": 0.10, "azumarill": 0.10, "medicham": 0.10,
}


def get_bcr(species_id: str) -> float:
    """Devuelve el BCR de una especie; 0.20 si no está en la tabla."""
    return BCR_DB.get(species_id, 0.20)
