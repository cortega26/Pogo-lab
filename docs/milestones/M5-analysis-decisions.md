# M5 — Analysis & Decisions

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Pendiente |
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

- [ ] `intervals.py`: `wilson_interval` (por defecto), `clopper_pearson_interval` (exacto), `beta_binomial_credible` (opcional).
- [ ] `stat_tests.py`: `exact_binomial_test` (hundos — **no** chi²); `uniformity_test` (auto: chi² si esperados≥5, si no **Monte Carlo** con `seed`); `independence_test` (Holm).
- [ ] Helpers de **tamaño de efecto** (Cramér's V) y `min_sample_for(metric)` (umbrales mínimos).
- [ ] Tests con **fixtures calculadas a mano** + property (exacto ≈ simulación).

### PR-15 · analysis

- [ ] `AnalysisRun` (fija `dataset + ruleset.version + algorithm_version + random_seed + code_sha`) + `AnalysisResult`.
- [ ] `run_personal_analysis(owner, filters)` — **separa obligatoriamente Lucky/normal** y por ruleset/periodo.
- [ ] Panel: IC, distribuciones (**Chart.js + tabla alternativa**), observado vs esperado, advertencias de calidad, umbrales.

### PR-16 · decisions

- [ ] `engine/decisions.py::evaluate()` — reglas deterministas puras.
- [ ] Modelos `DecisionRule` (versionada, `condition_spec`, `message_key` i18n) + `DecisionRecommendation`.
- [ ] Reglas: `insufficient_sample`, `separate_lucky_and_normal`, `mixed_rulesets_or_periods`, `compatible_with_model`, `trades_needed_for_confidence`, `small_effect_more_data`, `no_anomaly_conclusion`.

## Archivos / módulos afectados

`apps/analysis/`, `apps/decisions/`, `engine/intervals.py`, `engine/stat_tests.py`, `engine/decisions.py`.

## Pruebas

- [ ] Unit/property de estadística (fixtures a mano).
- [ ] Integración: recálculo al cambiar reglas; separación Lucky/normal.
- [ ] E2E del panel personal.

## Criterios de aceptación

- [ ] Con muestra pequeña muestra "compatible" o "insuficiente" — **nunca** "bug"/"manipulado".
- [ ] Análisis **reproducible** con la misma semilla y versiones.
- [ ] Recomendaciones trazables a `rule.key + version`, con explicación.

## Demo verificable

Panel personal con IC, distribución y recomendaciones prudentes.

## Riesgos

- Conclusiones engañosas → métodos exactos, umbrales, tamaño de efecto y lenguaje "compatible con" en el engine.

## Recortes posibles

`independence_test` y `beta_binomial_credible` a v1.1 (⏭️).

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
