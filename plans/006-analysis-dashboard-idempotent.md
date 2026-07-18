# Plan 006: Make the analysis dashboard idempotent (stop writing a run per GET)

> **Executor instructions**: Follow step by step; run every verification.
> Honor "STOP conditions". Update this plan's row in `plans/README.md`.
> Comments/docstrings/commit messages in **español neutral**. This plan adds a
> DB field and a migration — run the migration-check gate.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/analysis/`
> If changed, re-read `apps/analysis/services.py`, `views.py`, `models.py` and
> compare against "Current state".

## Status

- **Priority**: P2
- **Effort**: M
- **Risk**: MED (touches reproducibility metadata + adds a migration)
- **Depends on**: 001 (green baseline). Land **before** Plan 009 (both edit `apps/analysis/services.py`).
- **Category**: bug / perf
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

`analysis_dashboard` is a plain **GET** view, but on every request it calls
`run_personal_analysis(...)`, which unconditionally
`AnalysisRun.objects.create(...)` plus several `AnalysisResult.objects.create(...)`
per group. So every page load, refresh, or crawler hit **persists a brand-new
run and N result rows** and re-runs the full statistical workload (counts +
Monte-Carlo uniformity tests). The `AnalysisRun`/`AnalysisResult` tables grow
unbounded with traffic (not with data), and each run is later re-serialized into
the account export payload (`apps/accounts/views.py` `_build_export_payload`),
bloating exports over time. A GET must be idempotent: identical inputs (same
owner, same filters, same underlying valid observations) should **reuse** the
existing run instead of creating another.

## Current state

- `apps/analysis/views.py:27` — `run = run_personal_analysis(owner.pk, filters=filters)`
  on every GET; the view then renders `run.results.all()`.
- `apps/analysis/services.py`:
  - `run_personal_analysis(owner_id, filters=None, seed=None, code_sha="")`
    (line ~297) — creates the `AnalysisRun` (line ~320), sets `mixing_flags`
    (line ~334), and loops groups creating `AnalysisResult` rows
    (lines ~347, 359, 367).
  - `_valid_observations(owner_id, filters)` (line ~33) — the filtered
    `state="valid"` queryset (applies `friendship_level`, `trade_type`,
    `observed_after`, `observed_before`).
  - `_deterministic_seed_from_data(...)` (line ~275) — existing helper you can
    mirror for hashing.
- `apps/analysis/models.py` — `AnalysisRun` fields: `owner`, `filters` (JSON),
  `ruleset_version`, `algorithm_version`, `method_params` (JSON), `random_seed`,
  `code_sha`, `mixing_flags`. **No** input-fingerprint field yet.
- `TradeObservation` extends `TimestampedModel` (has `created_at`/`updated_at`),
  so a data-freshness signature `(count, max(updated_at))` is available.

## Commands you will need

| Purpose          | Command                                                     | Expected      |
|------------------|-------------------------------------------------------------|---------------|
| Make migration   | `uv run python manage.py makemigrations analysis`           | creates 1 file|
| Migration check  | `uv run python manage.py makemigrations --check --dry-run`  | exit 0 (none pending) |
| Targeted tests   | `uv run pytest tests/test_analysis.py -q`                   | all pass      |
| Full tests       | `uv run pytest -q`                                          | 0 failed      |
| Lint / types     | `uv run ruff check .` ; `uv run mypy config engine apps tests` | exit 0     |

## Scope

**In scope**:
- `apps/analysis/models.py` (add one field)
- `apps/analysis/migrations/` (the generated migration)
- `apps/analysis/services.py` (add fingerprint + `get_or_run_personal_analysis`)
- `apps/analysis/views.py` (call the new function)
- `tests/test_analysis.py`

**Out of scope**:
- The statistical functions (`_hundo_rate_analysis`, `_stat_uniformity_analysis`,
  `_sum_uniformity_analysis`) and their numbers — do not change any computation.
- The pooled/community path `compute_pooled_statistics` — that is Plan 009.
- Adding a queue/async — analysis stays synchronous by design.

## Git workflow

- Branch: `fix/006-analysis-idempotent`.
- Commit e.g. `perf(analysis): reutiliza AnalysisRun cuando la entrada no cambió`.

## Steps

### Step 1: Add an `input_fingerprint` field

In `apps/analysis/models.py`, add to `AnalysisRun`:

```python
input_fingerprint = models.CharField(max_length=64, blank=True, default="", db_index=True)
```

Generate and apply the migration:

```bash
uv run python manage.py makemigrations analysis
```

**Verify**: `uv run python manage.py makemigrations --check --dry-run` → exit 0
(no pending changes after generating).

### Step 2: Compute a fingerprint of the inputs

In `apps/analysis/services.py`, add a helper that captures owner + filters +
algorithm version + a data-freshness signature (count and latest `updated_at`
of the filtered valid observations):

```python
def _input_fingerprint(owner_id: int, filters: dict[str, Any] | None) -> str:
    qs = _valid_observations(owner_id, filters)
    agg = qs.aggregate(c=models.Count("id"), m=models.Max("updated_at"))
    signature = {
        "owner_id": owner_id,
        "filters": filters or {},
        "algorithm_version": ALGORITHM_VERSION,
        "count": agg["c"] or 0,
        "max_updated": agg["m"].isoformat() if agg["m"] else None,
    }
    raw = json.dumps(signature, sort_keys=True, default=str)
    return hashlib.sha256(raw.encode()).hexdigest()
