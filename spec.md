# Spec — Cierre de hallazgos P0/P1 restantes de `plans/` (batch 2026-07-21)

> **SSOT para esta sesión.** Lee este archivo antes de cada cambio. Cada
> implementación sigue TDD: test que falle primero, luego código, luego suite
> verde, luego marca en `todo.md`.
>
> Este documento **reemplaza el estado** de la versión anterior (commit
> `4112545`/`217864f`/`c1e4376`), que quedó desactualizada: las fases 1, 2, 3
> (parcial) y 5 ya se completaron en sesiones previas y están verificadas en
> `plans/README.md`. Solo se detalla aquí lo que sigue **TODO/PARTIAL**.

## 0. Regla de procedencia (no negociable, motivo del audit M2)

Esta sesión toca datos de combate (type chart, CPM, stat product) donde la
tentación de citar "la mecánica conocida de Pokémon" es alta. **Prohibido**:

- Afirmar que un valor está "verificado contra Game Master" o contra una
  versión oficial (`v0.295+`, etc.) sin un archivo/URL real que lo respalde.
- Usar "es de conocimiento general" como justificación de un fixture.

**Permitido y exigido:**

- Justificar cada fixture nuevo como *"derivado de `engine/types.py` (SSOT
  designado por el plan 046) + comparación exhaustiva de 324 celdas"* —
  la comparación programática ya se corrió en esta sesión y es evidencia
  primaria real, reproducible con el script en §3.1.
- Cualquier `data_version`/snapshot que se introduzca usa un identificador
  opaco (ej. `combat-data-v1`) con la nota "derivado de `engine/types.py`",
  nunca un rótulo que implique verificación externa no realizada.
- Si en cualquier plan (especialmente 048) no hay una fuente primaria citable
  para un valor y no puede derivarse por cálculo puro desde reglas ya
  verificadas (CPM, stats base), **STOP**: documentar el bloqueo aquí y
  preguntar al usuario. Esto no es una "duda resoluble leyendo el spec" —
  es una decisión de producto/dato que solo el usuario puede tomar.

## 1. Metas

1. Cerrar, en orden de dependencia, los planes que siguen **TODO/PARTIAL**
   en `plans/README.md`: **046 → 047 → 048 → 053 → 060 → 061**.
2. Una tabla de tipos única (`engine/types.py`); eliminar la duplicada de
   `engine/dps_data.py` sin romper la firma pública `type_multiplier(str, str,
   str | None)` que consumen `engine/dps.py` y `engine/breakpoints.py`.
3. Ningún nivel/IV/parámetro fuera de rango debe degradarse en silencio
   (fallback a CPM 40, división por cero, etc.) — falla controlada o rechazo.
4. Cada plan cerrado deja: test que fallaba antes del fix, fixtures nuevas
   documentadas con su procedencia, `plans/README.md` actualizado a DONE,
   y la fila correspondiente en este spec + `todo.md` marcada.
5. Trabajo en rama `fix/plans-046-061-combat-data-integrity` (no en `main`
   directo, dado el riesgo P0/HIGH de estos cambios sobre calculadoras que
   ya sirven tráfico real). Merge a `main` solo tras suite verde + revisión
   de sub-agente fresco.

## 2. Inventario verificado (commit base `f12a9dc`, 2026-07-24)

```
uv run pytest -q            → 883 passed, 0 skipped
uv run ruff check .         → All checks passed
uv run ruff format --check . → 190 files already formatted
uv run mypy config engine apps tests → 0 errors, 161 files
```

| Plan | Estado (plans/README.md) | Esta sesión |
|---|---|---|
| 029, 039, 044, 045, 049–052, 054–059 | DONE (archived o no) | No tocar |
| **046** | TODO | **Fase 1 — implementar ahora** |
| **047** | TODO (dep 046) | Fase 2 |
| **048** | TODO (dep 046) | Fase 3 — **tiene un STOP real, ver §5** |
| **053** | TODO (dep 046) | Fase 4 |
| **060** | TODO | Fase 5 |
| **061** | PARTIAL (dep 060) | Fase 6 |
| 062–064 | OPTION | **No tocar** — decisión de producto, no autorizada |

