"""Gate anti-duplicación de datos de combate (Plan 046, paso 6).

Falla si aparece, en cualquier módulo de `engine/` distinto de
`engine/types.py`, un diccionario literal grande cuyas claves sean tuplas
de 2 elementos — el patrón exacto de la tabla de efectividad duplicada que
este plan eliminó de `engine/dps_data.py`. El objetivo es que una futura
edición no reintroduzca una segunda tabla 18x18 a mano.
"""

import ast
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent.parent
ALLOWED_FILES = {"types.py"}
# La tabla de efectividad real tiene 100+ entradas no neutras; cualquier
# literal de este tamaño con claves de 2-tupla es sospechoso de ser una
# copia manual de la matriz de tipos.
SUSPICIOUS_ENTRY_THRESHOLD = 40


def _iter_engine_source_files():
    for path in ENGINE_DIR.glob("*.py"):
        if path.name in ALLOWED_FILES or path.name.startswith("test_"):
            continue
        yield path


def _dict_has_only_tuple_pair_keys(node: ast.Dict) -> bool:
    if not node.keys:
        return False
    return all(isinstance(k, ast.Tuple) and len(k.elts) == 2 for k in node.keys if k is not None)


def test_no_hardcoded_18x18_type_chart_outside_types_module():
    offenders = []
    for path in _iter_engine_source_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Dict)
                and len(node.keys) >= SUSPICIOUS_ENTRY_THRESHOLD
                and _dict_has_only_tuple_pair_keys(node)
            ):
                offenders.append(f"{path.name}:{node.lineno}")

    assert not offenders, (
        "Diccionario literal grande con claves de 2-tupla fuera de "
        f"engine/types.py (posible tabla de tipos duplicada): {offenders}"
    )
