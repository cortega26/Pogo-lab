# ADR-0012: Snapshots versionados de datos de referencia

- **Fecha:** 2026-07-26
- **Estado:** Propuesta bloqueada por fuente/licencia
- **Contexto:** `engine/dps_data.py` contiene un catálogo parcial y no
  verificado externamente. Las futuras calculadoras requieren datos que cambian
  con el juego, pero el cálculo debe seguir siendo reproducible y sin red.

## Decisión propuesta

Cuando una fuente sea aprobada, cada publicación será un snapshot inmutable
local. Tendrá IDs estables de especie/forma y movimiento, y un schema mínimo:

- stats base, tipos y tabla de tipos;
- movimientos PvE/PvP con precisión y reglas de redondeo explícitas;
- learnsets con vigencia y categoría `normal`, `legacy` o `elite`;
- un manifest con fuente, clase de procedencia, licencia, atribución, checksum
  del input, fecha efectiva, ruleset, versión del esquema y algoritmo;
- una versión de snapshot visible en resultados y share URLs para que un
  cálculo histórico permanezca identificado.

La precisión canónica se fija en el artefacto: stats base, potencia, energía,
turnos y costos son enteros; multiplicadores y otros valores no enteros se
serializan como cadenas decimales, nunca como floats binarios. La importación
no redondea. Cada algoritmo versionado define el punto y modo de redondeo de
sus resultados publicados; el manifest referencia esa versión. Un campo nuevo
sin unidad, precisión y regla de redondeo es inválido y bloquea publicación.

El artefacto se genera dos veces desde el mismo input fijado por checksum y
debe ser idéntico. Los cálculos leen únicamente el snapshot local: no habrá red
en request time ni fallback a `latest`. Los snapshots antiguos se retienen
mientras respalden resultados publicados; rollback significa seleccionar el
snapshot anterior compatible, nunca reescribir resultados históricos. La
atribución exigida se muestra junto al dato o resultado pertinente.

No se almacenan derivados masivos especie×nivel×IV ni rankings precomputados:
stats, CP, HP, breakpoints y rankings se calculan en el `engine/` desde los
insumos canónicos.

## Validación previa a publicación

| Validador | Regla | Bloquea publicación |
|---|---|:--:|
| Unicidad | IDs estables no duplicados | Sí |
| Referencias | tipos, movimientos y learnsets apuntan a IDs existentes | Sí |
| Tabla de tipos | matriz completa 18×18 | Sí |
| Rangos | stats y valores de movimiento en límites documentados | Sí |
| Precisión | cada campo tiene unidad, representación y regla de redondeo | Sí |
| Movimientos huérfanos | ningún movimiento requerido queda sin especie válida | Sí |
| Learnsets | especies aplicables no quedan sin learnset explicable | Sí |
| Diff semántico | cambios de stats, tipos, movimientos y vigencias son revisables | Sí |
| Golden vectors | fixtures manuales existentes preservan resultados esperados | Sí |

Un validador bloqueante fallido impide publicar. Si un dato externo contradice
un vector dorado, se abre una discrepancia con fuente y versión; no se edita el
vector silenciosamente.

## Consecuencias y estado

El diseño separa adquisición offline de cálculo runtime, mantiene `engine/`
puro y permite trazabilidad por fuente/versiones. Añade disciplina de manifests,
validadores y retención, pero evita una segunda fuente de verdad.

La decisión no autoriza un parser, esquema, ingestor ni migración: el registro
de fuentes está bloqueado por falta de evidencia de licencia y aprobación del
owner. Tras una aprobación se redactará un plan sucesor autocontenido para
input sintético, parser determinista, validadores, migración desde
`dps_data.py` y pruebas; antes no.