## 3. Fase 1 — Plan 046: unificar datos de combate — **DONE**

Implementado y verificado en esta sesión (rama
`fix/plans-046-061-combat-data-integrity`). Suite completa 1226 passed,
ruff/format/mypy/lint-imports/makemigrations limpios.

**Revisión de sub-agente fresco (checkpoint §10):** confirmó las 11 diffs y
el resto de la implementación, pero encontró 2 huecos reales que se
corrigieron antes de cerrar la fase:

1. `apps/dps/views.py::_parse_level` corregía el mismatch etiqueta/CPM pero
   lo hacía en silencio, sin aviso visible — contradecía lo que esta misma
   sección prometía ("siempre error controlado"). Fix: `_parse_level` ahora
   devuelve `(nivel, hubo_valor_invalido)`; las vistas exponen
   `level_invalid` en el contexto y las plantillas (`_ranking.html`,
   `compare.html`) muestran un aviso visible reusando el patrón `{% if
   error %}` ya establecido en `apps/calculators/templates/`.
2. El gate anti-segunda-tabla solo detectaba diccionarios literales de
   clave 2-tupla; no detectaba el patrón de asignación por doble subíndice
   (`TABLA[a][b] = valor`) que usa el propio `engine/types.py`. Se añadió
   un segundo detector AST (conteo de asignaciones por doble subíndice
   sobre el mismo nombre, umbral 30) — verificado que dispara con un
   archivo señuelo de 35 asignaciones y no da falso positivo hoy.

Hallazgos menores también corregidos: docstring de `engine/types.py`
decía "Inmune: ×0.39" (ahora ×0.390625, consistente con la constante real);
`COMBAT_DATA_VERSION` ahora tiene tests propios (no queda como código
muerto sin consumidor).

### 3.1 Evidencia verificada en esta sesión

Script comparativo real (no memoria): construye las 324 celdas de
`engine.types.TYPE_CHART` y las 324 celdas equivalentes derivadas de
`engine.dps_data.TYPE_EFFECTIVENESS` (con default 1.0 para pares ausentes) y
las compara con tolerancia `1e-9`. Resultado exacto:

```
Total diffs: 11
('dragon', 'fairy'):   types.py=0.390625  dps_data=0.39
('electric', 'ground'):types.py=0.390625  dps_data=0.39
('fighting', 'ghost'): types.py=0.390625  dps_data=0.39
('ghost', 'normal'):   types.py=0.390625  dps_data=0.39
('ground', 'flying'):  types.py=0.390625  dps_data=0.39
('normal', 'ghost'):   types.py=0.390625  dps_data=0.39
('poison', 'grass'):   types.py=1.6       dps_data=1.0   ← semántico (falta SE)
('poison', 'steel'):   types.py=0.390625  dps_data=0.39
('psychic', 'dark'):   types.py=0.390625  dps_data=0.39
('rock', 'grass'):     types.py=1.0       dps_data=0.625 ← semántico (no existe)
('rock', 'water'):     types.py=1.0       dps_data=0.625 ← semántico (no existe)
```

8 son de precisión (`0.39` vs `0.390625`, mismo signo/dirección — redondeo).
3 son semánticas: falta Poison→Grass súper efectivo; Rock→Water y Rock→Grass
no existen en la mecánica real (`engine/types.py` los deja en 1.0 por
`dict.fromkeys` default) pero `dps_data.py` los marca como resistidos.

`engine/types.py` es internamente consistente (18 tipos × 18 tipos completos,
cada fila tiene el número esperado de entradas SE/NVE/inmune sin huecos) y es
el que el propio plan 046 designa como SSOT. **No se re-verifica contra una
fuente externa** — eso violaría §0. Se adopta por: (a) mandato explícito del
plan 046, (b) consistencia interna verificable en el propio archivo.

### 3.2 Segundo bug confirmado: fallback silencioso de nivel/CPM

