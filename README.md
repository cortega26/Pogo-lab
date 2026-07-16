# Pogo-lab

**Mechanics Lab + Decision Planner** para Pokémon GO: entiende cómo funcionan realmente las mecánicas
(intercambios, IV y Pokémon Lucky) con matemática, fuentes trazables y datos empíricos, y usa esas probabilidades
para decidir mejor.

> ⚠️ **No afiliado** a Niantic ni a The Pokémon Company. Sin recursos oficiales (logos/sprites), sin APIs privadas,
> sin automatización del juego. Los datos comunitarios se presentan como tales, nunca como evidencia definitiva.

## Estado

🚧 **Planificación** — aún no hay código. Documentación:

- Plan maestro: [`docs/plan.md`](docs/plan.md)
- Seguimiento por milestone: [`docs/milestones/`](docs/milestones/) (tablero en su `README.md`)
- Guía para agentes/colaboradores: [`AGENTS.md`](AGENTS.md)

## Ciclo del producto

**Entender → Calcular → Registrar → Analizar → Decidir.**

## Stack (objetivo)

Django 5.2 · PostgreSQL 16 · templates SSR + HTMX · motor estadístico **puro** en Python (NumPy/SciPy) · `uv` ·
pytest/Hypothesis/Playwright. Bilingüe **es/en** (pt preparado).

## Cómo empezar (tras M1)

```bash
uv sync && docker compose up -d db
uv run python manage.py migrate && uv run python manage.py seed
uv run pytest && uv run python manage.py runserver
```

## Licencias

- **Código:** por definir (ver `docs/plan.md` §I).
- **Dataset comunitario:** por definir (CC BY / CC0 a decidir), sujeto a revisión legal antes de la beta.
