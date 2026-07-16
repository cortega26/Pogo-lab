"""Versionado del engine.

El `algorithm_version` se fija en cada `AnalysisRun` para garantizar
reproducibilidad: re-ejecutar con la misma versión produce el mismo resultado.
"""

# Versión semver del algoritmo del engine.
# Se incrementa cuando cambia la lógica matemática/estadística.
ALGORITHM_VERSION: str = "0.1.0-dev"


# Versión del schema de datos (rulesets, parámetros, resultados).
SCHEMA_VERSION: str = "1.0"


def algorithm_version() -> str:
    """Devuelve la versión actual del algoritmo.

    Se incorpora al AnalysisRun para reproducibilidad.
    """
    return ALGORITHM_VERSION


def schema_version() -> str:
    """Devuelve la versión del schema de datos del engine."""
    return SCHEMA_VERSION
