# TODO — Implementación de los hallazgos TODO restantes de `plans/`

> Spec canónico: `spec.md`. Marca `[x]` al completar cada sub-tarea verificada.
> Baseline: 757 passed, 4 skipped, ruff/mypy limpios.

## Fase 0 — Archivar planes DONE (ya archivados)

- [x] Archivar planes 022–043, 044–050, 059 (46 archivos en `plans/archive/`)
- [x] Actualizar `plans/README.md` (marcar archived)

## Fase 1 — Quick wins (sin dependencias)

### Plan 029 — IntegrityError catch en register_observation

- [ ] Verificar drift: `git diff --stat 40b1540..HEAD -- apps/trades/models.py apps/trades/services.py`
- [ ] Confirmar UniqueConstraint existe en `apps/trades/models.py`
- [ ] Confirmar migration `0002_add_dedup_unique_constraint.py` existe
- [ ] Escribir test que simula IntegrityError en `register_observation`
- [ ] Añadir `try/except IntegrityError` en `register_observation` (`apps/trades/services.py`)
- [ ] `uv run pytest apps/trades/ -v` verde
- [ ] `uv run ruff check apps/trades/services.py`
- [ ] Actualizar `plans/README.md` fila 029 → DONE

### Plan 039 — DPS view tests (verificar ya hecho)

- [ ] `uv run pytest tests/test_dps_views.py -v` verde (21 tests)
- [ ] `uv run ruff check tests/test_dps_views.py`
- [ ] Actualizar `plans/README.md` fila 039 → DONE

### Plan 057 — Bootstrap determinista

- [ ] Inventariar slugs de `seed` vs `seed_content`
- [ ] Verificar conflicto de slug `iv-en-intercambios`
- [ ] Hacer que `seed` orqueste `seed_content` (o delegar)
- [ ] Corregir `.env.example` puerto 5433
- [ ] `make bootstrap`: levanta DB, espera health, migra, siembra
- [ ] Test idempotencia (`make bootstrap` x2)
- [ ] Actualizar README/CONTRIBUTING/AGENTS
- [ ] `uv run pytest -q` verde
- [ ] Actualizar `plans/README.md` fila 057 → DONE

### Plan 056 — PostgreSQL CI gate

- [ ] Crear `config/settings/test_postgres.py` (URL obligatoria, guard anti DB no-test)
- [ ] Añadir service postgres:16 en `.github/workflows/ci.yml`
- [ ] Añadir job/matriz con `pytest -m postgres`
- [ ] Añadir marker `postgres` en `pyproject.toml`
- [ ] `make test-postgres` en Makefile
- [ ] Guard que rechace `DATABASE_URL` no-test
- [ ] `docker compose up -d db` + `DATABASE_URL=... pytest -m postgres -q` verde
- [ ] Actualizar `plans/README.md` fila 056 → DONE

## Fase 2 — Seguridad/producción

### Plan 051 — Rate limiting robusto

- [ ] Verificar topología de proxy (STOP si no documentada)
- [ ] Función de key probada (IPv4/IPv6, listas, spoof, ausencia)
- [ ] Caché compartida (PostgreSQL-backed o documentar excepción)
- [ ] Separar grupos y combinar IP con identidad normalizada
- [ ] Test multiworker (requiere 056)
- [ ] `uv run pytest tests/test_security.py apps/accounts/ -q` verde
- [ ] Actualizar `plans/README.md` fila 051 → DONE

### Plan 058 — Reconciliar docs

- [ ] Construir matriz evidencia→estado
- [ ] Corregir AGENTS/README/tablero/M7/M8
- [ ] `rg -n "aún no hay código|Estado.*✅|\[ \]"` sin contradicciones
- [ ] Actualizar `plans/README.md` fila 058 → DONE

## Fase 3 — Arquitectura

### Plan 060 — App boundaries

- [ ] Generar mapa actual de imports
- [ ] Definir DAG permitido en ADR
- [ ] Extraer AuditEvent.log de modelos a servicios
- [ ] Mover mark_observation/mark_dataset_suspicious
- [ ] Añadir contratos import-linter para capas/apps
- [ ] `uv run lint-imports` verde
- [ ] `uv run pytest -q` verde
- [ ] Actualizar `plans/README.md` fila 060 → DONE

### Plan 061 — AuditEvent inmutable

- [ ] Admin completamente readonly
- [ ] Bloquear update/delete de instancias persistidas
- [ ] Centralizar creación en servicio con correlation_id
- [ ] Actualizar casos de uso para pasar request ID
- [ ] Tests de admin POST/delete, .save(), PII centinela
- [ ] `uv run pytest apps/audit/ tests/test_security.py tests/test_account.py -q` verde
- [ ] Actualizar `plans/README.md` fila 061 → DONE

## Fase 4 — Datos canónicos (XL, dep 046)

### Plan 046 — Datos de combate canónicos

- [ ] Evaluación de alcance (¿requiere datamining completo?)
- [ ] Si excede alcance: documentar avance parcial

### Plan 047 — Validar breakpoints (dep 046)

- [ ] Pendiente hasta 046

### Plan 048 — Corregir PvP ranking (dep 046)

- [ ] Pendiente hasta 046

## Fase 5 — Producción/semántica (L, dep 056)

### Plan 052 — Gobernar publicación comunidad

- [ ] Pendiente hasta 056

### Plan 053 — Validar contratos calculadoras

- [ ] Pendiente hasta 046

### Plan 054 — Analysis runs atómicos

- [ ] Pendiente hasta 056

### Plan 055 — Endurecer trade ingestion

- [ ] Pendiente hasta 056

## Revisiones periódicas

- [ ] Iteración ~20: sub-agente "review spec.md and current implementation for gaps"
- [ ] Iteración ~40: sub-agente review

## Notas de bloqueo

(Si un plan se bloquea, documentar aquí por qué y qué se necesita.)
