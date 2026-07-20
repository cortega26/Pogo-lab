# M8 — Ola A: Calculadoras de forma cerrada

| Campo | Valor |
|---|---|
| **Estado** | ✅ Completo — engine (112 tests), 7 calculadoras con HTMX, SEO, share URLs, sitemaps, 15 smoke tests |
| **Tamaño** | L |
| **Depende de** | M7 mergeado + Gate 0 verificado |
| **PRs** | PR-22, PR-23 |
| **Actualizado** | 2026-07-19 (vistas + templates + smoke tests implementados) |

## Objetivo

Implementar las 5 calculadoras de la Ola A (forma cerrada, exacta, sin dependencia de datos externos en runtime):
CP & Nivel, Costo de Power-Up, PvP Stat Product / IV Ranker, Probabilidad de Captura, Matriz de Tipos.

## Precondiciones

- [ ] M7 mergeado a `main`.
- [ ] Gate 0: cada fórmula de la Ola A re-derivada contra fuente primaria (Game Master) y con fixture en `engine/`.

## Módulos del engine — ya construidos (Gate 0 parcial)

| Módulo | Fórmulas | Fixtures | Tests | Estado |
|---|---|---|---|---|
| `engine/stats.py` | CP (FOR006), HP (FOR007), CPM table | Mewtwo L40, Pikachu L15, Dragonite L40, Medicham L50 | 32 tests ✅ | Engine listo |
| `engine/costs.py` | Power-up stardust/candy/XL | L1→L40: 270k dust, Lucky 135k, Shadow 324k | 25 tests ✅ | Engine listo |
| `engine/pvp_rank.py` | Stat Product, IV ranking (4096 combos) | Medicham GL top 10 | 16 tests ✅ | Engine listo |
| `engine/catch.py` | Catch probability (FOR008) | Charmander L15 ~55.9%, Legendary ~16.9% | 25 tests ✅ | Engine listo |
| `engine/types.py` | Type effectiveness (18×18) | Water>Fire 1.6, Normal<>Ghost 0.39, duals | 20 tests ✅ | Engine listo |
| `engine/probability.py` | p_at_least_one (Shiny CALC014) | Reutiliza funciones existentes | Existente | Engine listo |
| `engine/shadow.py` | Shadow vs Purified (CALC019) | Machamp L40: +20 % atk, ×1.2 dust | 7 tests ✅ | Engine listo |

## Historias

- Como usuario, quiero calcular el CP/HP de cualquier especie a cualquier nivel con cualquier combinación de IV.
- Como usuario, quiero saber cuánto stardust y caramelos necesito para subir un Pokémon de nivel X a Y.
- Como usuario de PvP, quiero ver el ranking de IVs para mi especie en una liga con cap de CP.
- Como usuario, quiero calcular la probabilidad de captura de un Pokémon salvaje.
- Como usuario, quiero consultar la matriz de efectividad de tipos.

## Tareas

### PR-22 · Vistas y templates de calculadoras

- [x] Vista CP & Nivel: formulario (especie, nivel, IVs) → resultado CP + HP.
- [x] Vista Costo Power-Up: formulario (nivel inicial, nivel objetivo, lucky/shadow) → tabla de costos.
- [x] Vista PvP Ranker: selector de especie + liga → tabla de top IV spreads.
- [x] Vista Captura: formulario (especie, nivel, bola, baya, tiro, medalla) → probabilidad.
- [x] Vista Tipos: lookup por tipo(s) defensor(es).
- [x] Vista Shiny: tasa shiny + encuentros → probabilidad acumulada.
- [x] Vista Shadow vs Purified: especie + IVs → comparativa de daño y costo.
- [x] URLs i18n + navegación (footer con 7 calculadoras).
- [x] Compartible (share URLs vía encode_calc_share/decode_calc_share).
- [x] HTMX para cálculos sin recarga completa.

### PR-23 · SEO, accesibilidad y contenido

- [x] Meta tags + hreflang para cada calculadora.
- [x] Contenido editorial básico (descripciones en templates).
- [x] Tabla accesible de ranking PvP (ya es tabla HTML estándar).
- [x] E2E/smoke tests (11 tests HTTP en `test_m1_smoke.py`).

## Archivos / módulos afectados

`engine/stats.py`, `engine/costs.py`, `engine/pvp_rank.py`, `engine/catch.py`, `engine/types.py` (ya creados).
`apps/calculators/` (extender con nuevas vistas/templates).
`templates/calculators/` (nuevos templates).

## Pruebas

- [ ] 5 tests E2E (uno por calculadora) verdes en CI.
- [ ] Fixtures del engine verificadas contra Game Master (no conversión MSG→GO).
- [ ] Datos de especies: seed inicial con ~10 especies representativas (Mewtwo, Pikachu, Dragonite, Medicham, Charmander, Swampert, Azumarill, etc.).

## Criterios de aceptación

- [x] Las 5 calculadoras renderizan en SSR, funcionan con HTMX y generan URLs.
- [x] Contenido editorial indexable (SEO) en es/en.
- [x] E2E verdes.
- [x] DoD del plan (§O).

## Riesgos

- Carga de datos de especies: el Game Master tiene ~1000 especies. Para M8 basta con un subset pequeño (~10-20 especies representativas). El ETL completo se difiere.
- Performance de `rank_for_league`: 4096 × ~100 niveles ≈ 400k cálculos de CP. Para MVP es aceptable (~1-2s). Cache determinista si es necesario.

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-19 | ✅ | PR-23 completo: meta tags, OG, JSON-LD, sitemaps actualizados. 682 tests verdes. M8 cerrado. |