`engine/dps.py::_cp_multiplier(level: int)` usa una tabla `CPM_VALUES`
**distinta** de `engine.stats.CPM_TABLE` (tercera tabla duplicada). Si
`level` no está en el rango de interpolación, cae al `return CPM_40` final
sin avisar. `apps/dps/views.py::_parse_level` acepta cualquier `int` sin
rango. Combinados: `?level=999` renderiza "nivel 999" en la plantilla pero
calcula con el CPM de nivel 40.

### 3.3 Diseño

- `engine/types.py` es la única fuente de efectividad de tipos.
- `engine/dps_data.py::type_multiplier(attack_type: str, defender_type1: str,
  defender_type2: str | None) -> float` se reimplementa como adaptador: castea
  los strings a `PokemonType` y delega en `engine.types.type_effectiveness`.
  Se elimina el diccionario `TYPE_EFFECTIVENESS` (o se deja como alias
  `= None` marcado deprecated si algo externo lo importa — verificar
  `codegraph_callers` antes de borrar).
- `engine/dps.py` reutiliza `engine.stats.CPM_TABLE`/`cpm_for_level` en vez de
  su propio `CPM_VALUES`/`_cp_multiplier`. Los niveles fuera de tabla
  **lanzan `ValueError`**, nunca hacen fallback.
- `apps/dps/views.py::_parse_level` y `apps/calculators/views.py` (breakpoints,
  DPS) capturan ese `ValueError` y devuelven un error de UI legible (no 500,
  no fallback silencioso, no CPM_40 con etiqueta mentirosa).
- Metadato de snapshot: constante `COMBAT_DATA_VERSION = "combat-data-v1"` en
  `engine/types.py` (o módulo nuevo `engine/combat_data_version.py`) con
  docstring "derivado de engine/types.py, ver plans/046". Sin rótulo de
  versión de juego real.
- Gate anti-regresión: test que falla si aparece una segunda estructura
  `dict[tuple[str, str], float]` o `dict[Enum, dict[Enum, float]]` de 18×18
  en el árbol `engine/` fuera de `engine/types.py` (búsqueda AST o grep
  estructural sobre nombres de módulo, no un simple grep de texto frágil).

### 3.4.5 Deltas de fixtures documentados (implementado)

Solo 2 fixtures de `engine/tests/test_dps.py` dependían de un valor de los 11
corregidos, y ambas por la misma causa (precisión, no semántica):

| Test | Antes | Después | Causa |
|---|---|---|---|
| `test_normal_vs_ghost_is_immune` | `== 0.39` | `pytest.approx(0.390625)` | normal→ghost es uno de los 8 pares de precisión (§3.1) |
| `test_ground_vs_flying_is_immune` | `== 0.39` | `pytest.approx(0.390625)` | ground→flying es uno de los 8 pares de precisión (§3.1) |

Ninguna otra fixture de DPS/PvP/breakpoints usa las celdas semánticas
corregidas (poison/grass, rock/water, rock/grass) en sus escenarios de
prueba actuales, así que no hubo más deltas numéricos en esta fase.

### 3.4 Pasos (orden de ejecución)

1. `engine/tests/test_combat_data_parity.py` (nuevo): test matricial 324
   celdas que compara `dps_data.type_multiplier` contra
   `engine.types.type_effectiveness` para **todo par de tipos**, más 3 tests
   puntuales para los semánticos (`poison/grass == 1.6`, `rock/water == 1.0`,
   `rock/grass == 1.0`). **Debe fallar primero** contra el código actual.
2. Reimplementar `dps_data.type_multiplier` sobre `engine.types`; eliminar
   `TYPE_EFFECTIVENESS`. Confirmar con `codegraph_callers` que nadie más
   importa `TYPE_EFFECTIVENESS` directamente antes de borrar.
3. Test de nivel inválido: `engine/tests/test_dps.py` nuevo caso —
   `effective_atk(base, level=999)` (o la función que corresponda tras
   unificar con `engine.stats`) lanza `ValueError`; vista captura y no 500.
4. Unificar `engine/dps.py` sobre `engine.stats.CPM_TABLE`/`cpm_for_level`;
   eliminar `CPM_VALUES`/`_cp_multiplier` propios.
