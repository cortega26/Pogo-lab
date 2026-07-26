# TODO — Cierre de hallazgos P0/P1 restantes de `plans/`

> Spec canónico: `spec.md`. Marca `[x]` al completar cada sub-tarea verificada.
> Baseline (commit `f12a9dc`): 883 passed, 0 skipped; ruff/format/mypy limpios.
> Rama: `fix/plans-046-061-combat-data-integrity`.

## Fase 0 — Ya cerrado en sesiones previas (verificado contra `plans/README.md`, no re-tocar)

- [x] 029, 039, 044, 045, 049–052, 054–059 — DONE
- [x] Baseline de gates confirmado en esta sesión (883 pass, ruff/format/mypy limpios)

## Fase 1 — Plan 046: unificar datos de combate — **DONE**

- [x] Correr comparación programática de las 324 celdas (`types.py` vs `dps_data.py`) — 11 diffs confirmados y documentados en `spec.md` §3.1
- [x] `engine/tests/test_combat_data_parity.py`: test matricial 324 celdas (falló primero: 22 fallos, confirmado TDD-red)
- [x] Test puntual: `poison→grass == 1.6`
- [x] Test puntual: `rock→water == 1.0`
- [x] Test puntual: `rock→grass == 1.0`
- [x] Confirmar con `codegraph_impact`/grep quién importa `TYPE_EFFECTIVENESS`/`EFFECTIVENESS` (`apps/dps/services.py`, alias directo — sin más consumidores externos)
- [x] Reimplementar `TYPE_EFFECTIVENESS` como derivado de `engine.types.TYPE_CHART` (`_build_type_effectiveness()`); `type_multiplier` y el alias `EFFECTIVENESS` quedan intactos en su firma
- [x] Test: nivel fuera de rango en DPS lanza `ValueError` (no fallback a CPM_40) — `effective_atk(300, iv=15, level=999)` confirmado
- [x] Unificar `engine/dps.py` sobre `engine.stats.CPM_TABLE`/`cpm_for_level`; eliminados `CPM_VALUES`/`_cp_multiplier`/`CPM_40` propios
- [x] `apps/dps/views.py::_parse_level` valida contra niveles enteros válidos de `CPM_TABLE`; nivel inválido cae a 40 y el label mostrado siempre coincide con lo calculado (tests `test_invalid_level_does_not_500...`, `test_non_numeric_level_falls_back...`)
- [x] Recalcular fixtures de `engine/tests/test_dps.py` afectadas — solo 2 (`normal/ghost`, `ground/flying`, ambas de precisión); documentadas en `spec.md` §3.4.5
- [x] Añadir constante `COMBAT_DATA_VERSION = "combat-data-v1"` (identificador opaco, sin rótulo de versión oficial no verificada)
- [x] Gate anti-segunda-tabla: `engine/tests/test_no_duplicate_type_chart.py` (AST-based, falla si reaparece un dict grande de claves 2-tupla fuera de `engine/types.py`)
- [x] `uv run pytest engine/tests/test_combat_data_parity.py engine/tests/test_dps.py engine/tests/test_types.py engine/tests/test_no_duplicate_type_chart.py -q` verde
- [x] `uv run pytest -q` verde (sube de 883 por los tests nuevos de paridad/gate/vistas)
- [x] `uv run ruff check . && uv run ruff format --check .` limpio
- [x] `uv run mypy config engine apps tests` limpio (163 files)
- [x] `uv run lint-imports` verde (engine-purity KEPT)
- [x] `uv run python manage.py makemigrations --check --dry-run` sin cambios
- [x] Actualizar `plans/README.md` fila 046 → DONE
- [x] Commit de cierre de fase 1

## Fase 2 — Plan 047: validar breakpoints (dep. 046)

