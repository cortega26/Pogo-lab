# M5 — Analysis & Decisions

| Campo | Valor |
|---|---|
| **Estado** | ✅ Completado |
| **Tamaño** | L |
| **Depende de** | M4 |
| **PRs** | PR-14, PR-15, PR-16 |
| **Actualizado** | 2026-07-16 (creado) |

## Objetivo

Inferencia estadística **honesta y reproducible** + recomendaciones **deterministas** (nunca "bug", nunca LLM).

## Historias

- Como usuario, veo si mis resultados son "compatibles con el modelo" con intervalos y tamaño de efecto.
- Como usuario, recibo recomendaciones claras y trazables sobre qué hacer o registrar a continuación.

## Tareas

### PR-14 · engine (intervalos + pruebas)

- [x] `intervals.py`: `wilson_interval` (por defecto), `clopper_pearson_interval` (exacto), `beta_binomial_credible` (opcional).
- [x] `stat_tests.py`: `exact_binomial_test` (hundos — **no** chi²); `uniformity_test` (auto: chi² si esperados≥5, si no **Monte Carlo** con `seed`); `independence_test` (Holm).
- [x] Helpers de **tamaño de efecto** (Cramér's V) y `min_sample_for(metric)` (umbrales mínimos).
- [x] Tests con **fixtures calculadas a mano** + property (exacto ≈ simulación).

### PR-15 · analysis

- [x] `AnalysisRun` (fija `dataset + ruleset.version + algorithm_version + random_seed + code_sha`) + `AnalysisResult`.
- [x] `run_personal_analysis(owner, filters)` — **separa obligatoriamente Lucky/normal** y por ruleset/periodo.
- [x] Panel: IC, distribuciones (**Chart.js + tabla alternativa**), observado vs esperado, advertencias de calidad, umbrales.

### PR-16 · decisions

- [x] `engine/decisions.py::evaluate()` — reglas deterministas puras.
- [x] Modelos `DecisionRule` (versionada, `condition_spec`, `message_key` i18n) + `DecisionRecommendation`.
- [x] Reglas: `insufficient_sample`, `separate_lucky_and_normal`, `mixed_rulesets_or_periods`, `compatible_with_model`, `trades_needed_for_confidence`, `small_effect_more_data`, `no_anomaly_conclusion`.

## Archivos / módulos afectados

`apps/analysis/`, `apps/decisions/`, `engine/intervals.py`, `engine/stat_tests.py`, `engine/decisions.py`.

## Pruebas

- [x] Unit/property de estadística (fixtures a mano).
- [x] Integración: recálculo al cambiar reglas; separación Lucky/normal.
- [x] E2E del panel personal.

## Criterios de aceptación

- [x] Con muestra pequeña muestra "compatible" o "insuficiente" — **nunca** "bug"/"manipulado".
- [x] Análisis **reproducible** con la misma semilla y versiones.
- [x] Recomendaciones trazables a `rule.key + version`, con explicación.

## Demo verificable

Panel personal con IC, distribución y recomendaciones prudentes.

## Riesgos

- Conclusiones engañosas → métodos exactos, umbrales, tamaño de efecto y lenguaje "compatible con" en el engine.

## Recortes posibles

`independence_test` y `beta_binomial_credible` a v1.1 (⏭️).

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
| 2026-07-17 | ✅ | PR-14 (engine intervals + stat_tests): 179 tests engine. PR-15 (analysis): modelos, servicios, panel SSR+HTMX+Chart.js. PR-16 (decisions): evaluate() con 8 reglas, DecisionRule/Recommendation. Coverage 89% global, engine 99%. 353 tests total. |
