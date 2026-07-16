# Registro de avance — Pogo-lab (MVP)

Tablero de seguimiento por milestone del MVP **Mechanics Lab + Decision Planner** (intercambios, IV y Pokémon
Lucky). Cada hoja de milestone es **autocontenida**: en una sesión de implementación se carga solo el archivo del
milestone en curso (no el plan completo), lo que mantiene el contexto pequeño y el avance trazable.

- **Plan maestro (referencia, no recargar entero):** [`../plan.md`](../plan.md) · guía para agentes: [`../../AGENTS.md`](../../AGENTS.md)
- **Alcance elegido:** completo **M0–M7** (incluye dataset comunitario). Hosting: decisión reversible, PaaS por defecto, antes de M7.

## Leyenda de estado

| Símbolo | Significado |
|---|---|
| ⬜ | Pendiente |
| 🟨 | En progreso |
| ✅ | Completado |
| ⏭️ | Diferido / recortado |

## Tablero

| Milestone | Objetivo | Tamaño | Depende de | PRs | Estado |
|---|---|:--:|:--:|---|:--:|
| [M0 — Descubrimiento y decisiones](M0-descubrimiento.md) | Fijar stack, dominio y contratos estadísticos | S | — | ADR + skeleton | ✅ |
| [M1 — Fundación](M1-fundacion.md) | Proyecto ejecutable, CI, auth, i18n, layout, observabilidad | M | M0 | PR-01…05 | ✅ |
| [M2 — Rules & Evidence](M2-rules-evidence.md) | Conocimiento versionado con procedencia + admin + contenido | M | M1 | PR-07…09 | ✅ |
| [M3 — Calculadora pública](M3-calculadora.md) | Motor de probabilidad + calculadora SSR compartible + SEO | M | M1, M2 | PR-06, 10, 11 | ✅ |
| [M4 — Trade Tracker](M4-trade-tracker.md) | Registro de sesiones/observaciones (manual+CSV) + dashboard | L | M2, M3 | PR-12, 13 | ⬜ |
| [M5 — Analysis & Decisions](M5-analysis-decisions.md) | Inferencia honesta reproducible + recomendaciones | L | M4 | PR-14…16 | ⬜ |
| [M6 — Community Dataset](M6-community-dataset.md) | Contribución opt-in anonimizada + moderación + dashboard | L | M5 | PR-17…19 | ⬜ |
| [M7 — Hardening y beta](M7-hardening-beta.md) | E2E, a11y, seguridad, backup/restore, despliegue, beta | M | M1…M6 | PR-20, 21 | ⬜ |

## Cómo usar estas hojas

1. Al iniciar una sesión de implementación, abre **solo** la hoja del milestone en curso.
2. Marca `- [ ]` → `- [x]` conforme avanzas; cambia el **Estado** en la cabecera y en este tablero.
3. Registra hitos en la sección **Registro de avance** de cada hoja (fecha, estado, nota).
4. Un milestone se declara ✅ solo cuando **todos** sus *criterios de aceptación* están marcados.

## Camino crítico

`M0 → M1 → M2/M3 (engine/probability + calculadora)` valida el wedge "entender + calcular" con la menor superficie.
Candidatos a diferir sin dolor (ver plan §P): distribución de suma completa, test de independencia, bayesiano,
descarga pública del dataset, verificación de email.
