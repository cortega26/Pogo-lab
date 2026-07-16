# M1 — Fundación

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Pendiente |
| **Tamaño** | M |
| **Depende de** | M0 |
| **PRs** | PR-01 … PR-05 |
| **Actualizado** | 2026-07-16 (creado) |

## Objetivo
Proyecto Django ejecutable con CI verde, autenticación, i18n, layout base y observabilidad mínima.

## Historias
- Como visitante, puedo registrarme, iniciar sesión y cambiar de idioma.
- Como implementador, puedo `clonar → instalar → migrar → test → run` en pasos cortos y verificables.

## Tareas

### PR-01 · Bootstrap
- [ ] `uv init` + Django 5.2 + dependencias base.
- [ ] `config/settings/{base,dev,prod,test}.py` (por entorno).
- [ ] `.env.example` (sin secretos) + `django-environ`.
- [ ] `compose.yaml` con **PostgreSQL 16** (dev).
- [ ] `Makefile`/`justfile`: `bootstrap`, `test`, `run`, `seed`, `lint`.

### PR-02 · Calidad y CI
- [ ] **Ruff** (lint + format) configurado.
- [ ] **mypy** + `django-stubs`.
- [ ] **pre-commit** (Ruff, mypy, checks básicos).
- [ ] `.github/workflows/ci.yml` (lint/type/test) en **verde**.

### PR-03 · core
- [ ] `TimestampedModel` (mixin `created_at`/`updated_at`).
- [ ] `/healthz` (health check).
- [ ] Logging estructurado + **correlation id** (middleware).

### PR-04 · accounts
- [ ] **django-allauth**: registro/login/reset (email + password, verificación de email).
- [ ] `User` (email como login) + `UserProfile` (`locale`, `country` opcional, `default_contribution_optin`).
- [ ] Stubs de **exportación** y **eliminación** de cuenta (se completan en M7).

### PR-05 · i18n + layout
- [ ] `i18n_patterns` con `/es/` y `/en/`; carpeta `locale/` (pt preparado).
- [ ] Selector de idioma que preserva la ruta equivalente.
- [ ] Layout base con **Tailwind standalone CLI** (sin cadena Node en runtime).

## Archivos / módulos afectados
`config/`, `apps/core/`, `apps/accounts/`, `.github/workflows/`, `compose.yaml`, `Dockerfile` (base),
`templates/base.html`, `static/`, `locale/`.

## Pruebas
- [ ] Smoke de auth (registro/login/logout).
- [ ] `/healthz` responde 200.
- [ ] CI (Ruff + mypy + pytest) verde.

## Criterios de aceptación
- [ ] `clonar → uv sync → compose up → migrate → test → runserver` funciona en pasos cortos.
- [ ] Login funcional + cambio de idioma sin perder ruta.

## Demo verificable
Login + cambio de idioma es/en en el layout base.

## Riesgos
- Fricción del binario Tailwind → fallback a CSS propio con tokens (reversible, plan S6).

## Recortes posibles
Verificación de email diferible a M7 (⏭️).

## Registro de avance
| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
