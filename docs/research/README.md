# docs/research/ — Mapa de investigación (SIN verificar)

> ⚠️ **Todo lo de esta carpeta es insumo de investigación, no especificación.** Fue generado por un agente; los números, fórmulas y test vectors **no están verificados contra fuente primaria** y contienen errores conocidos. **No implementes directamente desde aquí.** La fuente de verdad verificada son las **fixtures del `engine/` calculadas a mano**, producidas en la compuerta de verificación (Gate 0) de [../milestones/fase-2.md](../milestones/fase-2.md).
>
> **Excepción:** [data_policy.md](data_policy.md) **sí es normativa** (política de datos vigente), no forma parte del mapa sin verificar.

## Contenido

| Archivo | Qué es | Estado |
|---|---|---|
| [research_report.md](research_report.md) | Informe y estrategia post-MVP | Mapa (sin verificar) |
| [formula_registry.csv](formula_registry.csv) | Registro de fórmulas | Mapa (sin verificar) |
| [test_vectors.json](test_vectors.json) | Vectores de prueba | **Sin verificar — errores conocidos** (ver `_meta`) |
| [dataset_registry.csv](dataset_registry.csv) | Inventario de datasets y procedencia | Mapa (ajustado a fair use) |
| [source_registry.csv](source_registry.csv) | Fuentes y confianza | Mapa |
| [calculator_backlog.csv](calculator_backlog.csv) | Backlog priorizado de calculadoras | Mapa |
| [tool_audit.csv](tool_audit.csv) | Auditoría de herramientas existentes | Mapa |
| [discrepancy_log.csv](discrepancy_log.csv) | Discrepancias detectadas | Mapa |
| [experiment_backlog.csv](experiment_backlog.csv) | Experimentos comunitarios candidatos | Mapa |
| [domain_research_packets/](domain_research_packets/) | Guías por dominio | Mapa (sin verificar) |
| [data_policy.md](data_policy.md) | Política de adquisición de datos / fair use | **Normativo** |

## Deuda de verificación conocida

Se hallaron **5 inconsistencias por muestreo** (2026-07-17). No es el conjunto completo: por eso Gate 0 **re-verifica todo**, no solo estas. La tabla detallada vive en [../milestones/fase-2.md](../milestones/fase-2.md) (sección *Deuda de verificación conocida*).

## Cómo usar esta carpeta

1. Úsala como **mapa** para decidir qué construir, dónde buscar fuentes y qué discrepancias existen.
2. Antes de implementar **cualquier** fórmula: re-derivarla contra fuente primaria y codificar su golden vector como **fixture del `engine/`** (SSOT). Ver Gate 0 en [../milestones/fase-2.md](../milestones/fase-2.md).
3. Antes de añadir **cualquier** fuente de datos: pasar el checklist de [data_policy.md](data_policy.md) §6.
