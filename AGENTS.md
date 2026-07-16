# AGENTS.md — Pogo-lab

Guía canónica para **cualquier agente o modelo** que trabaje en este repositorio (Claude Code u otro harness).
Léela **antes** de tocar nada. `CLAUDE.md` apunta aquí.

## Estado actual
Fase de **planificación**: aún no hay código. Artefactos (mapa de propiedad SSOT en `docs/README.md`):
- `docs/plan.md` — plan maestro **canónico** (arquitectura, modelo de datos, motor estadístico, decisiones). Referencia; **no lo recargues entero** cada sesión. (No edites la copia de `~/.claude/plans/`.)
- `docs/adr/` — **decisiones de arquitectura** por escrito (ADR-0001…0007). Registro detallado del *rationale*.
- `docs/milestones/` — seguimiento por milestone (`README.md` = tablero; `M0…M7` = hojas autocontenidas). **Carga solo la hoja del milestone en curso.**
- `CONTRIBUTING.md` — flujo de trabajo (TDD, commits, tooling y contratos de guardrails). `.github/PULL_REQUEST_TEMPLATE.md` — checklist de no-negociables.
- `.codegraph/` — índice de código (vacío hasta que haya fuentes).

## Qué es
Plataforma web que explica cómo funcionan las mecánicas de Pokémon GO (intercambios / IV / Lucky) con matemática,
fuentes trazables y datos empíricos, y convierte probabilidades en decisiones prácticas.
Ciclo del producto: **Entender → Calcular → Registrar → Analizar → Decidir**.

## Stack objetivo
Monolito modular **Django 5.2 LTS + PostgreSQL 16**, templates SSR + **HTMX** + Alpine mínimo, **Tailwind standalone
CLI**, `uv`, Ruff + mypy/django-stubs + pre-commit, pytest/pytest-django/hypothesis/Playwright, Chart.js
autohospedado. Un **paquete puro `engine/`** (sin Django) concentra toda la matemática/estadística/decisiones.

## Reglas de oro (NO NEGOCIABLES)
1. **Honestidad estadística.** Nunca afirmar "bug" ni "el juego está manipulado" a partir de una diferencia
   descriptiva o un p-valor. Distinguir **"compatible con el modelo"** de **"modelo demostrado"**. Hundos: **prueba
   binomial exacta** (chi² es inválido: la esperanza es minúscula). Intervalos: **Wilson** por defecto,
   Clopper–Pearson exacto disponible. **Umbrales mínimos de n** antes de inferir. Reportar **tamaño de efecto**, no
   solo significancia. Advertir sobre comparaciones múltiples y **sesgo de selección** del dataset comunitario.
2. **Procedencia separada.** Distinguir **oficial / comunidad / datamining / inferido / hipótesis**. Los pisos de
   IV (por nivel de amistad y **Lucky=12**) son **hechos comunitarios**: se modelan como `RuleParameter` +
   `SourceClaim` versionados y **se verifican contra datamining al hacer el seed** — **NUNCA** hardcodeados como
   verdad oficial ni "de memoria".
3. **Modelo IV correcto.** Re-roll **uniforme** en `[f,15]` (k = 16 − f), **sin pico** en el piso. No es clamping
   `max(iv, f)`. La **independencia** Att/Def/HP es un **supuesto** del modelo (con procedencia), no un hecho: la
   parte empírica lo prueba.
4. **`engine/` puro y testeado.** Sin imports de Django. Toda la matemática/estadística/decisiones vive ahí. Tests
   con **fixtures calculadas a mano** (p. ej. Lucky f=12 → k=4, p_hundo=**1/64**; estándar f=1 → k=15,
   p_hundo=**1/3375**) + **property-based** (Hypothesis: prob∈[0,1], Σdist=1, monotonía en n, exacto≈simulación).
   **No** snapshots opacos para validar matemática. Reproducibilidad: fijar `ruleset.version + algorithm_version +
   random_seed`.
5. **Sin LLM en runtime.** Las recomendaciones son **deterministas, versionadas y trazables** a `DecisionRule`. No
   generar recomendaciones con un modelo en producción.
