# Plan 004: Validate calculator POST input (no more public 500s)

> **Executor instructions**: Follow step by step; run every verification.
> Honor "STOP conditions". Update this plan's row in `plans/README.md`.
> Comments/docstrings/commit messages in **español neutral**.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/calculators/`
> If changed, re-read the files and compare against "Current state".

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: 001 (green baseline)
- **Category**: security / robustness
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

The calculator is a **public, unauthenticated** endpoint. On POST it parses
form fields with bare `int()`/`float()` and no bounds:

```python
n=int(post.get("n", 1)),
confidence=float(post.get("confidence", 0.5)),
```

Any request with `n=abc` (or a non-numeric `confidence`) raises `ValueError`,
which is uncaught on the POST path → **HTTP 500** on a public route (error
noise, alerting, and a poor signal to scanners). The GET `?share=` path already
funnels errors through a `try/except` and renders a friendly `error`; the POST
path should behave the same. (Note: the engine math is closed-form, so a large
`n` is *not* a compute DoS — this is purely input validation, but we also clamp
`n` to a sane range for hygiene.)

## Current state

`apps/calculators/views.py`:

- `calculator_view` POST branch (line ~17-26): `inputs = _inputs_from_post(request.POST)`
  then `compute_scenario_cached(inputs)`; for HTMX returns `_result.html`.
- The GET `?share=` branch (line ~27-33) wraps decode+compute in
  `try/except (ValueError, KeyError)` and sets `error = str(exc)`, then renders
  `page.html` with `error`. **`page.html` already displays `{{ error }}`.**
- `_inputs_from_post` (line ~69-77): the unguarded `int()/float()`.
- `_int_or_none` (line ~80-86): already safe (returns `None` on bad input) —
  use it as the pattern.

## Commands you will need

| Purpose        | Command                                            | Expected   |
|----------------|----------------------------------------------------|------------|
| Targeted tests | `uv run pytest tests/test_calculators.py -q`       | all pass   |
| Full tests     | `uv run pytest -q`                                 | 0 failed   |
| Lint / types   | `uv run ruff check .` ; `uv run mypy config engine apps tests` | exit 0 |

## Scope

**In scope**:
- `apps/calculators/views.py`
- `apps/calculators/templates/calculators/_result.html` (one-line error display, only if needed for the HTMX path)
- `tests/test_calculators.py`

**Out of scope**:
- `apps/calculators/services.py` and `engine/` — the math is fine; do not touch
  `compute_scenario`/probability functions.
- The share-URL encode/decode logic.

## Git workflow

- Branch: `fix/004-calculator-validation`.
- Commit e.g. `fix(calculators): valida entrada del POST público y evita 500`.

## Steps

### Step 1: Add a validating parser

Add a helper that raises a clean `ValueError` (with a user-facing message) on
bad input, and make `_inputs_from_post` use it. Bounds: `1 <= n <= 1_000_000`,
`0 < confidence < 1`; `threshold` keeps using `_int_or_none`.

```python
def _parse_int_in_range(raw: str | None, *, default: int, lo: int, hi: int, label: str) -> int:
    try:
        value = int(raw) if raw not in (None, "") else default
    except (TypeError, ValueError) as exc:
        raise ValueError(f"{label} debe ser un número entero.") from exc
    if not lo <= value <= hi:
        raise ValueError(f"{label} debe estar entre {lo} y {hi}.")
    return value


def _parse_confidence(raw: str | None, *, default: float = 0.5) -> float:
    try:
        value = float(raw) if raw not in (None, "") else default
    except (TypeError, ValueError) as exc:
        raise ValueError("La confianza debe ser un número.") from exc
    if not 0.0 < value < 1.0:
        raise ValueError("La confianza debe estar entre 0 y 1 (exclusivo).")
    return value
```

Rewrite `_inputs_from_post` to use these (`n` via `_parse_int_in_range(..., default=1, lo=1, hi=1_000_000, label="n")`, `confidence` via `_parse_confidence`).

### Step 2: Handle the error on the POST path

Wrap the POST branch so a `ValueError` renders an error instead of 500:

```python
if request.method == "POST":
    try:
        inputs = _inputs_from_post(request.POST)
        result = compute_scenario_cached(inputs)
        share_url = encode_share_url(inputs)
    except ValueError as exc:
        error = str(exc)
        if request.headers.get("HX-Request"):
            # htmx only swaps 2xx responses by default — return 200 so the error
            # message actually renders (a 400 would leave the results area blank).
            return render(request, "calculators/_result.html", {"result": None, "error": error})
        # fall through to render page.html with error (status 400 for non-htmx)
    else:
        if request.headers.get("HX-Request"):
            return render(request, "calculators/_result.html", {"result": result, "share_url": share_url})
```

For the non-HTMX error case, ensure the final `render(... "calculators/page.html" ...)`
receives `error` and returns `status=400`. (You may pass `status=400` only when
`error` is set; a normal empty-form GET stays 200.)

### Step 3: Show the error in the HTMX partial (only if the partial doesn't already)

Read `apps/calculators/templates/calculators/_result.html`. If it does not
already render `{{ error }}`, add a single guarded line at the top, modeling on
how `page.html` shows the error:

```django
{% if error %}<p class="text-red-600 text-sm">{{ error }}</p>{% endif %}
```

If `_result.html` assumes `result` is always present and would crash on
`result=None`, guard its body with `{% if result %}...{% endif %}`.

### Step 4: Tests

In `tests/test_calculators.py` add:

- `test_post_non_numeric_n_returns_400_not_500`: `client.post(url, {"n": "abc", ...})`
  → status 400 (NOT 500); response is renderable.
- `test_post_confidence_out_of_range_400`: `confidence="5"` → 400.
- `test_post_valid_input_still_ok`: a valid POST → 200 and a result (regression).
- `test_post_huge_n_clamped_or_rejected`: `n="999999999"` → 400 (above cap),
  and the request returns quickly (no hang).

Use `reverse("calculator")` for the URL; the endpoint is public (no login).

**Verify**: `uv run pytest tests/test_calculators.py -q` → all pass.

### Step 5: Full suite

**Verify**: `uv run pytest -q` → 0 failed; `uv run ruff check .` and
`uv run mypy config engine apps tests` → exit 0.

## Done criteria

ALL must hold:

- [ ] A public POST with `n=abc` returns 4xx (400), never 500, and does not raise.
- [ ] `n` is bounded (`1..1_000_000`) and `confidence` is in `(0,1)`.
- [ ] Valid POSTs still return 200 with a result (regression test passes).
- [ ] New tests exist and pass; `uv run pytest -q` → 0 failed.
- [ ] `ruff` + `mypy` clean; only in-scope files modified.
- [ ] `plans/README.md` row for 004 updated.

## STOP conditions

Stop and report if:

- `_result.html` has a structure that makes the `result=None` error case
  non-trivial to render — report it rather than reworking the template broadly.
- Bounding `n` breaks an existing calculator test that legitimately uses a
  larger value — report the value; the cap may need raising.

## Maintenance notes

- If the calculator gains new numeric inputs, route them through the same
  `_parse_*` helpers.
- Reviewer: confirm the GET `?share=` path still shows errors as before (its
  `try/except` is unchanged) and that a normal empty GET is still 200.
