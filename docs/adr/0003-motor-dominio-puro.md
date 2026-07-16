# ADR-0003 — Motor de dominio puro `engine/` (DIP, verificado por import-linter)

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §D, §F · ADR-0001 · ADR-0004

## Contexto

El valor diferencial de Pogo-lab es la **corrección y reproducibilidad** de la matemática/estadística. Ese código
debe ser testeable de forma aislada (fixtures calculadas a mano, property-based), reutilizable entre idiomas y
resistente a que la lógica de dominio se contamine con detalles de framework (ORM, request, i18n).

## Decisión

Toda la matemática, estadística y reglas de decisión viven en un **paquete Python puro `engine/`** sin ningún
import de Django. Las apps Django son **orquestación delgada** que llama al `engine/`. La dependencia va siempre
**hacia el dominio** (apps → engine), nunca al revés. Se aplica un **contrato `import-linter`** en CI:
`engine/` no puede importar Django ni las apps; las apps dependen de `engine/`. **El CI falla si se rompe.**

## Alternativas consideradas

- **Matemática dentro de las apps/servicios Django.** Más rápido al inicio, pero mezcla dominio con framework,
  dificulta el testeo puro y la reproducibilidad, y erosiona el límite con el tiempo (nadie lo vigila).
- **Convención sin contrato.** "Acordamos no importar Django en `engine/`": se degrada en el primer PR con prisa.
  Un modelo de implementación débil (otro harness) no se autopoliciona esta regla — necesita un gate mecánico.

## Consecuencias

- **Positivas:** SRP/DIP reales y verificados; tests del engine sin base de datos; el motor es la SSOT de las
  constantes (pisos, `1/64`, `1/3375`) que otros artefactos verifican (ADR-0004 y el test docs↔engine de M3).
- **Negativas / costes:** una frontera más que respetar; algo de mapeo entre modelos Django y estructuras del engine.
- **Mitigaciones:** dataclasses/pydantic en `engine/rulesets.py` como contrato de datos; el contrato import-linter
  hace el límite barato de mantener.

## Reversibilidad

Baja por diseño: es el guardrail que sostiene la corrección. Relajarlo reintroduciría el acoplamiento que evita.
