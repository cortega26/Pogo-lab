# Plan 009: Unify the personal (M5) and pooled (M6) analysis aggregators

> **Executor instructions**: This is the **trickiest** plan — it touches
> statistical output. The personal path's numbers must stay **byte-identical**;
> the only intended output change is the pooled path gaining sum-uniformity.
> Run every verification. If any existing statistical assertion changes value,
> that is a STOP condition. Update `plans/README.md`. Comments/commits in
> **español neutral**.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/analysis/services.py`
> If changed (e.g. Plan 006 landed), re-read the file; 006 is expected to have
> landed first — rebase on it.

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED (statistical output builders)
- **Depends on**: 001 (green baseline); land **after** 006 (same file).
- **Category**: tech-debt (+ correctness: fixes a metric asymmetry) (+ tests: parity)
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

`run_personal_analysis` (M5) builds its payloads with the helpers
`_hundo_rate_analysis`, `_stat_uniformity_analysis`, and
`_sum_uniformity_analysis`. `compute_pooled_statistics` (M6) **re-implements the
first two inline** instead of calling them, and **omits sum-uniformity
entirely**. So: (a) the two aggregators have already **diverged** — the
community/pooled report silently lacks a statistic the personal report shows;
and (b) every future schema/threshold change must be made in two places (that's
how the sum-uniformity gap slipped in). They should share one row-oriented
aggregator so they cannot drift, and the pooled path should produce the same
metric families as the personal one.

## Current state

`apps/analysis/services.py`:

- Personal helpers (operate on a **QuerySet**):
  - `_hundo_rate_analysis(observations, f)` (lines ~138-174): `n = observations.count()`,
    `successes = observations.filter(atk=15, iv_def=15, hp=15).count()`, then
    binomial test + Wilson interval, else `insufficient_sample`.
  - `_stat_uniformity_analysis(observations, f, seed)` (lines ~177-218): per stat
    (`atk`/`iv_def`/`hp`) build a `Counter`, `uniformity_test`.
  - `_sum_uniformity_analysis(observations, f, seed)` (lines ~221-259): IV-sum
    distribution via `iv_sum_distribution(f)`, `uniformity_test`.
- Pooled path `compute_pooled_statistics(anonymized_rows)` (lines ~376-476):
  groups list-of-dicts by `(is_lucky, friendship_level, ruleset_version)`, then
  **inlines** the hundo logic (lines ~408-431) and the per-stat uniformity loop
  (lines ~440-462). **No** sum-uniformity. Emits `{"hundo_analysis", "statistics"}`.
- Shared engine primitives already imported: `p_hundo`, `exact_binomial_test`,
  `wilson_interval`, `uniformity_test`, `min_sample_for`, `iv_sum_distribution`.

## Commands you will need

| Purpose        | Command                                             | Expected  |
|----------------|-----------------------------------------------------|-----------|
| Analysis tests | `uv run pytest tests/test_analysis.py -q`           | all pass  |
| Contrib tests  | `uv run pytest apps/contributions/tests/test_contributions.py -q` | all pass |
| Full tests     | `uv run pytest -q`                                  | 0 failed  |
| Lint / types   | `uv run ruff check .` ; `uv run mypy config engine apps tests` | exit 0 |

## Scope

**In scope**:
- `apps/analysis/services.py`
- `tests/test_analysis.py`, `apps/contributions/tests/test_contributions.py`
  (add parity test; update pooled expectations for the new sum metric)

**Out of scope**:
- `engine/` — do not change any statistical primitive.
- The grouping keys / floor resolution (`_build_groups`, `_group_floor`,
  `_floor_for_version`) — unchanged.
- `run_personal_analysis`'s persistence/idempotency (Plan 006).

## Git workflow

- Branch: `refactor/009-unify-aggregators` (rebased on 006).
- Commit e.g. `refactor(analysis): un solo agregador por filas para M5 y M6`.

## Steps

### Step 1: Extract counts-based payload builders

Add three helpers that take already-aggregated **primitive counts** (no
QuerySet, no dict-row knowledge) and return the exact payloads the personal
helpers produce today. Copy the bodies verbatim, parameterizing the inputs:

```python
def _hundo_payload(n: int, successes: int, f: int) -> dict[str, Any]:
    # identical body to _hundo_rate_analysis, but n/successes passed in
    ...

def _stat_uniformity_payloads(counts_by_stat: dict[str, list[int]], n: int, f: int, seed: int | None) -> dict[str, dict]:
    # identical per-stat body; counts_by_stat = {"atk": [...], "def": [...], "hp": [...]}
    ...