5. Recalcular fixtures de `engine/tests/test_dps.py` que dependan de los 11
   valores corregidos o del CPM unificado. **Para cada fixture que cambie de
   valor: registrar aquí (en una tabla nueva bajo este punto) el before/after
   y la celda de tipo que lo causa** — no aceptar el nuevo número sin
   explicar de qué diff viene.
6. Añadir el gate anti-segunda-tabla (paso 3.3).
7. Suite completa + ruff + mypy + `lint-imports` + `makemigrations --check`.
8. Actualizar `plans/README.md` fila 046 → DONE (con commit real).

### 3.5 Verificación

```bash
uv run pytest engine/tests/test_combat_data_parity.py engine/tests/test_dps.py engine/tests/test_types.py -q
uv run pytest -q
uv run ruff check . && uv run ruff format --check .
uv run mypy config engine apps tests
uv run lint-imports
uv run python manage.py makemigrations --check --dry-run
```

### 3.6 Criterios de terminado

- Una sola tabla de tipos en todo `engine/`; los 324 pares coinciden byte
  a byte entre cualquier consumidor y `engine.types.TYPE_CHART`.
- Ningún nivel fuera de la tabla CPM produce resultado silencioso; siempre
  error controlado con el nivel real en el mensaje.
- Cada delta de fixture DPS está documentado con su causa (§3.4.5).
- Gate anti-segunda-tabla en verde y falla si se reintroduce una duplicada.

## 4. Fase 2 — Plan 047: validar breakpoints (dep. 046)

**Decisión del usuario (2026-07-24), resolviendo el bloqueo de §11:** no hay
datos de learnset (qué fast/charge move aprende cada especie) en el repo ni
fuente primaria citable para fabricarlos. Se opta por **"deshabilitar
temporalmente lo no verificable"**: en vez de aparentar que la lista de
movimientos está filtrada por especie (falso hoy — devuelve el catálogo
completo bajo un comentario engañoso que dice filtrar por STAB sin hacerlo),
se hace **explícito y honesto** que la lista es el catálogo completo del
motor, no un learnset verificado, mientras se avanza con el resto del plan
que sí es derivable de reglas ya verificadas (fórmula PvE documentada en el
propio módulo + tabla de tipos de la Fase 1 + tabla CPM).

Alcance de esta fase:

1. `get_fast_moves_for_species`: eliminar el comentario/código muerto que
   afirma filtrar por STAB sin hacerlo; documentar honestamente la
   limitación (catálogo completo, no learnset verificado).
2. UI de breakpoints: aviso visible de que los movimientos no están
   verificados contra el learnset real de la especie.
3. `find_breakpoints` rechaza (con test que falla primero):
   `iv_atk` fuera de `[0, 15]`; `defender_def` no finito o `<= 0` (fixes el
   `ZeroDivisionError` real con `defender_def=0`); `min_level > max_level`
   o ambos fuera del rango de la tabla CPM canónica.
4. Fixtures manuales para `_pve_damage` (STAB on/off, efectividad
   simple/doble usando los valores ya corregidos en Fase 1, clima,
   amistad) — derivables por cálculo puro de la fórmula ya documentada,
   sin requerir fuente externa nueva.
5. Eliminar la duplicación de "todos los movimientos" entre
   `engine/breakpoints.py::get_fast_moves_for_species` y
   `apps/calculators/views.py::_move_choices_for` (el selector debe llamar
   al mismo helper del engine, no reimplementar el loop).
6. Subir cobertura de `engine/breakpoints.py` sobre el 31% actual con estos
   golden vectors.

**Estado: DONE.** Cobertura 31%→100%. Suite 1251 passed; ruff/format/mypy/
lint-imports limpios. Golden vectors de `_pve_damage` verificados con un
cálculo independiente antes de escribirlos (se detectó y corrigió un error
aritmético propio: 247 en vez de 185 para el caso combinado — la lección es
no confiar en aritmética mental para fixtures, siempre verificar con
código). `_move_choices_for` ya no duplica el loop de `FAST_MOVES`.

