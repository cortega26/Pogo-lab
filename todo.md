# TODO — Implementación de hallazgos de `plans/`

> Spec canónico: `spec.md`. Marca `[x]` al completar cada sub-tarea verificada.
> Estado inicial: 733 passed, ruff check verde, ruff format falla en 15 archivos.

## Fase 0 — Archivar planes DONE

- [x] Crear `plans/archive/`
- [x] Mover `plans/001-*.md` … `plans/021-*.md` (Batch 1&2, todos DONE)
- [x] Mover `plans/023-fix-cramers-v-dimension.md` (verificado DONE)
- [x] Mover `plans/025-harden-account-deletion.md` (verificado DONE)
- [x] Mover `plans/026-add-form-action-csp.md` (verificado DONE)
- [x] Mover `plans/027-fix-floating-point-decisions.md` (verificado DONE)
- [x] Mover `plans/033-optimize-docker-builds.md` (verificado DONE)
- [x] Mover `plans/034-set-csrf-cookie-httponly.md` (verificado DONE)
- [x] Mover `plans/038-fix-make-seed-command.md` (verificado DONE; supercedido por 057)
- [x] Actualizar `plans/README.md` (marcar archived)

## Fase 1 — Contención (P1/P0, sin dependencias)

### Plan 022 — Fix MC p-value normalization
- [x] Escribir test `test_monte_carlo_normalizes_probs` en `engine/tests/test_stat_tests.py`
- [x] Fix `engine/stat_tests.py:105`: `expected_probs` → `norm_probs`
- [x] `uv run pytest engine/tests/test_stat_tests.py -v` verde
- [x] `uv run pytest -q` verde
- [x] `uv run ruff check engine/stat_tests.py`
- [x] Actualizar `plans/README.md` fila 022 → DONE

### Plan 028 — Sanitize CSP report logging
- [x] Escribir test `test_csp_report_handles_malicious_uri` en `tests/test_security.py`
- [x] Fix `apps/core/views.py`: extraer `csp-report`, sanitizar, truncar
- [x] `uv run pytest tests/test_security.py -v` verde
- [x] `uv run pytest -q` verde
- [x] `uv run ruff check apps/core/views.py`
- [x] Actualizar `plans/README.md` fila 028 → DONE

### Plan 042 — Fix export filename (no PK leak)
- [x] Escribir test `test_export_filename_does_not_leak_pk` en `tests/test_account.py`
- [x] Fix `apps/accounts/views.py:110`: usar SHA-256 hash del email
- [x] `uv run pytest tests/test_account.py -v` verde
- [x] `uv run pytest -q` verde
- [x] `uv run ruff check apps/accounts/views.py`
- [x] Actualizar `plans/README.md` fila 042 → DONE

### Plan 024 — Rate limit IP meta key
- [x] Verificar `infra/nginx/default.conf` setea `X-Real-IP`
- [x] Añadir `RATELIMIT_IP_META_KEY = "REMOTE_ADDR"` en `config/settings/base.py`
- [x] Añadir `RATELIMIT_IP_META_KEY = "HTTP_X_REAL_IP"` en `config/settings/prod.py`
- [x] `uv run pytest -q` verde
- [x] `uv run ruff check config/settings/`
- [x] `uv run python manage.py check --settings=config.settings.prod`
- [x] Actualizar `plans/README.md` fila 024 → DONE (nota: supercedido por 051)

## Fase 2 — Correctitud del motor (TDD fuerte)

### Plan 035 — Species guard en DPS
- [x] Escribir test `test_compute_best_moveset_missing_species_returns_none` en `engine/tests/test_dps.py`
- [x] Añadir guard `if species_key not in SPECIES: return None` en `engine/dps.py`
- [x] `uv run pytest engine/tests/test_dps.py -v` verde
- [x] `uv run ruff check engine/dps.py`
- [x] Actualizar `plans/README.md` fila 035 → DONE

