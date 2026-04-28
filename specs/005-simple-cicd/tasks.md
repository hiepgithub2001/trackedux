---

description: "Task list for feature 005-simple-cicd"
---

# Tasks: Simple CI/CD Pipeline

**Input**: Design documents from `/specs/005-simple-cicd/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/workflow.md, quickstart.md
**Tests**: Tests are NOT explicitly requested for the pipeline itself; verification is performed via deliberately-failing PRs (per the spec's User Story acceptance scenarios). Two seed application tests are added so the existing toolchains have something to exercise — this is not a TDD layer for the workflow.
**User Add-On**: A repository-root `Makefile` mirroring CI commands locally is included in Setup (Phase 1) per the user's request.

**Organization**: Tasks are grouped by user story (US1–US4 from `spec.md`). Each user story phase is an additive layer on top of the prior phase, terminating in a verification step.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependency on incomplete earlier tasks)
- **[Story]**: User story label (US1, US2, US3, US4). Setup, Foundational, and Polish phases have no story label.
- File paths are absolute-from-repo-root.

## Path Conventions

This is a multi-stack web project: existing `backend/` (Python/FastAPI) and `frontend/` (React/Vite) siblings. The CI workflow lives at the repo-root path `.github/workflows/ci.yml` (single file per Decision 2 in `research.md`). Seed test files live alongside the existing test directories. The Makefile lives at repo root.

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the directories and seed files the pipeline depends on, plus the local-development Makefile.

- [X] T001 Create `.github/workflows/` directory at repo root (the only path where GitHub discovers workflow files). Verify it is tracked by git (it will be once the workflow file inside it is added in Phase 2).
- [X] T002 [P] Create `/home/lehiep/trackedux/Makefile` at the repo root with `.PHONY` targets that mirror every CI command so a contributor can run the same checks locally before pushing. Targets MUST include: `help` (default), `backend-lint` (`cd backend && ruff check .`), `backend-test` (`cd backend && pytest`), `backend-build` (`cd backend && pip install build && python -m build --wheel`), `frontend-lint` (`cd frontend && npm run lint`), `frontend-test` (`cd frontend && npx playwright test` with a `help` note that the Vite dev server must be running on `:5173`), `frontend-build` (`cd frontend && npm run build`), and `ci-local` (depends on all six above; the one-stop "validate-before-push" target). The `help` target lists each available target with a one-line description.
- [X] T003 [P] Create `/home/lehiep/trackedux/backend/tests/unit/test_smoke.py` with a single trivial test (e.g., `def test_smoke(): assert True`). Reason: Pytest exits with code 5 when zero tests are collected, which CI treats as failure. Without this seed, the green path of `backend-test` cannot be observed end-to-end. Per Decision 7 in `research.md`, this is scaffolding for the gate, not a substitute for real coverage.
- [X] T004 [P] Create `/home/lehiep/trackedux/frontend/tests/e2e/smoke.spec.js` (the directory does not yet exist; `mkdir -p` it). The spec MUST contain a single Playwright test that navigates to `/` (the dev server's homepage) and asserts the page title or a stable root selector is present (e.g., the React root `#root` is non-empty). Reason: Playwright errors with "No tests found" when its `testDir` is empty, blocking the green path of `frontend-test`. Per Decision 6 in `research.md`.

**Checkpoint**: Setup complete — local `make ci-local` (excluding `frontend-test`, which needs the dev server) can be invoked, and both seed tests pass when run locally.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Lay down the shell of `ci.yml` (top-level keys: `name`, `on`, `concurrency`, `permissions`, empty `jobs`) so all subsequent user-story phases can attach jobs to it.

**⚠️ CRITICAL**: User Story 1 cannot be merged without the workflow file existing.

