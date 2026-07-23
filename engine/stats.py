"""Cálculo de CP, HP y conversión de estadísticas base.

Procedencia: Game Master (datamining), comunidad (CPM table verificada).
Fuente canónica de base stats: Game Master (no conversión MSG→GO, que es aproximada).
"""

from __future__ import annotations

import math
from dataclasses import dataclass

# ─── CPM table ────────────────────────────────────────────────────────────────
# CpMultiplier por nivel (0.5 en 0.5), desde 1.0 hasta 55.0.
# Procedencia: comunidad (Silph Road / GamePress), verificada contra el Game Master.
# Confianza: alta. Versionado: reglas de redondeo de CP/HP (FOR006/FOR007).

CPM_TABLE: dict[float, float] = {
    1.0: 0.094,
    1.5: 0.135137432,
    2.0: 0.16639787,
    2.5: 0.192650919,
    3.0: 0.21573247,
    3.5: 0.236572661,
    4.0: 0.25572005,
    4.5: 0.273530381,
    5.0: 0.29024988,
    5.5: 0.306057377,
    6.0: 0.3210876,
    6.5: 0.335445036,
    7.0: 0.34921268,
    7.5: 0.362457751,
    8.0: 0.3752356,
    8.5: 0.387592416,
    9.0: 0.39956728,
    9.5: 0.411193551,
    10.0: 0.42250001,
    10.5: 0.432926419,
    11.0: 0.44310755,
    11.5: 0.453059958,
    12.0: 0.46279839,
    12.5: 0.472336083,
    13.0: 0.48168495,
    13.5: 0.4908558,
    14.0: 0.49985844,
    14.5: 0.508701765,
    15.0: 0.51739395,
    15.5: 0.525942511,
    16.0: 0.53435433,
    16.5: 0.542635767,
    17.0: 0.55079269,
    17.5: 0.558830576,
    18.0: 0.56675452,
    18.5: 0.574569153,
    19.0: 0.58227891,
    19.5: 0.589887917,
    20.0: 0.59740001,
    20.5: 0.604818814,
    21.0: 0.61215729,
    21.5: 0.619399365,
    22.0: 0.62656713,
    22.5: 0.633644533,
    23.0: 0.64065295,
    23.5: 0.647576426,
    24.0: 0.65443563,
    24.5: 0.661214806,
    25.0: 0.667934,
    25.5: 0.674577537,
    26.0: 0.68116492,
    26.5: 0.687680648,
    27.0: 0.69414365,
    27.5: 0.700538673,
    28.0: 0.70688421,
    28.5: 0.713164996,
    29.0: 0.71939909,
    29.5: 0.725571552,
    30.0: 0.7317,
    30.5: 0.734741009,
    31.0: 0.73776948,
    31.5: 0.740785574,
    32.0: 0.74378943,
    32.5: 0.746781211,
    33.0: 0.74976104,
    33.5: 0.752729087,
    34.0: 0.75568551,
    34.5: 0.758630378,
    35.0: 0.76156384,
    35.5: 0.764486065,
    36.0: 0.76739717,
    36.5: 0.770297266,
    37.0: 0.7731865,
    37.5: 0.776064962,
    38.0: 0.77893275,
    38.5: 0.781790055,
    39.0: 0.78463697,
    39.5: 0.787473578,
    40.0: 0.79030001,
    40.5: 0.79280395,
    41.0: 0.79530001,
    41.5: 0.79780392,
    42.0: 0.80030001,
    42.5: 0.80280389,
    43.0: 0.80530001,
    43.5: 0.80780387,
    44.0: 0.81030001,
    44.5: 0.81280384,
    45.0: 0.81530001,
    45.5: 0.81780382,
    46.0: 0.82030001,
    46.5: 0.8228038,
    47.0: 0.82530001,
    47.5: 0.82780378,
    48.0: 0.83030001,
    48.5: 0.83280375,
    49.0: 0.83530001,
    49.5: 0.83780373,
    50.0: 0.84030002,
    50.5: 0.84280371,
    51.0: 0.84530001,
    51.5: 0.84780364,
    52.0: 0.85030001,
    52.5: 0.85280357,
    53.0: 0.85530001,
    53.5: 0.85780351,
    54.0: 0.86030001,
    54.5: 0.86280345,
    55.0: 0.86530001,
}


