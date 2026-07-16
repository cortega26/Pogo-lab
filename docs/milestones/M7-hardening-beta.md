# M7 — Hardening y beta

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Pendiente |
| **Tamaño** | M |
| **Depende de** | M1 … M6 |
| **PRs** | PR-20, PR-21 |
| **Actualizado** | 2026-07-16 (creado) |

## Objetivo
Endurecer para beta: E2E completos, accesibilidad, rendimiento, seguridad, backup/restore, despliegue, analítica
de producto y revisión legal.

## Historias
- Como responsable, quiero desplegar con bajo costo y un restore probado antes de abrir la beta cerrada.
- Como usuario, quiero una experiencia accesible y rápida en móvil.

## Tareas

### PR-20 · hardening
- [ ] **CSP** estricta (JS autohospedado; sin inline salvo hashes).
- [ ] **Rate limiting** en login/registro/contribución.
- [ ] `pip-audit` en CI (sin vulnerabilidades críticas).
- [ ] Suite **Playwright completa**: los 10 flujos críticos (plan §13).
- [ ] Auditoría de **accesibilidad** (teclado, contraste, tabla alternativa a gráficos) + **Core Web Vitals**.

### PR-21 · deploy + beta
- [ ] `Dockerfile` de producción + `.github/workflows/deploy.yml`.
- [ ] **DECIDIR hosting** — PaaS por defecto (Fly.io/Railway/Render) vs VPS+Compose (decisión reversible).
- [ ] Postgres administrado + **backup** + **prueba de restore** verificada.
- [ ] Métricas de producto (plan §12/§18) sin invadir privacidad.
- [ ] Completar **exportación** y **eliminación** de cuenta (stubs de M1).
- [ ] Revisión legal/marca: disclaimer no afiliación, privacidad, ToS, licencias (código + dataset).

## Archivos / módulos afectados
`.github/workflows/`, infra/deploy, `apps/audit/`, `apps/accounts/` (export/delete), `docs/`.

## Pruebas
- [ ] Los 10 E2E verdes en CI.
- [ ] Smoke de despliegue en el entorno objetivo.
- [ ] **Restore** verificado desde backup.

## Criterios de aceptación
- [ ] **Definición de terminado** del plan (§O) completa.
- [ ] Entorno desplegado accesible + beta cerrada operativa.

## Demo verificable
Entorno desplegado con beta cerrada funcionando.

## Riesgos
- Revisión legal pendiente puede bloquear el lanzamiento → iniciarla temprano (no bloquea el código).

## Recortes posibles
Profundidad de la analítica de producto (empezar con métricas mínimas).

## Registro de avance
| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
