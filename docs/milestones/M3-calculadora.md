# M3 — Calculadora pública

| Campo | Valor |
|---|---|
| **Estado** | ⬜ Pendiente |
| **Tamaño** | M |
| **Depende de** | M1, M2 |
| **PRs** | PR-06, PR-10, PR-11 |
| **Actualizado** | 2026-07-16 (creado) |

## Objetivo
Motor de probabilidad implementado + **calculadora SSR compartible** (sin login) con SEO técnico es/en.
Es el núcleo del **camino crítico** (valida el wedge "entender + calcular").

## Historias
- Como visitante, calculo mi probabilidad acumulada y obtengo una explicación en lenguaje natural.
- Como visitante, comparto una URL que reproduce exactamente el mismo cálculo.

## Tareas

### PR-06 · engine/probability (implementación)
- [ ] `possible_values(f)`, `p_specific_iv(f)`, `p_stat_at_least(f,t)`, `p_hundo(f)`.
- [ ] `iv_sum_distribution(f)` + `p_sum_at_least(f,s)` (Σ=1 exacto).
- [ ] `p_at_least_one(p,n)`, `p_zero(p,n)`, `expected_successes(p,n)`, `outcome_distribution(p,n)`, `trades_for_confidence(p,c)`.
- [ ] `per_trade_success_prob(f, target)` (mapea objetivo → p; Lucky sobrescribe f=12).
- [ ] Tests **unit + property (Hypothesis)** + **fixtures calculadas a mano** (no snapshots).

### PR-10 · calculators
- [ ] `compute_scenario(CalcInput) -> CalcResult`.
- [ ] Formulario **HTMX** (amistad, tipo, objetivo, n, confianza) con recálculo sin recargar.
- [ ] `encode_share_url` / `decode_share_url` (determinista, canónico).
- [ ] Explicación en **lenguaje natural** + supuestos + enlace a metodología/fuentes.
- [ ] Caché por *hash* de `(inputs + ruleset.version + algorithm_version)`.

### PR-11 · SEO técnico + E2E
- [ ] Sitemaps por idioma + `hreflang` + canonical + Open Graph + `robots.txt`.
- [ ] Enlaces internos explicación ↔ calculadora ↔ datos ↔ metodología.
- [ ] **E2E**: "visitante calcula una probabilidad" y "URL compartida reproduce el cálculo".

## Archivos / módulos afectados
`apps/calculators/`, `engine/probability.py`, `templates/calculators/`, sitemaps en `config/`.

## Pruebas
- [ ] Unit + property del engine.
- [ ] Integración de la URL compartible (round-trip encode/decode).
- [ ] E2E de los dos flujos.

## Criterios de aceptación
- [ ] Casos de referencia correctos: **Lucky f=12 → k=4, p_hundo=1/64**; **estándar f=1 → k=15, p_hundo=1/3375**.
- [ ] Link compartible reproduce el cálculo exacto.
- [ ] Páginas es/en indexables (sitemap + hreflang).

## Demo verificable
Calculadora pública funcionando con enlace compartible.

## Riesgos
- Fricción HTMX en el recálculo → confirmar en spike (plan S5).

## Recortes posibles
Distribución de suma completa (mostrar primero hundo/acumulada) → ⏭️ si aprieta.

## Registro de avance
| Fecha | Estado | Nota |
|---|---|---|
| 2026-07-16 | ⬜ | Hoja creada. |
