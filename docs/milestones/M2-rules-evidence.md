# M2 — Rules & Evidence

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Pendiente |
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
- [ ] Modelos `Mechanic`, `MechanicRuleSet` (versión, `effective_from/to`, `is_published`), `RuleParameter`.
- [ ] Modelos `SourceReference` (tipo: oficial/community/datamining/inference/hypothesis; estado; fechas), `SourceClaim`.
- [ ] `publish_ruleset()` — congela y **valida parámetros contra el schema del engine** (`engine/rulesets.py`).
- [ ] `resolve_active_ruleset(mechanic, at_datetime)` por `effective_from/to`.
- [ ] `engine/rulesets.py` — schemas de parámetros (dataclasses/pydantic).
- [ ] Registro en **Django Admin** (mecánicas, rulesets, parámetros, fuentes, claims).
- [ ] **ERD auto-generado** desde los modelos (`django-extensions graph_models`) → `docs/` (evita drift del diagrama vs. el modelo real).

### PR-08 · Seed inicial
- [ ] Mecánica `trade_iv` + varios rulesets configurables.
- [ ] `RuleParameter` de pisos por amistad + `floor.lucky=12`.
  - [ ] ⚠️ **VERIFICAR los valores contra datamining comunitario** (Silph Road / GamePress / GAME_MASTER) — **no hardcodear de memoria**; marcarlos como `SourceClaim` tipo *community* con nivel de confianza.
- [ ] `SourceReference`/`SourceClaim` de ejemplo por cada tipo de fuente.
- [ ] Dataset **sintético** para pruebas.

### PR-09 · content (CMS ligero)
- [ ] Modelos `ContentPage` + `ContentPageTranslation` (único `(page, locale)`).
- [ ] Primeras páginas (§15) es/en: *Cómo funcionan los IV*, *Piso por categoría*, *Por qué un piso no comprime*, *No afiliación*.
- [ ] SEO base por página (`seo_title`, `seo_description`, OG).

## Archivos / módulos afectados
`apps/mechanics/`, `apps/sources/`, `apps/content/`, `engine/rulesets.py`, `fixtures/` o comando `seed`.

## Pruebas
- [ ] Unit: versionado inmutable + `resolve_active_ruleset` (por fecha).
- [ ] Integración: alta/edición vía Admin; validación de parámetros contra schema.

## Criterios de aceptación
- [ ] Un ruleset de intercambios **publicado e inmutable** con `SourceClaim` citados.
- [ ] Página de mecánica renderizada en es/en.
- [ ] Pisos por amistad presentados como **hechos comunitarios verificados**, no como verdad oficial.

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
