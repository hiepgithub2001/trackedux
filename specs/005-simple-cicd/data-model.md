# Phase 1 Data Model: Simple CI/CD Pipeline

**Feature**: 005-simple-cicd
**Date**: 2026-04-28

This feature is infrastructure — it does not introduce persisted application data. The "data model" here describes the **runtime entities the pipeline produces and the relationships between them**, mapped onto GitHub Actions concepts. This makes the spec's three Key Entities concrete and gives implementers and reviewers a shared vocabulary.

---

## Entity: Pipeline Run

A single end-to-end execution of the workflow, triggered by a specific Git event.

**Maps to**: A GitHub Actions `workflow_run` (visible in the **Actions** tab and via `gh run list`).

**Fields**:

| Field             | Source                                | Required | Notes                                                                   |
| ----------------- | ------------------------------------- | -------- | ----------------------------------------------------------------------- |
| `run_id`          | `${{ github.run_id }}`                | yes      | Unique numeric ID assigned by GitHub.                                   |
| `event`           | `${{ github.event_name }}`            | yes      | One of `pull_request`, `push`. Other events are not subscribed.         |
| `commit_sha`      | `${{ github.sha }}`                   | yes      | The exact commit the run validates.                                     |
| `ref`             | `${{ github.ref }}`                   | yes      | E.g., `refs/heads/main` or `refs/pull/42/merge`.                        |
| `triggered_by`    | `${{ github.actor }}`                 | yes      | Author of the commit/PR; visible in Actions UI.                         |
| `started_at`      | Workflow start timestamp              | yes      | Used to measure SC-002 (≤10 min warm-cache).                            |
| `concluded_at`    | Workflow end timestamp                | yes      | Populated when all jobs reach a terminal state.                         |
| `outcome`         | Aggregated from `ci` job              | yes      | `success` \| `failure` \| `cancelled`. Surfaced as the PR status check. |

**Lifecycle**:

```
queued → in_progress → (success | failure | cancelled)
```

- `queued` while waiting for a runner.
- `in_progress` while at least one job is running.
- `cancelled` only via FR-009 (newer commit superseded an older PR run) or manual user cancel; never on `push` to `main` (per Decision 9).
- A given `(commit_sha, event)` can have multiple Runs over time (e.g., user re-triggers); the **most recent** Run is what the PR status check reflects.

**Validation rules** (enforced by the workflow):
- `event` must be `pull_request` or `push`. Other event types silently no-op (workflow not subscribed).
- For `pull_request`, the `ref` must point to a PR targeting `main` (the workflow filters with `branches: [main]`).
- For `push`, the `ref` must equal `refs/heads/main`.

---

## Entity: Pipeline Job

An individually-runnable unit inside a Pipeline Run. Has its own logs, its own outcome, and can be retried in isolation.