def cpm_for_level(level: float) -> float:
    """Devuelve el CpMultiplier para un nivel dado.

    Args:
        level: Nivel del Pokémon (1.0 a 55.0, incrementos de 0.5).

    Returns:
        CpMultiplier correspondiente.

    Raises:
        ValueError: Si el nivel no está en la tabla CPM.
    """
    cpm = CPM_TABLE.get(level)
    if cpm is None:
        raise ValueError(f"Nivel {level} no encontrado en la tabla CPM.")
    return cpm


def effective_stat(base: int, iv: int, cpm: float) -> float:
    """Estadística efectiva de un Pokémon: (base + iv) * cpm.

    Args:
        base: Valor base de la especie (Atk/Def/Stam).
        iv: Valor IV individual (0 a 15).
        cpm: CpMultiplier del nivel.

    Returns:
        Estadística efectiva como flotante (sin redondeo).
    """
    return (base + iv) * cpm


def cp(
    base_atk: int, base_def: int, base_stam: int, iv_atk: int, iv_def: int, iv_stam: int, cpm: float
) -> int:
    """Calcula el CP (Puntos de Combate) según FOR006.

    CP = max(10, floor(Atk_eff * sqrt(Def_eff) * sqrt(Stam_eff) * CPM² / 10))

    Args:
        base_atk: Ataque base de la especie.
        base_def: Defensa base de la especie.
        base_stam: Stamina base de la especie.
        iv_atk: IV de ataque (0 a 15).
        iv_def: IV de defensa (0 a 15).
        iv_stam: IV de stamina (0 a 15).
        cpm: CpMultiplier del nivel.

    Returns:
        CP calculado (mínimo 10).
    """
    atk_eff = base_atk + iv_atk
    def_eff = base_def + iv_def
    stam_eff = base_stam + iv_stam

    raw = (atk_eff * math.sqrt(def_eff) * math.sqrt(stam_eff) * cpm * cpm) / 10.0
    return max(10, math.floor(raw))


def hp(base_stam: int, iv_stam: int, cpm: float) -> int:
    """Calcula los HP (Puntos de Vida) según FOR007.

    HP = max(10, floor(Stam_eff * CPM))

    Args:
        base_stam: Stamina base de la especie.
        iv_stam: IV de stamina (0 a 15).
        cpm: CpMultiplier del nivel.

    Returns:
        HP calculado (mínimo 10).
    """
    stam_eff = base_stam + iv_stam
    return max(10, math.floor(stam_eff * cpm))


def compute_cp_hp(
    base_atk: int,
    base_def: int,
    base_stam: int,
    iv_atk: int,
    iv_def: int,
    iv_stam: int,
    level: float,
) -> tuple[int, int]:
    """Conveniencia: calcula CP y HP para un nivel dado.

    Args:
        base_atk, base_def, base_stam: Estadísticas base de la especie.
        iv_atk, iv_def, iv_stam: IVs individuales (0 a 15).
        level: Nivel del Pokémon (1.0 a 55.0).

    Returns:
        Tupla (CP, HP).
    """
    cpm = cpm_for_level(level)
    return (
        cp(base_atk, base_def, base_stam, iv_atk, iv_def, iv_stam, cpm),
        hp(base_stam, iv_stam, cpm),
    )


@dataclass(frozen=True)
class SpeciesStats:
    """Estadísticas base inmutables de una especie (del Game Master)."""

    species_id: str
    base_atk: int
    base_def: int
    base_stam: int
    nerf_applied: bool = False


# ─── Fixtures de especies verificadas ─────────────────────────────────────────
# Usados en tests como golden vectors calculados a mano.
# Procedencia: Game Master (DAT001). No usar conversión MSG→GO.

MEWTWO = SpeciesStats(
    species_id="mewtwo",
    base_atk=300,
    base_def=182,
    base_stam=214,
    nerf_applied=True,
)

PIKACHU = SpeciesStats(
    species_id="pikachu",
    base_atk=112,
    base_def=95,
    base_stam=111,
    nerf_applied=False,
)

DRAGONITE = SpeciesStats(
    species_id="dragonite",
    base_atk=263,
    base_def=198,
    base_stam=209,
    nerf_applied=False,
)

MEDICHAM = SpeciesStats(
    species_id="medicham",
    base_atk=121,
    base_def=152,
    base_stam=155,
    nerf_applied=False,
)