**Revisión de sub-agente fresco (checkpoint §10):** confirmó todas las
afirmaciones anteriores (incluido el recálculo independiente de 8/8 golden
vectors) y el aviso de "no verificado" está bien puesto (única plantilla
con el selector; el swap HTMX solo reemplaza la tabla de resultados, no el
selector, así que el aviso queda siempre visible). Encontró **1 hueco
real**: el paso 3 del plan pedía property tests (niveles ordenados, daño
monótono, `max_results` respetado, nunca NaN/inf) que no se habían escrito
pese al 100% de cobertura por líneas. **Corregido:** se añadió
`TestFindBreakpointsProperties` con `hypothesis` (`@given` sobre especie,
movimiento, iv_atk, defender_def, max_results reales) verificando las 4
propiedades en un solo test combinado. Suite final: 1252 passed.

## 5. Fase 3 — Plan 048: corregir PvP ranking (dep. 046) — **DONE**

**Decisión del usuario (2026-07-24), resolviendo el STOP:** implementar el
fix determinista y publicarlo con nota de migración (sin esperar un
oráculo externo), ya que el cálculo es puro sobre reglas ya verificadas
en este repo (`engine.stats.cp`/`hp`, CPM_TABLE).

**Fix:** `stat_product` multiplicaba `stam_eff * cpm` continuo en vez del
HP entero real (`engine.stats.hp`: `max(10, floor(stam_eff*cpm))`).
`IVSpread.hp` además era una `@property` que siempre devolvía `0` (código
muerto — el comentario decía "se completa en el constructor" pero nunca
pasaba). Ahora `hp` es un campo real poblado en `rank_for_league`, y
`stat_product` usa `engine.stats.hp()` para el componente HP.

**Evidencia concreta del cambio visible (antes/después), Medicham Great
League (121/152/155, max_cp=1500, level_cap=50):**

```
ANTES (bug)  #1: IVs 5/15/15, nivel 50.0, CP 1499, stat_product 2122457
DESPUÉS (fix) #1: empate IVs 5/15/14 (CP 1494) y 5/15/15 (CP 1499),
               ambos stat_product 2109813 (gana 5/15/14 por orden de
               generación en el empate exacto)
```

Calculado ejecutando ambas versiones del algoritmo (la anterior reimplementada
localmente para comparar, no una fuente externa) contra el código real de este
repo — ver commit para el script de comparación usado.

**Nota de migración (mecanismo + registro):** `PVP_RANK_VERSION` pasa de un
"v1" implícito (no documentado, previo a este plan) a `"pvp-rank-v2"`
(`engine/pvp_rank.py`). La clave de caché de `apps.calculators.services
.top_spreads_cached` incluye esta versión, así que un despliegue nunca
sirve un ranking v1 obsoleto desde caché — el bump de versión ES el
mecanismo técnico de migración, documentado además en el docstring del
módulo y aquí. También se agregó caché determinista (antes recalculaba
4096 combinaciones × niveles en cada request) y se expone `hp` en la UI
(`_pvp_result.html`, nueva columna).

**Verificación:** 1254 passed (era 1252 antes de esta fase); coverage de
`engine/pvp_rank.py` 98% (única línea sin cubrir es un `return` defensivo
inalcanzable preexistente, fuera de alcance de este plan); ruff/format/mypy
(164 files)/lint-imports/makemigrations limpios.

**Revisión de sub-agente fresco (checkpoint §10):** recalculó de forma
independiente ambos golden vectors (Medicham GL antes/después y el caso de
nivel 40) y coincidieron dígito a dígito; confirmó que `PVP_RANK_VERSION`
sí participa en la clave de caché (mecanismo de invalidación real, no
cosmético). Encontró **2 huecos reales**: (1) la nota de migración solo
existía en documentación interna (spec.md/todo.md/docstring), no en ningún
lugar que el usuario final viera — el propio plan 048 (paso 5) pedía
"nota de cambio si rankings visibles varían" en la superficie del
producto. **Corregido:** aviso visible en `_pvp_result.html` (texto
específico con fecha, mismo estilo muted que otras notas de la app) + test
que confirma que aparece en el HTML renderizado. (2) El plan pedía
verificar el fix en más de una especie/liga; solo se había probado
Medicham en Great League. **Corregido:** se agregó `test_always_matches_
integer_hp_formula` (property test con `hypothesis` sobre stats/IVs/nivel
arbitrarios) y un caso concreto adicional (Azumarill, Ultra League,
max_cp=2500) verificado por cálculo independiente antes de escribirlo
(HP esperado 202, confirmado). Suite final: 1257 passed.

