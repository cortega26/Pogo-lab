# M7 — Hardening y beta

| Campo | Valor |
|---|---|
| **Estado** | 🟨 PR-20 hardening completo; PR-21 scaffold pendiente de humano |
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

- [x] **CSP** estricta (JS autohospedado; sin inline salvo hashes).
- [x] **Rate limiting** en login/registro/contribución.
- [x] `pip-audit` en CI (sin vulnerabilidades críticas).
- [x] Suite **Playwright completa**: los 10 flujos críticos (plan §13).
- [x] Auditoría de **accesibilidad** (teclado, contraste, tabla alternativa a gráficos) + **Core Web Vitals**.
- [x] **Determinismo del agregado** comunitario (mismo dataset → mismo p-valor).
- [x] **Verificación de email** activa (`mandatory` en prod).

### PR-21 · deploy + beta

- [x] `Dockerfile` de producción + `.github/workflows/deploy.yml`.
- [ ] **DECIDIR hosting** — PaaS por defecto (Fly.io/Railway/Render) vs VPS+Compose. **PENDIENTE-HUMANO**
- [x] Postgres administrado + **backup** + **procedimiento de restore** documentado.
- [x] Métricas de producto (plan §12/§18) sin invadir privacidad.
- [x] Completar **exportación** y **eliminación** de cuenta (stubs de M1).
- [ ] Revisión legal/marca: disclaimer no afiliación, privacidad, ToS, licencias. **PENDIENTE-HUMANO — placeholders creados**

## Archivos / módulos afectados

`.github/workflows/`, infra/deploy, `apps/audit/`, `apps/accounts/` (export/delete), `docs/`.

## Pruebas

- [x] Los 10 E2E verdes en CI.
- [ ] Smoke de despliegue en el entorno objetivo. **PENDIENTE-HUMANO**
- [ ] **Restore** verificado desde backup. **PENDIENTE-HUMANO**

## Criterios de aceptación

- [x] **Definición de terminado** del plan (§O) — hardening completo.
- [ ] Entorno desplegado accesible + beta cerrada operativa. **PENDIENTE-HUMANO**

## Demo verificable

Entorno desplegado con beta cerrada funcionando. **PENDIENTE-HUMANO**

## Riesgos

- Revisión legal pendiente puede bloquear el lanzamiento → iniciarla temprano (no bloquea el código).

## Recortes posibles

Profundidad de la analítica de producto (empezar con métricas mínimas).

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
| 2026-07-17 | 🟨 | PR-20 hardening completo: 10 E2E verdes, CSP estricta, rate limiting, pip-audit, determinismo del agregado, verificación de email, export/delete cuenta. PR-21 scaffold: Dockerfile, deploy.yml, backup/restore, /healthz, placeholders legales. Pendiente de humano: hosting, despliegue en vivo, restore verificado, revisión legal. |
