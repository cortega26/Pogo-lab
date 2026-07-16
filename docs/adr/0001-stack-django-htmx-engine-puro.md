# ADR-0001 — Stack: Django + PostgreSQL + HTMX + motor puro

- **Estado:** Aceptada
- **Fecha:** 2026-07-16
- **Relacionadas:** `plan.md` §D, §7, §19-#1 · ADR-0003

## Contexto

Pogo-lab es una plataforma **content/SEO-first** con un **núcleo numérico-estadístico** (probabilidades e
inferencia sobre IV de intercambios) y un **panel administrativo pesado** (mecánicas, rulesets, fuentes,
traducciones, datasets). La especificación pide monolito modular, bajo costo operativo, mínima dependencia externa
y evitar una SPA salvo justificación fuerte. Debe operar en es/en desde el inicio.

## Decisión

**Monolito modular Django 5.2 LTS + PostgreSQL 16**, con templates SSR + **HTMX** (Alpine mínimo) y un **paquete
puro `engine/`** (sin Django) para toda la matemática/estadística/decisiones. Gráficos con Chart.js autohospedado.

## Alternativas consideradas

- **TypeScript + Fastify (+ SPA/Next.js).** Da tipos front-back y realtime, pero: (1) **no hay equivalente maduro a
  SciPy** en Node — habría que reimplementar tests exactos y distribuciones, justo donde la corrección es el
  diferenciador; (2) exige ensamblar auth, migraciones, i18n, admin y SSR pieza por pieza; (3) empuja a una SPA
  separada (dos builds/despliegues). "TS7"/tsgo acelera el *typecheck*, no cambia el ecosistema estadístico.
- **Flask/FastAPI.** Más ligeros pero sin admin, migraciones, i18n ni forms de primera parte; reconstruiríamos lo
  que Django ya trae.

## Consecuencias

- **Positivas:** SciPy/NumPy para el motor; Django Admin cubre ~80% del panel (§16); i18n, sitemaps, ORM,
  migraciones, auth y CSRF de fábrica; un proceso + Postgres, un solo lenguaje de servidor; despliegue trivial.
- **Negativas / costes:** Python como único lenguaje (sin tipos compartidos con el cliente); HTMX en vez de un
  framework SPA para interactividad rica.
- **Mitigaciones:** tipos con `mypy` + `django-stubs` + dataclasses en el `engine/`; islas Alpine/JS puntuales si
  alguna vista exige más interactividad.

## Reversibilidad

Media. El `engine/` puro (ADR-0003) es portable a cualquier backend; migrar de HTMX a islas JS es incremental. Un
cambio de framework se justificaría solo si el producto virara a altamente interactivo/realtime.