```

The `(count, max_updated)` pair changes when observations are added, edited, or
removed from the filtered valid set — so a stale run is never reused.

### Step 3: Store the fingerprint on the run, and add get-or-run

- In `run_personal_analysis`, accept an optional precomputed fingerprint and
  persist it. Simplest: compute it if not provided, and set it on the created
  run:

  ```python
  def run_personal_analysis(owner_id, filters=None, seed=None, code_sha="", input_fingerprint=None):
      ...
      if input_fingerprint is None:
          input_fingerprint = _input_fingerprint(owner_id, filters)
      run = AnalysisRun.objects.create(
          owner_id=owner_id,
          filters=filters or {},
          algorithm_version=ALGORITHM_VERSION,
          random_seed=seed,
          code_sha=code_sha,
          input_fingerprint=input_fingerprint,
      )
      ...
  ```

- Add the idempotent entry point:

  ```python
  def get_or_run_personal_analysis(owner_id, filters=None, seed=None, code_sha=""):
      """Reutiliza un AnalysisRun si la entrada (owner+filtros+datos) no cambió."""
      fingerprint = _input_fingerprint(owner_id, filters)
      existing = (
          AnalysisRun.objects.filter(owner_id=owner_id, input_fingerprint=fingerprint)
          .order_by("-created_at")
          .first()
      )
      if existing is not None:
          return existing
      return run_personal_analysis(
          owner_id, filters=filters, seed=seed, code_sha=code_sha,
          input_fingerprint=fingerprint,
      )
  ```

### Step 4: Use it in the dashboard GET

In `apps/analysis/views.py`, change the import and the call:

```python
from .services import get_or_run_personal_analysis
...
run = get_or_run_personal_analysis(owner.pk, filters=filters)
```

Leave the rest of the view (rendering `run.results.all()`, recommendations,
chart data) unchanged.

### Step 5: Tests

In `tests/test_analysis.py` add (model after the existing analysis tests that
create observations and call `run_personal_analysis`):

- `test_dashboard_get_is_idempotent`: create a user with some valid
  observations; `client.force_login`; GET the dashboard twice; assert
  `AnalysisRun.objects.filter(owner=user).count() == 1` after both.
- `test_new_observation_creates_new_run`: GET once (1 run); register a new
  valid observation; GET again; assert 2 runs.
- `test_get_or_run_reuses_same_run`: call `get_or_run_personal_analysis` twice
  with identical inputs → same `.pk`.
- Keep an existing test asserting the statistical payloads are unchanged
  (regression) — do not alter expected numbers.

**Verify**: `uv run pytest tests/test_analysis.py -q` → all pass.

### Step 6: Full suite + gates

**Verify**: `uv run pytest -q` → 0 failed;
`uv run python manage.py makemigrations --check --dry-run` → exit 0;
`ruff` + `mypy` clean.

## Test plan

- New idempotency tests (Step 5): two GETs → one run; data change → new run;
  helper reuse returns same pk.
- Regression: existing statistical-correctness tests still pass with identical
  numbers (the computation is untouched; only *when* a run is persisted changes).
- Verification: `uv run pytest tests/test_analysis.py -q` + full suite.

## Done criteria

ALL must hold:

- [ ] `AnalysisRun` has `input_fingerprint`; a migration exists and
      `makemigrations --check --dry-run` is clean.
- [ ] Two dashboard GETs with unchanged data create exactly **one** run.
- [ ] Adding/changing a valid observation causes the next GET to create a new run.
- [ ] All existing analysis tests still pass with unchanged expected values.
- [ ] `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean; only in-scope files modified.
- [ ] `plans/README.md` row for 006 updated.

## STOP conditions

Stop and report (do not improvise) if:

- Making the GET reuse a run breaks an existing test that asserts a new run is
  created on each dashboard load — report it; the intended semantics may need a
  product decision (reuse vs. always-new).
- `_valid_observations`/filter shape has drifted so `.aggregate(Max("updated_at"))`
  isn't available (e.g. `TradeObservation` no longer has `updated_at`) — report
  it instead of inventing a fingerprint.

## Maintenance notes

- Two concurrent first-time GETs can both miss the cache and create two runs
  (benign race). If this ever matters, wrap creation in `get_or_create`-style
  logic on `(owner, input_fingerprint)`.
- If `AnalysisRun` gains a real `ruleset_version`/`dataset_version` that affects
  results, fold it into `_input_fingerprint`.
- Reviewer: confirm the export payload now contains far fewer (deduplicated)
  runs and that reproducibility metadata (seed/algorithm_version) is intact.
- Plan 009 refactors `compute_pooled_statistics` in this same file — rebase it
  on top of this plan.
