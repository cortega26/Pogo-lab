# Plan 003: Make consent grant/revoke POST-only with a validated redirect

> **Executor instructions**: Follow step by step; run every verification.
> Honor "STOP conditions". Update this plan's row in `plans/README.md`.
> Comments/docstrings/commit messages in **español neutral**.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/contributions/views.py apps/contributions/urls.py`
> If changed, re-read the files and compare against "Current state" before proceeding.

## Status

- **Priority**: P2
- **Effort**: S
- **Risk**: LOW
- **Depends on**: 001 (green baseline)
- **Category**: security
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

`grant_consent_view` and `revoke_consent_view` change a **GDPR-relevant
consent flag** (whether the user's trade observations may enter the public
community dataset) but do not require POST. Because they run on GET, they are
CSRF-able: a logged-in victim who merely loads
`<img src="https://site/es/contribuciones/consentir/">` (or clicks a crafted
link) silently grants or revokes consent — GET is exempt from Django's CSRF
protection. The GET path also bypasses the view's own rate limiter (it only
counts `method="POST"`). Both views additionally redirect to an unvalidated
`HTTP_REFERER` (a weak open-redirect).

## Current state

`apps/contributions/views.py` (full relevant code):

```python
@login_required
def grant_consent_view(request: HttpRequest) -> HttpResponse:
    if _is_rate_limited(request):
        return render(request, "core/429.html", status=429)
    DataContributionConsent.grant_consent(request.user, SCOPE, CONSENT_TEXT_VERSION)
    messages.success(request, _("Has dado tu consentimiento para contribuir."))
    return redirect(request.META.get("HTTP_REFERER", "/"))


@login_required
def revoke_consent_view(request: HttpRequest) -> HttpResponse:
    if _is_rate_limited(request):
        return render(request, "core/429.html", status=429)
    DataContributionConsent.revoke_consent(request.user, SCOPE)
    messages.info(request, _("Has revocado tu consentimiento."))
    return redirect(request.META.get("HTTP_REFERER", "/"))
```

- URLs (`apps/contributions/urls.py`): `consentir/` → `grant`, `revocar/` →
  `revoke`; included under `contribuciones/` in `config/urls.py` (so reachable
  at e.g. `/es/contribuciones/consentir/`).
- `_is_rate_limited` uses `method="POST"` only — GET is unmetered.
- Tests: `apps/contributions/tests/test_contributions.py` (use as the pattern
  for new tests; it already exercises consent grant/revoke).

## Commands you will need

| Purpose        | Command                                                        | Expected      |
|----------------|---------------------------------------------------------------|---------------|
| Targeted tests | `uv run pytest apps/contributions/tests/test_contributions.py -q` | all pass  |
| Full tests     | `uv run pytest -q`                                             | 0 failed      |
| Lint           | `uv run ruff check .`                                          | exit 0        |
| Typecheck      | `uv run mypy config engine apps tests`                         | exit 0        |

## Scope

**In scope**:
- `apps/contributions/views.py`
- `apps/contributions/tests/test_contributions.py` (add/adjust tests)
- Any template that links to `contributions:grant`/`contributions:revoke` via a
  plain link — convert to a POST form (see Step 3; there may be none).

**Out of scope**:
- `DataContributionConsent.grant_consent`/`revoke_consent` model methods — the
  consent logic itself is correct; only the HTTP entry points change.
- The rate-limit rate/threshold values.

## Git workflow

- Branch: `fix/003-consent-csrf`.
- Commit e.g. `fix(contributions): consentimiento solo por POST con redirección validada`.

## Steps

### Step 1: Require POST on both views

Add `from django.views.decorators.http import require_POST` and decorate both
views. Keep `@login_required` outermost:

```python
@login_required
@require_POST
def grant_consent_view(request: HttpRequest) -> HttpResponse:
    ...
```

Same for `revoke_consent_view`. Now GET → HTTP 405, and the rate limiter (POST)
applies to the only allowed method.

### Step 2: Validate the redirect target

Add a helper and use it in both views instead of the raw referer:

```python
from django.utils.http import url_has_allowed_host_and_scheme


def _safe_referer(request: HttpRequest, default: str = "/") -> str:
    ref = request.META.get("HTTP_REFERER", "")
    if ref and url_has_allowed_host_and_scheme(
        url=ref,
        allowed_hosts={request.get_host()},
        require_https=request.is_secure(),
    ):
        return ref
    return default
```

Replace `return redirect(request.META.get("HTTP_REFERER", "/"))` with
`return redirect(_safe_referer(request))` in both views.

**Verify**: `uv run ruff check .` and `uv run mypy config engine apps tests` → exit 0.

### Step 3: Convert any UI link to a POST form

Search for template usage:

```bash
grep -rniE "contributions:(grant|revoke)|consentir|revocar" apps/*/templates templates
```

- If a template links to these via `<a href="...">`, change it to a small POST
  form with `{% csrf_token %}` and a submit button (model after any existing
  POST form, e.g. `apps/trades/templates/trades/observation_create.html`).
- If there are **no** template references (the UI is not wired yet), note that
  in your report and skip — the security fix stands regardless.

### Step 4: Tests

In `apps/contributions/tests/test_contributions.py` add:

- `test_grant_consent_rejects_get`: logged-in `client.get(reverse("contributions:grant"))`
  → status 405, and consent is **not** created.
- `test_grant_consent_via_post_works`: `client.post(...)` → consent active
  (mirror the existing grant test but via POST).
- `test_revoke_consent_rejects_get`: analogous for revoke.
- `test_consent_redirect_ignores_external_referer`: POST with
  `HTTP_REFERER="https://evil.example/"` → the response redirect `Location`
  is the internal default (`/`), not the external URL.

**Verify**: `uv run pytest apps/contributions/tests/test_contributions.py -q` → all pass (incl. the 4 new).

### Step 5: Full suite

**Verify**: `uv run pytest -q` → 0 failed.

## Test plan

- New tests listed in Step 4: GET-rejection (405, no state change), POST happy
  path, and external-referer rejection.
- Pattern to follow: existing consent tests in the same file.
- If any existing test did `client.get()` on these endpoints expecting a
  redirect, update it to `client.post()`.

## Done criteria

ALL must hold:

- [ ] Both consent views are `@require_POST` (GET → 405) and still `@login_required`.
- [ ] Redirect goes through `_safe_referer`; external referer → internal default.
- [ ] 4 new tests exist and pass; `uv run pytest -q` → 0 failed.
- [ ] `uv run ruff check .` and `uv run mypy config engine apps tests` → exit 0.
- [ ] Only in-scope files modified.
- [ ] `plans/README.md` row for 003 updated.

## STOP conditions

Stop and report if:

- A template drives these endpoints via HTMX in a way that a plain POST form
  would break (e.g. relies on a GET partial) — report the template so the UI
  change can be designed deliberately.
- Making them POST-only breaks an existing passing test you cannot trivially
  convert to POST — report it.

## Maintenance notes

- If a self-service "data sharing" settings page is built later, it should use
  these POST endpoints with CSRF, and can pass an explicit `next` you validate
  the same way.
- Reviewer: confirm the rate limiter now actually protects these endpoints
  (POST is the only method) and that consent state is unchanged on a rejected
  GET.