- [X] T005 Create `/home/lehiep/trackedux/.github/workflows/ci.yml` containing only the workflow scaffolding required by every job:
  - `name: CI`
  - `on:` with `pull_request: branches: [main]` only (the `push: branches: [main]` trigger is added in US2; `workflow_dispatch:` is included so a maintainer can manually trigger from the Actions UI).
  - `permissions:` set to least privilege: `contents: read`. No other scopes (no `pull-requests: write`, no `actions: write` etc.) — preserves FR-013 fork safety even before any secrets are introduced.
  - `concurrency:` is **omitted** at this stage; it is added in US3 (T014) where its behavior is verified.
  - `jobs:` declared as an empty mapping (`jobs: {}` is invalid YAML for Actions; instead leave with a TODO comment under the `jobs:` key — the next US1 task will add the first job).
  - Do **not** subscribe to `pull_request_target` (it would expose secrets to fork PRs and violate FR-013).

**Checkpoint**: Foundation ready — the workflow file exists, `actions/checkout` discovery passes, and US1 jobs can be appended in parallel.

---

## Phase 3: User Story 1 - Automated quality gate on pull requests (Priority: P1) 🎯 MVP

**Goal**: A PR opened against `main` automatically runs lint and tests for both backend and frontend, and reports a single aggregate `ci` status check that can be used as a merge gate.

**Independent Test**: Open a PR with a deliberate `# noqa` removal that re-introduces a Ruff violation; confirm `backend-lint` fails, `ci` is reported as not-passed, and the failing step is directly addressable from the PR Checks tab. Open a clean PR; confirm `ci` reports green.

### Implementation for User Story 1

- [X] T006 [P] [US1] Add the `backend-lint` job to `/home/lehiep/trackedux/.github/workflows/ci.yml`. Steps: `actions/checkout@v4`; `actions/setup-python@v5` with `python-version: "3.11"`; `pip install -e backend[dev]` (installs Ruff via the dev extra); `working-directory: backend`, `run: ruff check .`. Set `runs-on: ubuntu-latest`, `timeout-minutes: 15` (FR-014). Each step has a `name:` (FR-008).
- [X] T007 [P] [US1] Add the `frontend-lint` job to `/home/lehiep/trackedux/.github/workflows/ci.yml`. Steps: `actions/checkout@v4`; `actions/setup-node@v4` with `node-version: "20"`; `working-directory: frontend`, `run: npm ci` then `run: npm run lint`. `runs-on: ubuntu-latest`, `timeout-minutes: 15`. Each step has a `name:`.
- [X] T008 [P] [US1] Add the `backend-test` job to `/home/lehiep/trackedux/.github/workflows/ci.yml`. Steps: `actions/checkout@v4`; `actions/setup-python@v5` with `python-version: "3.11"`; `pip install -e backend[dev]` (installs pytest, pytest-asyncio, httpx, testcontainers[postgres]); `working-directory: backend`, `run: pytest`. Per Decision 4, do NOT add a `services: postgres` block — `testcontainers` will spin Postgres via the runner's pre-installed Docker. `runs-on: ubuntu-latest`, `timeout-minutes: 15`.
- [X] T009 [P] [US1] Add the `frontend-test` job to `/home/lehiep/trackedux/.github/workflows/ci.yml`. Steps: `actions/checkout@v4`; `actions/setup-node@v4` with `node-version: "20"`; `working-directory: frontend`, `run: npm ci`; `run: npx playwright install --with-deps chromium` (Chromium only per existing `playwright.config.js`); `run: npm run dev &` to background the Vite dev server; wait for `http://localhost:5173` to respond (use `npx wait-on http://localhost:5173` or a curl/sleep loop with a hard cap); `run: npx playwright test`. Add an `if: failure()` step that uses `actions/upload-artifact@v4` to upload `frontend/playwright-report` and `frontend/test-results` (artifact names `playwright-report`, `playwright-results`, `retention-days: 14`) per Decision 6. `runs-on: ubuntu-latest`, `timeout-minutes: 20` (longer to absorb cold Playwright browser install on first runs).
- [X] T010 [US1] Add the aggregator `ci` job to `/home/lehiep/trackedux/.github/workflows/ci.yml`. `runs-on: ubuntu-latest`, `timeout-minutes: 5`, `needs: [backend-lint, frontend-lint, backend-test, frontend-test]`, single step `name: OK / run: echo OK`. Do NOT add `if: always()` — its absence is what makes it act as a gate (Decision 10, contract §4). Depends on T006–T009 being merged into the file.
- [ ] T011 [US1] Verify MVP. Open a feature PR (can be the PR that introduces this workflow itself once T005–T010 are pushed) and confirm: (a) the four worker jobs run in parallel and complete; (b) the `ci` aggregator passes when all four pass; (c) a deliberately-introduced lint violation surfaces as a `backend-lint` or `frontend-lint` failure with the failing step directly addressable; (d) when any worker fails, `ci` is reported as not-passed (skipped). Document the run URL and outcome in the PR description.

