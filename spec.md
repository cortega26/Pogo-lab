# Spec — Implementación de los hallazgos TODO restantes de `plans/`

> **SSOT para esta sesión.** Lee este archivo antes de cada cambio. Cada
> implementación sigue TDD: test que falle primero, luego código, luego suite
> verde, luego marca en `todo.md`.

## 1. Metas

1. **Archivar planes DONE restantes.** Los planes 022–043 (Batch 3) y
   044–050, 059 (Batch 4) ya están DONE y archivados en `plans/archive/`.
2. **Implementar los planes TODO restantes** en orden de prioridad y
   dependencia, verificando cada uno con tests antes de marcarlo DONE.
3. **No tocar los planes OPTION (062–064)**: requieren decisión de producto.
4. Los planes 046–048, 052–055 son XL/L y dependen de 046 (datos canónicos)
   o 056 (PostgreSQL gate). Se abordan si el tiempo lo permite; si no, se
   documenta el avance parcial.
5. Cada plan termina con la suite completa verde (`uv run pytest -q`) y
   `uv run ruff check .` limpio.

## 2. Inventario del estado actual (verificado contra código vivo)

Baseline al iniciar esta sesión (commit `a285ad3`):

- `uv run pytest -q --ignore=tests/test_e2e.py` → 757 passed, 4 skipped
- `uv run ruff check .` → All checks passed
- `uv run ruff format --check .` → 175 files already formatted
- `uv run mypy config engine apps tests` → 0 errors in 152 files

| Plan | Estado verificado | Evidencia |
|---|---|---|
| 029 | **Parcial** | UniqueConstraint existe en `apps/trades/models.py:133`; migration `0002_add_dedup_unique_constraint.py` existe; pero `register_observation` no captura `IntegrityError` |
| 039 | **DONE** | `tests/test_dps_views.py` existe con 21 tests |
| 046 | **TODO** | Datos de combate no unificados (XL) |
| 047 | **TODO** | Breakpoints sin golden vectors (dep 046) |
| 048 | **TODO** | PvP ranking sin corregir (dep 046) |
| 051 | **TODO** | Rate limiting usa LocMem; no shared cache; topología proxy no documentada |
| 052 | **TODO** | Publicación comunidad sin cuarentena (dep 056) |
| 053 | **TODO** | Contratos calculadoras sin validar (dep 046) |
| 054 | **TODO** | Analysis runs no atómicos (dep 056) |
| 055 | **TODO** | Trade ingestion sin endurecer (dep 056) |
| 056 | **TODO** | No hay gate PostgreSQL en CI |
| 057 | **TODO** | Bootstrap no determinista; `seed` vs `seed_content` duplican slug |
| 058 | **TODO** | Docs de milestones/estado no reconciliadas (dep 045–057) |
| 060 | **TODO** | App boundaries sin mecanizar (dep 052, 054, 055) |
| 061 | **TODO** | AuditEvent mutable, correlation_id no propagado (dep 060) |

## 3. Orden de ejecución

### Fase 1 — Quick wins (sin dependencias, S/M)

1. **029** — IntegrityError catch en `register_observation` (constraint ya existe)
2. **039** — Verificar que los 21 tests pasan y marcar DONE
3. **057** — Bootstrap determinista: `seed` orquesta `seed_content`, `.env.example` puerto 5433, `make bootstrap` levanta DB
4. **056** — PostgreSQL CI gate: settings `test_postgres.py`, service en CI, `make test-postgres`

### Fase 2 — Seguridad/producción (P0, dependen de 056 o topología)

1. **051** — Rate limiting: función de key probada, caché compartida (PostgreSQL-backed)
2. **058** — Reconciliar docs de estado (tras 057)

### Fase 3 — Arquitectura (P2, dependen de 052/054/055)

1. **060** — App boundaries: DAG permitido, import-linter contracts
2. **061** — AuditEvent inmutable: admin readonly, bloquear update/delete, propagar correlation_id

### Fase 4 — Datos canónicos (XL, dependen de 046)

1. **046** — Datos de combate canónicos (evaluación de alcance)
2. **047** — Validar breakpoints (dep 046)
3. **048** — Corregir PvP ranking (dep 046)

### Fase 5 — Producción/semántica (L, dependen de 056)

1. **052** — Gobernar publicación comunidad
2. **053** — Validar contratos calculadoras
3. **054** — Analysis runs atómicos
4. **055** — Endurecer trade ingestion

