# Phase 0 Research: Simple CI/CD Pipeline

**Feature**: 005-simple-cicd
**Date**: 2026-04-28
**Purpose**: Resolve open technical questions and record decisions before Phase 1 design.

The Technical Context in `plan.md` introduced no remaining `NEEDS CLARIFICATION` markers (the spec's two markers were resolved during `/speckit-specify`). This document captures the implementation choices that make those resolved requirements concrete, with rationale and alternatives considered for each.

---

## Decision 1: CI Platform

**Decision**: Use **GitHub Actions** as the CI runtime.

**Rationale**:
- The repo is already hosted on GitHub (`git@github.com:hiepgithub2001/trackedux.git`). Using GitHub-native CI removes the need to add or trust a second SaaS account.
- GitHub Actions publishes commit status checks back to pull requests natively, satisfying FR-007 (aggregate pass/fail status on PR), FR-016 (eligible to be a required check via branch protection), and FR-008 (per-step logs are individually addressable in the Actions UI).
- The `pull_request` event runs fork PRs without secret access by default, satisfying FR-013 (fork safety) without custom plumbing.
- `concurrency` groups satisfy FR-009 (supersede stale runs on new commits) in a single line of YAML.
- "Re-run failed jobs" is a built-in UI affordance, satisfying FR-010 with no custom work.
- Free for public repos and includes a generous monthly minutes allowance for private repos at the project's current scale.

**Alternatives considered**:
- **CircleCI / GitLab CI / Buildkite / Jenkins** — all are competent, but they add a second integration surface and either a paid plan or self-hosted infrastructure for an "infrequent commits, single-repo, simple gate" use case. Rejected as over-scoped for the "simple" mandate.
- **Pre-commit hooks (instead of CI)** — runs locally only, cannot enforce a merge gate, cannot be a status check on a fork PR. Rejected: violates FR-001 and FR-016. (Pre-commit hooks may complement CI later; not part of this feature.)

---

## Decision 2: Workflow File Layout

**Decision**: A **single workflow file** at `.github/workflows/ci.yml` with multiple parallel jobs (one per logical step). No reusable workflow split, no matrix.

**Rationale**:
- The spec is explicit: "simple" CI/CD. One file is the smallest, most readable surface.
- Job-level parallelism inside one workflow already satisfies FR-012 (run independent steps in parallel).
- Splitting into `lint.yml`, `test.yml`, `build.yml` would yield three separate runs each with their own setup overhead, three required-status-checks to configure for FR-016, and no real benefit at this scale.
- A future split (e.g., a separate `deploy.yml` once deployment is added) is a cheap refactor when actual deployment work begins.

**Alternatives considered**:
- **One workflow per concern** (lint / test / build) — cleaner separation but requires per-workflow toolchain setup and complicates branch-protection configuration. Rejected for current scope.
- **Reusable workflow (`workflow_call`)** — useful when multiple repos or multiple workflows share steps. Single repo + single workflow → premature abstraction. Rejected.
- **Matrix build (Python × Node version matrix)** — Assumptions in the spec explicitly say one supported runtime version per stack. Rejected.

---

## Decision 3: Job Topology

**Decision**: Six top-level jobs, all running in parallel from a shared `setup` foundation:

| Job ID            | Purpose                          | Toolchain                                           | Approx. time |
| ----------------- | -------------------------------- | --------------------------------------------------- | ------------ |
| `backend-lint`    | Lint backend Python code         | Python 3.11 + Ruff                                  | < 1 min      |
| `backend-test`    | Run backend automated test suite | Python 3.11 + Pytest + Docker (testcontainers)      | 2–5 min      |
| `backend-build`   | Verify backend builds            | Python 3.11 + `python -m build`                     | < 1 min      |
| `frontend-lint`   | Lint frontend JS                 | Node 20 + ESLint                                    | < 1 min      |
| `frontend-test`   | Run Playwright E2E suite         | Node 20 + Playwright (Chromium) + frontend dev server| 3–6 min      |
| `frontend-build`  | Verify production frontend bundle| Node 20 + `npm run build` (Vite)                    | < 1 min      |

A final no-op `ci` job depends on all six and acts as the **single aggregate status check** that branch protection can require (FR-007, FR-016).

**Rationale**:
- Each logical concern is its own job → per-step logs are clean and addressable (FR-008), and a single failed job can be retried without re-running the others (FR-010).
- All six can run in parallel (FR-012); they share no execution dependencies, only setup-cache dependencies which Actions cache resolves transparently.
- The aggregate `ci` job gives FR-007 (one status to read, one check to require) without inventing custom aggregation logic.
- Six jobs × ~5 min worst case ≈ 5 min wall-clock when fully parallel, well inside the 10 min warm-cache target (SC-002).

**Alternatives considered**:
- **One big job** that runs everything serially — simpler YAML, but breaks FR-008 (mixed logs), FR-010 (no per-step retry), and FR-012 (no parallelism). Rejected.
- **Combined lint+test job per stack** (i.e., "backend" and "frontend" as super-jobs) — saves a small amount of setup overhead but loses individual retry. Marginal benefit; rejected.
- **Build only on main** (not on PR) — slightly faster PRs, but it allows a tested-but-unbuildable change to merge. Spec FR-006 says builds must run on every pipeline run. Rejected.

---

## Decision 4: Backend Test Service Strategy (PostgreSQL)

**Decision**: Use **`testcontainers[postgres]` (already a dev dependency)** to spin Docker-based ephemeral Postgres on the Actions runner. **Do not** declare a `services: postgres` block in the workflow.

**Rationale**:
- `backend/pyproject.toml` already pins `testcontainers[postgres]>=4.0.0` — the test code is written against that pattern. Using it from CI keeps "tests run in CI" identical to "tests run locally," removing a class of "passes locally / fails in CI" bugs.
- `ubuntu-latest` runners ship with Docker pre-installed, so testcontainers works out of the box with zero workflow plumbing.
- Adding a duplicate `services: postgres` block would create two configurable Postgres surfaces (one in test code, one in workflow) that can drift in version, port, or credentials.

**Alternatives considered**:
- **`services: postgres:16` in the workflow** — works but duplicates configuration and still wouldn't match how tests run locally. Rejected.
- **SQLite for tests** — backend uses Postgres-specific features (asyncpg dialect, FK constraints across tenants). Switching to SQLite for tests would silently lose coverage. Rejected.

---

## Decision 5: Caching Strategy

**Decision**: Three independent caches, keyed on the relevant lockfile content hash:

| Cache key prefix          | Path(s)                                           | Invalidated by                       |
| ------------------------- | ------------------------------------------------- | ------------------------------------ |
| `pip-${hash(pyproject)}`  | `~/.cache/pip`, `backend/venv` (or pip's wheel cache) | `backend/pyproject.toml` change   |
| `npm-${hash(lockfile)}`   | `~/.npm`, `frontend/node_modules`                 | `frontend/package-lock.json` change  |
| `playwright-${hash(lockfile)}-${PW_VERSION}` | `~/.cache/ms-playwright`             | Playwright version change in lockfile|

Caches are populated by `actions/setup-python` (with `cache: pip`) and `actions/setup-node` (with `cache: npm`) where possible — these are first-party and handle invalidation correctly. The Playwright browser cache requires a manual `actions/cache` step because `setup-node` doesn't know about it.

**Rationale**:
- Caching dependency installs is the largest per-job time saver — uncached `npm ci` on a fresh runner is dominated by network, not CPU.
- Caching the Playwright browser binaries (`~/.cache/ms-playwright`, ~300 MB) is the *single biggest* savings on the frontend test job, often shaving 60–90s.
- Keying on lockfile hashes means a dependency change automatically invalidates the cache — satisfies FR-011 ("does not compromise correctness").
- We do not cache test outputs, build outputs, or the repo working tree — those would risk staleness for negligible benefit.

**Alternatives considered**:
- **No caching** — simplest YAML, but cold installs add several minutes to every run. Rejected: SC-002 requires ≤10 min warm-cache, and "warm" is meaningless without a cache.
- **Single monolithic cache for all dependencies** — tightly couples backend and frontend invalidation; a backend dep bump invalidates frontend caching. Rejected.

---

## Decision 6: Frontend E2E Strategy

**Decision**: Run Playwright tests in CI as follows:
1. Install Node deps (`npm ci`).
2. Install Playwright browsers via `npx playwright install --with-deps chromium` (Chromium only, matching `playwright.config.js`).
3. Start the Vite dev server in the background (`npm run dev`) and wait for `http://localhost:5173` to respond. (`playwright.config.js` comment: "The dev server is already running, don't start another one.")
4. Run `npx playwright test`.
5. On failure, upload `playwright-report/` and any `test-results/` as a workflow artifact via `actions/upload-artifact` so the failure can be diagnosed without re-running.

**Rationale**:
- Matches the existing local-dev assumption baked into `playwright.config.js` rather than fighting it.
- `--with-deps` installs the Linux system libraries Chromium needs on a fresh `ubuntu-latest` runner.
- Uploading the HTML report on failure is the single best diagnostic affordance Playwright offers — directly serves SC-003 (root cause findable in <2 min for ≥90% of failures).
- Chromium-only matches the existing config; adding Firefox/WebKit is out of scope.

**Open consideration**: The frontend has **no Playwright spec files yet** (`frontend/tests/e2e/` does not exist). Without at least one spec, `npx playwright test` exits non-zero with "No tests found." A single seed smoke spec (`smoke.spec.js`) that asserts the homepage renders will be added so the green path is demonstrable. This is consistent with the spec's Assumptions section: "Bringing tests up to that standard, if they currently fall short, is part of executing this feature."

**Alternatives considered**:
- **Use `webServer:` in `playwright.config.js`** so Playwright manages the dev server — cleaner long-term, but requires editing the existing config file. Deferred as a separate cleanup; the workflow-side approach works today.
- **Build + serve the prod bundle for E2E** instead of running the dev server — closer to production behavior, but slower and changes how tests run vs. local. Rejected for "simple."

---

## Decision 7: Backend Test Seeding

**Decision**: Add a **single trivial smoke test** to `backend/tests/unit/` (e.g., `test_smoke.py` with one assertion) so the green path is demonstrable.

**Rationale**:
- The three backend test directories (`unit/`, `integration/`, `contract/`) currently contain only `__init__.py`. Pytest exits with code 5 ("no tests collected") which CI treats as failure.
- A single trivial unit test is the minimum that lets the green path be observed end-to-end on day one. It is *not* a substitute for real test coverage — it is scaffolding for the gate.
- Configuring Pytest to ignore "no tests collected" (via `--exitcode-on-no-tests-collected=0` plugin or `[tool.pytest.ini_options] empty_parameter_set_mark = ...`) would silently mask a real "all tests deleted" regression. Rejected.

**Alternatives considered**:
- **Skip backend tests entirely until real tests exist** — defeats the spec (FR-004). Rejected.
- **Author full test coverage as part of this feature** — out of scope; this feature is about the gate, not about reaching coverage.

---

## Decision 8: Backend "Build" Step

**Decision**: For the `backend-build` job, run **`python -m build --wheel`** on `backend/` to produce a wheel artifact and verify the package metadata is valid. Do **not** ship the artifact anywhere.

**Rationale**:
- `pyproject.toml` already declares `[build-system]` with setuptools — `python -m build` will exercise that toolchain and fail loudly if e.g., a missing `__init__.py`, a malformed dependency, or a deleted package directory breaks the build.
- This is the closest "production-mode build" analog for a Python service that doesn't ship a binary today, and it catches the class of bug described in spec User Story 4 (passes tests, fails to build).
- No Docker image build is required — that would belong with deployment (FR-017 explicitly out of scope).

**Alternatives considered**:
- **Build a Docker image of the backend** — would be the most production-faithful build, but pulls in Dockerfile authoring and registry choices that belong in a deployment feature. Rejected for scope.
- **Skip backend-build entirely** — the spec FR-006 requires production-mode build of both stacks. Rejected.

---

## Decision 9: Concurrency, Cancellation, Timeouts

**Decision**:
- Use a workflow-level `concurrency` group keyed on `${{ github.workflow }}-${{ github.ref }}` with `cancel-in-progress: true` for `pull_request` events and `cancel-in-progress: false` for `push` to main (so main-branch runs always complete and produce a status).
- Per-job `timeout-minutes: 15` as a default, with `frontend-test` raised to 20 to absorb cold Playwright browser installs.

**Rationale**:
- Satisfies FR-009 (supersede stale PR runs) and FR-014 (per-job timeout) directly.
- Distinguishing PR vs. push is important: cancelling a main-branch run mid-flight could leave `main` without a current status check.

**Alternatives considered**:
- **Single concurrency group across all events** — risks cancelling main-branch runs. Rejected.
- **No timeouts** — a hung job consumes runner minutes for hours. Rejected.

---

## Decision 10: Status Aggregation

**Decision**: Add a final job named `ci` whose only step is `echo OK`, with `needs: [backend-lint, backend-test, backend-build, frontend-lint, frontend-test, frontend-build]`. This single job's status is the one branch-protection requires for merging.

**Rationale**:
- `needs:` semantics in Actions: the `ci` job only runs if all upstream jobs succeed; if any upstream fails or is cancelled, `ci` is skipped, which presents to branch protection as "not passed." This delivers FR-007 with no custom aggregation code.
- Maintainers configure exactly **one** required check (`ci`) instead of six, which is easier to administer and avoids accidentally letting a job slip through unprotected.

**Alternatives considered**:
- **Require all six checks individually in branch protection** — works, but each new job in the future would need a branch-protection update. The `ci` aggregator is forward-compatible. Rejected as more brittle.

---

## Summary of Resolutions

| Question                                       | Resolution                                                                                          |
| ---------------------------------------------- | --------------------------------------------------------------------------------------------------- |
| CI platform                                    | GitHub Actions                                                                                      |
| Workflow file layout                           | Single `.github/workflows/ci.yml`, parallel jobs                                                    |
| Job topology                                   | 6 jobs (lint/test/build × backend/frontend) + 1 aggregate `ci` job                                  |
| Backend Postgres in CI                         | `testcontainers[postgres]` from test code, not workflow `services:`                                 |
| Caching                                        | `actions/setup-python` (pip cache), `actions/setup-node` (npm cache), separate `actions/cache` for Playwright browsers |
| Frontend E2E setup                             | `npm ci` → install Chromium → start dev server → run Playwright; upload `playwright-report` on failure |
| Empty test suites                              | Add minimal seed tests so the green path is demonstrable; do not silence "no tests collected"      |
| Backend "build"                                | `python -m build --wheel`                                                                           |
| Concurrency / cancel-in-progress / timeouts    | Cancel stale PR runs; never cancel main-branch runs; per-job timeout 15–20 min                      |
| Status aggregation for FR-007/FR-016           | Single dependent `ci` job acts as the required check                                                |

All resolutions are consistent with the spec's "simple" mandate and the resolved scope (no deployment, no new frontend test framework). No outstanding `NEEDS CLARIFICATION` items remain.
