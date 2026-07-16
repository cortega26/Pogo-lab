# ADR-0004 — Métodos estadísticos y comunicación honesta

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §F, §4.6, §19-#15 · ADR-0003

## Contexto

El producto compara datos empíricos con un modelo teórico de IV. La tentación de afirmar "hay un bug" a partir de
una diferencia o un p-valor es el mayor riesgo de credibilidad. Además, los eventos relevantes (hundos) son
**raros** (p ≈ (1/4)³ en Lucky, (1/15)³ en estándar), lo que invalida métodos que asumen frecuencias esperadas
grandes.

## Decisión

Métodos seleccionados y **encapsulados en el `engine/`**:
- **Intervalos de proporción:** **Wilson** por defecto (buena cobertura con n pequeño y p extrema); **Clopper–Pearson**
  exacto disponible para modo estricto. Se descarta **Wald**.
- **Hundos vs modelo:** **prueba binomial exacta** (`scipy.stats.binomtest`). **Chi-cuadrado queda prohibido** para
  hundos (esperados minúsculos).
- **Uniformidad por stat:** chi-cuadrado **solo si todos los esperados ≥ 5**; en caso contrario, **p-valor por
  Monte Carlo** con semilla fija.
- **Siempre:** reportar **tamaño de efecto**, respetar **umbrales mínimos de n** antes de inferir, advertir sobre
  comparaciones múltiples y sesgo de selección.
- **Lenguaje:** se distingue **"compatible con el modelo"** de **"modelo demostrado"**; nunca "bug"/"manipulado".

## Alternativas consideradas

- **Chi-cuadrado en todo.** Simple y familiar, pero **incorrecto** con esperados pequeños (hundos) → conclusiones
  espurias.
- **Solo p-valores / Wald.** Falsa precisión, cobertura pobre, y significancia sin magnitud.
- **Bayesiano completo por defecto.** Potente pero excesivo para el MVP; se deja un intervalo creíble Beta-Binomial
  **opcional** (v1.1) para comunicar "compatible con".

## Consecuencias

- **Positivas:** inferencia correcta para eventos raros; comunicación prudente y auditable; reproducible con semilla.
- **Negativas / costes:** más ramas de método (auto chi²/MC) y necesidad de umbrales bien elegidos.
- **Mitigaciones:** `min_sample_for(metric)` centraliza umbrales; fixtures calculadas a mano validan cada método.

## Reversibilidad

Baja: cambiar a métodos laxos contradiría la tesis del producto. Añadir métodos (bayesiano) es aditivo y reversible.
