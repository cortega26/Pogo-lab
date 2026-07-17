"""Validacion de observaciones contra el modelo de re-roll uniforme.

Funciones puras del engine para verificar que los IVs observados son
consistentes con el modelo de re-roll uniforme en [f, 15].
"""


def ivs_consistent_with_floor(f: int, atk: int, def_: int, hp: int) -> bool:
    """True si (atk, def_, hp) son consistentes con re-roll uniforme en [f, 15].

    Es decir, los tres stats estan en [f, 15]. Un IV < f contradice el modelo.
    (No valida el rango 0..15; eso es validacion de datos de la app, no del modelo.)
    """
    return atk >= f and def_ >= f and hp >= f
