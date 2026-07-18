# Plan 008: Fix the CSV/bulk import N+1 and add query-count regression guards

> **Executor instructions**: Follow step by step; run every verification.
> Honor "STOP conditions". Update this plan's row in `plans/README.md`.
> Comments/docstrings/commit messages in **español neutral**.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/trades/services.py apps/mechanics/services.py`
> If changed, re-read and compare against "Current state".

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: LOW-MED (behavior-preserving refactor of the import hot path)
- **Depends on**: 001 (green baseline). Shares `apps/trades/services.py` with 005 — see Maintenance notes.
- **Category**: perf (+ tests: query-count guards)
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

`bulk_create_observations` loops `register_observation(**data)` once per row
inside a transaction, and **each call re-resolves the same invariant floor**:

- `_determine_state` → `resolve_trade_floor(friendship_level, trade_type)` (`services.py:83`)
- `register_observation` → `resolve_trade_floor(...)` **again** (`services.py:160`)
- then `MechanicRuleSet.objects.filter(...).first()` (`services.py:162`)
- plus the per-row dedup `.exists()` (`services.py:93`) and the insert.

`resolve_trade_floor` itself issues ~3 queries. So a row costs ~9 queries, and a
500-row CSV import (`import_csv` → `bulk_create_observations`) issues ~4,500
queries re-resolving a floor that depends only on `(friendship_level,
trade_type)` — of which there are at most a handful of distinct combinations in
any batch. Resolve each distinct combo **once** per batch. The repo currently
has **zero** query-count assertions anywhere, so this (and future N+1s) can
regress invisibly — this plan adds the guard.

## Current state

`apps/trades/services.py`:

- `bulk_create_observations` (lines ~199-212):

  ```python
  with transaction.atomic():
      for data in observations:
          obs = register_observation(**data)
          results.append(obs)
  ```

- `register_observation` (lines ~107-196): calls `_determine_state` (which calls
  `resolve_trade_floor` for the floor `f`), then **again** resolves at
  lines ~159-170:

  ```python
  try:
      _f_ruleset, ruleset_version = resolve_trade_floor(friendship_level, trade_type)
      if ruleset_version is not None:
          ruleset = MechanicRuleSetModel.objects.filter(
              version=ruleset_version, mechanic__key="trade_iv", is_published=True
          ).first()
      else:
          ruleset = None
  except RulesetUnavailableError:
      ruleset = None
  ```

- `_determine_state` (lines ~64-104): resolves `f` via `resolve_trade_floor`
  (fallback `f = 0` on `RulesetUnavailableError`), then does `ivs_consistent_with_floor`
  and the dedup `.exists()`.
- Both `resolve_trade_floor` calls in a single `register_observation` return the
  **same** `(f, ruleset_version)` — they can be resolved once and shared.

## Commands you will need

| Purpose        | Command                                   | Expected  |
|----------------|-------------------------------------------|-----------|
| Targeted tests | `uv run pytest tests/test_trades.py -q`   | all pass  |
| Full tests     | `uv run pytest -q`                        | 0 failed  |
| Lint / types   | `uv run ruff check .` ; `uv run mypy config engine apps tests` | exit 0 |

## Scope

**In scope**:
- `apps/trades/services.py` (hoist floor/ruleset resolution; add an optional
  pre-resolved param to `register_observation` and `_determine_state`)
- `tests/test_trades.py` (query-count guards + behavior regression)

**Out of scope**:
- `apps/mechanics/services.py` (`resolve_trade_floor` internals) — don't change
  its logic; just call it fewer times.
- The dedup granularity and `_compute_dedup_hash` — unchanged.
- Any change to what state/ruleset a row ends up with — this is a pure
  performance refactor; **outputs must be identical**.

## Git workflow

- Branch: `perf/008-import-nplus1`.
- Commit e.g. `perf(trades): resuelve el piso una vez por combo en import por lotes`.

## Steps

### Step 1: Let `register_observation` accept a pre-resolved floor/ruleset

Add an optional keyword `resolved` to `register_observation` (default `None`),
carrying `{"floor": int|None, "ruleset_version": int|None, "ruleset": MechanicRuleSet|None}`.

- When `resolved` is provided: use `resolved["floor"]` for the state
  determination and `resolved["ruleset"]` for the FK, skipping both
  `resolve_trade_floor` calls and the `MechanicRuleSet` query.
- When `resolved is None`: behave exactly as today (standalone correctness for
  the manual-entry caller).

Thread the floor into `_determine_state` via an optional `resolved_floor`
parameter: if provided, skip its internal `resolve_trade_floor` and use it
directly (keeping the `f = 0` fallback semantics when `resolved_floor is None`
and resolution fails).

### Step 2: Resolve once per distinct combo in `bulk_create_observations`

```python
def bulk_create_observations(observations):
    resolved_cache: dict[tuple[str, str], dict] = {}

    def _resolve(friendship_level: str, trade_type: str) -> dict:
        key = (friendship_level, trade_type)
        if key not in resolved_cache:
            try:
                f, ruleset_version = resolve_trade_floor(friendship_level, trade_type)
            except RulesetUnavailableError:
                f, ruleset_version = 0, None
            ruleset = None
            if ruleset_version is not None:
                ruleset = MechanicRuleSetModel.objects.filter(
                    version=ruleset_version, mechanic__key="trade_iv", is_published=True
                ).first()
            resolved_cache[key] = {"floor": f, "ruleset_version": ruleset_version, "ruleset": ruleset}
        return resolved_cache[key]

    results = []
    with transaction.atomic():
        for data in observations:
            resolved = _resolve(data["friendship_level"], data["trade_type"])
            results.append(register_observation(**data, resolved=resolved))
    return results