## 5.1 Fase 3 — texto original del plan (referencia)

El propio plan dice: *"los tests actuales se derivan del mismo algoritmo y no
constituyen un oráculo externo"*; y que corregir el bug de HP truncado
**altera el top de Medicham** (cambio visible al usuario). Combinado con la
regla de procedencia (§0): **no puedo generar golden vectors de PvP desde
memoria/entrenamiento** sin violar la prohibición de fabricar verificación.

**Plan de acción al llegar a esta fase:**

1. Implementar el fix determinista (HP entero vía `engine.stats.hp`, sin
   truncar el stat product completo) — esto es cálculo puro sobre reglas ya
   verificadas (CPM, stats base), no requiere fuente externa nueva.
2. Antes de publicar/mergear el cambio de ranking visible: **detenerse y
   preguntarle al usuario** si (a) tiene una fuente real (PvPoke, export
   propio) para validar el nuevo top de al menos una especie conocida, o
   (b) acepta el cambio solo como "corrección determinista sin oráculo
   externo" con nota de migración visible en la UI/changelog.
   Esto **no** es una duda resoluble leyendo el spec o corriendo tests —
   es la decisión de producto que el plan mismo exige.
3. Cachear rankings (4096 spreads recalculados por request hoy) con clave
   determinista `(species, base stats, max_cp, level_cap)`.

## 6. Fase 4 — Plan 053: validar contratos de calculadoras (dep. 046) — **DONE**

### 6.1 Bugs reales confirmados antes de tocar código

Reproducidos con `pytest` (no solo leídos del plan), cada uno con traceback
real capturado antes del fix:

1. **Codec genérico (`decode_calc_share`)**: JSON que decodifica a una
   lista (no dict) → `AttributeError: 'list' object has no attribute
   'get'` sin capturar (el `payload.get("v")` vivía fuera del `try`).
   Payload sin clave `t` → `KeyError` sin capturar.
2. **Costo de power-up**: `to_level="inf"` → `OverflowError: cannot
   convert float infinity to integer` en `_level_to_powerup_index`
   (`round((inf-1)*2)`), no es `ValueError`/`KeyError` → 500 real
   confirmado vía `pytest` (Django logea "Internal Server Error").
3. **Shiny**: `rate="1.0", n="-1"` → `p_at_least_one` hace `0.0 **
   (negativo)` → `ZeroDivisionError` sin capturar → 500 real confirmado.
4. **Shadow**: `iv_atk="99"` se aceptaba sin validar — no crashea, pero
   calcula y muestra un CP/HP "real" con un IV imposible (bug semántico,
   coincide con la evidencia del plan).
5. **`_get_params`**: descartaba el `calc_type` devuelto por
   `decode_calc_share` — una share URL de PvP se aceptaba en la
   calculadora de CP (cálculo cruzado, confirmado).

### 6.2 Alcance implementado (sin framework nuevo, según pide el plan)

- `decode_calc_share`: límite de longitud (`MAX_SHARE_URL_LENGTH=2048`),
  valida que el payload sea `dict`, valida versión, valida presencia de
  `t` — todo como `ValueError` controlado, nunca
  `AttributeError`/`KeyError`.
- `_get_params`: rechaza (cae a defaults) si el `calc_type` decodificado
  no coincide con la vista actual.
- Nuevo helper `_parse_finite_float` (mismo estilo que
  `_parse_int_in_range`/`_parse_confidence` ya existentes): rechaza
  no-finito y aplica rango. Aplicado a: `from_level`/`to_level` (costo),
  `level`/`ball`/`berry`/`throw`/`medal` (captura), `rate`/`confidence`
  (shiny), `level` (shadow).
