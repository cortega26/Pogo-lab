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

## Fase 3 — Plan 048: corregir PvP ranking (dep. 046) — tiene STOP real

- [ ] Implementar HP entero real en `IVSpread` (usar `engine.stats.hp`, no `stam_val` continuo truncado al final)
- [ ] Corregir `stat_product` para no perder precisión antes de tiempo
- [ ] **STOP — preguntar al usuario** antes de publicar el cambio de ranking visible: ¿hay fuente real para validar al menos un caso (ej. Medicham), o se acepta como corrección determinista sin oráculo externo + nota de migración?
- [ ] Cachear `rank_for_league` con clave determinista `(species, base stats, max_cp, level_cap)`
- [ ] Fixtures actualizadas con nota explícita de "antes/después" y causa (no aceptar a ciegas)
- [ ] Suite + ruff + mypy verdes
- [ ] Actualizar `plans/README.md` fila 048 → DONE

## Fase 4 — Plan 053: validar contratos de calculadoras (dep. 046)

- [ ] Releer `plans/053-validate-calculator-contracts.md` completo (post-046/047/048)
- [ ] Inventariar las 8 calculadoras y sus parámetros de entrada + share-URL
- [ ] Diseñar contrato de validación reutilizable (`apps/calculators/`)
- [ ] Aplicar a cada calculadora; ningún input inválido produce 500
- [ ] Tests de contrato por calculadora (happy path + bordes)
- [ ] Suite + ruff + mypy verdes
- [ ] Actualizar `plans/README.md` fila 053 → DONE

## Fase 5 — Plan 060: límites entre apps

- [ ] Releer `plans/060-enforce-application-boundaries.md` completo
- [ ] Generar mapa actual de imports entre apps
- [ ] Definir DAG permitido en un ADR nuevo
- [ ] Extraer `AuditEvent.log` de modelos a servicios donde corresponda
- [ ] Mecanizar límites con contratos de `import-linter`
- [ ] `uv run lint-imports` verde
- [ ] Suite verde
- [ ] Actualizar `plans/README.md` fila 060 → DONE

## Fase 6 — Plan 061: AuditEvent inmutable (dep. 060)

- [ ] Releer `plans/061-enforce-audit-event-integrity.md` completo
- [ ] Admin de `AuditEvent` completamente readonly (bloquear add/change/delete)
- [ ] Bloquear `save()`/`delete()` de instancias ya persistidas a nivel de modelo
- [ ] Propagar `correlation_id` real (middleware → thread-local → todos los `AuditEvent.log`)
- [ ] Test: admin POST/delete bloqueados
- [ ] Test: `.save()` de instancia existente bloqueado
- [ ] Test: centinela de PII ausente en metadata
- [ ] Suite + ruff + mypy verdes
- [ ] Actualizar `plans/README.md` fila 061 → DONE

## Revisiones periódicas (sub-agente fresco)

- [ ] Tras cerrar Fase 1 (o iteración ~20, lo que ocurra primero): sub-agente "review spec.md and the current implementation for gaps"
- [ ] Tras cerrar Fase 3
- [ ] Tras cerrar Fase 6 (revisión final antes de proponer merge a main)

## Notas de bloqueo

(Si un plan se bloquea, documentar aquí por qué y qué se necesita.)
