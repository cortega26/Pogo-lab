# Plan 001: Green CI baseline — fix the broken language switcher and stale EN smoke tests

> **Executor instructions**: Follow this plan step by step. Run every
> verification command and confirm the expected result before moving on. If
> anything in "STOP conditions" occurs, stop and report — do not improvise.
> When done, update the status row for this plan in `plans/README.md`.
> All code comments/docstrings/commit messages must be in **español neutral**
> (no voseo): "ajusta", "corrige", "revisa".
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- templates/base.html apps/core/templatetags/seo_tags.py tests/test_m1_smoke.py tests/test_e2e.py`
> If any changed since this plan was written, compare the "Current state"
> excerpts against the live code before proceeding; on a mismatch, treat it as
> a STOP condition.

## Status

- **Priority**: P1 (do this FIRST — it unblocks every other plan's green-gate)
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: bug / dx
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

`main` is **red**: `uv run pytest` fails 3 tests and GitHub Actions CI on `main`
fails on every push. Two are stale tests; **one is a real user-facing bug** — the
language switcher no longer switches language. A visitor on `/es/calculadora/`
who picks "English" does **not** land on `/en/calculator/`.

**Verified root cause.** Commit `c72f387` made the `<select>` submit a `next`
value with the `/es/` prefix stripped, then POST to Django's `set_language`.
`set_language` translates `next` via `translate_url` **at POST time**, under
whatever language is active *then* — and on a first visit (no `django_language`
cookie) that is driven by the browser's `Accept-Language`. Playwright's default
is `en-US`, so at the POST the active language is **en**, `translate_url` cannot
resolve the `/es/…` source path, and the user is bounced back to Spanish. This
was proven empirically against this repo:

```
POST /i18n/setlang/ next=/es/calculadora/  Accept-Language=en-US  ->  /es/calculadora/   (FAILS)
POST /i18n/setlang/ next=/es/calculadora/  Accept-Language=es-ES  ->  /en/calculator/    (works)
```

The robust fix is to translate the URL **at render time**, where the active
language is the page's own language (`es` on `/es/…`), so `translate_url`
resolves correctly, and navigate straight to the translated URL — no dependence
on `set_language`'s POST-time language:

```
render-time translate_url('/es/calculadora/', 'en')  with active=es  ->  /en/calculator/   ✓
```

Bonus: the existing `change_lang` template tag (used for hreflang) is **also
buggy** — it renders `/en/es/calculadora/` (doubled prefix) — so fixing it here
also fixes the hreflang SEO links on every page. No test asserts hreflang
output, so this is safe.

## Current state

- `apps/core/templatetags/seo_tags.py:9-27` — the buggy `change_lang` tag. It
  reverses the *current* view name and blindly prepends `/{lang}`, which
  double-prefixes an already-prefixed reversed URL:

  ```python
  @register.simple_tag(takes_context=True)
  def change_lang(context, lang: str) -> str:
      request = context.get("request")
      if not request:
          return f"/{lang}/"
      try:
          url_parts = resolve(request.path_info)
          url = reverse(url_parts.view_name, args=url_parts.args, kwargs=url_parts.kwargs)
          return f"/{lang}{url}"   # BUG: url already carries a /es/ prefix -> /en/es/...
      except Exception:
          return request.path
  ```

- `templates/base.html:47-59` — the language selector form (the switcher bug):

  ```django
  <form action="{% url 'set_language' %}" method="post">
    {% csrf_token %}
    {% with path=request.get_full_path %}
    <input name="next" type="hidden" value="{% if path|length > 4 %}{{ path|slice:'4:' }}{% else %}/{% endif %}">
    {% endwith %}
    <select name="language" id="language-selector" ... onchange="this.form.submit()">
      {% for code, name in LANGUAGES %}
        <option value="{{ code }}" {% if code == LANGUAGE_CODE %}selected{% endif %}>{{ name }}</option>
      {% endfor %}
    </select>
  </form>
  ```

- `templates/base.html:14-21` — hreflang block already calls `{% change_lang lang.code %}`
  (so fixing the tag fixes hreflang for free).
- `tests/test_e2e.py:385-402` — `test_language_switch`: `page.goto(.../es/calculadora/)`,
  `page.select_option("#language-selector", "en")`, asserts `"/en/" in page.url`.
  **`select_option(..., "en")` matches by the option's `value`**, so the
  `<option value="{{ code }}">` values MUST stay `es`/`en` — put the target URL
  in a `data-url` attribute, not in `value`.
- `tests/test_m1_smoke.py:132-138` — two stale tests requesting the old
  Spanish-spelled `/en/cuenta/...` paths (now 404; real EN URL is
  `/en/account/exportar/` — prefix translated, suffix not). `reverse("account_export")`
  under the `en` locale → `/en/account/exportar/`.
- The repo pins tests with `--randomly-seed=0` in `pyproject.toml`. **Do NOT
  pass `-p no:randomly`** — it makes pytest error "unrecognized arguments".

## Commands you will need

| Purpose        | Command                                                     | Expected            |
|----------------|-------------------------------------------------------------|---------------------|
| Install        | `uv sync --group dev`                                       | exit 0              |
| Full tests     | `uv run pytest -q`                                          | 0 failed            |
| Smoke tests    | `uv run pytest tests/test_m1_smoke.py -q`                   | all pass            |
| E2E (browser)  | `uv run playwright install chromium` then `uv run pytest tests/test_e2e.py::test_language_switch -q` | 1 passed |
| Lint / format  | `uv run ruff check .` ; `uv run ruff format --check .`      | exit 0              |

## Scope

**In scope** (only these files):
- `apps/core/templatetags/seo_tags.py` (fix `change_lang`)
- `templates/base.html` (rewrite the selector; drop the `set_language` form)
- `tests/test_m1_smoke.py` (the two `*_en_redirects_when_anon` tests)

**Out of scope** (do NOT touch):
- Django's `set_language` view / `i18n_patterns` config.
- `apps/accounts/urls.py` URL-suffix translation (separate decision — see notes).
- `locale/**` `.po`/`.mo` files.
- `apps/core/templatetags/__init__.py` — it contains a *duplicate, unused*
  `change_lang`; leave it (note it in your report as dead code).

## Git workflow

- Branch: `fix/001-i18n-language-switcher`.
- One commit is fine; message in español neutral, e.g.
  `fix(i18n): traduce la URL al cambiar de idioma en tiempo de render`.
- Do NOT push or open a PR unless the operator instructed it.

## Steps

### Step 1: Fix the `change_lang` tag to use `translate_url`

In `apps/core/templatetags/seo_tags.py`, replace the body so it returns the
current full path translated into `lang` (this resolves under the page's active
language at render time, which is correct):

```python
from django.urls import translate_url

@register.simple_tag(takes_context=True)
def change_lang(context, lang: str) -> str:
    """Devuelve la URL actual traducida a otro idioma (p. ej. /en/calculator/)."""
    request = context.get("request")
    if not request:
        return f"/{lang}/"
    return translate_url(request.get_full_path(), lang)
```

(`translate_url` returns the input unchanged if it can't resolve — safe default.)

**Verify**: render check (browser-free) —

```bash
DJANGO_SETTINGS_MODULE=config.settings.test uv run python -c "
import django; django.setup()
from django.conf import settings; settings.ALLOWED_HOSTS=['*']
from django.test import Client
html = Client().get('/es/calculadora/', HTTP_ACCEPT_LANGUAGE='en-US').content.decode()
assert '/en/calculator/' in html, 'change_lang did not produce /en/calculator/'
assert '/en/es/calculadora/' not in html, 'double-prefix bug still present'
print('OK: change_lang renders /en/calculator/')
"
```

### Step 2: Rewrite the selector to navigate directly (keep `value` = code)

In `templates/base.html`, replace the whole `<form>…</form>` switcher block with
a `<select>` that carries the translated URL per option in `data-url` and
navigates on change. **Keep `id="language-selector"` and `value="{{ code }}"`**
(the E2E selects by value):

```django
<select id="language-selector" class="rounded border px-2 py-1 text-sm"
        onchange="if(this.selectedOptions[0].dataset.url){window.location.href=this.selectedOptions[0].dataset.url}">
  {% for code, name in LANGUAGES %}
    <option value="{{ code }}" data-url="{% change_lang code %}" {% if code == LANGUAGE_CODE %}selected{% endif %}>
      {{ name }}
    </option>
  {% endfor %}
</select>
```

Remove the `<form>`, `{% csrf_token %}`, the `{% with %}` block, and the hidden
`next` input. (This drops the `set_language` POST; language is set by the URL
prefix on navigation. The `onchange` inline handler is the same CSP class as the
one it replaces.)

**Verify**: `uv run playwright install chromium` (once), then
`uv run pytest tests/test_e2e.py::test_language_switch -q` → `1 passed`.
If chromium cannot be installed in your environment, rely on Step 1's render
check plus Step 4, and note the skip in your report.

### Step 3: Point the two stale smoke tests at the real English URLs

In `tests/test_m1_smoke.py`, update the two `*_en_redirects_when_anon` tests:

```python
def test_export_page_en_redirects_when_anon(self):
    from django.urls import reverse
    from django.utils import translation
    with translation.override("en"):
        url = reverse("account_export")
    response = Client().get(url)
    assert response.status_code == 302

def test_delete_page_en_redirects_when_anon(self):
    from django.urls import reverse
    from django.utils import translation
    with translation.override("en"):
        url = reverse("account_delete")
    response = Client().get(url)
    assert response.status_code == 302
```

**Verify**: `uv run pytest tests/test_m1_smoke.py -q` → all pass.

### Step 4: Full suite green

**Verify**: `uv run pytest -q` → `0 failed` (was `453 passed, 3 failed`; expect
`456 passed`). Then `uv run ruff check .` and `uv run ruff format --check .` → exit 0.

## Test plan

- No new test files. You fix production code (tag + template) so the existing
  `test_language_switch` E2E passes, and correct two stale smoke assertions.
- Regression covered by `test_language_switch` (ES→EN reaches `/en/`), the two
  smoke tests (EN account pages redirect anon users), and Step 1's render check.
- Verification: `uv run pytest -q` → 0 failed.

## Done criteria

ALL must hold:

- [ ] `change_lang` uses `translate_url`; Step 1's render check passes
      (`/en/calculator/` present, `/en/es/calculadora/` absent).
- [ ] The selector navigates via `data-url`; `<option value="{{ code }}">` is
      preserved (E2E selects by value).
- [ ] `uv run pytest tests/test_e2e.py::test_language_switch -q` passes (or
      documented as un-runnable locally due to browser install).
- [ ] `uv run pytest -q` → 0 failed.
- [ ] `ruff check` + `ruff format --check` → exit 0.
- [ ] Only `seo_tags.py`, `base.html`, `test_m1_smoke.py` modified (`git status`).
- [ ] `plans/README.md` status row for 001 updated.

## STOP conditions

Stop and report (do not improvise) if:

- After Steps 1-2, `test_language_switch` still fails — capture the final
  `page.url` and the rendered `data-url` for the `en` option, and report. Do NOT
  start editing `apps/accounts/urls.py`, the `.po` files, or `set_language`.
- The drift check shows `base.html`/`seo_tags.py` already changed and no longer
  matches the excerpts.
- Fixing these reveals *other* newly-failing tests (baseline drifted further) —
  report the new failures.

## Maintenance notes

- **Bonus fixed here:** hreflang links (`base.html:17`) now emit correct
  translated URLs (`/en/calculator/`) instead of the broken `/en/es/calculadora/`.
- **Dead code (report, don't fix here):** `apps/core/templatetags/__init__.py`
  has a duplicate, unused `change_lang`. Consider deleting it in a follow-up.
- **Cookie stickiness (follow-up):** dropping `set_language` means the language
  is set purely by the URL prefix, not persisted in a `django_language` cookie.
  Since every app URL is under `i18n_patterns`, this is fine; if sticky
  persistence across non-prefixed entry points is wanted later, POST the
  *pre-translated* `next` to `set_language` instead of navigating directly.
- **Half-translated URLs (separate ticket):** `/en/account/exportar/` (English
  prefix, Spanish suffix) because `apps/accounts/urls.py` uses plain
  `"exportar/"`. For clean bilingual URLs, wrap the suffixes in `gettext_lazy`,
  add `.po` translations, and `compilemessages`. Changes public URLs — decide
  deliberately.
- Reviewer: confirm the switch works **both** directions and on a page with
  query params.
