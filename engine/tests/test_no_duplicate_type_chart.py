"""Gate anti-duplicación de datos de combate (Plan 046, paso 6).

Falla si aparece, en cualquier módulo de `engine/` distinto de
`engine/types.py`, una matriz de tipos 18x18 reconstruida a mano — el
patrón exacto del bug que este plan corrigió en `engine/dps_data.py`.
Detecta las dos formas en que ese patrón se puede escribir en Python:

1. Un diccionario literal grande con claves de 2-tupla (la forma que tenía
   `dps_data.TYPE_EFFECTIVENESS` antes de este plan).
2. Muchas asignaciones por doble subíndice sobre el mismo nombre
   (`TABLA[a][b] = valor`) — la forma que usa `engine/types.py` para
   construir su propia tabla. Si otro módulo reconstruye una tabla así
   fuera de `types.py`, también es una duplicación real.

Ningún archivo de `engine/` fuera de `types.py` usa hoy ninguno de los dos
patrones por encima del umbral (verificado con un grep exhaustivo al
escribir este gate), así que ambos umbrales tienen margen para no ser
falsos positivos ante asignaciones dobles incidentales y no relacionadas.
"""

import ast
from collections import Counter
from pathlib import Path

ENGINE_DIR = Path(__file__).resolve().parent.parent
ALLOWED_FILES = {"types.py"}

# La tabla de efectividad real tiene 100+ entradas no neutras; cualquier
# literal de este tamaño con claves de 2-tupla es sospechoso de ser una
# copia manual de la matriz de tipos.
SUSPICIOUS_DICT_ENTRY_THRESHOLD = 40

# engine/types.py construye su matriz con ~140 asignaciones de la forma
# `_TYPE_CHART_DATA[Tipo][Tipo] = valor`. Cualquier otro módulo que acumule
# muchas asignaciones de doble subíndice sobre el mismo nombre está
# reconstruyendo el mismo patrón.
SUSPICIOUS_SUBSCRIPT_ASSIGN_THRESHOLD = 30


def _iter_engine_source_files():
    for path in ENGINE_DIR.glob("*.py"):
        if path.name in ALLOWED_FILES or path.name.startswith("test_"):
            continue
        yield path


def _dict_has_only_tuple_pair_keys(node: ast.Dict) -> bool:
    if not node.keys:
        return False
    return all(isinstance(k, ast.Tuple) and len(k.elts) == 2 for k in node.keys if k is not None)


def _double_subscript_base_name(target: ast.expr) -> str | None:
    """Si `target` es `NOMBRE[x][y]`, devuelve "NOMBRE"; si no, None."""
    if not isinstance(target, ast.Subscript):
        return None
    inner = target.value
    if not isinstance(inner, ast.Subscript):
        return None
    base = inner.value
    if isinstance(base, ast.Name):
        return base.id
    return None


def test_no_hardcoded_type_chart_dict_outside_types_module():
    offenders = []
    for path in _iter_engine_source_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Dict)
                and len(node.keys) >= SUSPICIOUS_DICT_ENTRY_THRESHOLD
                and _dict_has_only_tuple_pair_keys(node)
            ):
                offenders.append(f"{path.name}:{node.lineno}")

    assert not offenders, (
        "Diccionario literal grande con claves de 2-tupla fuera de "
        f"engine/types.py (posible tabla de tipos duplicada): {offenders}"
    )


def test_no_hardcoded_type_chart_double_subscript_outside_types_module():
    offenders = []
    for path in _iter_engine_source_files():
        tree = ast.parse(path.read_text(), filename=str(path))
        counts: Counter[str] = Counter()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Assign):
                continue
            for target in node.targets:
                base_name = _double_subscript_base_name(target)
                if base_name is not None:
                    counts[base_name] += 1
        for base_name, count in counts.items():
            if count >= SUSPICIOUS_SUBSCRIPT_ASSIGN_THRESHOLD:
                offenders.append(f"{path.name}:{base_name} ({count} asignaciones)")

    assert not offenders, (
        "Muchas asignaciones `X[a][b] = valor` sobre el mismo nombre fuera de "
        f"engine/types.py (posible tabla de tipos reconstruida a mano): {offenders}"
    )