- [x] Bloqueo de learnsets documentado (spec.md §11) y resuelto por el usuario: deshabilitar/hacer honesto lo no verificable, avanzar con el resto
- [x] `get_fast_moves_for_species`: quitado comentario/código muerto de "filtro STAB" falso; docstring honesto
- [x] UI de breakpoints: aviso visible "se muestran todos los fast moves del motor, aún no verificamos cuáles aprende cada especie"
- [x] Test (TDD-red confirmado, 8 fallos): `find_breakpoints` rechaza `iv_atk` fuera de `[0, 15]`
- [x] Test: `find_breakpoints` rechaza `defender_def` no finito (`inf`/`nan`) o `<= 0` (incl. el `ZeroDivisionError` real reproducido antes del fix)
- [x] Test: `find_breakpoints` rechaza `min_level > max_level` o rango completamente fuera de la tabla CPM; test adicional para rango parcialmente solapado (se salta niveles fuera de tabla sin crashear)
- [x] Fixtures manuales para `_pve_damage` (sin modificadores, STAB, SE/doble-SE/NVE, clima, amistad, combinado, daño mínimo=1) — verificadas con cálculo independiente antes de escribirlas (un error mental propio corregido: 247→185)
- [x] `_move_choices_for` (apps/calculators/views.py) delega en `get_fast_moves_for_species`; imports `FM`/`DPS_SPECIES` no usados eliminados
- [x] Cobertura de `engine/breakpoints.py`: 31% → **100%** (2 tests extra para tipo secundario STAB y rango parcialmente fuera de tabla)
- [x] Suite completa 1251 passed; ruff/format/mypy (164 files)/lint-imports (engine-purity KEPT) verdes
- [x] Actualizar `plans/README.md` fila 047 → DONE
- [x] Commit de cierre de fase 2
- [x] Revisión de sub-agente: confirmó todo, encontró 1 hueco real (faltaban property tests del paso 3 del plan) → corregido con `TestFindBreakpointsProperties` (hypothesis); suite final 1252 passed

## Fase 3 — Plan 048: corregir PvP ranking (dep. 046) — tenía STOP real

