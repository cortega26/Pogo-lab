# Plan 002: Add `.dockerignore` so secrets and cruft never enter the image

> **Executor instructions**: Follow step by step; run every verification and
> confirm the expected result. Honor "STOP conditions". Update this plan's row
> in `plans/README.md` when done. Comments/commit messages in **español
> neutral**. **Never print the contents of any `.env*` file or any file under
> `infra/keys/` — reference them by path only.**
>
> **Drift check (run first)**: `git diff --stat fae5586..HEAD -- Dockerfile` and
> `ls -la .dockerignore`. If `.dockerignore` now exists, STOP and report (it
> may already have been added). If `Dockerfile` changed, re-read it before
> proceeding.

## Status

- **Priority**: P1
- **Effort**: S
- **Risk**: LOW
- **Depends on**: none
- **Category**: security
- **Planned at**: commit `fae5586`, 2026-07-17

## Why this matters

The `Dockerfile` builds the image with `COPY . .` and there is **no
`.dockerignore`**. The Docker build context therefore includes files that must
never be baked into an image layer:

- `.env` and `.env-oci` — application/OCI secrets (env values).
- `infra/keys/` — **three private keys** (an OCI API private key, a VM SSH
  key, and a deploy SSH key). These are gitignored (good) but sit in the
  working tree, so `COPY . .` copies them into the image.
- `.git/` (full history), `.venv/` (host-built, wrong-arch binaries),
  `htmlcov/`, `.mypy_cache/`, `.ruff_cache/`, `.pytest_cache/`,
  `.hypothesis/`, `node_modules/` — bloat and, in `.git`'s case, more history
  than the runtime needs.

Anyone who can pull the built image or inspect its layers can extract those
secrets — a defense-in-depth failure with a one-file fix. (Confirmed: all five
sensitive paths are present in the current build context.)

## Current state

- `Dockerfile:12` (builder stage): `COPY . .` — copies the **entire** context.
- No `.dockerignore` at the repo root (confirmed absent).
- `.gitignore` already enumerates the non-essential paths (secrets, caches,
  `.venv`, `node_modules`, `.codegraph`) — use it as the reference list, and
  additionally exclude `.git`.
- **Do not exclude source the build needs**: `pyproject.toml`, `uv.lock`,
  `manage.py`, `config/`, `apps/`, `engine/`, `static/`, `templates/`,
  `locale/`. The builder runs `uv sync` and
  `manage.py collectstatic` (`Dockerfile:13-14`), which need these.

## Commands you will need

| Purpose            | Command                                            | Expected                    |
|--------------------|----------------------------------------------------|-----------------------------|
| Confirm no file yet| `ls -la .dockerignore`                             | "No such file" (before)     |
| Pattern check      | `git check-ignore -v --no-index -- .env infra/keys/oci_api_key.pem` | n/a (this is git, see Step 2 for the real check) |
| Build (if docker)  | `docker build -t pogolab-ignore-test .`            | builds OK                   |
| Secret-absence     | `docker run --rm pogolab-ignore-test sh -c 'ls /app/.env /app/infra 2>&1'` | "No such file or directory" |

If no Docker daemon is available in your environment, use the file-content
verification in Step 2 as the hard gate and note that the live build check was
skipped.

## Scope

**In scope** (create this one file):
- `.dockerignore` (new, repo root)

**Out of scope**:
- `Dockerfile` — do **not** change `COPY . .`; the `.dockerignore` is what
  scopes it. (A later hardening plan may switch to explicit `COPY` of subdirs;
  not here.)
- Any `.env*` or `infra/keys/*` file — never open, move, print, or delete them.
- Secret **rotation** — none is required: these keys were never committed to
  git history (verified), so they are not burned; this plan only prevents
  future image leakage.

## Git workflow

- Branch: `fix/002-dockerignore`.
- One commit; message e.g. `chore(docker): añade .dockerignore para excluir secretos y caché`.
- Do NOT push unless instructed.