- `_parse_int_in_range` (ya existente) reutilizado para
  `iv_atk`/`iv_def`/`iv_stam` de shadow y `n` de shiny.
- Fuzz test genérico con `hypothesis` (`TestCalculatorFuzzing`) sobre 19
  combinaciones (endpoint, campo) × valores sospechosos (`nan`, `inf`,
  `-inf`, enteros extremos) — cierra el paso 5 del plan de forma amplia,
  no solo para los 5 casos puntuales encontrados.
- No se construyó un sistema de Forms/schema genérico nuevo: los helpers
  ya existentes (`_parse_int_in_range`, `_parse_confidence`) eran
  suficientes y solo faltaba aplicarlos consistentemente + el nuevo
  `_parse_finite_float` para los casos de nan/inf. Coherente con la nota
  del plan: "no añadir framework genérico sin necesidad".
- `tests/test_calculator_views.py` (mencionado en la verificación del plan
  original) no se creó como archivo nuevo: la infraestructura ya
  existente (`tests/test_sad_paths.py`, con la convención establecida
  "cada calculadora devuelve 200 con error, nunca 500") ya cubría
  exactamente ese propósito — se extendió en vez de fragmentar.

### 6.3 Verificación

Suite completa 1268 passed; ruff/format/mypy(164 files)/lint-imports/
makemigrations limpios.

**Revisión de sub-agente fresco (checkpoint §10):** reprodujo de forma
independiente los 5 bugs originales contra el commit padre (restaurando
el código viejo y corriendo pytest real, no un script suelto) y confirmó
que ya no ocurren; confirmó que el fuzz test es sustantivo (lo hizo
fallar reintroduciendo deliberadamente el bug de `to_level=inf`).
Encontró **1 hueco real**: en CP (patrón preexistente, no de esta sesión),
shiny (`n`) y shadow (`iv_atk`/`iv_def`/`iv_stam`), la revalidación recibía
`str(valor_ya_defaulteado)` en vez del input crudo — un IV/n no numérico
como `"abc"` nunca llegaba a `_parse_int_in_range` como tal, porque
`_int_or_default` ya lo había sustituido en silencio por el default antes
de "validar" (que terminaba revalidando el default, siempre válido).
**Corregido:** las tres re-validaciones ahora reciben `params.get(...)`
directo. Se añadieron tests que fallaban primero (confirmado) para los
tres casos, y se sumaron valores no numéricos (`"abc"`, inyección SQL de
juguete) a `_SUSPICIOUS_VALUES` del fuzz test. Suite final: 1270 passed.

## 7. Fase 5 — Plan 060: límites entre apps (independiente) — **DONE**

### 7.1 Ciclo real confirmado (evidencia del plan, verificada)

`apps.contributions.models.DataContributionConsent.grant_consent/revoke_consent`
llamaban `AuditEvent.log(...)` directamente. `apps.audit.services` (solo
`mark_observation` + `mark_dataset_suspicious`) importaba
`apps.contributions.models.DatasetVersion` y
`apps.trades.models.TradeObservation`. Ciclo: `contributions` → `audit`,
`audit` → `contributions`/`trades`. `import-linter` no lo veía porque
`root_packages` solo tenía `"engine"` — las apps de Django no estaban bajo
ningún contrato.

### 7.2 Fix

- `apps.contributions.models`: ya no importa `apps.audit.models`. Los
  classmethods `grant_consent`/`revoke_consent` quedan como mutación pura
  de datos (se mantuvieron con la misma firma — son la base de ~40 tests
  de setup en `test_contributions.py`, no se podían eliminar).
- Nuevos `apps.contributions.services.grant_consent`/`revoke_consent`:
  orquestan mutación + `AuditEvent.log`. La vista de producción
  (`apps/contributions/views.py`) ahora llama a estos, no al modelo.
  Se replicó con cuidado la semántica original de `revoke_consent`
  (auditar solo si había un consentimiento *activo* antes de revocar, no
  en un doble-revoke) — un chequeo de pre-estado, no de post-estado.
