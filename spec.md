# Spec — Implementación ordenada de los hallazgos TODO de `plans/`

> **SSOT para esta sesión.** Lee este archivo antes de cada cambio. Cada
> implementación sigue TDD: test que falle primero, luego código, luego suite
> verde, luego marca en `todo.md`. Los planes se ejecutan en el orden
> recomendado por `plans/README.md` (P1 → P2 → P3, respetando dependencias).

## 1. Metas

1. **Archivar planes DONE.** Mover todos los archivos `plans/0NN-*.md` cuyo
   estado sea `DONE` a `plans/archive/`, dejando en `plans/` solo los pendientes
   y el `README.md`.
2. **Implementar los planes TODO restantes** de Batch 3 (022–043) y los P0/P1
   accionables de Batch 4 (044–059), en orden de prioridad y dependencia.
3. **No tocar los planes OPTION (062–064)**: requieren decisión de producto
   explícita y no están autorizados para implementación autónoma.
4. Cada plan termina con la suite completa verde (`uv run pytest -q`) y
   `uv run ruff check .` limpio, y su fila en `plans/README.md` actualizada a
   `DONE`.

## 2. Inventario inicial (estado verificado contra el código vivo al iniciar)

Planes verificados contra `engine/stat_tests.py`, `apps/core/views.py`,
`config/settings/`, `apps/accounts/views.py`, `apps/trades/{models,services,views}.py`,
`Dockerfile`, `.dockerignore`, `Makefile`, etc.:

| Plan | Estado verificado | Evidencia |
|---|---|---|
| 022 | **DONE** | `engine/stat_tests.py:105` ahora usa `norm_probs`; test de regresión verde |
| 023 | **DONE** (archived) | `engine/stat_tests.py:376` ya usa `min(len(sorted_rows), len(sorted_cols))` |
| 024 | **DONE** | `config/settings/prod.py:13` tiene `RATELIMIT_IP_META_KEY = "HTTP_X_REAL_IP"` |
| 025 | **DONE** (archived) | `apps/accounts/views.py` ya tiene `DeleteAccountForm` + `check_password` + `logout` |
| 026 | **DONE** (archived) | `config/settings/base.py:165` ya tiene `"form-action": [SELF]` |
| 027 | **DONE** (archived) | `engine/decisions.py` ya importa y llama `trades_for_confidence` |
| 028 | **DONE** | `apps/core/views.py` sanitiza CSP report (extrae csp-report, trunca, quita newlines) |
| 029 | **TODO** | `grep UniqueConstraint apps/trades/models.py` → 1 (pero hay que verificar `condition`) |
| 030 | **DONE** | `dashboard_stats` usa `.aggregate()` (no 3 `.count()`) |
| 031 | **DONE** | `Paginator` en `session_list` (25) y `session_detail` (50); templates actualizadas |
| 032 | **DONE** | `session_detail` usa `.select_related("ruleset")` |
| 033 | **DONE** (archived) | `.dockerignore` existe (704 bytes) |
| 034 | **DONE** (archived) | `config/settings/prod.py:8` ya tiene `CSRF_COOKIE_HTTPONLY = True` |
| 035 | **DONE** | `engine/dps.py:204` tiene guard `if species_key not in SPECIES: return None` |
| 036 | **DONE** | moves `double_kick`/`double_iron_bash`/`hurricane` añadidos a dps_data.py |
| 037 | **TODO** (merge con 045) | CI duplica pytest+coverage |
| 038 | **DONE** (archived; merge con 057) | `make seed` funciona; `seed` management command existe |
| 039 | **TODO** | `tests/test_dps_views.py` existe pero cobertura DPS views < 60% |
| 040 | **DONE** | README/AGENTS actualizados (ya no dicen "aún no hay código") |
| 041 | **DONE** | `_hundo_rate_analysis` usa aggregate; `delete_account` sin PKs en metadata |
| 042 | **DONE** | export filename usa SHA-256 hash del email (no PK) |
| 043 | **DONE** | `resolve_trade_floor` retorna instancia; `_floor_for_version` filtra `is_published`; `build_dataset_version` sin N+1 |
| 044–051, 056–061 | **TODO** | Batch 4, ver §4 |

## 3. Orden de ejecución (respetando dependencias y prioridad)

### Fase 1 — Contención (P1/P0 pequeños, sin dependencias)
1. **022** — Fix MC p-value normalization (1 línea + test).
2. **028** — Sanitize CSP report logging.
3. **042** — Fix export filename (no PK leak).
4. **024** — Rate limit IP meta key (config only).

