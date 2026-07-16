# CLAUDE.md

La guía canónica de este repositorio está en **[AGENTS.md](AGENTS.md)** — léela primero.

Recordatorio de no-negociables (detalle en `AGENTS.md`):

- **`engine/` puro** y testeado con **fixtures calculadas a mano**; **binomial exacta** para hundos (no chi²),
  **Wilson** por defecto; reproducibilidad con semilla.
- **Procedencia separada**; los pisos de IV son **hechos comunitarios** versionados (`SourceClaim`), **verificados
  al seed**, nunca presentados como oficiales. Modelo IV = re-roll uniforme en `[f,15]` (sin pico), no clamping.
- Recomendaciones **deterministas** (sin LLM en runtime). App **`analysis`**, no `statistics`.
- **Español neutral** en código, contenido y commits.

Seguimiento: `docs/milestones/` (carga **solo** la hoja del milestone en curso). Plan maestro: `docs/plan.md`.

> Las preferencias globales de `~/.claude/CLAUDE.md` (CodeGraph, español neutral) también aplican. Usa CodeGraph
> para preguntas estructurales en cuanto exista código.