```

This preserves the exact `(state, floor, ruleset)` each row gets — it only
computes them once per distinct `(friendship_level, trade_type)`.

### Step 3 (optional): batch the dedup check

Optional extra win (do only if Step 1-2 land cleanly): pre-fetch the owner's
existing non-deleted `dedup_hash` set once
(`set(TradeObservation.objects.filter(owner_id=owner, ...).exclude(state="deleted").values_list("dedup_hash", flat=True))`)
and pass it in so `_determine_state` checks membership in-memory instead of a
per-row `.exists()`. If this complicates correctness, **skip it** — the Step 1-2
win already removes the dominant cost.

### Step 4: Query-count guard (closes the "no assertNumQueries anywhere" gap)

Use pytest-django's `django_assert_max_num_queries` fixture. In
`tests/test_trades.py`:

- `test_bulk_import_query_count_is_near_linear`: build a CSV / observation list
  with, say, 10 rows all in ONE `(friendship_level, trade_type)` combo, seed the
  ruleset, then:

  ```python
  def test_bulk_import_query_count_is_near_linear(self, django_assert_max_num_queries, ...):
      rows = [...]  # 10 valid rows, same combo
      with django_assert_max_num_queries(10 + 3 * 10):  # generous ceiling, well below old ~9*10
          bulk_create_observations(rows)
  ```

  Pick the ceiling comfortably below the pre-fix cost (~9/row) but above the
  post-fix cost (~2/row plus a small constant) — e.g. `4 + 3 * n`. The point is
  to fail loudly if the per-row floor resolution ever comes back.

- `test_bulk_import_results_unchanged`: assert the created observations have the
  same `state`/`ruleset`/`is_lucky` as before (regression — reuse an existing
  import test's expectations).

**Verify**: `uv run pytest tests/test_trades.py -q` → all pass.

### Step 5: Full suite

**Verify**: `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.

## Test plan

- Query-count guard (`django_assert_max_num_queries`) proving import is no
  longer ~9/row.
- Behavior regression: same `state`/`ruleset`/`is_lucky` per row as before;
  existing `import_csv`/`bulk_create_observations` tests still pass unchanged.
- Verification: `uv run pytest tests/test_trades.py -q` + full suite.

## Done criteria

ALL must hold:

- [ ] `bulk_create_observations` resolves the floor/ruleset once per distinct
      `(friendship_level, trade_type)`, not per row.
- [ ] `register_observation(resolved=None)` behaves exactly as before (manual
      path unaffected).
- [ ] A `django_assert_max_num_queries` test locks the import query count near-
      linear and passes.
- [ ] All existing trade tests pass with identical row outcomes.
- [ ] `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean; only in-scope files modified.
- [ ] `plans/README.md` row for 008 updated.

## STOP conditions

Stop and report (do not improvise) if:

- The two `resolve_trade_floor` calls in `register_observation` turn out to
  return **different** values (they shouldn't) — do not "fix" it silently; report.
- Any existing import test's row outcome (state/ruleset/is_lucky) changes — the
  refactor must be output-identical; report the diff.
- `resolve_trade_floor`'s signature or return shape has drifted from
  `(floor, ruleset_version)` — report instead of guessing.

## Maintenance notes

- **Ordering with Plan 005** (same file): 005 adds enum validation at the top of
  `register_observation`; this plan adds the `resolved` kwarg and the batch
  cache. They don't conflict logically — rebase whichever lands second and
  re-run both plans' tests.
- If a future import needs per-row rulesets (e.g. importing historical data
  tagged with old ruleset versions), the per-combo cache key must include that
  ruleset dimension.
- Reviewer: confirm the query-count ceiling is meaningful (not so loose it never
  fails) and that row outcomes are unchanged.
