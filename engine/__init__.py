"""engine — Motor matemático y estadístico puro.

Sin imports de Django (contrato import-linter, ADR-0003).
Toda la matematica, estadistica y reglas de decision del producto viven aqui.
"""

# Version del algoritmo de probabilidad (plan §F, §H).
# Se incrementa al cambiar las formulas de probability.py.
# Se usa en el cache de la calculadora y en AnalysisRun.
ALGORITHM_VERSION: str = "1.0.0"
