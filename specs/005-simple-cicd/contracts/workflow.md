# Workflow Contract: `.github/workflows/ci.yml`

**Feature**: 005-simple-cicd
**Date**: 2026-04-28

This document is the **interface contract** of the CI workflow this feature delivers. It specifies what the workflow *consumes* (events, inputs, repository state) and what it *produces* (jobs, statuses, artifacts) — independent of the YAML implementation details, so reviewers can verify the implementation against a stable target.

The implementation file is `.github/workflows/ci.yml` (single file, see Decision 2 in `research.md`).

---

## 1. Inputs (what the workflow consumes)

### 1.1 Triggering events

| Event              | Filter                          | Purpose                                                              | Spec ref |
| ------------------ | ------------------------------- | -------------------------------------------------------------------- | -------- |
| `pull_request`     | `branches: [main]`              | Validate proposed changes before merge.                              | FR-001   |
| `push`             | `branches: [main]`              | Validate post-merge state of `main`.                                 | FR-001, US2 |
| `workflow_dispatch`| (no filter)                     | Allow a maintainer to manually re-run the workflow on demand.        | (operational) |

The workflow is **not** subscribed to any other event (no `schedule`, no `release`, no `pull_request_target`). `pull_request_target` is intentionally avoided — it is the event that exposes secrets to fork PRs, which would violate FR-013.

### 1.2 Repository state assumed present

| File / directory                      | Why the workflow needs it                                |
| ------------------------------------- | -------------------------------------------------------- |
| `backend/pyproject.toml`              | Declares Python deps (incl. ruff, pytest, build deps).   |
| `backend/ruff.toml`                   | Lint rules consumed by `backend-lint`.                   |
| `backend/tests/**`                    | Test discovery root for `backend-test`.                  |
| `frontend/package.json`               | Declares Node deps and `lint` / `build` scripts.         |
| `frontend/package-lock.json`          | Required for `npm ci` (deterministic install).           |
| `frontend/eslint.config.js`           | Lint config consumed by `frontend-lint`.                 |
| `frontend/playwright.config.js`       | Test config consumed by `frontend-test`.                 |
| `frontend/tests/e2e/**`               | Test discovery root for Playwright (created by this feature if absent). |

If any of the above are missing or misconfigured, the relevant job MUST fail with a clear message — not silently pass.

### 1.3 Secrets / sensitive inputs

**None.** This feature introduces no secrets. Per FR-013, secrets MUST NOT be exposed to fork-originated runs; the simplest way to honor that is to not require any secrets at all in this workflow. If a future feature (e.g., deployment, coverage upload) needs a secret, it MUST be added in a separate workflow that runs only on `push` to protected branches.

---

## 2. Outputs (what the workflow produces)

### 2.1 Status checks posted to the commit

Per Decision 10 in `research.md`, exactly **one** stable check name is the merge gate:

| Check name | Posted by job | Required for merge? | Notes                                                          |
| ---------- | ------------- | ------------------- | -------------------------------------------------------------- |
| `ci`       | `ci` job      | Yes (set by maintainer in branch protection — admin step) | Aggregates the six worker jobs. |
| `backend-lint`, `backend-test`, `backend-build`, `frontend-lint`, `frontend-test`, `frontend-build` | each respective job | No (informational; visible in PR Checks tab) | Per-job status enables FR-008/FR-010. |

**Stability guarantee**: The `ci` check name MUST NOT change without a deliberate, announced refactor. Adding/removing/renaming worker jobs is permitted as long as the aggregate `ci` job remains.

### 2.2 Artifacts

| Artifact name        | Produced by      | When                  | Retention | Purpose                                    |
| -------------------- | ---------------- | --------------------- | --------- | ------------------------------------------ |
| `playwright-report`  | `frontend-test`  | On job failure only   | 14 days   | HTML report for debugging E2E failures.    |
| `playwright-results` | `frontend-test`  | On job failure only   | 14 days   | Raw screenshots, traces, videos.           |

No artifacts are produced on success (would burn storage for no diagnostic value). No backend artifacts are uploaded — the wheel built in `backend-build` is throwaway, used only to prove the package builds.

### 2.3 Side effects

| Side effect                                               | Visibility                                  |
| --------------------------------------------------------- | ------------------------------------------- |
| Concurrency group cancels in-progress PR runs on new push | Visible in Actions UI as "Cancelled". FR-009. |
| Per-job timeout aborts a stuck job                        | Visible as "Failure - timeout exceeded". FR-014. |
| Cache writes on success                                   | Speeds up subsequent runs. FR-011.          |