CHARMANDER = SpeciesStats(
    species_id="charmander",
    base_atk=116,
    base_def=93,
    base_stam=118,
    nerf_applied=False,
)

SWAMPERT = SpeciesStats(
    species_id="swampert",
    base_atk=208,
    base_def=175,
    base_stam=225,
    nerf_applied=False,
)

AZUMARILL = SpeciesStats(
    species_id="azumarill",
    base_atk=112,
    base_def=152,
    base_stam=225,
    nerf_applied=False,
)

GENGAR = SpeciesStats(
    species_id="gengar",
    base_atk=261,
    base_def=149,
    base_stam=155,
    nerf_applied=False,
)

TYRANITAR = SpeciesStats(
    species_id="tyranitar",
    base_atk=251,
    base_def=207,
    base_stam=225,
    nerf_applied=False,
)

METAGROSS = SpeciesStats(
    species_id="metagross",
    base_atk=257,
    base_def=228,
    base_stam=190,
    nerf_applied=False,
)

RAYQUAZA = SpeciesStats(
    species_id="rayquaza",
    base_atk=284,
    base_def=170,
    base_stam=213,
    nerf_applied=True,
)

KYOGRE = SpeciesStats(
    species_id="kyogre",
    base_atk=270,
    base_def=228,
    base_stam=205,
    nerf_applied=True,
)

GROUDON = SpeciesStats(
    species_id="groudon",
    base_atk=270,
    base_def=228,
    base_stam=205,
    nerf_applied=True,
)

MACHAMP = SpeciesStats(
    species_id="machamp",
    base_atk=234,
    base_def=159,
    base_stam=207,
    nerf_applied=False,
)

GARDEVOIR = SpeciesStats(
    species_id="gardevoir",
    base_atk=237,
    base_def=195,
    base_stam=169,
    nerf_applied=False,
)

UMBREON = SpeciesStats(
    species_id="umbreon",
    base_atk=126,
    base_def=240,
    base_stam=216,
    nerf_applied=False,
)

LUCARIO = SpeciesStats(
    species_id="lucario",
    base_atk=236,
    base_def=144,
    base_stam=172,
    nerf_applied=False,
)

DIALGA = SpeciesStats(
    species_id="dialga",
    base_atk=275,
    base_def=211,
    base_stam=205,
    nerf_applied=True,
)

# ─── Base de datos de especies (canónica, generada desde dps_data) ─────────────


def _build_species_db() -> dict[str, SpeciesStats]:
    """Construye SPECIES_DB: primero desde dps_data (~159 especies), luego
    sobrescribe con especies definidas manualmente (stats verificados en Gate 0)."""
    db: dict[str, SpeciesStats] = {}

    # Base: dps_data.SPECIES (Game Master)
    try:
        from engine.dps_data import SPECIES as DPS_SPECIES

        for key, info in DPS_SPECIES.items():
            db[key] = SpeciesStats(
                species_id=key,
                base_atk=info.stats.atk,
                base_def=info.stats.def_,
                base_stam=info.stats.sta,
                nerf_applied=False,
            )
    except ImportError:
        pass

    # Override: especies verificadas manualmente (Gate 0)
    _manual: dict[str, SpeciesStats] = {
        "mewtwo": MEWTWO,
        "pikachu": PIKACHU,
        "dragonite": DRAGONITE,
        "medicham": MEDICHAM,
        "charmander": CHARMANDER,
        "swampert": SWAMPERT,
        "azumarill": AZUMARILL,
        "gengar": GENGAR,
        "tyranitar": TYRANITAR,
        "metagross": METAGROSS,
        "rayquaza": RAYQUAZA,
        "kyogre": KYOGRE,
        "groudon": GROUDON,
        "machamp": MACHAMP,
        "gardevoir": GARDEVOIR,
        "umbreon": UMBREON,
        "lucario": LUCARIO,
        "dialga": DIALGA,
    }
    db.update(_manual)
    return db


SPECIES_DB: dict[str, SpeciesStats] = _build_species_db()

SPECIES_CHOICES: list[tuple[str, str]] = sorted(
    [(k, v.species_id.replace("_", " ").title()) for k, v in SPECIES_DB.items()],
    key=lambda x: x[1],
)
