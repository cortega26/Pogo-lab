# Plan 010: Enforce published-ruleset immutability on `RuleParameter`

> **Executor instructions**: Follow step by step; run every verification.
> Honor "STOP conditions". Update `plans/README.md`. Comments/commits in
> **español neutral**.
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- apps/mechanics/`
> If changed, re-read `apps/mechanics/models.py` and compare against "Current state".

## Status

- **Priority**: P3
- **Effort**: M
- **Risk**: MED (tightens an admin-editable invariant)
- **Depends on**: 001 (green baseline)
- **Category**: integrity / security
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

The project treats **reproducibility** as a core invariant: a published ruleset
defines the floor `f` used to interpret historical observations and the
community dataset, and `MechanicRuleSet.clean()` already blocks editing a ruleset
once it is published. But the **floor values themselves live in `RuleParameter`
rows**, and `RuleParameter` has **no immutability guard**. A staff user can edit
(or add/delete) a published ruleset's parameters via the admin, silently
changing the floor used to (re)interpret already-recorded data — breaking
reproducibility **without** tripping the "no editing a published ruleset" guard.
Extend the invariant to the child parameters: published ruleset ⇒ parameters
frozen; new floors require a new ruleset version.

## Current state

`apps/mechanics/models.py`:

- `MechanicRuleSet.clean()` (lines ~79-85) blocks editing a published ruleset:

  ```python
  def clean(self):
      if self.is_published and self.pk:
          original = MechanicRuleSet.objects.get(pk=self.pk)
          if original.is_published:
              raise ValidationError(_("No se puede editar un ruleset ya publicado."))
      ...
  ```

- `MechanicRuleSet.publish()` (lines ~91-99) validates parameters then sets
  `is_published=True`. **It does not save individual `RuleParameter` rows** — so
  freezing parameter saves when the ruleset is published will NOT interfere with
  `publish()` (parameters are created while the ruleset is still unpublished).
- `RuleParameter` (lines ~102-129) — `ruleset` FK, `key`, `value` (JSON),
  `data_type`, `unit`. **No `clean`/`save`/`delete` guard.**
- `RuleParameter` is edited via the admin (`apps/mechanics/admin.py` exposes it,
  per the security audit).

## Commands you will need

| Purpose        | Command                                       | Expected  |
|----------------|-----------------------------------------------|-----------|
| Mechanics tests| `uv run pytest tests/test_mechanics_integration.py -q` | all pass |
| Full tests     | `uv run pytest -q`                            | 0 failed  |
| Migration check| `uv run python manage.py makemigrations --check --dry-run` | exit 0 (no schema change expected) |
| Lint / types   | `uv run ruff check .` ; `uv run mypy config engine apps tests` | exit 0 |

## Scope

**In scope**:
- `apps/mechanics/models.py` (add guards to `RuleParameter`)
- `tests/test_mechanics_integration.py` (or the mechanics test file that seeds
  rulesets) — add immutability tests

**Out of scope**:
- `MechanicRuleSet` behavior (already guarded).
- `apps/mechanics/admin.py` — model-level guards are enough; do not add
  admin-only logic that could be bypassed by the ORM.
- Any change that would block creating parameters on an **unpublished** ruleset
  (the normal authoring/seed flow must keep working).

## Git workflow

- Branch: `fix/010-ruleparameter-immutability`.
- Commit e.g. `fix(mechanics): congela RuleParameter cuando el ruleset está publicado`.

## Steps

### Step 1: Block edits/creates of parameters on a published ruleset

Add `clean()` and `save()` to `RuleParameter`:

```python
def clean(self):
    if self.ruleset_id and self.ruleset.is_published:
        raise ValidationError(
            _("No se pueden modificar los parámetros de un ruleset ya publicado. "
              "Crea una nueva versión del ruleset.")
        )

def save(self, *args, **kwargs):
    self.clean()
    super().save(*args, **kwargs)
```

This blocks both creating a new parameter under a published ruleset and editing
an existing one. It does **not** affect authoring parameters on an unpublished
ruleset, nor `publish()` (which doesn't save parameters).

### Step 2: Block deletes of parameters on a published ruleset

Override `delete()`:

```python
def delete(self, *args, **kwargs):
    if self.ruleset_id and self.ruleset.is_published:
        raise ValidationError(
            _("No se pueden eliminar los parámetros de un ruleset publicado.")
        )
    return super().delete(*args, **kwargs)
```

(Note the caveat in Maintenance notes about queryset `.delete()`.)

### Step 3: Confirm no migration and no seed breakage

- `uv run python manage.py makemigrations --check --dry-run` → exit 0 (these are
  behavior-only methods; no schema change).
- Confirm the seed still works: `uv run python manage.py seed` under the test DB,
  or rely on the existing seed test. The seed creates parameters **before**
  publishing, so it must still pass. If the seed publishes then adds params,
  that's a real ordering bug to report (STOP).

### Step 4: Tests

In the mechanics test file add:

- `test_cannot_add_parameter_to_published_ruleset`: create a published ruleset,
  then `RuleParameter(ruleset=published, ...).save()` (or `.full_clean()`)
  raises `ValidationError`.
- `test_cannot_edit_parameter_of_published_ruleset`: create params on an
  unpublished ruleset, publish it, then editing a param's `value` and saving
  raises `ValidationError`.
- `test_cannot_delete_parameter_of_published_ruleset`: `.delete()` on such a
  param raises `ValidationError`.
- `test_can_still_author_parameters_before_publish`: adding/editing params on an
  **unpublished** ruleset works (regression — the seed/authoring flow).

**Verify**: `uv run pytest tests/test_mechanics_integration.py -q` → all pass.

### Step 5: Full suite

**Verify**: `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.

## Test plan

- Immutability tests (add/edit/delete blocked when published) + a regression
  test that pre-publish authoring still works.
- Pattern: the existing mechanics ruleset/publish tests.

## Done criteria

ALL must hold:

- [ ] Creating, editing, or deleting a `RuleParameter` whose ruleset
      `is_published` raises `ValidationError`.
- [ ] Authoring parameters on an unpublished ruleset still works; `seed` and its
      tests still pass.
- [ ] `makemigrations --check --dry-run` → exit 0 (no schema change).
- [ ] New tests pass; `uv run pytest -q` → 0 failed; `ruff` + `mypy` clean.
- [ ] Only in-scope files modified; `plans/README.md` row for 010 updated.

## STOP conditions

Stop and report (do not improvise) if:

- The seed or an existing test creates/edits parameters **after** publishing a
  ruleset — that's a legitimate flow this guard would break; report it so the
  invariant (or the seed) can be reconciled, rather than weakening the guard.
- `publish()` turns out to save parameters after setting `is_published` — report
  (Step 1's guard would then break publish).

## Maintenance notes

- **Caveat**: overriding `Model.delete()` does not intercept
  `QuerySet.delete()` (bulk deletes) or cascade deletes when the parent ruleset
  is removed. This plan blocks the common admin path (per-object edit/delete).
  If bulk mutation of published parameters must also be prevented, add a
  `pre_save`/`pre_delete` signal — call that out in review as a follow-up.
- The intended workflow after this: to change a published floor, create a **new
  `MechanicRuleSet` version** with new parameters and publish that. Confirm the
  admin/seed docs reflect this.
- Reviewer: verify the guard reads the *current* `ruleset.is_published` and
  doesn't accidentally block the publish transaction.
