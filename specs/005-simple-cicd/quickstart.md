# Quickstart: Living with the CI Pipeline

**Feature**: 005-simple-cicd
**Audience**: Anyone contributing to or maintaining this repository.

This is a working guide. It tells you how to (a) interpret a CI result on a PR, (b) recover from a flaky failure, (c) make changes to the pipeline itself, and (d) what to do on the day someone wants to add deployment. It deliberately does not repeat the spec or the workflow contract — those live in `spec.md` and `contracts/workflow.md`.

---

## 1. Reading a CI result on a PR

You opened a PR against `main`. Within ~30 seconds, the **Checks** section at the bottom of the PR begins populating.

### Green path

When the green checkmark appears next to **`ci`**, your PR is ready for review. That single check aggregates all six worker jobs (lint × 2, test × 2, build × 2). On a warm cache, expect this within ~5–10 minutes (SC-002).

You don't need to inspect the individual `backend-*` / `frontend-*` checks unless you're curious — they're informational.

### Red path

When the red X appears next to **`ci`**, the PR is **blocked from merging** (assuming branch protection is configured to require `ci`). The fix:

1. Look at the PR Checks list: the *failed worker job* is the one with a red X — `backend-lint`, `frontend-test`, etc. The `ci` row will show as "skipped," not "failed" — that is expected (it depends on the workers).
2. Click into the failing job. The Actions UI takes you straight to that job's log.
3. Each job runs as a sequence of named steps. The failing step is highlighted. **Read that step first** — most failures are reproducible by running the same command locally.

### Where the underlying commands live

So you can run the same thing locally:

| Failing job        | Local equivalent (from repo root)                    |
| ------------------ | ---------------------------------------------------- |
| `backend-lint`     | `cd backend && ruff check .`                         |
| `backend-test`     | `cd backend && pytest`                               |
| `backend-build`    | `cd backend && python -m build --wheel`              |
| `frontend-lint`    | `cd frontend && npm run lint`                        |
| `frontend-test`    | `cd frontend && npx playwright test` *(needs the dev server running on `:5173`)* |
| `frontend-build`   | `cd frontend && npm run build`                       |

If a command passes locally but fails in CI, the difference is almost always **environment** (e.g., a test depends on developer-local DB state). Bring the test up to "runs in a clean env" rather than chasing CI-only fixes.

---

## 2. Recovering from a flaky failure

A genuinely intermittent failure (network blip pulling a Docker image, a one-off Playwright timing flake) is recoverable **without** re-running the entire pipeline:

1. Open the failed run in the Actions tab.
2. Click **Re-run failed jobs** (top-right).

Only the failing job re-executes; the other five jobs keep their successful status. This is FR-010 in action and is the path SC-005 measures.

If a job is failing flakily *more than once a week*, that is a signal — file an issue and fix the test, do not paper it over with retries. Repeated flake recovery counts toward SC-005's "<10% of recoveries require a full pipeline re-run" budget; if you find yourself doing it routinely, the gate is being eroded.

---

## 3. Inspecting Playwright failures specifically

Playwright failures are the hardest to reproduce mentally. The pipeline uploads two artifacts on `frontend-test` failure:

- **`playwright-report`** — the standard HTML report. Download it from the failed run's "Artifacts" section, unzip, open `index.html` locally. Each failed test has its own page with screenshots, traces, and the error message.
- **`playwright-results`** — the raw `test-results/` directory. Useful when you want the trace files (`*.trace.zip`) to feed into `npx playwright show-trace`.

Artifacts are kept for **14 days**, then deleted. If you need them after that, re-run the failed job to regenerate them.

---

## 4. Modifying the pipeline

The workflow is a regular file in the repo: `.github/workflows/ci.yml`. Changes to it go through the **same PR review** as any other change (FR-015). To verify a change before opening a PR:

1. **Lint the YAML** with whatever editor support you use (most editors will catch unbalanced braces, etc.).
2. **Push to a feature branch** and open a draft PR. The pipeline runs against your branch — you can see exactly what your change does without having to merge.
3. **Watch for a regression** in run time. If your change roughly doubles the warm-cache time, you've likely broken caching (Decision 5 in `research.md`).

Things to be careful about:

- **Don't add a `pull_request_target` trigger.** It exposes secrets to fork PRs and would violate FR-013.
- **Don't remove `timeout-minutes` from a job.** Section 3 of the workflow contract requires it.
- **Don't add `continue-on-error: true` to lint/test/build steps.** That silently weakens the gate.
- **Don't rename the `ci` job.** Branch-protection rules reference it by name (Decision 10). Renaming it silently turns the merge gate off until a maintainer reconfigures protection.

---

## 5. Adding a new check

You want CI to run a new tool — e.g., a type-checker, a security scanner, a coverage report.

1. Add a new worker job (`name`, `runs-on: ubuntu-latest`, `timeout-minutes`, your steps).
2. Add the job's id to the `ci` aggregator's `needs:` list. **This is the step people forget** — without it, the new check is informational and does not gate merges.
3. Open a PR. Confirm in the PR's Checks section that the new check appears, runs in parallel with the others, and that `ci` waits for it.

Per the workflow contract, you do **not** need to update branch protection — protection requires `ci`, and `ci` already aggregates `needs:` automatically.

---

## 6. The day someone wants to add deployment

This feature is CI-only. When deployment becomes a real requirement:

1. **Open a new spec** (`/speckit-specify`). Do not bolt deployment onto this workflow ad-hoc — the FR-017 resolution explicitly drew the line here so the next conversation gets a clean scope.
2. **Put deployment in a separate workflow** triggered on `push` to `main` (and `release`, etc.) — never on `pull_request`. Deployment workflows handle secrets; mixing them with PR validation breaks fork safety (FR-013).
3. **Reuse `ci`'s outputs.** A deployment workflow can be gated on a `workflow_run` of `ci` succeeding, so the same green bar that today merges a PR will tomorrow also be the green bar that deploys it.

This separation also means the deployment feature does not have to re-invent any of the validation steps — they're already enforced upstream.

---

## 7. Operational checklist (one-time, after this feature merges)

A maintainer (someone with admin access to the repo) does these once:

- [ ] In **Settings → Branches → Branch protection rules** for `main`, set `ci` as a **required status check**. This is what turns the workflow into a hard gate per FR-016.
- [ ] Verify a deliberately-broken PR (e.g., introduce a lint error in a throwaway branch) is blocked from merging.
- [ ] Verify a clean PR shows `ci` green within the expected time.
- [ ] Optional: set the default branch's required reviewers to ≥1 so `ci` + review act as twin gates.

After this checklist, the pipeline is fully live and the SC-001 / SC-006 success criteria are observably enforced.

---

## 8. Where to look when something is weird

| Symptom                                                  | First place to look                                                  |
| -------------------------------------------------------- | -------------------------------------------------------------------- |
| `ci` is "skipped" on every PR                            | A worker job is failing — check the PR Checks list.                  |
| Workflow doesn't run at all on a new PR                  | The PR is from a fork **and** the fork has Actions disabled, OR the workflow file has a YAML syntax error on `main`. Check the **Actions** tab for parse errors. |
| Dependency installs take 5+ minutes every run            | Cache is missing or its key is changing every run. Re-check Decision 5 in `research.md`. |
| A test passes locally but fails in CI                    | Almost always env: stale local DB, dev-only seed data, or local node_modules out of sync with `package-lock.json`. Run `npm ci` (not `npm install`) and re-check. |
| Playwright says "no tests found"                         | `frontend/tests/e2e/` is empty or the test file does not match Playwright's discovery pattern. |
| Pytest exits with code 5                                 | All backend test directories contain only `__init__.py`. Add at least one real test (a deleted seed test would also produce this). |
| `ci` is green but the merge button is still red          | Branch protection requires another check (e.g., review approvals). Read the PR's Merging section — it will say which gate is missing. |