- [x] **STOP resuelto por el usuario (2026-07-24):** implementar y publicar con nota de migración
- [x] Test (TDD-red confirmado, 3 fallos): `IVSpread.hp` ya no placeholder; `stat_product` usa HP entero; golden vector Medicham (1695612 buggy vs 1691183 correcto)
- [x] `IVSpread.hp` es ahora un campo real (antes `@property` muerta que devolvía 0)
- [x] `stat_product` usa `engine.stats.hp()` (HP entero) en vez de `stam_eff*cpm` continuo
- [x] `rank_for_league` popula `hp` real por spread
- [x] Evidencia concreta antes/después documentada en spec.md §5 (Medicham GL: #1 cambia de 5/15/15 a empate 5/15/14≈5/15/15)
- [x] `PVP_RANK_VERSION = "pvp-rank-v2"` — mecanismo de migración (invalida caché v1 automáticamente)
- [x] Caché determinista: `apps/calculators/services.py::top_spreads_cached` (patrón igual a `compute_scenario_cached`)
- [x] `apps/calculators/views.py::_pvp_result` usa `top_spreads_cached`; expone `hp` en el resultado
- [x] `_pvp_result.html`: columna HP nueva
- [x] Suite completa 1254 passed; ruff/format/mypy(164 files)/lint-imports/makemigrations verdes; coverage pvp_rank.py 98%
- [x] Actualizar `plans/README.md` fila 048 → DONE
- [x] Commit de cierre de fase 3
- [x] Revisión de sub-agente: confirmó golden vectors y mecanismo de caché; encontró 2 huecos reales (nota de migración no visible al usuario final; fix solo probado en Medicham GL) → ambos corregidos: aviso visible en `_pvp_result.html` + test, y `test_always_matches_integer_hp_formula` (hypothesis) + caso Azumarill/Ultra League; suite final 1257 passed

## Fase 4 — Plan 053: validar contratos de calculadoras (dep. 046) — DONE

- [x] Releer `plans/053-validate-calculator-contracts.md` completo
- [x] Inventariar las 8 calculadoras (`views.py`: cp, cost, pvp, catch, types, shiny, shadow, breakpoints)
- [x] Reproducir con pytest (no solo leer del plan) 5 bugs reales: codec AttributeError/KeyError, cost OverflowError (500 real confirmado), shiny ZeroDivisionError (500 real confirmado), shadow IV sin validar, cross-calculator share URL
- [x] `decode_calc_share`: límite de longitud, valida dict, valida `t`, nunca deja escapar AttributeError/KeyError
- [x] `_get_params`: rechaza share URL de otra calculadora (cae a defaults)
- [x] Nuevo helper `_parse_finite_float` (mismo estilo que los ya existentes); aplicado a cost/catch/shiny/shadow
- [x] `_parse_int_in_range` reutilizado para IVs de shadow y `n` de shiny
- [x] Tests TDD por bug (fallan primero, confirmado) + `TestGenericCalcShareCodec` (codec) + `TestCrossCalculatorShareURL`
- [x] Fuzz test genérico con hypothesis (`TestCalculatorFuzzing`, 19 combinaciones endpoint×campo × valores sospechosos) — cierra el paso 5 del plan
- [x] No se creó framework nuevo (helpers existentes + 1 nuevo bastaban, según pide el plan)
- [x] `tests/test_calculator_views.py` no se creó como archivo nuevo — se extendió `tests/test_sad_paths.py` (ya cubría exactamente ese propósito)
- [x] Suite completa 1268 passed; ruff/format/mypy(164 files)/lint-imports/makemigrations verdes
- [x] Actualizar `plans/README.md` fila 053 → DONE
- [x] Commit de cierre de fase 4
- [x] Revisión de sub-agente: confirmó los 5 bugs reales (reproducidos contra el commit padre) y el fuzz test sustantivo; encontró 1 hueco real (cp/shiny/shadow revalidaban el default ya sustituido, no el input crudo — "abc" nunca se rechazaba) → corregido en los 3 lugares + valores no numéricos agregados al fuzz test; suite final 1270 passed

## Fase 5 — Plan 060: límites entre apps — DONE

- [x] Releer `plans/060-enforce-application-boundaries.md` completo
- [x] Generar mapa actual de imports entre apps (`rg '^from apps\.'`) — confirmado el ciclo exacto de la evidencia (contributions.models -> audit.models; audit.services -> contributions.models + trades.models)
- [x] `apps.contributions.models`: quitado el import de `AuditEvent`; `grant_consent`/`revoke_consent` quedan como mutación pura (mantuvieron su firma — ~40 tests de setup dependían de ella)
- [x] `apps.contributions.services.grant_consent`/`revoke_consent`: orquestan mutación + auditoría; replicada con cuidado la semántica exacta de revoke (auditar solo si había consentimiento activo antes, no en doble-revoke — test `test_double_revoke_does_not_double_log`)
- [x] Vista de producción (`apps/contributions/views.py`) actualizada para usar los servicios, no el modelo; tests nuevos que verifican el AuditEvent end-to-end vía la vista real (`test_grant_view_creates_audit_event`, `test_revoke_view_creates_audit_event`)
- [x] `mark_observation` movido a `apps.trades.services` (dueño de `TradeObservation`)
- [x] `mark_dataset_suspicious` movido a `apps.contributions.services` (dueño de `DatasetVersion`)
- [x] `apps/audit/services.py` eliminado (quedó vacío); `apps.audit` es sink puro
- [x] Tests reubicados a las apps dueñas (`tests/test_trades.py::TestMarkObservation`, `apps/contributions/tests/test_contributions.py::TestMarkDatasetSuspicious`); `apps/audit/tests/test_audit.py` solo conserva `TestAuditEvent`
- [x] `pyproject.toml`: `root_packages` incluye `"apps"`; 2 contratos `forbidden` nuevos (`audit-is-a-sink-not-a-source`, `domain-models-do-not-import-audit`)
- [x] Verificado que los contratos detectan la regresión real (reintroduje el import viejo temporalmente, `lint-imports` lo cachó incluyendo la ruta transitiva vía `experiments.models`)
- [x] ADR nuevo `docs/adr/0011-limites-entre-apps.md` (+ agregado ADR-0010 al índice, faltaba de antes)
- [x] `uv run lint-imports` verde (3 contratos, 0 rotos)
- [x] Suite completa 1274 passed; ruff/format/mypy(163 files)/makemigrations verdes
- [x] Actualizar `plans/README.md` fila 060 → DONE
- [x] Commit de cierre de fase 5
- [x] Revisión de sub-agente: confirmó producción (AuditEvent vía vista real) y doble-revoke correctos; encontró 1 hallazgo real (`apps/core/metrics.py` código muerto rompía la invariante "core sin imports hacia arriba" que afirma la ADR) → eliminado (sin consumidores en todo el repo); ADR-0011 actualizado; suite sin cambio (1274 passed)

## Fase 6 — Plan 061: AuditEvent inmutable (dep. 060) — DONE

- [x] Releer `plans/061-enforce-audit-event-integrity.md` completo
- [x] Admin de `AuditEvent` completamente readonly — **ya estaba hecho** (verificado, no era cierto lo que decía el texto del plan original de 2026-07-21; `plans/README.md` ya lo marcaba PARTIAL con esto hecho)
- [x] Bloquear `save()`/`delete()` de instancias ya persistidas a nivel de modelo (`AuditEvent.save()`/`.delete()`) + `AuditEventQuerySet`/`Manager` propios bloqueando `.update()`/`.delete()` en bloque (el admin readonly no cubre esta vía)
- [x] Propagar `correlation_id` real: `AuditEvent.log()` hereda `get_correlation_id()` del thread-local cuando no se pasa explícito; fuera de request genera un UUID propio (nunca en blanco)
- [x] Hallazgo propio no listado en el plan original: el middleware confiaba ciegamente en el header `HTTP_X_CORRELATION_ID` del cliente — un valor con `\r\n` crasheaba con `BadHeaderError` (reproducido antes del fix). Nuevo `sanitize_correlation_id()` (charset seguro + longitud ≤64, si no cumple genera UUID nuevo), aplicado en middleware y en `AuditEvent.log` (defensa en profundidad)
- [x] Test: admin POST/delete bloqueados (ya existían, verdes)
- [x] Test: `.save()`/`.delete()` de instancia existente bloqueado + `.update()`/`.delete()` de queryset bloqueado (4 tests nuevos)
- [x] Test: propagación real de correlation_id (thread-local, fuera de request, HTTP end-to-end, header malicioso sanitizado, header válido preservado — 6 tests nuevos)
- [x] Test: scanner recursivo de centinela PII sobre un flujo completo (consentir → registrar → moderar → build dataset → moderar dataset → revocar); se detectó y corrigió un error propio en el diseño del test (centinela mezclado con texto de `reason` administrativo)
- [x] Suite completa 1286 passed; ruff/format/mypy(162 files)/lint-imports(3 contratos)/makemigrations verdes; confirmado por grep que ningún código de producción muta/borra AuditEvent directamente
- [x] Actualizar `plans/README.md` fila 061 → DONE
- [x] Commit de cierre de fase 6

## Revisiones periódicas (sub-agente fresco)

- [ ] Tras cerrar Fase 1 (o iteración ~20, lo que ocurra primero): sub-agente "review spec.md and the current implementation for gaps"
- [ ] Tras cerrar Fase 3
- [ ] Tras cerrar Fase 6 (revisión final antes de proponer merge a main)

## Notas de bloqueo

(Si un plan se bloquea, documentar aquí por qué y qué se necesita.)
