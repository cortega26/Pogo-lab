# M4 — Trade Tracker

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Pendiente |
| **Tamaño** | L |
| **Depende de** | M2, M3 |
| **PRs** | PR-12, PR-13 |
| **Actualizado** | 2026-07-16 (creado) |

## Objetivo

Registrar sesiones y observaciones de intercambios (manual + por lotes + CSV) con validación y estados, más un
dashboard personal básico.

## Historias

- Como usuario, registro intercambios rápido desde el móvil.
- Como usuario, importo mis intercambios por CSV y veo mis totales separando Lucky de no Lucky.

## Tareas

### PR-12 · trades (modelos + entrada)

- [ ] Modelos `TradeSession` y `TradeObservation` (campos plan §E).
- [ ] Validaciones: `0<=IV<=15`; coherencia **piso↔ruleset**; `is_lucky` consistente con `trade_type`.
- [ ] Estados: `draft/valid/excluded/suspicious/duplicate/deleted` (+ `exclusion_reason`).
- [ ] Entrada rápida móvil (teclado numérico, Atk/Def/HP en una fila, toggles Lucky/garantizado, "guardar y siguiente").
- [ ] Modo por **lotes** (`bulk_add`).

### PR-13 · CSV + dashboard básico

- [ ] `import_csv()` con **vista previa** + errores por fila + `dedup_hash`.
- [ ] Export CSV del usuario (**anti spreadsheet-injection**: prefijar celdas que empiezan por `= + - @`).
- [ ] Plantilla `docs/csv_template.csv` documentada.
- [ ] Dashboard básico: totales, **Lucky vs normal separados**.

## Archivos / módulos afectados

`apps/trades/`, `templates/trades/`, `docs/csv_template.csv`.

## Pruebas

- [ ] Integración: alta individual, por lotes, import CSV (ok + errores), validaciones, dedup.
- [ ] E2E: "usuario registra una sesión" + "usuario consulta su dashboard".

## Criterios de aceptación

- [ ] Importar el CSV de ejemplo (sin OCR) y ver totales **separados Lucky/normal**.
- [ ] Observaciones inválidas quedan en estado `excluded`/`suspicious` con motivo.

## Demo verificable

Sesión creada + dashboard básico con distribución por tipo.

## Riesgos

- Complejidad del import CSV → puede ir como *fast-follow* si la entrada manual ya demuestra valor.

## Recortes posibles

Import CSV a fast-follow (⏭️); empezar solo con entrada manual + lotes.

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
