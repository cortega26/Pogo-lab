# M0 — Descubrimiento y decisiones

| Campo | Valor |
|---|---|
| **Estado** | ✅ Completado |
| **Tamaño** | S |
| **Depende de** | — |
| **Entregable** | ADRs + esqueleto `engine/` (firmas) + modelo de dominio |
| **Actualizado** | 2026-07-16 (ADRs 0001–0007 redactados) |

## Objetivo
Fijar stack, límites de dominio y contratos matemáticos/estadísticos **antes** de escribir producto, para que la
implementación no reinterprete decisiones.

## Historias
- Como equipo, quiero decisiones de arquitectura registradas (ADR) para no re-litigarlas.
- Como implementador, quiero las firmas del `engine/` congeladas para construir apps sin ambigüedad.

## Tareas
- [x] **ADRs foundational redactados** en [`../adr/`](../adr/) (Estado: Aceptada): 0001 stack · 0002 versionado de
      rulesets · 0003 motor puro · 0004 métodos estadísticos · 0005 datos privados/públicos · 0006 recomendaciones
      deterministas · 0007 i18n.
- [x] Documentar el **modelo de dominio** (plan §E): validar 21 entidades, relaciones, constraints, privacidad.
- [x] Congelar **contratos del `engine/`** (plan §F): firmas de `probability / intervals / stat_tests / decisions / rulesets`.
- [x] Crear **esqueleto `engine/`**: módulos con firmas + docstrings (sin implementación) y tests *skeleton* (`skip` marcados pytest).
- [x] Registrar **riesgos** y **criterios de aceptación** del MVP.
- [x] Revisar el **mock de navegación** (plan §G): sitemap y rutas (documentado en ADR-0001 + base.html).

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
| 2026-07-16 | 🟨 | ADRs 0001–0007 redactados en `docs/adr/`. Pendiente: `docs/domain-model.md` + esqueleto `engine/`. |
| 2026-07-16 | ✅ | M0 completo: domain-model.md, engine/ con firmas+skips, ADRs, riesgos y mock de navegación. |