The workflow MUST NOT:
- Push commits, tags, or releases.
- Comment on issues or PRs.
- Modify branch protection or repository settings.
- Send notifications outside of GitHub's default behavior.
- Publish to any external registry.

---

## 3. Job contract (each worker job)

Every worker job MUST satisfy:

1. **Idempotent**: running it twice in a row on the same commit produces the same outcome. No mutable shared state.
2. **Self-contained**: depends only on the repository checkout and on toolchains it installs itself (no `needs:` from other worker jobs).
3. **Per-step labeled**: every meaningful action is its own `name:`-d step, so a failed step is identifiable from the job UI without reading raw logs (FR-008).
4. **Timeouts**: `timeout-minutes` set on the job (default 15, `frontend-test` 20).
5. **Cache-aware**: where install time is non-trivial, the job MUST consume one of the caches defined in research Decision 5.
6. **Failure-noisy**: any non-zero exit from the underlying tool MUST fail the job. No `continue-on-error: true` on lint/test/build steps.

---

## 4. Aggregator contract (`ci` job)

1. `needs:` MUST list **every** worker job. Adding a new worker job in the future MUST also add it to `needs:`.
2. The job's `if:` condition MUST NOT be set to `always()` — the default behavior (skip if any `needs:` failed) is what makes it work as a gate.
3. The single step MUST be a deterministic no-op (e.g., `run: echo OK`). Adding logic here would create an aggregator that itself can fail unpredictably, breaking the contract.

---

## 5. Pre-merge guarantees (the gate)

A pull request opened against `main`, with `ci` configured as a required status check, has the following guarantees before merge:

| Guarantee                                                                          | Mechanism                                                | Spec ref     |
| ---------------------------------------------------------------------------------- | -------------------------------------------------------- | ------------ |
| Backend code passes Ruff lint at error severity.                                   | `backend-lint` → `ci`                                    | FR-002       |
| Frontend code passes ESLint at error severity.                                     | `frontend-lint` → `ci`                                   | FR-003       |
| Backend Pytest suite passes.                                                       | `backend-test` → `ci`                                    | FR-004       |
| Frontend Playwright E2E suite passes.                                              | `frontend-test` → `ci`                                   | FR-005       |
| Both backend and frontend produce a successful production-mode build.              | `backend-build`, `frontend-build` → `ci`                 | FR-006       |
| The status reflects the **latest** commit, not a stale earlier one.                | `concurrency: cancel-in-progress: true` on `pull_request`| FR-009       |
| No secrets were exposed to a fork PR.                                              | No secrets used; `pull_request_target` not subscribed    | FR-013       |
| A hung step did not silently consume runner minutes.                               | `timeout-minutes` on every job                           | FR-014       |
| The pipeline definition itself was reviewed in the same PR flow.                   | `.github/workflows/ci.yml` is a regular tracked file     | FR-015       |

---

## 6. Non-goals (what this contract explicitly does NOT cover)

- **Deployment**. No job pushes to a registry, no environment is updated, no rollback is performed. Per FR-017 resolution.
- **Frontend unit/component tests**. Only the existing Playwright E2E suite is exercised. Per FR-018 resolution.
- **Test matrix across Python/Node versions**. One supported version per stack, per Assumptions.
- **Self-hosted runners**. `ubuntu-latest` only.
- **Branch protection configuration**. Maintainer task; this feature only guarantees a stable `ci` check name to require.
- **Coverage reporting / code-quality dashboards / SAST**. Not in scope; cleanly addable in a future feature.
- **Notifications** beyond GitHub's defaults (no Slack, no email, no third-party integration).

---

## 7. Verifying conformance

A reviewer (or a future audit) can check this contract by:

1. Opening any recent run in the Actions tab and confirming exactly six worker jobs + one `ci` job exist.
2. Opening a PR with a deliberate lint violation; confirming the corresponding `*-lint` job fails and `ci` is skipped.
3. Pushing a second commit to that PR; confirming the older run is cancelled (FR-009) and a fresh run starts on the new commit.
4. Inspecting `.github/workflows/ci.yml` and confirming: no `pull_request_target` trigger, no `secrets:` references, every job has `timeout-minutes`, the `ci` job's only step is a no-op, and `concurrency` is configured.
5. Opening a `gh run view <run_id>` and confirming the failed job's log link is directly accessible (FR-008).
