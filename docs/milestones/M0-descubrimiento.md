# M0 — Descubrimiento y decisiones

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Pendiente |
| **Tamaño** | S |
| **Depende de** | — |
| **Entregable** | ADRs + esqueleto `engine/` (firmas) + modelo de dominio |
| **Actualizado** | 2026-07-16 (creado) |

## Objetivo
Fijar stack, límites de dominio y contratos matemáticos/estadísticos **antes** de escribir producto, para que la
implementación no reinterprete decisiones.

## Historias
- Como equipo, quiero decisiones de arquitectura registradas (ADR) para no re-litigarlas.
- Como implementador, quiero las firmas del `engine/` congeladas para construir apps sin ambigüedad.

## Tareas
- [ ] **ADR-0001** — Stack: Django 5.2 + Postgres + HTMX vs TS+Fastify/SPA (incluir justificación: SciPy, admin, i18n, monolito).
- [ ] **ADR-0002** — Versionado inmutable de rulesets (`effective_from/to`, publicación congelada).
- [ ] Documentar el **modelo de dominio** (plan §E): validar 21 entidades, relaciones, constraints, privacidad.
- [ ] Congelar **contratos del `engine/`** (plan §F): firmas de `probability / intervals / stat_tests / decisions / rulesets`.
- [ ] Crear **esqueleto `engine/`**: módulos con firmas + docstrings (sin implementación) y tests *skeleton* (`xfail`/`skip`).
- [ ] Registrar **riesgos** y **criterios de aceptación** del MVP.
- [ ] Revisar el **mock de navegación** (plan §G): sitemap y rutas.

## Archivos / módulos afectados
- `docs/adr/ADR-0001-stack.md`, `docs/adr/ADR-0002-ruleset-versioning.md`
- `docs/domain-model.md`
- `engine/{probability,intervals,stat_tests,decisions,rulesets,versioning}.py` (solo firmas)
- `engine/tests/` (skeleton)

## Pruebas
- [ ] Revisión de contratos del engine (firmas acordadas).
- [ ] Tests *skeleton* corren (marcados como pendientes) sin romper la recolección de pytest.

## Criterios de aceptación
- [ ] ADR-0001 y ADR-0002 aprobados.
- [ ] Firmas del `engine/` acordadas y documentadas.
- [ ] Modelo de dominio revisado contra el plan §E.

## Demo verificable
Documento de decisiones + árbol de repo con `engine/` firmado.

## Riesgos
- Sobre-ingeniería de abstracciones → mantener **contratos mínimos** solo para la 1ª familia (plan §19-#17).

## Recortes posibles
Ninguno: es el cimiento.

## Registro de avance
| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada a partir del plan aprobado. |