### Fase 2 — Correctitud del motor (engine/, TDD fuerte)
5. **035** — Species guard en `compute_best_moveset`.
6. **036** — Add missing DPS moves (depende lógicamente de 035).

### Fase 3 — Performance y limpieza (P2/P3)
7. **030** — `dashboard_stats` triple COUNT → aggregate.
8. **041** — `_hundo_rate_analysis` double COUNT + quitar PKs de audit metadata.
9. **043** — `resolve_trade_floor` retorna instancia + `is_published` filter + preload.
10. **032** — `select_related("ruleset")` en session_detail.
11. **031** — Pagination en session_list y session_detail (depende de 032).
12. **040** — Update stale README + AGENTS.

### Fase 4 — Infraestructura / DX (P2/P1)
13. **037** (merge con **045**) — Restaurar gates: `ruff format`, pre-commit, CI.
14. **044** — Secret boundaries (`.env-*`, Dockerfile allowlist).
15. **050** — Fail-closed production email.
16. **049** — Completar borrado de cuenta (allauth/MFA + quitar PKs).
17. **051** — Rate limiting robusto (supercede 024; requiere 056 para multiworker).
18. **056** — PostgreSQL CI gate.
19. **057** — Bootstrap determinista (supercede 038).
20. **059** — Pin Tailwind toolchain.
21. **058** — Reconciliar docs de estado (depende de 045–057).

### Fase 5 — Batch 4 grandes (P0/P1, dependen de 046 o son XL)
22. **046** — Datos de combate canónicos (L, HIGH) — evaluación de alcance.
23. **047** — Validar breakpoints (depende 046).
24. **048** — Corregir PvP ranking (depende 046).
25. **052** — Gobernar publicación comunidad (depende 056).
26. **053** — Validar contratos de calculadoras (depende 046).
27. **054** — Analysis runs atómicos (depende 056).
28. **055** — Endurecer trade ingestion (depende 056).
29. **060** — Enforce app boundaries (depende 052, 054, 055).
30. **061** — AuditEvent inmutable + correlation_id (depende 060).

> **Nota de alcance:** Los planes 046–048, 052–055, 060–061 son de esfuerzo
> L/XL y riesgo HIGH, y varios dependen de decisiones de datos canónicos o
> del gate PostgreSQL. Se abordan tras las Fases 1–4. Si un plan excede el
> alcance razonable de una sesión (ej. requiere datamining completo), se
> documenta el avance parcial en `todo.md` y se deja el plan en `TODO` con
> un comentario de bloqueo.

## 4. Detalles de implementación por plan

### Plan 022 — MC p-value normalization
- **Archivo:** `engine/stat_tests.py:105`.
- **Cambio:** `sim_expected = np.array([p * n_total for p in norm_probs])`.
- **Test:** `test_monte_carlo_normalizes_probs` en
  `engine/tests/test_stat_tests.py`: pasa `probs=[0.3,0.3,0.3]` (suma 0.9),
  verifica `0 < p_value < 1` y `method_used == "monte_carlo"`.
- **Verificación:** `uv run pytest engine/tests/test_stat_tests.py -v` verde.

### Plan 028 — CSP report sanitization
- **Archivo:** `apps/core/views.py`.
- **Cambio:** Extraer `csp_data = report.get("csp-report", {})`, construir
  `sanitized` dict con `blocked-uri` truncado a 200 chars y newlines
  reemplazados por espacios; loguear `sanitized` no `report`.
- **Test:** `test_csp_report_handles_malicious_uri` en `tests/test_security.py`
  envía `blocked-uri` con `\nFAKE` y verifica 200.

### Plan 042 — Export filename sin PK
- **Archivo:** `apps/accounts/views.py:110`.
- **Cambio:** `safe_id = hashlib.sha256(request.user.email.encode()).hexdigest()[:16]`.
- **Test:** `test_export_filename_does_not_leak_pk` en `tests/test_account.py`.

### Plan 024 — Rate limit IP meta key
- **Archivos:** `config/settings/base.py` (añadir
  `RATELIMIT_IP_META_KEY = "REMOTE_ADDR"`) y `config/settings/prod.py` (añadir
  `RATELIMIT_IP_META_KEY = "HTTP_X_REAL_IP"`).
- **Verificación nginx:** `infra/nginx/default.conf` ya setea `X-Real-IP`.
- **Test:** `grep` verification + `manage.py check --settings=config.settings.prod`.

### Plan 035 — Species guard
- **Archivo:** `engine/dps.py`, función `compute_best_moveset`.
- **Cambio:** Tras `if species_key not in BEST_MOVESETS: return None`, añadir
  `if species_key not in SPECIES: return None`.
