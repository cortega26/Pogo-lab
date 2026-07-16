# ADR-0006 — Recomendaciones deterministas sin LLM en runtime

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §4.7, §21 · ADR-0004

## Contexto

El Decision Planner traduce el análisis en acciones ("necesitarías ~N intercambios…", "separa tus Lucky antes de
comparar…"). Estas recomendaciones tocan afirmaciones sensibles (probabilidades, prudencia estadística) que deben
ser **explicables, testeables y trazables**, y no pueden variar de forma opaca entre ejecuciones.

## Decisión

Las recomendaciones se generan por un **motor de reglas determinista** (`engine/decisions.py::evaluate()`), con
`DecisionRule` **versionadas** (`condition_spec` declarativo, `message_key` i18n). Cada `DecisionRecommendation`
referencia la regla (`key + version`) que la produjo. **No se usa un LLM en runtime** para generar recomendaciones.

## Alternativas consideradas

- **LLM en runtime.** Flexible y natural, pero no determinista, difícil de testear, puede alucinar afirmaciones
  estadísticas irresponsables y no es trazable a una regla — inaceptable dado el eje de credibilidad del producto.
- **Reglas dispersas en las vistas.** Rápido, pero no versionable ni reutilizable entre familias de mecánicas.

## Consecuencias

- **Positivas:** salidas reproducibles, testeables (fixtures), auditables y traducibles; extensibles a futuras
  familias vía nuevas `DecisionRule`.
- **Negativas / costes:** menos "flexibilidad" expresiva; hay que redactar y versionar cada regla.
- **Mitigaciones:** `message_key` i18n permite redacción rica sin lógica; el `condition_spec` declarativo mantiene
  las reglas simples y testeables.

## Reversibilidad

Alta para **añadir** reglas; la política de "sin LLM en runtime" es deliberada y estable. Un LLM podría, si acaso,
asistir *offline* en la redacción de plantillas, nunca en la generación en producción.