def _sum_uniformity_payload(sum_counts: list[int], sum_values: list[int], sum_probs: list[float], n: int, seed: int | None) -> dict:
    # identical body to _sum_uniformity_analysis, but counts/values/probs passed in
    ...
```

### Step 2: Rewrite the personal helpers to delegate (output must be identical)

- `_hundo_rate_analysis(observations, f)` → compute `n`/`successes` from the
  queryset, then `return _hundo_payload(n, successes, f)`.
- `_stat_uniformity_analysis(observations, f, seed)` → build
  `counts_by_stat = {"atk": ..., "def": ..., "hp": ...}` from Counters over the
  queryset (materialize the queryset once into a list first to avoid re-scans),
  then `return _stat_uniformity_payloads(counts_by_stat, n, f, seed)`.
- `_sum_uniformity_analysis(observations, f, seed)` → build the sum counts, then
  delegate to `_sum_uniformity_payload`.

**Verify (critical)**: `uv run pytest tests/test_analysis.py -q` → all pass with
**unchanged** expected numbers. If any value differs, STOP.

### Step 3: Make the pooled path call the SAME builders (and gain sum-uniformity)

In `compute_pooled_statistics`, per group, compute from the dict rows:
`n`, `successes` (rows with `atk==15 and def==15 and hp==15`), `counts_by_stat`
(Counters over `r["atk"]/r["def"]/r["hp"]`), and the sum counts (Counter over
`r["atk"]+r["def"]+r["hp"]` against `iv_sum_distribution(f)`). Then call:

```python
group_result = {
    "is_lucky": is_lucky,
    "friendship_level": friendship_level,
    "ruleset_version": ruleset_version,
    "n": n,
    "floor": f,
    "hundo_analysis": _hundo_payload(n, successes, f),
    "statistics": _stat_uniformity_payloads(counts_by_stat, n, f, dataset_seed),
    "sum_analysis": _sum_uniformity_payload(sum_counts, sum_values, sum_probs, n, dataset_seed),
}
```

Delete the inline hundo/stat reimplementations (lines ~408-462). The pooled
output now includes `sum_analysis` — a **new key** (the intended parity fix).

### Step 4: Parity + regression tests

- In `tests/test_analysis.py`, add `test_personal_and_pooled_parity`: build one
  set of observations; run `run_personal_analysis` and, from the same rows,
  build the anonymized-row dicts and run `compute_pooled_statistics`; assert
  that for a matching group the **metric families match** — same `hundo_analysis`
  keys/values and same per-stat `p_value`/`method_used`, and that **both** now
  produce a sum metric.
- Update any existing pooled test in `apps/contributions/tests/test_contributions.py`
  that asserts the pooled result **shape** to expect the new `sum_analysis` key
  (do not weaken existing value assertions — add to them).

**Verify**: both test files pass.

### Step 5: Full suite

**Verify**: `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.

## Test plan

- Regression: existing personal-path statistical values unchanged (Step 2 gate).
- New parity test: identical data → identical metric families across both paths.
- Pooled now exposes `sum_analysis`; its existing tests updated to expect it.

## Done criteria

ALL must hold:

- [ ] The inline hundo/stat reimplementation in `compute_pooled_statistics` is
      gone; both paths call `_hundo_payload`/`_stat_uniformity_payloads`.
- [ ] Pooled output includes `sum_analysis` (parity with personal).
- [ ] Personal-path statistical values are **unchanged** (existing tests pass
      without edits to expected numbers).
- [ ] Parity test exists and passes; `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.
- [ ] Only in-scope files modified; `plans/README.md` row for 009 updated.

## STOP conditions

Stop and report (do NOT improvise) if:

- Any existing statistical assertion in `tests/test_analysis.py` changes value
  after Step 2 — the extraction must be output-identical.
- The reviewer/product owner has NOT decided whether the community/pooled
  dataset should expose IV-sum uniformity — Step 3 changes public pooled output.
  If unsure, do Steps 1-2 (pure dedup, no output change) and land those; leave
  Step 3 (`sum_analysis`) for a follow-up and say so.
- The pooled seed (`dataset_seed`) vs. personal seed differ in a way that makes
  the parity test fail on values (they use different seed sources by design) —
  assert metric **structure/keys** and `insufficient_sample`/`method_used`
  rather than exact p-values across the two paths, and note it.

## Maintenance notes

- After this, a schema/threshold change to any metric is made **once** in the
  counts-based builder and both paths inherit it.
- Reviewer: confirm the personal path output is unchanged and that pooled now
  carries the sum metric (or that Step 3 was deliberately deferred).
- This composes with Plan 006 (idempotency) — both edit this file; 006 first.