- **Test:** `test_compute_best_moveset_missing_species_returns_none` en
  `engine/tests/test_dps.py` (usa `"roaring_moon"` que está en BEST_MOVESETS
  pero no en SPECIES).

### Plan 036 — Missing DPS moves
- **Archivo:** `engine/dps_data.py`.
- **Cambios:** Añadir a `FAST_MOVES`: `"double_kick": MoveData("fighting", 10.0, 1.0, 8.0)`.
  Añadir a `CHARGE_MOVES`: `"double_iron_bash": MoveData("steel", 100.0, 2.0)`,
  `"hurricane": MoveData("flying", 110.0, 2.7)`.
- **Tests:** `test_terrakion_has_valid_moves`, `test_melmetal_has_valid_moves`,
  `test_tornadus_therian_has_valid_moves` en `engine/tests/test_dps.py`.
  (Verificar primero que las especies existen en SPECIES; si no, el test
  verifica `result is None` tras el guard de 035.)

### Plan 030 — dashboard_stats aggregate
- **Archivo:** `apps/trades/services.py`, función `dashboard_stats`.
- **Cambio:** `base.aggregate(total=Count("id"), lucky=Count("pk", filter=Q(is_lucky=True)), normal=Count("pk", filter=Q(is_lucky=False)))`.
- **Verificación:** tests existentes de `dashboard_stats` pasan sin cambios.

### Plan 041 — Analysis counts + audit PKs
- **Archivos:** `apps/analysis/services.py` (`_hundo_rate_analysis` →
  `aggregate(n=..., successes=Count("pk", filter=Q(...)))`),
  `apps/accounts/views.py` (quitar `*_pks` de metadata, dejar solo `*_count`).
- **Test:** buscar `grep -rn "observation_pks\|session_pks" tests/` y actualizar.

### Plan 043 — Mechanics lookups
- **Archivos:** `apps/mechanics/services.py` (`resolve_trade_floor` retorna
  `tuple[str, MechanicRuleSet | None]`), `apps/trades/services.py` (usar
  instancia retornada), `apps/analysis/services.py` (`_floor_for_version` añade
  `is_published=True`), `apps/contributions/services.py`
  (`build_dataset_version` pre-carga rulesets_map).
- **Test:** actualizar callers/mocks de `resolve_trade_floor`.

### Plan 032 → 031 — select_related + pagination
- **032:** `apps/trades/views.py` `session_detail` añade
  `.select_related("ruleset")`.
- **031:** Añade `Paginator(qs, 25)` (sessions) y `Paginator(qs, 50)` (obs).
  Actualiza templates `session_list.html` y `session_detail.html` con controles
  de paginación. Actualiza tests para usar `page_obj`.

### Plan 040 — Docs
- **Archivos:** `README.md` (Estado → beta con tabla de milestones), `AGENTS.md`
  (Estado actual → beta, nota `.codegraph/`, nota tooling M1).

### Plan 037 + 045 — Quality gates
- **045:** `uv run ruff format .` (15 archivos), alinear pre-commit
  (`ruff>=0.15.22`), hook mypy con targets `config engine apps tests`, consolidar
  CI pytest+coverage en un paso. Añadir test de contrato de paridad.
- **037:** Absorbido por 045 (misma duplicación de CI).

### Plan 044 — Secret boundaries
- **Archivos:** `.gitignore`, `.dockerignore` (patrón `.env-*`), `Dockerfile`
  (allowlist en vez de `COPY . .`).
- **Test:** test de build context con centinelas.

### Plan 050 — Fail-closed email
- **Archivo:** `config/settings/prod.py` (validar `EMAIL_URL` al importar).
- **Test:** `tests/test_settings.py`: prod sin `EMAIL_URL` o con `consolemail://`
  falla al cargar.

### Plan 049 — Account erasure completo
- **Archivo:** `apps/accounts/views.py` (borrar `EmailAddress`,
  `Authenticator`, sessions dentro de la transacción; quitar PKs de metadata).
- **Test:** test con email centinela en User + EmailAddress, MFA falso, sesión;
  verificar ausencia del centinela tras borrar.

### Plan 051 — Rate limiting robusto (supercede 024)
- Requiere topología de proxy conocida + caché compartida (PostgreSQL o Redis).
- Si la topología no está documentada → STOP y dejar 024 como interim.

### Plan 056 — PostgreSQL CI gate
- **Archivos:** `config/settings/test_postgres.py`, `.github/workflows/ci.yml`
  (service postgres:16, job/matrix con `pytest -m postgres`), `Makefile`
  (`test-postgres`).