**Maps to**: A GitHub Actions job (visible as a row in the run's UI, and via `gh run view <run_id> --json jobs`).

**Fields**:

| Field            | Source                                  | Required | Notes                                                            |
| ---------------- | --------------------------------------- | -------- | ---------------------------------------------------------------- |
| `job_id`         | Auto-assigned by Actions                | yes      | Numeric, used in API and re-run UI.                              |
| `job_key`        | YAML job id                             | yes      | One of: `backend-lint`, `backend-test`, `backend-build`, `frontend-lint`, `frontend-test`, `frontend-build`, `ci`. |
| `runner`         | `runs-on:`                              | yes      | Always `ubuntu-latest` for this feature.                         |
| `timeout_minutes`| `timeout-minutes:`                      | yes      | 15 default; 20 for `frontend-test`. Enforces FR-014.             |
| `outcome`        | Computed                                | yes      | `success` \| `failure` \| `cancelled` \| `skipped`.              |
| `started_at`     | Job-level timestamp                     | yes      | Per-job duration is visible in the Actions UI.                   |
| `concluded_at`   | Job-level timestamp                     | yes      |                                                                  |
| `log_url`        | Derived                                 | yes      | Deep-linkable URL into the run's logs for this job — addressable per FR-008. |

**Job catalog** (the canonical set this feature defines):

| `job_key`         | What it runs                                                                       | Depends on |
| ----------------- | ---------------------------------------------------------------------------------- | ---------- |
| `backend-lint`    | `cd backend && ruff check .`                                                       | —          |
| `backend-test`    | `cd backend && pytest` (with Docker available for testcontainers)                  | —          |
| `backend-build`   | `cd backend && python -m build --wheel`                                            | —          |
| `frontend-lint`   | `cd frontend && npm ci && npm run lint`                                            | —          |
| `frontend-test`   | `cd frontend && npm ci && npx playwright install --with-deps chromium && (start dev server) && npx playwright test` | —          |
| `frontend-build`  | `cd frontend && npm ci && npm run build`                                           | —          |
| `ci`              | `echo OK`                                                                          | all 6 above|

**Lifecycle**: Same five states as a Run (`queued → in_progress → success | failure | cancelled | skipped`). A job is `skipped` (not `failure`) if any of its `needs:` failed — used by the `ci` aggregator job.

**Validation rules**:
- All six worker jobs MUST be independent (no `needs:`) so they run fully in parallel — enforces FR-012.
- The `ci` aggregator MUST list all six worker jobs in `needs:` — enforces FR-007 (one aggregate status).
- Every job MUST have `timeout-minutes` set — enforces FR-014.

---

## Entity: Status Check

The pass/fail signal the Pipeline Run publishes back onto a pull request or commit. This is the gate that merge tooling consults.

**Maps to**: The "Checks" tab on a PR / commit, populated automatically by GitHub for each completed job.

**Fields**:

| Field         | Source                                       | Required | Notes                                                                      |
| ------------- | -------------------------------------------- | -------- | -------------------------------------------------------------------------- |
| `name`        | Job name (`job_key`)                         | yes      | The aggregator's name is `ci` — this is the one a maintainer should require. |
| `state`       | Job outcome                                  | yes      | `pending` \| `success` \| `failure` \| `error`.                            |
| `target_url`  | Link to the job's logs                       | yes      | Auto-populated; satisfies FR-008's "directly addressable" log requirement. |
| `commit_sha`  | The commit the check is attached to          | yes      | Always the latest commit on the PR or main, per FR-009.                    |

**Required-check eligibility (FR-016)**:
- A maintainer adds `ci` (the aggregator's check name) as a Required Status Check in the repo's branch-protection rule for `main`.
- This feature does **not** configure branch protection itself (branch-protection is administrative state, not workflow code), but it guarantees `ci` is a stable, single name that survives future job-set changes.

---

## Entity Relationships

```text
                       ┌──────────────────────┐
                       │     Pipeline Run     │  (1)
                       │  (workflow_run)      │
                       └──────────┬───────────┘
                                  │ 1
                                  │
                                  │ has many
                                  │ N
                       ┌──────────▼───────────┐
                       │   Pipeline Job       │  (6 worker jobs + 1 aggregator)
                       └──────────┬───────────┘
                                  │ 1
                                  │
                                  │ produces
                                  │ 1
                       ┌──────────▼───────────┐
                       │     Status Check     │  (one per job, posted to commit)
                       └──────────────────────┘
                                  │
                                  │ aggregator's check (`ci`)
                                  │ is referenced by ↓
                                  │
                       ┌──────────▼───────────┐
                       │  Branch Protection   │  (admin config, NOT in scope of this
                       │   Required Check     │   feature's deliverable; only the
                       └──────────────────────┘   stable `ci` name is in scope)
```

---

## Side-effect: Pipeline Artifacts

The `frontend-test` job uploads diagnostics on failure for triage:

| Artifact name        | Source path                       | Retention | Trigger                          |
| -------------------- | --------------------------------- | --------- | -------------------------------- |
| `playwright-report`  | `frontend/playwright-report/`     | 14 days   | `if: failure()` on `frontend-test` |
| `playwright-results` | `frontend/test-results/`          | 14 days   | `if: failure()` on `frontend-test` |

These artifacts are ephemeral, scoped to the Run, and exist only to serve SC-003 (diagnose root cause in <2 min for ≥90% of failures). No long-lived storage and no production artifact registry is introduced — consistent with the FR-017 resolution (no CD).
