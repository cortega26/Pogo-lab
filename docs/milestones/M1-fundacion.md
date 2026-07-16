# M1 — Fundación

| Campo | Valor |
|---|---|
| **Estado** | ✅ Completado |
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
- [x] `uv init` + Django 5.2 + dependencias base.
- [x] `config/settings/{base,dev,prod,test}.py` (por entorno).
- [x] `.env.example` (sin secretos) + `django-environ`.
- [x] `compose.yaml` con **PostgreSQL 16** (dev).
- [x] `Makefile`: `bootstrap`, `test`, `run`, `seed`, `lint`.

### PR-02 · Calidad y CI
- [x] **Ruff** (lint + format) configurado.
- [x] **mypy** + `django-stubs`.
- [x] **pre-commit** (Ruff, mypy, checks básicos).
- [x] `.github/workflows/ci.yml` (lint/type/test) en **verde**, junto al `docs.yml` ya existente.
- [x] **import-linter**: contrato "`engine/` no importa Django; las apps dependen de `engine/`" — **CI falla si se rompe**.
- [x] Cobertura con umbral (objetivo `engine/` ≥95%) + `pytest-randomly` (orden determinista).
- [x] Activar en `.pre-commit-config.yaml` los hooks de **código** (Ruff, mypy, import-linter, pytest rápido).
- [x] CHANGELOG con `git-cliff` (Conventional Commits) + añadir ecosistema `pip` a `.github/dependabot.yml`.

### PR-03 · core
- [x] `TimestampedModel` (mixin `created_at`/`updated_at`).
- [x] `/healthz` (health check).
- [x] Logging estructurado + **correlation id** (middleware).

### PR-04 · accounts
- [x] **django-allauth**: registro/login/reset (email + password, verificación de email).
- [x] `User` (email como login) + `UserProfile` (`locale`, `country` opcional, `default_contribution_optin`).
- [x] Stubs de **exportación** y **eliminación** de cuenta (se completan en M7).

### PR-05 · i18n + layout
- [x] `i18n_patterns` con `/es/` y `/en/`; carpeta `locale/` (pt preparado).
- [x] Selector de idioma que preserva la ruta equivalente.
- [x] Layout base con **Tailwind standalone CLI** (sin cadena Node en runtime).

## Archivos / módulos afectados
`config/`, `apps/core/`, `apps/accounts/`, `.github/workflows/`, `compose.yaml`, `Dockerfile` (base),
`templates/base.html`, `static/`, `locale/`.

## Pruebas
- [x] Smoke de auth (registro/login/logout).
- [x] `/healthz` responde 200.
- [x] CI (Ruff + mypy + pytest) verde.

## Criterios de aceptación
- [x] `clonar → uv sync → compose up → migrate → test → runserver` funciona en pasos cortos.
- [x] Login funcional + cambio de idioma sin perder ruta.

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
| 2026-07-16 | 🟨 | PR-01 (bootstrap) completado. |
| 2026-07-16 | 🟨 | PR-02 (calidad y CI) completado. |
| 2026-07-16 | 🟨 | PR-03 (core) completado. |
| 2026-07-16 | 🟨 | PR-04 (accounts) completado. |
| 2026-07-16 | ✅ | M1 completo: PR-01..05, CI verde, i18n, Tailwind layout. |
