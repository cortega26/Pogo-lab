# ADR-0011 — Límites entre apps: audit como sink, modelos sin side effects cross-app

- **Estado:** Aceptada
- **Fecha:** 2026-07-25
- **Relacionadas:** `plan.md` §19 · plan 060 (`plans/060-enforce-application-boundaries.md`) · ADR-0003

## Contexto

`apps.contributions.models.DataContributionConsent` llamaba a `apps.audit.models.AuditEvent.log(...)`
directamente desde sus classmethods `grant_consent`/`revoke_consent`. Al mismo tiempo,
`apps.audit.services` (que agrupaba `mark_observation` y `mark_dataset_suspicious`) importaba
`apps.contributions.models.DatasetVersion` y `apps.trades.models.TradeObservation`. El resultado era
un ciclo conceptual: `contributions` dependía de `audit`, y `audit` dependía de vuelta de
`contributions`/`trades`. `import-linter` no lo detectaba porque `root_packages` solo incluía
`engine` — las apps de Django no estaban bajo ningún contrato.

Esto viola la regla general de dominio (ADR-0003): un modelo no debería disparar coordinación hacia
otra app; eso es trabajo de la capa de servicio/orquestación.

## Decisión

1. **`apps.audit` es un sink puro**: expone el modelo `AuditEvent` (consultable por cualquier app) y
   nada más. No tiene `services.py`, no importa modelos de otras apps de dominio.
2. **Los modelos de dominio nunca importan `apps.audit`** ni disparan `AuditEvent.log(...)` desde sus
   propios métodos. `DataContributionConsent.grant_consent`/`revoke_consent` quedan como mutaciones
   puras de datos (siguen existiendo con la misma firma — son la base de ~40 tests de setup en
   `apps/contributions/tests/test_contributions.py` — pero ya no auditan).
3. **La orquestación (mutación + auditoría) vive en la capa de servicio de la app dueña del
   agregado**: `apps.contributions.services.grant_consent`/`revoke_consent`/`mark_dataset_suspicious`
   (dueño: `DatasetVersion`, `DataContributionConsent`); `apps.trades.services.mark_observation`
   (dueño: `TradeObservation`). Los servicios SÍ pueden importar `apps.audit.models` — es la
   dirección permitida (servicio → sink), nunca al revés.
4. **Mecanizado con `import-linter`** (`pyproject.toml`): `root_packages` ahora incluye `"apps"`, con
   dos contratos `forbidden`:
   - `audit-is-a-sink-not-a-source`: `apps.audit` no puede importar ninguna app de dominio.
   - `domain-models-do-not-import-audit`: ningún `*.models` de las apps de dominio puede importar
     `apps.audit`.

## Alternativas consideradas

- **Capa genérica de eventos/señales de dominio** (event bus, signals de Django para desacoplar) —
  descartada: el propio plan 060 advierte no crear una capa genérica cuando tres funciones explícitas
  bastan. Con dos flujos de moderación y dos de consentimiento, una capa de eventos sería
  sobre-ingeniería.
- **Mover `AuditEvent` a un módulo compartido sin app propia** (ej. dentro de `apps.core`) — descartada:
  `AuditEvent` ya tiene su propio modelo, admin y migraciones estables; moverlo es una migración de
  base de datos innecesaria para resolver un problema que es de *dirección de import*, no de
  *ubicación del modelo*.
- **Contrato `layers` estricto para todas las apps** (en vez de `forbidden` puntual) — descartada por
  ahora: el grafo real de imports (`core` en la base; `content`/`mechanics`/`sources`/`trades`/`audit`
  como apps de dominio; `analysis`/`experiments`/`decisions`/`contributions` construyendo sobre esas)
  ya es acíclico fuera del caso `audit`↔`contributions`/`trades` corregido aquí. Definir un `layers`
  contract exhaustivo es más arriesgado (puede revelar/romper relaciones legítimas no inventariadas)
  y no lo pedía la evidencia concreta de este plan. Se puede añadir después si aparece un nuevo ciclo.

## Consecuencias

- **Positivas:** el ciclo real desaparece (verificado: `apps.contributions.models` ya no importa
  `apps.audit`, `apps.audit` no tiene ningún import hacia apps de dominio). Los dos contratos nuevos
  mecanizan la regla — un test manual (reintroducir el import viejo) confirmó que `lint-imports`
  detecta la regresión, incluso transitivamente (`experiments.models` → `contributions.models` →
  `audit.models`).
- **Negativas / costes:** dos puntos de entrada para "otorgar consentimiento" (el classmethod del
  modelo, sin auditoría; el servicio, con auditoría) — riesgo de que código nuevo llame al classmethod
  directamente en producción y se salte la auditoría. Mitigado con un test explícito
  (`test_model_classmethod_no_longer_emits_audit_event`) que deja la asimetría documentada, y con que
  la vista de producción (`apps/contributions/views.py`) ya solo importa las funciones de servicio, no
  el modelo.
- **Mitigaciones:** si en el futuro se detecta una llamada directa al classmethod del modelo en una
  vista/comando de producción, es una señal de que falta pasar por el servicio — no se necesita un
  contrato de import-linter adicional para esto porque `apps.contributions.views` ya no importa el
  modelo directamente (solo el servicio).

## Reversibilidad

Alta. Revertir implicaría devolver el `AuditEvent.log(...)` a los classmethods del modelo y recrear
`apps/audit/services.py` — un cambio de código sin migraciones de base de datos, disparado si un caso
de uso futuro necesita que TODA llamada al classmethod audite (no solo la vía servicio).
