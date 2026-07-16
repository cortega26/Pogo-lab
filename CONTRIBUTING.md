# Cómo contribuir a Pogo-lab

Lee primero [`AGENTS.md`](AGENTS.md) (reglas no-negociables) y el mapa de documentación en [`docs/README.md`](docs/README.md).

## Principios de trabajo

- **DRY / SOLID / KISS atados a contratos verificables**, no a prosa (ver `AGENTS.md` § Principios de diseño).
- Cambios **pequeños y verticales**: un PR ≈ un item del roadmap (ver [`docs/plan.md`](docs/plan.md) §M — 21 PRs).
- Trabaja **milestone por milestone**: abre solo la hoja del milestone en curso ([`docs/milestones/`](docs/milestones/)).

## Flujo por cambio: "test antes y después" (TDD)

1. **Antes (rojo):** escribe o actualiza el test que expresa el comportamiento deseado y **falla**. En el `engine/`,
   empieza por la **fixture calculada a mano** (nunca un snapshot opaco).
2. **Implementa (verde):** el mínimo código para que pase.
3. **Después (regresión):** `pre-commit` (sub-segundo) en local + **suite completa en CI**. Nada se fusiona en rojo.

Ciclo en vivo opcional: `ptw`/`pytest-watch` para correr los tests afectados al guardar (el "antes/después" continuo).

> La suite completa **no** va en `pre-commit` (invitaría a `git commit --no-verify`): pre-commit = higiene + lint
> rápido; CI = tests, tipos, cobertura y contratos. Así el guardrail no se puede esquivar por comodidad.

## Commits: Conventional Commits

`tipo(scope): descripción` en **español neutral**. Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`,
`ci`, `build`, `perf`. Habilita el hook: `pre-commit install --hook-type commit-msg`.
El CHANGELOG se generará desde los commits (`git-cliff`) a partir de M1.

## Ramas

`main` protegida (verde en CI). Trabaja en ramas cortas (`feat/…`, `fix/…`, `docs/…`) y abre PR con el checklist.

## Tooling y guardrails (decisión registrada aquí; se **implementan en M1**)

Se documentan hoy para no re-decidir; se construyen **con** el código, donde corren en verde (no se pre-crean
inertes para que no drifteen contra lo que genere `uv init`).

| Herramienta | Rol | Contrato / gate en CI |
|---|---|---|
| **Ruff** | lint + format | Falla en violaciones |
| **mypy** + `django-stubs` | tipos | Falla en errores de tipo |
| **import-linter** | pureza de capas (SOLID/DIP) | Contrato: `engine/` **no** importa Django; las apps dependen de `engine/`, no al revés → **CI falla si se rompe** |
| **pytest** + `pytest-django` | tests | Suite completa; recolección determinista (`pytest-randomly`) |
| **hypothesis** | property-based | Invariantes del `engine/` (prob∈[0,1], Σ=1, monotonía, exacto≈MC) |
| **Playwright** | E2E | Flujos críticos (plan §13) |
| **coverage** | umbral | `engine/` alto (objetivo ≥95%), global razonable |
| **pip-audit** / `uv` | auditoría de dependencias | Falla en vulnerabilidades críticas |
| **Dependabot** | anti-drift de dependencias | PRs automáticos (GitHub Actions ya; pip en M1) |

Dos gates específicos anti-regresión (agendados):
- **M1** — contrato import-linter "`engine/` no importa Django".
- **M3** — test "**constantes de docs == salida del engine**" (`1/64`, `1/3375`, pisos): una sola fuente, los
  ejemplos de `plan.md`/`AGENTS.md` se verifican contra lo que calcula el `engine/`.

## Antes de abrir un PR

Sigue [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md): tests verdes, docs actualizadas (sin
duplicar hechos), ADR si la decisión es arquitectónica, y el **checklist de no-negociables** (lo que ningún linter
atrapa). La **Definición de Terminado** está en `docs/plan.md` §O.
