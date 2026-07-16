<!-- Ver CONTRIBUTING.md y AGENTS.md. Marca solo lo que aplique; borra secciones irrelevantes. -->

## Descripción

<!-- Qué cambia y por qué. Enlaza el milestone/PR del roadmap (docs/plan.md §M) y el milestone afectado. -->

## Tipo de cambio

- [ ] feat  - [ ] fix  - [ ] docs  - [ ] test  - [ ] refactor  - [ ] chore/ci/build

## Checklist general

- [ ] Tests añadidos/actualizados y **verdes** (escritos antes del cambio; suite completa en CI).
- [ ] Documentación actualizada; **sin duplicar hechos** (mapa SSOT en `docs/README.md`).
- [ ] **ADR** añadido si la decisión es arquitectónica (`docs/adr/`).
- [ ] `pre-commit` y CI en **verde**.

## Guardrails no-negociables

> Ningún linter atrapa esto: es responsabilidad del autor y del revisor. Detalle en `AGENTS.md`.

- [ ] **Estadística honesta:** hundos con **binomial exacta** (no chi²); intervalos **Wilson / Clopper–Pearson**
      (no Wald); nada de "bug"/"manipulado"; se distingue "compatible con" de "demostrado"; se reporta **tamaño de
      efecto**; se respetan **umbrales mínimos** de n.
- [ ] **Procedencia:** toda regla/piso cita un `SourceClaim` con tipo y confianza; los pisos comunitarios están
      **verificados** y **no** se presentan como oficiales.
- [ ] **Modelo IV:** re-roll **uniforme** en `[f,15]` (sin pico); independencia Att/Def/HP tratada como **supuesto**.
- [ ] **`engine/` puro:** sin imports de Django; matemática cubierta por **fixtures a mano** + property-based.
- [ ] **Sin LLM en runtime:** recomendaciones **deterministas**, versionadas y trazables a `DecisionRule`.
- [ ] **Privacidad:** sin nombre de entrenador ni ubicación precisa; `notes` privadas **nunca** agregadas; snapshot
      público **anonimizado e inmutable**.
- [ ] **i18n:** contenido indexable **SSR**; `hreflang`/canonical correctos.

## Reproducibilidad (si el PR toca análisis)

- [ ] El `AnalysisRun` fija `dataset + ruleset.version + algorithm_version + random_seed`; el resultado es reproducible.
