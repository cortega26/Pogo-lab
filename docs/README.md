# Documentación de Pogo-lab

Índice y **mapa de propiedad (SSOT)**: cada hecho vive en **un solo** documento; los demás enlazan. Es DRY aplicado
a la documentación — la regla que evita el *drift*.

| Documento | Fuente única de… | No debe duplicar (enlaza) |
|---|---|---|
| [`plan.md`](plan.md) **(canónico)** | Arquitectura, modelo de datos, motor estadístico, roadmap, resumen de decisiones (§19), Definición de Terminado (§O) | — |
| [`adr/`](adr/) | Registro **detallado** de decisiones arquitectónicas (contexto/decisión/consecuencias) | El resumen de §19 (lo enlaza) |
| [`../AGENTS.md`](../AGENTS.md) | Reglas no-negociables, convenciones y principios de diseño | El *rationale* de decisiones (vive en `adr/`) |
| [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | Flujo de trabajo, TDD, commits, tooling y contratos de guardrails | Reglas de producto (viven en `AGENTS.md`) |
| [`milestones/`](milestones/) | Estado de ejecución por milestone (tablero + hojas M0–M7) | El diseño (vive en `plan.md`) |
| [`../CLAUDE.md`](../CLAUDE.md) | Puntero a `AGENTS.md` para Claude Code | Todo lo demás |

## Reglas de la documentación (anti-drift)

1. **`plan.md` es la copia canónica y versionada.** Existe otra copia en el almacén interno de Claude Code
   (`~/.claude/plans/`) que **no** se mantiene y **no** debe editarse. Todo cambio del plan va aquí, en git.
2. **Cero duplicación de hechos.** Si un dato aparecería en dos documentos, uno lo posee y el otro enlaza. Ejemplo:
   la Definición de Terminado se posee en `plan.md` §O; ningún otro documento la copia.
3. **Las constantes numéricas tienen una sola fuente de verdad de código** (engine/seed). Los ejemplos que
   aparecen en docs (pisos, `1/64`, `1/3375`) se verifican contra el engine mediante un test (se activa en M3). No
   se “fijan a mano” en varios sitios.
4. **Auto-generación real = derivada de código, y llega con el código:** ERD desde los modelos Django
   (`django-extensions graph_models`, M2) y CHANGELOG desde los commits (Conventional Commits + `git-cliff`, M1+).
   Hoy, “automático” = integridad de enlaces + lint en CI, nada de scripts bespoke.

## Cómo navegar

- ¿Qué construimos y por qué? → [`plan.md`](plan.md) y [`adr/`](adr/).
- ¿Cómo trabajo y qué guardrails aplican? → [`../CONTRIBUTING.md`](../CONTRIBUTING.md) y [`../AGENTS.md`](../AGENTS.md).
- ¿En qué punto estamos? → [`milestones/README.md`](milestones/README.md) (tablero).