- `mark_observation` → movido a `apps.trades.services` (dueño de
  `TradeObservation`). `mark_dataset_suspicious` → movido a
  `apps.contributions.services` (dueño de `DatasetVersion`).
- `apps/audit/services.py` eliminado (quedó vacío tras la extracción).
  `apps.audit` es ahora un sink puro: solo `AuditEvent` + admin.
- Tests movidos a las apps dueñas del agregado (`tests/test_trades.py`,
  `apps/contributions/tests/test_contributions.py`); `apps/audit/tests/
  test_audit.py` conserva solo `TestAuditEvent` (el modelo en sí).
- `pyproject.toml`: `root_packages` ahora incluye `"apps"`; 2 contratos
  `forbidden` nuevos (`audit-is-a-sink-not-a-source`,
  `domain-models-do-not-import-audit`). Verificado que detectan la
  regresión real (reintroduje el import viejo en `contributions/models.py`
  y `lint-imports` lo cachó, incluso transitivamente vía
  `experiments.models`).
- ADR nuevo: `docs/adr/0011-limites-entre-apps.md` (documenta el DAG, las
  alternativas descartadas — capa de eventos genérica, mover AuditEvent,
  `layers` contract exhaustivo — y la asimetría aceptada entre el
  classmethod del modelo y el servicio).

### 7.3 Verificación

Suite completa 1274 passed; ruff/format/mypy(163 files)/lint-imports (3
contratos, 0 rotos)/makemigrations limpios.

## 8. Fase 6 — Plan 061: AuditEvent inmutable (dep. 060)

Detallar al llegar: releer `plans/061-enforce-audit-event-integrity.md`.
Ya sabido de antemano (confirmado en el propio plan): admin no es
completamente readonly (`has_add/change/delete_permission` no están
bloqueados), `AuditEvent.log` defaultea `correlation_id=""` y la mayoría de
llamadas no propaga el ID real que el middleware ya coloca en
request/thread-local.

## 9. Convenciones (de AGENTS.md, sin cambios)

- Español neutral (sin voseo).
- Sin comentarios en el código salvo que expliquen un WHY no obvio.
- TDD en `engine/`: fixtures a mano primero, con procedencia documentada
  (§0) — nunca "valores conocidos" sin cita.
- `engine/` puro: sin imports de Django.
- Commits solo cuando se pide explícitamente completar una fase (no dejar
  WIP a medio verificar commiteado).
- Suite verde obligatoria antes de marcar cualquier plan DONE.

## 10. Loop de revisión

- Cada ~20 iteraciones (o al cerrar cada fase, lo que ocurra primero):
  sub-agente fresco con prompt "review spec.md and the current
  implementation for gaps" — no debe ver el resto de esta conversación,
  solo el spec + el estado real del código/tests en la rama.
- Si el sub-agente encuentra una discrepancia, se resuelve antes de avanzar
  a la siguiente fase; se registra la resolución en §11.

## 11. Bitácora de decisiones y bloqueos

(Se completa a medida que se avanza. No editar retroactivamente sin dejar
rastro de qué decía antes.)

### Bloqueo real — Plan 047 (learnsets), 2026-07-24

Al empezar la Fase 2 se confirmó (grep + lectura de `engine/dps_data.py`)
que `SpeciesInfo` no tiene ningún campo de learnset (qué fast/charge moves
aprende cada especie); solo existen `FAST_MOVES`/`CHARGE_MOVES` como
catálogos globales sin asociación a especie. El plan 047 exige: *"Si no
hay datos verificados suficientes, ocultar/desactivar la calculadora con
mensaje honesto en vez de inventar compatibilidad."* No hay ninguna fuente
primaria en el repo para esto, y por la regla de procedencia (§0) no puede
fabricarse desde memoria/entrenamiento. Es la misma clase de bloqueo ya
anticipado para el plan 048 — decisión de producto/dato, no resoluble
leyendo código o corriendo tests. **Se detiene la Fase 2 aquí y se
pregunta al usuario** (ver conversación) antes de tocar `get_fast_moves_for_species`.
