# ADR-0002 — Versionado inmutable de rulesets con procedencia

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §E, §19-#5, §19-#6 · ADR-0004

## Contexto

Las reglas del juego (pisos de IV por amistad, Lucky=12) son **conocimiento comunitario cambiante**, no verdad
oficial. Además, los análisis históricos deben poder **reproducirse** con las reglas que estaban vigentes cuando se
registraron los datos. Cambiar una regla nunca debe alterar retroactivamente un análisis pasado.

## Decisión

`MechanicRuleSet` es **inmutable una vez publicado** (`is_published`), con `version`, `effective_from` y
`effective_to`. Los valores concretos viven como `RuleParameter` **citados por `SourceClaim`** (tipo de fuente +
nivel de confianza). Cada `TradeObservation` referencia el ruleset vigente al registrarse; cada `AnalysisRun` fija
la versión de ruleset usada. Un cambio de reglas crea una **nueva versión**, no edita la anterior.

## Alternativas consideradas

- **Editar el ruleset en sitio.** Simple, pero rompe la reproducibilidad histórica y borra la trazabilidad de por
  qué un análisis dio cierto resultado.
- **Parámetros hardcodeados en código.** Acopla reglas comunitarias volátiles al despliegue y las presenta con
  falsa autoridad; imposible actualizar con fechas efectivas sin release.

## Consecuencias

- **Positivas:** reproducibilidad histórica; separación clara oficial/comunidad/inferido; el admin actualiza reglas
  con fechas efectivas sin tocar análisis pasados; procedencia auditable.
- **Negativas / costes:** más entidades y una capa de resolución (`resolve_active_ruleset(mechanic, at)`).
- **Mitigaciones:** la resolución por fecha es una consulta simple; la validación de parámetros contra el schema del
  `engine/` (`engine/rulesets.py`) ocurre al publicar.

## Reversibilidad

Baja: es un cimiento de la honestidad del producto. Revertir a reglas mutables invalidaría la reproducibilidad, que
es requisito, no lujo.
