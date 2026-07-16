# M2 — Rules & Evidence

| Campo | Valor |
|---|---|
| **Estado** | ✅ Completado |
| **Tamaño** | M |
| **Depende de** | M1 |
| **PRs** | PR-07, PR-08, PR-09 |
| **Actualizado** | 2026-07-16 (creado) |

## Objetivo
Conocimiento **versionado con procedencia** (reglas, parámetros, fuentes, claims) + Django Admin + contenido base.

## Historias
- Como usuario, veo una página de mecánica con reglas vigentes, fuentes por tipo y nivel de confianza.
- Como admin, publico un ruleset inmutable con fechas efectivas sin alterar análisis históricos.

## Tareas

### PR-07 · mechanics + sources
- [x] Modelos `Mechanic`, `MechanicRuleSet` (versión, `effective_from/to`, `is_published`), `RuleParameter`.
- [x] Modelos `SourceReference` (tipo: oficial/community/datamining/inference/hypothesis; estado; fechas), `SourceClaim`.
- [x] `publish_ruleset()` — congela y **valida parámetros contra el schema del engine** (`engine/rulesets.py`).
- [x] `resolve_active_ruleset(mechanic, at_datetime)` por `effective_from/to`.
- [x] `engine/rulesets.py` — schemas de parámetros (dataclasses/pydantic) + `validate_parameters()`.
- [x] Registro en **Django Admin** (mecánicas, rulesets, parámetros, fuentes, claims).
- [x] **ERD auto-generado** desde los modelos (`django-extensions graph_models`) → `docs/erd-m2.dot`.

### PR-08 · Seed inicial
- [x] Mecánica `trade_iv` + varios rulesets configurables (Good/Great/Ultra/Best + Lucky).
- [x] `RuleParameter` de pisos por amistad + `floor.lucky=12`.
  - [x] ⚠️ **VERIFICAR los valores contra datamining comunitario** (Silph Road / GamePress / GAME_MASTER) — **no hardcodear de memoria**; marcarlos como `SourceClaim` tipo *community* con nivel de confianza.
- [x] `SourceReference`/`SourceClaim` de ejemplo por cada tipo de fuente (5 fuentes, 5 claims).
- [x] Dataset **sintético** para pruebas (en tests de integración).

### PR-09 · content (CMS ligero)
- [x] Modelos `ContentPage` + `ContentPageTranslation` (único `(page, locale)`).
- [x] Primeras páginas (§15) es/en: *Cómo funcionan los IV*, *Piso por categoría*, *Por qué un piso no comprime*, *No afiliación*.
- [x] SEO base por página (`seo_title`, `seo_description`, OG).

## Archivos / módulos afectados
`apps/mechanics/`, `apps/sources/`, `apps/content/`, `engine/rulesets.py`, comando `seed`.

## Pruebas
- [x] Unit: versionado inmutable + `resolve_active_ruleset` (por fecha) + `validate_parameters`.
- [x] Integración: alta/edición; validación de parámetros contra schema.

## Criterios de aceptación
- [x] Un ruleset de intercambios **publicado e inmutable** con `SourceClaim` citados.
- [x] Página de mecánica renderizada en es/en (`/es/mecanicas/iv-en-intercambios/`, `/en/mecanicas/iv-en-intercambios/`).
- [x] Pisos por amistad presentados como **hechos comunitarios verificados**, no como verdad oficial.

## Demo verificable
Página de mecánica con reglas vigentes, fuentes por tipo y changelog.

## Riesgos
- Valores comunitarios erróneos → claims verificables y marcados; nunca oficial (plan S2).

## Recortes posibles
Número de rulesets seed (empezar con Good/Great/Ultra/Best + Lucky).

## Registro de avance
| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
| 2026-07-16 | ✅ | M2 completado. PR-07, PR-08, PR-09 implementados: apps mechanics+sources+content, engine/rulesets.py con validación y resolución, seed con trade_iv y pisos comunitarios citados, páginas de contenido es/en. 79 tests pasan (incl. sad paths: publicación inmutable, resolución por fecha, validación de parámetros, vistas con/sin datos), lint/mypy/import-linter verdes. |
