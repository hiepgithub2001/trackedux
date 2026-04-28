# Implementation Plan: Simple CI/CD Pipeline

**Branch**: `005-simple-cicd` | **Date**: 2026-04-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/005-simple-cicd/spec.md`

## Summary

Add a repository-defined CI pipeline that runs automatically on every pull request to `main` and on every push to `main`, producing a single aggregate pass/fail status check. The pipeline runs (in parallel where independent): backend lint (Ruff), backend tests (Pytest), frontend lint (ESLint), frontend end-to-end tests (Playwright), and production-mode builds for both the backend and the frontend. The "CD" portion is descoped to **build-artifact verification only** — no automatic deployment. Frontend testing is restricted to the **existing Playwright suite** — no new unit/component test framework is introduced. The implementation is GitHub Actions because the project is already hosted on GitHub (`github.com:hiepgithub2001/trackedux`), GitHub's native PR status checks satisfy FR-007/FR-016, and its `pull_request` event model gives FR-013 (fork safety) for free.

## Technical Context

**Language/Version**: Workflow definition is GitHub Actions YAML (no language version). Targeted toolchains: Python 3.11+ (matches `backend/pyproject.toml: requires-python = ">=3.11"`), Node 20 LTS (latest LTS supported by Vite 8 and Playwright 1.59).
**Primary Dependencies**: GitHub Actions (`actions/checkout`, `actions/setup-python`, `actions/setup-node`, `actions/cache`, `actions/upload-artifact`); existing repo-level toolchains: Ruff, Pytest (+ pytest-asyncio, testcontainers[postgres], httpx), ESLint, Vite, Playwright.
**Storage**: N/A for the pipeline itself. Backend tests use ephemeral PostgreSQL via `testcontainers[postgres]`, which spins Docker containers on the Actions runner (Linux runners have Docker pre-installed).
**Testing**: Backend → Pytest. Frontend → Playwright (Chromium only, per existing `playwright.config.js`). The pipeline is itself "tested" by deliberately failing PRs (lint violation, broken test, broken build) and confirming each surfaces as a per-step failure.
**Target Platform**: GitHub-hosted `ubuntu-latest` runners only (no matrix, no self-hosted, no Windows/macOS) — keeps with the spec's "simple" mandate and the Assumptions section.
**Project Type**: Infrastructure / repository configuration. No application code is added; only `.github/workflows/*.yml` and (where required) seed test files so the pipeline does not fail with "no tests collected."
**Performance Goals**: SC-002 → warm-cache PR run completes in **≤ 10 minutes** wall-clock; cold-cache run no hard target but should be observably worse than warm to confirm caching is working (FR-011).
**Constraints**:
- No automatic deployment (FR-017 resolution).
- No new frontend test framework (FR-018 resolution).
- No secrets exposed to fork-originated runs (FR-013).
- Per-job timeout enforced so a hung step fails cleanly (FR-014).
- Workflow definition lives in the repo and goes through PR review (FR-015).
**Scale/Scope**: Single repo, one supported runtime version per stack, ~6 logical jobs, ~1 workflow file. Expected delta: ≤ 200 lines of YAML plus a small number of seed test files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project's constitution at `.specify/memory/constitution.md` is currently the unfilled template (all placeholders, no ratified principles). There are therefore **no enforced project-level gates** to evaluate at this time.

In place of formal gates, this plan honors the explicit "simple" bar that the user set in the feature title and the resolved clarifications:
- **Scope discipline**: No deployment automation, no new frontend test framework, no test matrix, no self-hosted runners.
- **Single source of truth**: One workflow file, repository-defined, version-controlled (FR-015).
- **No premature abstraction**: Reusable workflows (`workflow_call`), composite actions, and matrix builds are *not* introduced — they would be cleanly addable later if real duplication or scaling pressure appears.
- **Re-check after Phase 1 design**: PASS — the design in `research.md` and the contracts below introduce no new constraints beyond what the spec already mandates.

No Complexity Tracking entries are required.

## Project Structure

### Documentation (this feature)

```text
specs/005-simple-cicd/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature spec (already authored by /speckit-specify)
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/           # Phase 1 output (this command)
│   └── workflow.md      # GitHub Actions workflow contract: triggers, jobs, statuses, artifacts
├── checklists/
│   └── requirements.md  # Spec quality checklist (already authored)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
.github/
└── workflows/
    └── ci.yml                      # NEW — single CI workflow: lint + test + build for backend & frontend

backend/                            # EXISTING — Python / FastAPI
├── app/                            # Application source
├── alembic/                        # DB migrations (used by integration tests)
├── tests/
│   ├── unit/                       # EXISTING (currently only __init__.py — seed test added by this feature)
│   ├── integration/                # EXISTING (currently only __init__.py — seed test added by this feature)
│   └── contract/                   # EXISTING (currently only __init__.py)
├── pyproject.toml                  # EXISTING — declares dev deps incl. ruff, pytest
└── ruff.toml                       # EXISTING — lint config

frontend/                           # EXISTING — React / Vite
├── src/                            # Application source
├── tests/
│   └── e2e/                        # NEW dir (Playwright config references it; seed spec added by this feature)
├── package.json                    # EXISTING — declares scripts (dev/build/lint)
├── eslint.config.js                # EXISTING — lint config
└── playwright.config.js            # EXISTING — testDir = './tests/e2e', chromium only
```

**Structure Decision**: This is a multi-stack web project (existing `backend/` + `frontend/` siblings). The CI workflow lives at the repository root under `.github/workflows/` — the standard, only location GitHub will discover. No application-layer code is added; the only repository changes outside `.github/` are seed tests under existing test directories so that the pipeline exercises the toolchains with at least one passing assertion (otherwise Pytest exits 5 / Playwright errors with "no tests found", and the green path cannot be demonstrated per FR-007).

## Complexity Tracking

> Not applicable — Constitution Check has no violations.
