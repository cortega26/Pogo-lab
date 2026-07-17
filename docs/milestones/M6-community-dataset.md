# M6 — Community Dataset

| Campo | Valor |
|---|---|
| **Estado** | ✅ Completado |
| **Tamaño** | L |
| **Depende de** | M5 |
| **PRs** | PR-17, PR-18, PR-19 |
| **Actualizado** | 2026-07-17 (implementado) |

## Objetivo

Contribución **opt-in anonimizada** con consentimiento/revocación, moderación, versionado de datasets y dashboard
público (con advertencia de sesgo de selección).

> Recomendación del plan (§P): lanzar el dashboard en **solo lectura** primero; activar la descarga pública solo
> tras `min_sample_met` + revisión legal de la licencia del dataset.

## Historias

- Como usuario, doy consentimiento explícito para aportar mis observaciones anonimizadas y puedo revocarlo.
- Como visitante, veo el dataset comunitario con su metodología, versión y **advertencia de sesgo**.

## Tareas

### PR-17 · contributions (consentimiento + build)

- [x] Modelo `DataContributionConsent` (versión de texto, `granted_at`/`revoked_at`, revocable, auditado).
- [x] `grant_consent()` / `revoke_consent()`.
- [x] `build_dataset_version()` — anonimiza (**excluye `notes`**, sin trainer/ubicación, **país agregado**), `dedup_hash`, aplica `min_sample`, marca `is_public`.

### PR-18 · dashboard comunitario

- [x] Dashboard público: total válidas, periodo, rule sets incluidos, Lucky/no, distribución agregada, metodología, limitaciones, versión/fecha.
- [x] **Advertencia de sesgo de selección** (no es muestra aleatoria).
- [x] Descarga pública **solo si `min_sample_met`**.

### PR-19 · audit + moderación

- [x] `AuditEvent` en cambios sensibles (+ `correlation_id`).
- [x] Moderación `suspicious`/`duplicate`; marcar datasets sospechosos.
- [x] Recálculo **idempotente** del agregado (management command).

## Archivos / módulos afectados

`apps/contributions/`, `apps/experiments/`, `apps/audit/`, `templates/dataset/`.

## Pruebas

- [x] Integración: consentimiento, revocación, build de dataset, export, dedup.
- [x] E2E: "aporta datos opt-in", "revoca consentimiento", "admin invalida observación", "recálculo del agregado".

## Criterios de aceptación

- [x] Opt-in/revocación funcionan; la revocación **excluye de builds futuros**.
- [x] Dataset público **sin PII**, solo si `min_sample_met`, con metodología y versión.
- [x] Advertencia de sesgo visible; datasets sospechosos se pueden marcar.

## Demo verificable

Dashboard comunitario con dataset versionado y advertencia de sesgo.

## Riesgos

- Presentar datos sesgados como definitivos → advertencia + umbral mínimo antes de publicar.
- Carga de privacidad/legal → revisión de licencia del dataset antes de activar descarga.

## Recortes posibles

Descarga pública diferible (⏭️); empezar con dashboard de **solo lectura**.

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
| 2026-07-17 | ✅ | PR-17/18/19 implementados. 45 tests nuevos (33 contributions + 6 experiments + 6 audit). Gates: ruff/mypy/lint-imports/pytest(403)/coverage(92%). apps/contributions + apps/experiments + apps/audit creados. Dashboard público con advertencia de sesgo. Dataset inmutable con checksum idempotente. AuditEvent con metadata sin PII. |