- **STOP:** si `DATABASE_URL` no identifica DB de test.

### Plan 057 — Bootstrap determinista (supercede 038)
- **Archivos:** `Makefile` (`bootstrap` levanta DB, espera health, migra,
  siembra), `.env.example` (puerto 5433), `seed` command (orquesta
  `seed_mechanics` + `seed_content` sin duplicar).
- **Test:** idempotencia (`make bootstrap` x2), checksum de slugs.

### Plan 059 — Pin Tailwind
- **Archivos:** `Makefile` (`tailwind-install` con versión+checksum+arch),
  `tailwind.config.js`, CI reconstruye CSS.
- **Test:** checksum incorrecto nunca se ejecuta.

### Plan 058 — Reconciliar docs (al final)
- Actualiza `docs/milestones/` y estado real tras Fases 1–4.

### Planes 046–048, 052–055, 060–061
- Se abordan tras Fases 1–4. Cada uno tiene su drift check y STOP conditions.
- 046 requiere unificación de datos de combate (esfuerzo L); 052/054/055
  requieren gate PostgreSQL (056) como prerrequisito.

## 5. Verificación (cómo se demuestra que cada pieza funciona)

### Por plan
Cada plan tiene sus propios comandos de verificación en su archivo. En
general, para marcar un plan como `DONE`:
1. **Test específico del plan pasa:** `uv run pytest <test_especifico> -v`.
2. **Suite completa verde:** `uv run pytest -q` → 0 failed (o +1 test por cada
   test nuevo añadido).
3. **Lint limpio:** `uv run ruff check <archivos_modificados>`.
4. **Mypy limpio** (si se tocaron archivos tipados):
   `uv run mypy config engine apps tests`.
5. **Migraciones** (si aplica): `uv run python manage.py makemigrations --check --dry-run` sin cambios pendientes.
6. **Sin archivos fuera de alcance modificados:** `git diff --stat` solo muestra
   los archivos listados en el plan.

### Por fase
- **Fase 1 (contención):** Suite verde + `ruff check` + `mypy` limpio. Los tests
  de seguridad (`tests/test_security.py`) cubren 028 y 024 (config).
- **Fase 2 (motor):** `uv run pytest engine/tests/ -v` verde. Los tests del
  engine usan fixtures calculadas a mano (AGENTS.md regla 4).
- **Fase 3 (perf):** `uv run pytest apps/ tests/ -q` verde. Verificación de
  reducción de queries con `django.assertNumQueries` donde aplique.
- **Fase 4 (infra):** `uv run ruff format --check .` verde (045). Docker build
  sin secretos (044). `manage.py check --settings=config.settings.prod` falla
  sin `EMAIL_URL` (050). `make bootstrap` idempotente (057).

### Tests end-to-end (`tests/`)
- **`tests/test_plans_regression.py`** (nuevo): un test por plan implementado,
  que documenta el fix y verifica la no-regresión. Ej:
  - `test_plan_022_mc_normalizes_probs`
  - `test_plan_028_csp_report_sanitized`
  - `test_plan_042_export_filename_no_pk`
  - etc.
- Estos tests son la "fuente de verdad" de que cada plan quedó implementado.
- Se ejecutan con `uv run pytest tests/test_plans_regression.py -v`.

### Loop de revisión (cada ~20 iteraciones)
- Llamar a un sub-agente con: "review spec.md and the current implementation
  for gaps".
- El sub-agente debe: leer `spec.md`, leer `todo.md`, ejecutar la suite,
  verificar que los planes marcados DONE están realmente implementados y
  verificados, y reportar gaps.
- Iterar hasta alineación.

## 6. Convenciones y reglas (de AGENTS.md, no negociables)

- **Idioma:** español neutral (sin voseo).
- **Comentarios:** no añadir comentarios salvo que se pidan.
- **TDD en `engine/`:** tests con fixtures calculadas a mano primero.
- **Honestidad estadística:** distinguir "compatible con el modelo" de
  "modelo demostrado".
- **`engine/` puro:** sin imports de Django.
- **Sin commits** salvo que el usuario los pida explícitamente.
- **Suite verde obligatoria:** ningún plan se marca DONE sin `uv run pytest -q`
  en verde (regla 9 de AGENTS.md).

## 7. Gestión de `plans/README.md`

- Al archivar un plan DONE, mover el archivo a `plans/archive/` y actualizar su
  fila en `plans/README.md` a `DONE | archived`.
- Al completar un plan TODO, actualizar su fila a `DONE` (sin archivar aún,
  hasta el final de la sesión).
- Al final de la sesión, mover todos los DONE a `plans/archive/`.
