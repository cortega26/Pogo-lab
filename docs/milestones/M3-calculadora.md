# M3 — Calculadora pública

| Campo | Valor |
|---|---|
| **Estado** | ✅ Completado |
| **Tamaño** | M |
| **Depende de** | M1, M2 |
| **PRs** | PR-06, PR-10, PR-11 |
| **Actualizado** | 2026-07-16 (completado) |

## Objetivo

Motor de probabilidad implementado + **calculadora SSR compartible** (sin login) con SEO técnico es/en.
Es el núcleo del **camino crítico** (valida el wedge "entender + calcular").

## Historias

- Como visitante, calculo mi probabilidad acumulada y obtengo una explicación en lenguaje natural.
- Como visitante, comparto una URL que reproduce exactamente el mismo cálculo.

## Tareas

### PR-06 · engine/probability (implementación)

- [x] `possible_values(f)`, `p_specific_iv(f)`, `p_stat_at_least(f,t)`, `p_hundo(f)`.
- [x] `iv_sum_distribution(f)` + `p_sum_at_least(f,s)` (Σ=1 exacto).
- [x] `p_at_least_one(p,n)`, `p_zero(p,n)`, `expected_successes(p,n)`, `outcome_distribution(p,n)`, `trades_for_confidence(p,c)`.
- [x] `per_trade_success_prob(f, target)` (mapea objetivo → p; Lucky sobrescribe f=12).
- [x] Tests **unit + property (Hypothesis)** + **fixtures calculadas a mano** (no snapshots).
- [x] **Test anti-drift de datos:** los ejemplos de `docs/plan.md` / `AGENTS.md` (`1/64`, `1/3375`, pisos) se verifican contra la salida del `engine/` — una sola fuente de verdad.

### PR-10 · calculators

- [x] `compute_scenario(CalcInput) -> CalcResult`.
- [x] Formulario **HTMX** (amistad, tipo, objetivo, n, confianza) con recálculo sin recargar.
- [x] `encode_share_url` / `decode_share_url` (determinista, canónico).
- [x] Explicación en **lenguaje natural** + supuestos + enlace a metodología/fuentes.
- [x] Caché por *hash* de `(inputs + ruleset.version + algorithm_version)`.

### PR-11 · SEO técnico + E2E

- [x] Sitemaps por idioma + `hreflang` + canonical + Open Graph + `robots.txt`.
- [x] Enlaces internos explicación ↔ calculadora ↔ datos ↔ metodología.
- [x] **E2E**: "visitante calcula una probabilidad" y "URL compartida reproduce el cálculo".

## Archivos / módulos afectados

`apps/calculators/`, `engine/probability.py`, `templates/calculators/`, sitemaps en `config/`.

## Pruebas

- [x] Unit + property del engine (50 tests).
- [x] Integración de la URL compartible (round-trip encode/decode).
- [x] E2E de los dos flujos (skipped por defecto, requieren navegador).

## Criterios de aceptación

- [x] Casos de referencia correctos: **Lucky f=12 → k=4, p_hundo=1/64**; **estándar f=1 → k=15, p_hundo=1/3375**.
- [x] Link compartible reproduce el cálculo exacto.
- [x] Páginas es/en indexables (sitemap + hreflang).

## Demo verificable

Calculadora pública funcionando con enlace compartible.

## Riesgos

- Fricción HTMX en el recálculo → confirmar en spike (plan S5). No surgió.

## Recortes posibles

Distribución de suma completa (mostrar primero hundo/acumulada) → ⏭️ si aprieta. No recortado.

## Registro de avance

| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
| 2026-07-16 | 🟨 | PR-06 engine/probability implementado: 50 tests (0 skips), fixtures a mano, Hypothesis, anti-drift gate. |
| 2026-07-16 | 🟨 | PR-10 calculators: CalcInput→CalcResult, HTMX, share URL, caché, 23 tests. |
| 2026-07-16 | ✅ | PR-11 SEO+E2E: sitemaps, hreflang, canonical, OG, robots.txt, enlaces internos, E2E Playwright. Gate completo: 152 tests pasan, 25 skipped, ruff/mypy/import-linter verdes. |
