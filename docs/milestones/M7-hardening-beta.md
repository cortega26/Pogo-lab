# M7 — Hardening y beta

| Campo | Valor |
|---|---|
| **Estado** | 🟨 PR-21 deploy + infra listos; pendiente humano: legal, deploy smoke, restore verify |
| **Tamaño** | M |
| **Depende de** | M1 … M6 |
| **PRs** | PR-20, PR-21 |
| **Actualizado** | 2026-07-18 |

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
- [x] **DECIDIR hosting** — Oracle Cloud Infrastructure (OCI) capa gratuita (ARM Ampere A1, Docker Compose). Ver ADR-0009.
- [x] Postgres administrado + **backup** + **procedimiento de restore** documentado.
- [x] Métricas de producto (plan §12/§18) sin invadir privacidad.
- [x] Completar **exportación** y **eliminación** de cuenta (stubs de M1).
- [ ] Revisión legal/marca: disclaimer no afiliación, privacidad, ToS, licencias. **PENDIENTE-HUMANO — plantillas sustantivas creadas, URLs corregidas, fechas puestas. Revisión profesional requerida.**

## Archivos / módulos afectados

`.github/workflows/`, `infra/`, `compose.prod.yaml`, `compose.micro.yaml`, `bin/` (setup-oci, backup, restore),
`apps/audit/`, `apps/accounts/` (export/delete), `templates/legal/`, `docs/`.

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
| 2026-07-17 | 🟨 | PR-20 hardening completo. Hosting decidido: OCI Santiago (AMD Micro, 1 GB). Desplegado en http://146.181.47.12. Pendiente: GitHub Actions secrets, SSL/Lets Encrypt, backup automático, revisión legal. |
| 2026-07-18 | 🟨 | PR-21: deploy.yml + compose.prod/micro + OCI scripts + ADR-0009 + backup/restore. Legal templates pulidos (ToS/privacy/disclaimer). healthcheck.json fuera de i18n. Tests de vistas legales (11 nuevos, 491 total). Pendiente humano: revisión legal, smoke deploy, restore verify. |