**Checkpoint**: User Story 1 is fully functional. The PR gate works end-to-end against any PR targeting `main`. **This is the MVP — stop here and validate before continuing.**

---

## Phase 4: User Story 2 - Continuous validation of the main branch (Priority: P2)

**Goal**: After a PR merges into `main`, the same checks re-run against the post-merge state of `main` so a regression that slipped through (e.g., from a merge conflict resolution) is surfaced immediately.

**Independent Test**: Merge a known-good PR into `main` and confirm a fresh pipeline run starts on the latest `main` commit and reports green. Optionally, push a deliberately-broken commit directly to a temporary branch, fast-forward `main` to it (or merge it via PR), and confirm the post-merge run reports red.

### Implementation for User Story 2

- [X] T012 [US2] Extend the `on:` block in `/home/lehiep/trackedux/.github/workflows/ci.yml` to also subscribe to `push: branches: [main]`. The same six jobs (four currently, six after US4) re-execute on every push to `main`, satisfying the "main-branch validation" requirement and posting commit-level status checks visible from the repo home page.
- [ ] T013 [US2] Verify US2. Merge a clean PR that has just gone green; immediately observe a new run start on the post-merge `main` commit; confirm it reports green and the status appears on the latest commit at `https://github.com/hiepgithub2001/trackedux/commits/main`. Document the run URL in the PR description.

**Checkpoint**: User Stories 1 AND 2 work independently. The `main` branch now has a continuously-updated health signal.

---

## Phase 5: User Story 3 - Fast, predictable feedback for contributors (Priority: P2)

**Goal**: Make the pipeline fast (warm-cache ≤10 min, SC-002), recoverable (retry-failed-job-only, FR-010 / SC-005), and stable (cancel stale PR runs, never cancel main runs, FR-009).

**Independent Test**: Measure end-to-end run time on a representative PR after the cache is populated; confirm it is ≤10 minutes. Trigger a single failing step, click "Re-run failed jobs," and confirm only that job re-executes while the others retain their successful status. Push a second commit to a PR while the first run is still in progress; confirm the older run is cancelled.

### Implementation for User Story 3