6. **Privacidad y minimización.** Sin nombre de entrenador, sin ubicación precisa (solo **país agregado**). Las
   `notes` privadas **nunca** se agregan. El dataset público es un **snapshot anonimizado inmutable**
   (`DatasetVersion`); la **revocación** de consentimiento excluye de builds futuros.
7. **Simplicidad de infraestructura.** Sin microservicios, Redis, colas ni event sourcing salvo necesidad
   demostrada. Análisis **síncrono** + caché determinista en el MVP.
8. **i18n indexable.** Contenido editorial traducido y **renderizado en servidor** (no traducción cliente). Rutas
   `/es/` `/en/` (pt preparado), `hreflang`, canonical.

## Convenciones de código
- **Idioma: español neutral** en comentarios, docstrings, mensajes de consola, contenido y commits (sin voseo:
  "ajusta", "ejecuta", "revisa" — no "ajustá", "corré").
- Tipos claros (mypy razonable); apps de dominio **delgadas** sobre `engine/`; Ruff format.
- **App `analysis`, NO `statistics`** (colisiona con el módulo stdlib de Python).
- Commits/PRs **pequeños y revisables** (ver `docs/plan.md` §M — 21 PRs) que terminan con
  `Co-Authored-By` cuando aplique.

## Principios de diseño (atados a contratos, no prosa)
- **KISS / YAGNI.** Sin microservicios, colas, Redis ni abstracciones genéricas sin necesidad demostrada
  (`docs/plan.md` §21). Se construye la **1ª familia** (intercambios/IV); las demás se **documentan**, no se pre-abstraen.
- **DRY.** Cada hecho vive en **un solo** documento/módulo (mapa SSOT en `docs/README.md`). Las constantes (pisos,
  `1/64`, `1/3375`) tienen **una fuente** (engine/seed); un test verifica que los ejemplos de los docs coinciden con
  el engine (gate de **M3**).
- **SOLID / DIP.** Las capas dependen **hacia el dominio**, no al revés. Contrato **import-linter** (**M1**):
  `engine/` no importa Django; las apps dependen de `engine/` → **CI falla si se rompe** (ver
  [ADR-0003](docs/adr/0003-motor-dominio-puro.md)).
- **SRP.** `engine/` = verdad matemática; apps = orquestación delgada; `content` = editorial. Un módulo, una sola
  razón para cambiar.

**Dónde se hacen cumplir:** reglas **mecanizables** → CI/pre-commit (Ruff, mypy, import-linter, tests); reglas **no
mecanizables** (honestidad estadística, procedencia) → checklist de PR + revisión humana. Decisiones arquitectónicas
→ `docs/adr/`. Flujo de trabajo → `CONTRIBUTING.md`.

## Cómo trabajar
1. Abre `docs/milestones/README.md` (tablero) y la **hoja del milestone en curso**.
2. **TDD en el `engine/`**: escribe primero las fixtures/tests con valores calculados a mano; luego implementa hasta
   que pasen. Es la red de seguridad que atrapa errores de **cualquier** modelo.
3. Marca tareas `- [ ]` → `- [x]`, actualiza el **Estado** (⬜/🟨/✅/⏭️) y el **Registro de avance** de la hoja.
4. Un milestone es ✅ **solo** con todos sus criterios de aceptación cumplidos.

## Comandos de desarrollo (objetivo — disponibles tras M1)
```bash
uv sync                                   # dependencias
docker compose up -d db                   # PostgreSQL 16
uv run python manage.py migrate
uv run python manage.py seed              # datos iniciales (mecánica trade_iv)
uv run pytest                             # tests (engine + apps)
uv run python manage.py runserver
```
`manage.py`, `compose.yaml`, `Makefile`, etc. se crean en **M1** (ver `docs/milestones/M1-fundacion.md`).

## Estrategia de modelos (si se implementa con varios agentes)
- Modelo económico: scaffolding, CRUD, plantillas, formularios, i18n, CSV (M1, gran parte de M4).
- Modelo fuerte / revisión obligatoria: **`engine/` estadístico** (M3, M5) y contratos de versionado/reproducibilidad.
- Guardrail universal: **tests/fixtures del `engine/` primero**, exigidos en CI.