### Plan 036 — Add missing DPS moves
- [x] Verificar `MoveData` signature en `engine/dps_data.py`
- [x] Verificar que terrakion/melmetal/tornadus_therian existen en SPECIES (terrakion sí; melmetal/tornadus_therian no — el guard de 035 los maneja)
- [x] Añadir `double_kick` a FAST_MOVES
- [x] Añadir `double_iron_bash` a CHARGE_MOVES
- [x] Añadir `hurricane` a CHARGE_MOVES
- [x] Escribir tests para las 3 especies en `engine/tests/test_dps.py`
- [x] `uv run pytest engine/tests/test_dps.py -v` verde
- [x] `uv run ruff check engine/dps_data.py`
- [x] Actualizar `plans/README.md` fila 036 → DONE

## Fase 3 — Performance y limpieza

### Plan 030 — dashboard_stats aggregate
- [x] Reemplazar 3 `.count()` por `aggregate(...)` en `apps/trades/services.py`
- [x] `uv run pytest apps/trades/ tests/ -v` verde
- [x] `uv run ruff check apps/trades/services.py`
- [x] Actualizar `plans/README.md` fila 030 → DONE

### Plan 041 — Analysis counts + audit PKs
- [x] Verificar qué tests inspeccionan `*_pks` en metadata
- [x] Fix `_hundo_rate_analysis` en `apps/analysis/services.py` → aggregate
- [x] Quitar `obs_pks`/`session_pks`/etc de `delete_account` metadata
- [x] Actualizar tests afectados
- [x] `uv run pytest apps/analysis/ apps/accounts/ tests/ -v` verde
- [x] `uv run ruff check apps/analysis/services.py apps/accounts/views.py`
- [x] Actualizar `plans/README.md` fila 041 → DONE

### Plan 043 — Mechanics lookups
- [x] Cambiar `resolve_trade_floor` a retornar `tuple[str, MechanicRuleSet | None]`
- [x] Actualizar callers en `apps/trades/services.py`
- [x] Añadir `is_published=True` en `_floor_for_version`
- [x] Pre-cargar rulesets en `build_dataset_version`
- [x] Actualizar tests/mocks de `resolve_trade_floor`
- [x] `uv run pytest apps/mechanics/ apps/trades/ apps/analysis/ apps/contributions/ -v` verde
- [x] `uv run ruff check` en los 4 archivos
- [x] Actualizar `plans/README.md` fila 043 → DONE

### Plan 032 — select_related session_detail
- [x] Añadir `.select_related("ruleset")` en `apps/trades/views.py` session_detail
- [x] `uv run pytest apps/trades/ tests/ -v` verde
- [x] `uv run ruff check apps/trades/views.py`
- [x] Actualizar `plans/README.md` fila 032 → DONE

### Plan 031 — Pagination (depende de 032)
- [x] Añadir `Paginator` en `session_list` (25/page) y `session_detail` (50/page)
- [x] Actualizar `templates/trades/session_list.html` con controles de paginación
- [x] Actualizar `templates/trades/session_detail.html` con controles de paginación
- [x] Actualizar tests existentes para usar `page_obj`
- [x] Añadir `test_session_list_pagination` y `test_session_detail_pagination`
- [x] `uv run pytest apps/trades/ tests/ -v` verde
- [x] `uv run ruff check apps/trades/views.py`
- [x] Actualizar `plans/README.md` fila 031 → DONE

### Plan 040 — Update stale docs
- [x] Actualizar `README.md` sección Estado (tabla de milestones)
- [x] Actualizar `AGENTS.md` sección Estado actual
- [x] Verificar que no queda "aún no hay código"
- [x] Actualizar `plans/README.md` fila 040 → DONE

## Fase 4 — Infraestructura / DX

### Plan 045 + 037 — Quality gates
- [x] `uv run ruff format .` (15 archivos)
- [x] Verificar diff puramente mecánico
- [x] Alinear pre-commit ruff con `>=0.15.22`
- [x] Hook mypy: `uv run mypy config engine apps tests`
- [x] Consolidar CI pytest+coverage en un paso
- [x] Añadir test de contrato de paridad
- [x] `uv run ruff format --check .` verde
- [x] `uv run pre-commit run --all-files` verde
- [x] `uv run mypy config engine apps tests` verde
- [ ] Actualizar `plans/README.md` filas 037 y 045 → DONE