- [X] T014 [US3] Add a workflow-level `concurrency:` block to `/home/lehiep/trackedux/.github/workflows/ci.yml`: `group: ${{ github.workflow }}-${{ github.ref }}`. Set `cancel-in-progress: ${{ github.event_name == 'pull_request' }}` (true on PRs, false on push to main per Decision 9). This satisfies FR-009 without breaking US2's main-branch invariant.
- [X] T015 [P] [US3] Enable pip caching in the `backend-lint` and `backend-test` jobs in `/home/lehiep/trackedux/.github/workflows/ci.yml` by setting `cache: pip` and `cache-dependency-path: backend/pyproject.toml` on the `actions/setup-python@v5` step. (Same cache key is reused across both jobs since they install the same dev extra.)
- [X] T016 [P] [US3] Enable npm caching in the `frontend-lint`, `frontend-test`, and (later, after T020) `frontend-build` jobs in `/home/lehiep/trackedux/.github/workflows/ci.yml` by setting `cache: npm` and `cache-dependency-path: frontend/package-lock.json` on the `actions/setup-node@v4` step.
- [X] T017 [US3] Add Playwright browser caching to the `frontend-test` job in `/home/lehiep/trackedux/.github/workflows/ci.yml`. Use `actions/cache@v4` with `path: ~/.cache/ms-playwright` and `key: playwright-${{ runner.os }}-${{ hashFiles('frontend/package-lock.json') }}`. Place the cache-restore step BEFORE `npx playwright install --with-deps chromium`. The install command is a no-op when the browser binaries are already present, so on cache hit this saves ~60–90s per run (the single biggest savings, per Decision 5).
- [ ] T018 [US3] Verify US3. After T014–T017 are merged: (a) push two commits to a PR in quick succession and confirm the older run is cancelled; (b) re-run the same PR after caches warm up and measure end-to-end time — confirm ≤10 minutes (SC-002); (c) deliberately fail one job, click "Re-run failed jobs" in the Actions UI, and confirm only that job re-runs while the others retain success.

**Checkpoint**: User Story 3 layered on top of 1+2. The gate is now sustainable: fast, retryable, and self-cleaning on superseded commits.

---

## Phase 6: User Story 4 - Build verification of deployable artifacts (Priority: P3)

**Goal**: Catch the class of regressions where tests pass but the production build is broken (e.g., a dev-only import, missing static asset, dynamic require that fails under bundling).