## Steps

### Step 1: Create `.dockerignore`

Create `.dockerignore` at the repo root with exactly this content:

```gitignore
# Control de versiones
.git
.gitignore

# Secretos / entorno (NUNCA en la imagen)
.env
.env.*
!.env.example
.env-oci
infra/keys/

# Entornos virtuales / dependencias locales
.venv/
node_modules/

# Caché de tests / type checking / lint / coverage
.pytest_cache/
.mypy_cache/
.ruff_cache/
.hypothesis/
htmlcov/
.coverage
.coverage.*
__pycache__/
*.py[cod]

# Artefactos de Playwright / reportes
/test-results/
/playwright-report/
/blob-report/

# Índice local de CodeGraph
.codegraph/

# Artefactos de trabajo / skills locales
plans/
skills-lock.json
.agents/
.claude/
```

Note: `.env.example` is re-included via `!.env.example` (harmless; it is a
placeholder template, not a secret). `static/`, `templates/`, `locale/`,
`config/`, `apps/`, `engine/`, `manage.py`, `pyproject.toml`, `uv.lock` are
deliberately **not** listed — the build needs them.

**Verify**: `cat .dockerignore` shows the content above; `ls -la .dockerignore`
exits 0.

### Step 2: Verify the sensitive paths are excluded

Hard gate (no Docker required): every sensitive path must match a
`.dockerignore` line. Run:

```bash
for p in .env .env-oci infra/keys/oci_api_key.pem infra/keys/vm_key infra/keys/deploy_key .git .venv; do
  grep -qE "^($(printf '%s' "$p" | cut -d/ -f1))" .dockerignore && echo "covered: $p" || echo "MISSING: $p"
done
```

**Expected**: every line prints `covered:` — no `MISSING:`.

### Step 3 (optional, if Docker is available): prove the image is clean

```bash
docker build -t pogolab-ignore-test .
docker run --rm pogolab-ignore-test sh -c 'ls /app/.env /app/.env-oci /app/infra 2>&1'
```

**Expected**: the `ls` reports "No such file or directory" for each — the
secrets are not in the image. The build itself should still succeed (source is
intact).

## Test plan

- No unit tests (build-tooling change). The verification is the Step 2 pattern
  check (mandatory) and the Step 3 image inspection (when Docker is present).
- Confirm the app still builds: if Docker is available, Step 3's `docker build`
  must succeed, proving no needed source was excluded.

## Done criteria

ALL must hold:

- [ ] `.dockerignore` exists at repo root with the content from Step 1.
- [ ] Step 2 prints `covered:` for all seven paths, no `MISSING:`.
- [ ] If Docker available: `docker build` succeeds and Step 3 shows the secret
      paths absent from `/app`. If not available: documented as skipped.
- [ ] No other file modified (`git status` shows only the new `.dockerignore`).
- [ ] `plans/README.md` status row for 002 updated.

## STOP conditions

Stop and report if:

- `docker build` fails after adding `.dockerignore` (means a needed path was
  excluded — report which `COPY`/command failed; do not start editing the
  `Dockerfile`).
- `.dockerignore` already exists with different content (drift) — report,
  don't overwrite blindly.
- You find a secret value while working — do not paste it anywhere; note only
  the file path and that it exists.

## Maintenance notes

- Keep `.dockerignore` and `.gitignore` in sync when new secret/cache paths are
  added.
- Follow-up worth a ticket (not here): the builder copies the whole tree then
  `uv sync`s; consider switching `COPY . .` to explicit `COPY` of
  `config/ apps/ engine/ static/ templates/ locale/ manage.py` for a tighter,
  more auditable image. Also consider a runtime `HEALTHCHECK` for the `web`
  service.
- A reviewer should confirm the running image still serves static files
  (collectstatic ran) — i.e. excluding paths didn't drop `static/`.
