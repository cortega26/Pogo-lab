# Plan 005: Validate friendship/trade-type enums in `register_observation`

> **Executor instructions**: Follow step by step; run every verification.
> Honor "STOP conditions". Update this plan's row in `plans/README.md`.
> Comments/docstrings/commit messages in **español neutral**.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/trades/services.py apps/trades/views.py`
> If changed, re-read and compare against "Current state".

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: 001 (green baseline)
- **Category**: bug / data-integrity
- **Planned at**: commit `fae5586`, 2026-07-17
- **Interacts with**: 007 and 008 (all three touch `apps/trades/`) — see Maintenance notes for ordering.

## Why this matters

`parse_csv_row` validates `friendship_level ∈ {good, great, ultra, best}` and
`trade_type ∈ {normal, lucky, lucky_guaranteed}` before creating an
observation. But the **manual** (`observation_create`) and **bulk** (`bulk_add`)
entry paths call `register_observation(...)` directly, which goes straight to
`TradeObservation.objects.create(...)` — Django `.create()` does **not** enforce
model `choices`. So a request with `friendship_level=lolz` (or any garbage
`trade_type`) is persisted silently. Downstream, `apps/analysis/services.py`
`_build_groups` turns each distinct `friendship_level` into its own analysis
group, so garbage enums produce **spurious, mislabeled statistical groups** —
directly undermining the project's statistical-honesty invariant. This closes
the validation gap so all three ingestion paths reject the same invalid enums.

## Current state

`apps/trades/services.py`:

- `parse_csv_row` (lines ~230-236) — the *only* path that validates enums:

  ```python
  friendship_level = row.get("friendship_level", "").strip()
  if friendship_level not in ("good", "great", "ultra", "best"):
      return f"Fila {row_num}: friendship_level invalido: {friendship_level}"
  trade_type = row.get("trade_type", "").strip()
  if trade_type not in ("normal", "lucky", "lucky_guaranteed"):
      return f"Fila {row_num}: trade_type invalido: {trade_type}"
  ```

- `register_observation` (lines ~107-196) — receives `friendship_level`/
  `trade_type` and calls `TradeObservation.objects.create(...)` at line ~172
  with **no** enum check. `_derive_is_lucky` silently treats any unknown
  `trade_type` as non-lucky.

- Callers that bypass validation: `apps/trades/views.py` `observation_create`
  (lines ~77-78) and `bulk_add` (lines ~141-142) pass request data straight
  through.

## Commands you will need

| Purpose        | Command                                       | Expected   |
|----------------|-----------------------------------------------|------------|
| Targeted tests | `uv run pytest tests/test_trades.py -q`       | all pass   |
| Full tests     | `uv run pytest -q`                            | 0 failed   |
| Lint / types   | `uv run ruff check .` ; `uv run mypy config engine apps tests` | exit 0 |

## Scope

**In scope**:
- `apps/trades/services.py` (add validation + shared constants; refactor
  `parse_csv_row` to reuse the constants)
- `tests/test_trades.py`

**Out of scope**:
- `apps/trades/views.py` — view-level error rendering for the raised
  `ValueError` is Plan 007's job. This plan makes the **service** reject bad
  enums; see Maintenance notes.
- The IV range check and dedup logic (already correct).

## Git workflow

- Branch: `fix/005-observation-enum-validation`.
- Commit e.g. `fix(trades): valida enums de friendship/trade_type en register_observation`.

## Steps

### Step 1: Extract shared enum constants

At the top of `apps/trades/services.py` (after imports) add:

```python
FRIENDSHIP_LEVELS = ("good", "great", "ultra", "best")
TRADE_TYPES = ("normal", "lucky", "lucky_guaranteed")
```

Refactor `parse_csv_row` to reference these constants instead of the inline
tuples (behavior identical — just DRY).

### Step 2: Validate inside `register_observation`

At the start of `register_observation` (before computing `is_lucky`), add:

```python
if friendship_level not in FRIENDSHIP_LEVELS:
    raise ValueError(f"friendship_level inválido: {friendship_level!r}")
if trade_type not in TRADE_TYPES:
    raise ValueError(f"trade_type inválido: {trade_type!r}")
```

This makes every path (manual, bulk, CSV) reject the same invalid enums. Since
`bulk_create_observations` runs inside `transaction.atomic()`, a raised
`ValueError` rolls back the whole batch (acceptable — an invalid batch should
not partially persist).

### Step 3: Tests

In `tests/test_trades.py` add:

- `test_register_observation_rejects_bad_friendship`: calling
  `register_observation(..., friendship_level="lolz", trade_type="normal", ...)`
  raises `ValueError`, and no `TradeObservation` row is created.
- `test_register_observation_rejects_bad_trade_type`: analogous for `trade_type`.
- `test_bulk_create_rejects_and_rolls_back`: a 2-item batch where the 2nd item
  has a bad enum raises `ValueError` and creates **zero** rows (atomic rollback).
- Confirm a valid `register_observation` still works (regression) — reuse an
  existing valid-observation test as the template.

**Verify**: `uv run pytest tests/test_trades.py -q` → all pass.

### Step 4: Full suite

**Verify**: `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.

## Test plan

- New tests in Step 3 (reject bad friendship, reject bad trade_type, atomic
  rollback, valid still works).
- Pattern: existing `register_observation`/`bulk_create_observations` tests in
  `tests/test_trades.py`.

## Done criteria

ALL must hold:

- [ ] `register_observation` raises `ValueError` on invalid `friendship_level`
      or `trade_type`; no row persisted.
- [ ] `parse_csv_row` uses the shared `FRIENDSHIP_LEVELS`/`TRADE_TYPES`
      constants (its existing CSV tests still pass).
- [ ] New tests pass; `uv run pytest -q` → 0 failed.
- [ ] `ruff` + `mypy` clean; only in-scope files modified.
- [ ] `plans/README.md` row for 005 updated.

## STOP conditions

Stop and report if:

- An existing test deliberately calls `register_observation` with a
  `friendship_level`/`trade_type` outside these sets and expects success —
  report it; the allowed sets may be incomplete.
- The model defines a different/larger set of valid choices than the CSV
  validator uses (check `TradeObservation` field `choices` in
  `apps/trades/models.py`) — if they differ, report the mismatch instead of
  guessing which is authoritative.

## Maintenance notes

- **Ordering with Plans 007 and 008** (all touch `apps/trades/`): land 005 and
  007 close together. After 005, a bad manual enum makes the **service** raise
  `ValueError`; Plan 007 adds the view-level `try/except` that turns that into a
  friendly form error instead of a 500. If 007 lands first, its handler will
  already catch this `ValueError`. Plan 008 edits the import/query path in the
  same file — rebase whichever lands second.
- Reviewer: confirm the three ingestion paths (manual, bulk, CSV) now reject
  the identical enum sets, and that the constants are the single source of truth.
