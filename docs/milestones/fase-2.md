# Fase 2 — Expansión post-MVP (roadmap + compuerta de verificación)

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Planificación — no iniciar hasta cerrar precondiciones |
| **Tipo** | Epic (se descompone en milestones M8+) |
| **Depende de** | M7 mergeado · PR-21 (legal/hosting) resuelto |
| **Entrada (no confiable)** | [../research/](../research/) — mapa de investigación **sin verificar** |
| **Actualizado** | 2026-07-17 (creado) |

## Objetivo

Expandir Pogo-lab desde el MVP (intercambios / IV / Lucky) hacia calculadoras de **combate (PvE/PvP), captura, recursos, huevos y Max Battles**, manteniendo el ADN del proyecto: `engine/` puro, **fixtures calculadas a mano**, procedencia separada y versionada, recomendaciones deterministas (sin LLM en runtime).

## Precondiciones (secuenciación) — NO ejecutar antes

- [ ] **M7 mergeado** a `main`.
- [ ] **PR-21 resuelto**: hosting decidido + revisión legal/marca. Esta fase multiplica la superficie ToS/IP (datos comunitarios, rosters de raid, redistribución de datos derivados) → la base legal debe existir primero. Ver [../research/data_policy.md](../research/data_policy.md).

## Principio rector: verificar antes de construir

El research pack es un **mapa, no una especificación**. Ninguna calculadora se implementa sobre sus números. Por cada fórmula priorizada:

1. **Re-derivar** contra fuente primaria (no el pack).
2. Codificar el golden vector como **fixture del `engine/` calculada a mano** (única SSOT).
3. Registrar **procedencia** y documentar **rounding/floors/caps**; etiquetar discrepancias.

Los CSV/JSON de `docs/research/` quedan como investigación; la verdad verificada vive en `engine/` + CI.

## Gate 0 — Compuerta de verificación (primer criterio de salida de cada ola)

- [ ] Cada fórmula de la ola re-derivada vs fuente primaria y con **fixture** en `engine/`.
- [ ] Rounding / floors / caps documentados por fórmula.
- [ ] Discrepancias resueltas o etiquetadas explícitamente.
- [ ] Deuda de verificación conocida (abajo) cerrada.

### Deuda de verificación conocida (hallada por muestreo — 2026-07-17)

> Estas 5 son las que **se encontraron por muestreo**, no el conjunto completo. Por eso Gate 0 re-verifica **todo**, no solo esto.

| # | Dónde | El doc dice | Recálculo verificado | Acción |
|---|---|---|---|---|
| 1 | `test_vectors.json` · Pikachu CP (L15, 10/10/10) | 387 | **369** | corregir inputs o valor al re-derivar |
| 2 | `formula_registry` FOR003 / `test_vectors` · Pikachu Def base | 96 | la fórmula da **95** | la conversión MSG→GO es **aproximada**: no usarla como SSOT de base stats — usar el **Game Master** |
| 3 | `test_vectors.json` · daño PvE | 139 (nota: `floor(138.38)`) | **244** (`floor(243.15)`) | recalcular; la nota es aritméticamente imposible |
| 4 | `test_vectors.json` · daño PvP | 74 (nota: `floor(73.535)`) | **77** (`floor(76.17)`) | recalcular |
| 5 | `domain_research_packets/pvp_combat.md` · Medicham L50 15/15/15 CP | 1431 | **~1617** (además excede el cap de 1500 de Great League) | corregir; el óptimo GL está en el nivel/IV que respeta el cap |

## Alcance faseado (forma cerrada primero)

Orden por confianza matemática y **baja dependencia de datos externos**:

**Ola A — forma cerrada, alto valor, exacta** (candidatos a M8):
CP & Nivel (CALC003) · Costo de Power-Up (CALC006) · PvP Stat Product / IV Ranker (CALC009) · Probabilidad de captura (CALC012) · Matriz de tipos (CALC027).

