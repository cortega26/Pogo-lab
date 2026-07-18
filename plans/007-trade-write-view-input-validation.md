# Plan 007: Stop trade write-views from 500-ing on malformed input

> **Executor instructions**: Follow step by step; run every verification.
> Honor "STOP conditions". Update this plan's row in `plans/README.md`.
> Comments/docstrings/commit messages in **español neutral**.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/trades/views.py`
> If changed, re-read and compare against "Current state".

## Status

- **Priority**: P3
- **Effort**: S
- **Risk**: LOW
- **Depends on**: 001 (green baseline). Pairs with 005 (its `ValueError` from bad enums is caught here). Both edit `apps/trades/` — see Maintenance notes.
- **Category**: bug / robustness
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

The authenticated trade data-entry views parse request input with bare
`datetime.fromisoformat`/`int()`/`.decode()` and no error handling, so
malformed input returns **HTTP 500** on the app's core workflow:

- `observation_create`: `datetime.datetime.fromisoformat(observed_at_str)` and
  `int(request.POST.get("atk"/"def"/"hp"))` — bad date or non-numeric IV → 500.
- `bulk_add`: assumes `data` (parsed JSON) is a **list** and does
  `int(item.get(...))` per item — a non-list JSON body or non-numeric field → 500.
- `csv_import`: `uploaded.read().decode("utf-8-sig")` — a non-UTF-8 (e.g.
  binary) upload → `UnicodeDecodeError` → 500.

These are self-inflicted by the logged-in user, but they generate error noise/
alerting and a poor experience on the primary data-entry paths. Return
field-level errors instead.

## Current state

`apps/trades/views.py`:

- `observation_create` (lines ~64-109): `observed_at` parse at line ~73;
  `int(...)` IVs at lines ~79-81; renders `trades/observation_create.html`
  (HTMX returns `trades/_observation_row.html`).
- `bulk_add` (lines ~112-158): `json.loads` already guarded for
  `JSONDecodeError` (lines ~120-127), but the subsequent `for item in data`
  loop (lines ~130-149) assumes a list and does `int(item.get(...))` unguarded.
- `csv_import` (lines ~161-196): `content = uploaded.read().decode("utf-8-sig")`
  at line ~179 unguarded.
- Existing error-render pattern: `bulk_add` already renders
  `trades/bulk_add.html` with `{"error": "JSON invalido"}` — mirror it.

## Commands you will need

| Purpose        | Command                                   | Expected  |
|----------------|-------------------------------------------|-----------|
| Targeted tests | `uv run pytest tests/test_trades.py -q`   | all pass  |
| Full tests     | `uv run pytest -q`                        | 0 failed  |
| Lint / types   | `uv run ruff check .` ; `uv run mypy config engine apps tests` | exit 0 |

## Scope

**In scope**:
- `apps/trades/views.py`
- `tests/test_trades.py`
- If needed, a minimal `{% if error %}` line in the relevant trades templates
  (`observation_create.html`, `csv_import.html`) — only if they don't already
  show an `error`.

**Out of scope**:
- `apps/trades/services.py` — service-layer enum validation is Plan 005; the
  N+1 fix is Plan 008. This plan only makes the **views** fail gracefully.

## Git workflow

- Branch: `fix/007-trade-input-validation`.
- Commit e.g. `fix(trades): entradas malformadas devuelven error, no 500`.

## Steps

### Step 1: Guard `observation_create`

Wrap the date and IV parsing (and the `register_observation` call, so a
`ValueError` from Plan 005's enum check is also caught) in `try/except`:

```python
try:
    observed_at = (
        datetime.datetime.fromisoformat(observed_at_str)
        if observed_at_str
        else datetime.datetime.now(tz=datetime.UTC)
    )
    atk = int(request.POST.get("atk", 0))
    def_ = int(request.POST.get("def", 0))
    hp = int(request.POST.get("hp", 0))
    obs = register_observation(...)  # existing call
except (ValueError, TypeError) as exc:
    ctx = {"error": str(exc) or "Datos inválidos"}
    if request.headers.get("HX-Request"):
        # htmx only swaps 2xx by default — return 200 so the error renders
        # (a 400 would leave the HTMX target blank).
        return render(request, "trades/observation_create.html", ctx, status=200)
    return render(request, "trades/observation_create.html", ctx, status=400)
```

(Adjust to keep the existing success rendering intact.) If
`observation_create.html` doesn't render `{{ error }}`, add a single
`{% if error %}<p class="text-red-600 text-sm">{{ error }}</p>{% endif %}` near
the top of its form.

### Step 2: Guard `bulk_add`

- After `json.loads`, assert it's a list: `if not isinstance(data, list): return render(..., {"error": "Se esperaba una lista de observaciones"})`.
- Wrap the per-item `int(...)` conversions (and `fromisoformat`) in `try/except (ValueError, TypeError)` → render `trades/bulk_add.html` with an `error` (mirror the existing JSON-error render), status 400.

### Step 3: Guard `csv_import`

Wrap the decode:

```python
try:
    content = uploaded.read().decode("utf-8-sig")
except UnicodeDecodeError:
    error = "El archivo no es un CSV de texto UTF-8 válido."
else:
    result = import_csv(content, owner_id)
    ...
```

Keep the rest (preview/error messaging) intact.

### Step 4: Tests

In `tests/test_trades.py` add (all logged-in; model after existing trade view
tests that `force_login` and POST):

- `test_observation_create_bad_date_returns_400_not_500`: POST `observed_at="not-a-date"` → status 400, no `TradeObservation` created.
- `test_observation_create_non_numeric_iv_400`: POST `atk="x"` → 400.
- `test_bulk_add_non_list_json_400`: POST `observations_json='{"a":1}'` → 400, renders error.
- `test_csv_import_binary_file_shows_error`: upload bytes `b"\xff\xfe\x00"` as `csv_file` → response is 200/400 with an error message, not 500.

**Verify**: `uv run pytest tests/test_trades.py -q` → all pass.

### Step 5: Full suite

**Verify**: `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.

## Test plan

- New tests in Step 4 cover each malformed-input path (date, IV, non-list JSON,
  non-UTF-8 upload) returning a handled response, never 500.
- Pattern: existing authenticated trade view tests in `tests/test_trades.py`.

## Done criteria

ALL must hold:

- [ ] Malformed date / non-numeric IV / non-list JSON / non-UTF-8 CSV all
      return a handled 4xx (or 200-with-error), never 500, and persist nothing.
- [ ] Valid submissions still succeed (existing tests pass).
- [ ] New tests pass; `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.
- [ ] Only in-scope files modified; `plans/README.md` row for 007 updated.

## STOP conditions

Stop and report if:

- A template's structure makes rendering an `error` non-trivial (e.g. it
  requires context the error path can't supply) — report rather than reworking.
- Any existing test expected one of these malformed inputs to succeed — report it.

## Maintenance notes

- **Ordering with Plan 005**: if 005 lands first, its `ValueError` on bad enums
  is already caught by Step 1's `try/except`. If 007 lands first, 005 will slot
  in behind the same handler. Either order is fine; rebase whichever is second.
- **Ordering with Plan 008**: 008 edits `apps/trades/services.py` (not views), so
  no direct conflict, but land them on separate branches and rebase.
- Reviewer: confirm no double-submit or partial-persist on the bulk path when an
  item mid-batch is invalid (it's atomic in the service).