### Plan 044 — Secret boundaries
- [x] Añadir patrón `.env-*` en `.gitignore` y `.dockerignore`
- [x] Reemplazar `COPY . .` en Dockerfile con allowlist
- [x] Test de build context con centinelas
- [x] `git check-ignore -v .env-tokenrouter .env-oci`
- [x] `uv run pytest -q` verde
- [x] Actualizar `plans/README.md` fila 044 → DONE

### Plan 050 — Fail-closed production email
- [x] Validar `EMAIL_URL` al importar `config/settings/prod.py`
- [x] Rechazar console/locmem/dummy/file backends en prod
- [x] Añadir `EMAIL_URL` obligatorio en `bin/setup-oci.sh`/Compose
- [x] Test `tests/test_settings.py`: prod sin EMAIL_URL o con console falla
- [x] `uv run pytest tests/test_settings.py tests/test_account.py -q` verde
- [x] Actualizar `plans/README.md` fila 050 → DONE

### Plan 049 — Completar account erasure
- [x] Inventario de relaciones reversas de User (allauth EmailAddress, MFA)
- [x] Borrar EmailAddress/Authenticator/sessions en la transacción
- [x] Quitar PKs de metadata de audit (hecho en plan 041)
- [x] Test con email centinela en User + EmailAddress + MFA falso
- [x] `uv run pytest tests/test_account.py apps/audit/ -q` verde
- [x] Actualizar `plans/README.md` fila 049 → DONE

### Plan 051 — Rate limiting robusto
- [ ] Verificar topología de proxy (STOP si no documentada)
- [ ] Función de key probada (IPv4/IPv6, listas, spoof)
- [ ] Caché compartida (PostgreSQL o documentar excepción)
- [ ] Test multiworker (requiere 056)
- [ ] Actualizar `plans/README.md` fila 051 → DONE

### Plan 056 — PostgreSQL CI gate
- [ ] Crear `config/settings/test_postgres.py`
- [ ] Añadir service postgres:16 en CI
- [ ] Job/matrix con `pytest -m postgres`
- [ ] `make test-postgres` en Makefile
- [ ] Guard anti `DATABASE_URL` no-test
- [ ] `docker compose up -d db` + `DATABASE_URL=... pytest -m postgres -q` verde
- [ ] Actualizar `plans/README.md` fila 056 → DONE

### Plan 057 — Bootstrap determinista
- [ ] Inventariar slugs de `seed` vs `seed_content`
- [ ] Resolver `iv-en-intercambios` (una sola definición)
- [ ] `make bootstrap`: levanta DB, espera health, migra, siembra
- [ ] Corregir `.env.example` puerto 5433
- [ ] Test idempotencia (`make bootstrap` x2)
- [ ] Actualizar `plans/README.md` fila 057 → DONE

### Plan 059 — Pin Tailwind
- [x] Fijar versión exacta + SHA-256 en `Makefile`
- [x] Soportar x64/arm64
- [x] CI reconstruye CSS, diff vacío
- [x] Test checksum incorrecto
- [x] Actualizar `plans/README.md` fila 059 → DONE

### Plan 058 — Reconciliar docs (al final)
- [ ] Actualizar `docs/milestones/` con estado real
- [ ] Reconciliar checkboxes contradictorios
- [ ] Actualizar `plans/README.md` fila 058 → DONE

## Fase 5 — Batch 4 grandes (dependen de 046 o son XL)

> Se abordan tras Fases 1–4. Cada uno requiere evaluación de alcance.

- [ ] 046 — Datos de combate canónicos
- [ ] 047 — Validar breakpoints (dep 046)
- [ ] 048 — Corregir PvP ranking (dep 046)
- [ ] 052 — Gobernar publicación (dep 056)
- [ ] 053 — Validar contratos calculadoras (dep 046)
- [ ] 054 — Analysis runs atómicos (dep 056)
- [ ] 055 — Endurecer trade ingestion (dep 056)
- [ ] 060 — Enforce app boundaries (dep 052, 054, 055)
- [ ] 061 — AuditEvent inmutable (dep 060)

## Revisiones periódicas

- [x] Iteración ~20: sub-agente "review spec.md and current implementation for gaps"
- [ ] Iteración ~40: sub-agente review
- [ ] Iteración ~60: sub-agente review

## Notas de bloqueo

(Si un plan se bloquea, documentar aquí por qué y qué se necesita.)