> **Nota de alcance:** Las Fases 4–5 son de esfuerzo L/XL. Si un plan excede
> el alcance razonable, se documenta el avance parcial y se deja en TODO.

## 4. Detalles de implementación por plan

### Plan 029 — IntegrityError catch en register_observation

- **Archivo:** `apps/trades/services.py`, función `register_observation`.
- **Cambio:** Envolver `TradeObservation.objects.create(...)` en
  `try/except IntegrityError`; en el catch, re-buscar el duplicado y
  retornarlo. Importar `IntegrityError` de `django.db.utils`.
- **Test:** Test que simula la carrera (mock `create` para lanzar
  `IntegrityError`, verifica que retorna el existing).
- **Verificación:** `uv run pytest apps/trades/ -v` verde.

### Plan 039 — DPS view tests

- **Verificación:** `uv run pytest tests/test_dps_views.py -v` verde (21 tests).
- Marcar DONE en README.

### Plan 057 — Bootstrap determinista

- **Archivos:** `Makefile` (`bootstrap` levanta DB, espera health, migra,
  siembra), `apps/mechanics/management/commands/seed.py` (orquesta
  `seed_content` o delega), `.env.example` (puerto 5433).
- **STOP:** Si `iv-en-intercambios` tiene dos versiones editoriales
  distintas, no elegir por fecha — registrar diferencia y pedir decisión.
- **Test:** Idempotencia (`make bootstrap` x2), checksum de slug.

### Plan 056 — PostgreSQL CI gate

- **Archivos:** `config/settings/test_postgres.py` (URL obligatoria con
  guard anti DB no-test), `.github/workflows/ci.yml` (service postgres:16,
  job con `pytest -m postgres`), `Makefile` (`test-postgres`), `pyproject.toml`
  (marker `postgres`).
- **STOP:** Si `DATABASE_URL` no identifica DB de test.
- **Verificación:** `DATABASE_URL=postgres://...pogo_test... pytest -m postgres -q` verde.

### Plan 051 — Rate limiting robusto

- **STOP:** Si la topología real incluye CDN/LB adicional no documentado.
  El plan 024 ya configuró `RATELIMIT_IP_META_KEY = "HTTP_X_REAL_IP"`.
  Este plan añade: función de key probada (IPv4/IPv6, spoof), caché compartida
  (PostgreSQL-backed), test multiworker (requiere 056).
- **Si la topología no está documentada:** dejar 024 como interim y
  documentar el bloqueo.

### Plan 058 — Reconciliar docs

- **Archivos:** `README.md`, `AGENTS.md`, `docs/milestones/`.
- **Verificación:** `rg -n "aún no hay código|Estado.*✅|\[ \]"` no encuentra
  contradicciones.

### Plan 060 — App boundaries

- **Depende de:** 052, 054, 055 (que dependen de 056). Si esos no están
  hechos, se puede avanzar el inventario de imports y el ADR, pero los
  contratos de import-linter se diseñan sobre el estado final.
- **STOP:** Si romper el ciclo exige mover modelos/migraciones.

### Plan 061 — AuditEvent inmutable

- **Depende de:** 060. Admin readonly, bloquear update/delete, propagar
  correlation_id desde el middleware a todos los `AuditEvent.log` calls.
- **Test:** admin POST/delete bloqueados, `.save()` bloqueado, PII centinela.

## 5. Verificación

### Por plan

1. Test específico del plan pasa.
2. `uv run pytest -q --ignore=tests/test_e2e.py` verde.
3. `uv run ruff check .` limpio.
4. `uv run ruff format --check .` limpio.
5. `uv run mypy config engine apps tests` limpio (si se tocaron archivos tipados).
6. `uv run python manage.py makemigrations --check --dry-run` sin cambios (si aplica).

### Tests end-to-end (`tests/`)

- `tests/test_plans_regression.py` — ya tiene 37 tests de los planes anteriores.
- Se añaden tests nuevos para cada plan implementado en esta sesión.
- `uv run pytest tests/test_plans_regression.py -v` debe pasar.

### Loop de revisión (cada ~20 iteraciones)

- Sub-agente con "review spec.md and the current implementation for gaps".

## 6. Convenciones (de AGENTS.md)

- Español neutral (sin voseo).
- Sin comentarios salvo que se pidan.
- TDD en `engine/`: fixtures a mano primero.
- `engine/` puro: sin imports de Django.
- Sin commits salvo que se pidan.
- Suite verde obligatoria.