**Independent Test**: Introduce a change that breaks only the production build (e.g., an `import` from a path that resolves in dev mode but not in `vite build`, or a backend module that is missing from `pyproject.toml`'s `[tool.setuptools.packages.find]`). Confirm `frontend-build` or `backend-build` fails even though all linters and tests pass.

### Implementation for User Story 4

- [X] T019 [P] [US4] Add the `backend-build` job to `/home/lehiep/trackedux/.github/workflows/ci.yml`. Steps: `actions/checkout@v4`; `actions/setup-python@v5` with `python-version: "3.11"` and `cache: pip` + `cache-dependency-path: backend/pyproject.toml`; `run: pip install build` (the `build` package is a build-time tool, not a project dep); `working-directory: backend`, `run: python -m build --wheel` per Decision 8. `runs-on: ubuntu-latest`, `timeout-minutes: 15`. Do NOT upload the wheel as an artifact — it is throwaway diagnostic output (contract §2.2).
- [X] T020 [P] [US4] Add the `frontend-build` job to `/home/lehiep/trackedux/.github/workflows/ci.yml`. Steps: `actions/checkout@v4`; `actions/setup-node@v4` with `node-version: "20"` and `cache: npm` + `cache-dependency-path: frontend/package-lock.json`; `working-directory: frontend`, `run: npm ci`; `run: npm run build` (Vite production build). `runs-on: ubuntu-latest`, `timeout-minutes: 15`.
- [X] T021 [US4] Update the `ci` aggregator job in `/home/lehiep/trackedux/.github/workflows/ci.yml` to add the two new jobs to its `needs:` list. The full list becomes `needs: [backend-lint, frontend-lint, backend-test, frontend-test, backend-build, frontend-build]`. This ensures both build jobs are part of the merge gate (FR-006, FR-007). Depends on T019 and T020.
- [ ] T022 [US4] Verify US4. Push a temporary commit that breaks ONLY the production build (suggested: in `frontend/src/main.jsx`, add `import './does-not-exist.css';` — Vite dev resolves the missing file lazily but `vite build` fails on it). Confirm `frontend-build` reports failure even though `frontend-lint` and `frontend-test` pass, and the `ci` aggregator does not pass. Revert the temporary commit. Document the run URL in the verifying PR.

**Checkpoint**: All four user stories are now layered into a single workflow file. The pipeline matches the full contract in `contracts/workflow.md` and satisfies all 18 functional requirements in `spec.md`.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, maintainer onboarding, and documentation hand-off.

- [ ] T023 Walk through `/home/lehiep/trackedux/specs/005-simple-cicd/quickstart.md` § 7 "Operational checklist" with a maintainer (someone with admin access to `github.com/hiepgithub2001/trackedux`). Concretely: (a) in **Settings → Branches → Branch protection rules** for `main`, add `ci` as a Required Status Check; (b) verify a deliberately-broken PR cannot be merged; (c) verify a clean PR can be merged. This is the moment FR-016 / SC-006 become observable; until this step is done, the workflow runs but does not gate.
- [X] T024 [P] Add a short paragraph to `/home/lehiep/trackedux/README.md` (under an "Continuous Integration" or similar section) that links to `specs/005-simple-cicd/quickstart.md` for contributors. One paragraph max — covers: which checks run, where to look on a failed PR, how to retry a flake, and the local `make ci-local` shortcut. Do not duplicate the quickstart's content; link to it.
- [ ] T025 Run final cross-validation against `/home/lehiep/trackedux/specs/005-simple-cicd/contracts/workflow.md` § 7 "Verifying conformance" — execute each of the five conformance checks listed there and confirm pass. Capture the resulting Actions run URLs in the merging PR description so the audit trail is preserved.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — T001–T004 can all start immediately. T002, T003, T004 are mutually independent (different files) and run in parallel; T001 is just `mkdir`.
- **Foundational (Phase 2)**: Depends on Setup completion (specifically T001 — the `.github/workflows/` directory must exist before T005 writes a file into it). T005 writes one file; no parallelism inside this phase.
- **User Story 1 (Phase 3)**: Depends on Foundational (T005). T006–T009 all edit the same file (`ci.yml`) but they add **different jobs** under the `jobs:` key, so they can be drafted in parallel and merged sequentially with trivial conflicts. T010 depends on T006–T009 being present. T011 (verification) depends on T006–T010.
- **User Story 2 (Phase 4)**: Depends on US1 being merged. T012 edits the same `ci.yml`. T013 depends on T012.
- **User Story 3 (Phase 5)**: Depends on US1 being merged (caching/concurrency need jobs to exist). T015–T017 can be drafted in parallel; T014 is a single workflow-level edit. T018 (verification) depends on T014–T017.
- **User Story 4 (Phase 6)**: Depends on US1 being merged. T019–T020 are independent jobs and can be drafted in parallel. T021 depends on T019 AND T020. T022 (verification) depends on T021.
- **Polish (Phase 7)**: Depends on US1–US4 being merged. T023 must be done by a repo admin. T024 is independent. T025 is the final stamp.

### User Story Dependencies

- **US1**: No dependencies on other stories.
- **US2**: Independent of US3/US4 (just adds a trigger), but US2 verification (T013) is meaningless until US1 jobs exist on `main`.
- **US3**: Independent of US2/US4 in implementation, but its verification (measuring "warm-cache ≤10 min") is more meaningful once all six jobs (post-US4) exist.
- **US4**: Independent of US2/US3 in implementation. T021 is the only inter-story task (touches the aggregator `needs:` list which US1 created).

### Within Each User Story

- Implementation tasks edit `ci.yml` in additive blocks. Marked `[P]` only when they affect different jobs (different YAML keys); when the same key is touched (T021 expands `needs:` from US1's list), the task is non-parallel.
- Verification (`Tnnn [USx] Verify ...`) is always the last task of its phase and depends on all preceding phase tasks being merged.

### Parallel Opportunities

- **Within Setup**: T002 (Makefile), T003 (backend smoke test), T004 (frontend smoke test) all touch different files — fully parallel.
- **Within US1 implementation**: T006, T007, T008, T009 each add a distinct job — can be drafted in parallel by four contributors. They do all merge into one file; resolution is trivial (different YAML mapping keys).
- **Within US3**: T015, T016, T017 touch different jobs / different concerns — parallel.
- **Within US4**: T019, T020 add separate jobs — parallel.
- **Cross-story**: After US1 merges, US2 + US3 + US4 can be developed in parallel branches and merged in any order; only US3's "warm-cache 10min" verification is meaningfully order-dependent.

---

## Parallel Example: Setup (Phase 1)

```bash
# Three independent files; safe to launch concurrently.
Task: "Create /home/lehiep/trackedux/Makefile with backend-lint, frontend-lint, backend-test, frontend-test, backend-build, frontend-build, ci-local, help targets"
Task: "Create /home/lehiep/trackedux/backend/tests/unit/test_smoke.py with a single trivial test"
Task: "Create /home/lehiep/trackedux/frontend/tests/e2e/smoke.spec.js asserting the Vite homepage loads"
```

## Parallel Example: User Story 1 Implementation

```bash
# Four jobs, four distinct YAML keys under `jobs:` — concurrent drafting safe; final sequential merge is trivial.
Task: "Add backend-lint job to .github/workflows/ci.yml (Ruff)"
Task: "Add frontend-lint job to .github/workflows/ci.yml (ESLint)"
Task: "Add backend-test job to .github/workflows/ci.yml (Pytest + Docker for testcontainers)"
Task: "Add frontend-test job to .github/workflows/ci.yml (Playwright + dev server + on-failure artifact upload)"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup — Makefile and seed tests in place.
2. Complete Phase 2: Foundational — workflow scaffold exists.
3. Complete Phase 3: User Story 1 — four worker jobs + `ci` aggregator on `pull_request`.
4. **STOP and VALIDATE**: Open a PR, see `ci` go green or red appropriately. T011 is the gate.
5. Optionally: ship just this MVP, configure branch protection (T023 from Polish, brought forward), and earn the merge-gate value immediately. US2/US3/US4 become follow-up PRs.

### Incremental Delivery

1. Setup + Foundational + US1 → MVP merge-gate (live).
2. Add US2 → main-branch health signal.
3. Add US3 → fast, retryable, self-cleaning gate.
4. Add US4 → build-verification layer.
5. Polish → branch protection turned on, README updated, contract conformance check signed off.

Each layer is independently shippable as its own PR — the workflow file remains valid YAML at each intermediate state.

### Parallel Team Strategy

With multiple contributors:

1. One person does Phase 1 + Phase 2 (small, sequential).
2. Once US1 has merged: a second contributor can pick up US3 (caching/concurrency) while a third picks up US4 (build jobs); US2 is a trivial one-line trigger addition that anyone can land. These are three independent PRs that merge cleanly because they touch different parts of `ci.yml`.
3. Polish is owned by whoever has admin rights on the repo.

---

## Notes

- The implementation deliberately avoids: matrix builds, multiple workflow files, reusable workflows, self-hosted runners, secrets, deployment, `pull_request_target`, and any new test framework. Each was considered and rejected in `research.md`.
- Verification tasks (T011, T013, T018, T022, T025) are non-skippable — they are how the user-story acceptance scenarios in `spec.md` are signed off. If a verification fails, the corresponding implementation tasks are not done.
- The Makefile (T002) is local-developer ergonomics; CI does NOT call `make` (it invokes the underlying tools directly). This avoids coupling CI behavior to a Makefile change.
- The seed tests (T003, T004) are scaffolding, not coverage. They exist so the green path is observable on day one. Replacing them with real tests is welcome but out of scope for this feature.
- Commit one logical group at a time (e.g., US1 implementation as one commit, US1 verification as a follow-up commit if the verification PR catches an issue).
- Stop at any checkpoint to validate before proceeding.