**Ola B — requiere datos vivos / más superficie legal** (M9+):
Breakpoints PvE (CALC007) · Shadow vs Purified (CALC019) · Elite TM (CALC020) · Shiny confidence (CALC014).

**Ola C — simuladores y datos pesados (diferir a Fase 3):**
Simulador PvE por ticks (CALC008) · Simulador de turnos PvP (CALC010) · Team builders · Huevos · Max Battles.

> **Rationale:** los simuladores son heurísticos/no cerrados y tensionan el ethos "exacto/auditable"; los módulos de datos pesados dependen de pipelines que hay que mantener frescos (ver [data_policy.md](../research/data_policy.md)). Empezar por forma cerrada maximiza valor con mínimo riesgo y reutiliza el `engine/` existente.

## Datos y legalidad

Toda fuente nueva pasa por el checklist §6 de [../research/data_policy.md](../research/data_policy.md). Procedencia versionada (`SourceClaim`); nada comunitario presentado como oficial.

## Modelo de datos

Entidades nuevas propuestas (`Species`, `Move`, `MoveStat` inmutable, `RaidBoss` — ver `research_report.md` §9) **a validar en diseño**, no a adoptar tal cual.

### Principio de arquitectura de datos: almacenar insumos, computar derivados

Regla fija para la Ola A y siguientes: **poseer la data de referencia en local** (no depender de fuentes externas al calcular) guardando solo los **insumos canónicos pequeños** y **computando** todo lo derivado en el `engine/`.

- **Se almacena** (canónico, ~pocos MB, versionado): base stats por especie (`base_atk`/`base_def`/`base_stamina`), tabla de **CPM** por nivel (~100 filas), movimientos (PvE/PvP), tabla de tipos, costos. ≈ DAT001 (Game Master).
- **Se computa en runtime, nunca se almacena**: stats por nivel (`(base+IV)×CPM`), las **4096 combinaciones de IV** / rank de Stat Product, CP/HP por combinación, breakpoints, TDO. Es barato (microsegundos) y las **fixtures del `engine/`** validan el cálculo.
- **No precomputar derivados.** Una tabla especie×nivel×IV serían ~400 M de filas para algo calculable al vuelo, y crearía una segunda SSOT que se desincroniza al corregir un redondeo o un base stat.

> ⚠️ Los **IV** son la tirada aleatoria de cada *ejemplar*, no una propiedad de la especie: no se "descargan IVs". Se descargan base stats + CPM y se generan las combinaciones al calcular.

### Snapshot versionado y desacople calc-time / fetch-time

- La dependencia externa vive **solo en un job de ETL** que trae el snapshot público, lo valida (hash + cross-check con PvPoke), lo **versiona con fecha efectiva + ruleset** y lo seedea. El **cálculo es 100% local y sin red** (ADN del proyecto).
- **Reproducibilidad**: toda sesión/observación/resultado guardado referencia la **versión de ruleset** usada, para que los cálculos históricos no cambien al actualizar la data. Conecta con `MoveStat`/`RuleSet` inmutables (§9) y la procedencia de M2.
- **Legal**: bundlear un snapshot normalizado/derivado con atribución para calcular es el caso de uso ETL de fair use — ver [../research/data_policy.md](../research/data_policy.md).

## Criterios de aceptación (de esta hoja como roadmap)

- [ ] Precondiciones cerradas (M7 + PR-21).
- [ ] Gate 0 superado para la Ola A **antes** de construir UI/calculadoras.
- [ ] Cada milestone M8+ decantado en su propia hoja con su DoD.

## Riesgos

- Construir sobre el pack sin re-derivar → propagar errores (ya hay 5 conocidos) y romper la tesis de credibilidad del producto. Mitigación: Gate 0 obligatorio.
- Arrancar antes de la base legal/hosting → deuda legal en producción. Mitigación: precondiciones.

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-17 | ⬜ | Hoja creada como roadmap post-MVP. Entrada = research pack (sin verificar). Gate 0 y deuda de verificación (5 inconsistencias) definidos. Bloqueada por M7 merge + PR-21. |
