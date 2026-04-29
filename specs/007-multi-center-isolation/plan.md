# Implementation Plan: Multi-Center Data Isolation

**Branch**: `007-multi-center-isolation` | **Date**: 2026-04-29 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/007-multi-center-isolation/spec.md`

## Summary

Harden the existing multi-tenant center infrastructure to ensure complete data isolation. The system already has a `Center` model with `center_id` foreign keys on all core models and a `get_center_id()` helper used in most API endpoints. However, a codebase audit reveals several isolation gaps: `delete_class_session` and `unenroll_student` lack center scoping, `check_scheduling_conflicts` queries across all centers, the auth flow does not check center `is_active` on API requests, and the `enroll_student` CRUD has no cross-center validation. This plan closes every gap at the database query layer, API layer, and frontend routing layer.

## Technical Context

**Language/Version**: Python 3.11+ (backend, `pyproject.toml: requires-python = ">=3.11"`), JavaScript/ES2020+ (frontend, React 19 + Vite 8).
**Primary Dependencies**: FastAPI, SQLAlchemy 2 (async), Alembic (migrations), Pydantic v2 (schemas); React, Ant Design 5, TanStack Query v5, react-i18n (frontend).
**Storage**: PostgreSQL via SQLAlchemy async + `asyncpg`. No schema changes required — all `center_id` FKs already exist on every model.
**Testing**: Pytest + pytest-asyncio (backend), Playwright (frontend E2E).
**Target Platform**: Linux server (Docker), browser (Chromium/Firefox/Safari).
**Project Type**: Multi-stack web application (existing `backend/` + `frontend/` siblings).
**Performance Goals**: Center filtering adds no measurable overhead — all `center_id` columns are already indexed.
**Constraints**: No database migrations needed. All changes are code-level enforcement. Cross-center access returns 404 (not 403) per clarification.
**Scale/Scope**: ~200 students per center, ~20 classes, ~10 attendance sessions/day. Delta: ~10 files modified across backend CRUD, services, deps, and frontend routing.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project's constitution at `.specify/memory/constitution.md` is currently the unfilled template (all placeholders, no ratified principles). There are therefore **no enforced project-level gates** to evaluate at this time.

In place of formal gates, this plan honors the patterns established in prior specs:
- **Center scoping pattern**: All queries filter by `center_id` using `get_center_id()` (established in spec 004).
- **404 for cross-center access**: Per clarification, cross-center resource access returns 404 (not 403) to prevent enumeration.
- **Auth-layer center check**: Center `is_active` checked during authentication, not via token revocation.
- **No premature abstraction**: Simple function-parameter additions, no new architectural patterns.
- **Re-check after Phase 1 design**: PASS — the design adds center_id parameters to existing functions only.

No Complexity Tracking entries are required.

## Project Structure

### Documentation (this feature)

```text
specs/007-multi-center-isolation/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature spec (already authored by /speckit-specify)
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/           # Phase 1 output (this command)
│   └── api.md           # API isolation contract
├── checklists/
│   └── requirements.md  # Spec quality checklist (already authored)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── core/
│   │   └── deps.py                     # MODIFIED — add center is_active check in get_current_user
│   ├── api/
│   │   ├── auth.py                     # MODIFIED — add center is_active check at login
│   │   └── classes.py                  # MODIFIED — pass center_id to delete and unenroll
│   ├── crud/
│   │   └── class_session.py            # MODIFIED — add center_id to delete_class_session, unenroll_student, enroll cross-center validation
│   ├── services/
│   │   └── schedule_service.py         # MODIFIED — add center_id filter to check_scheduling_conflicts
│   └── ...                             # Other files already properly scoped
└── tests/
    └── test_center_isolation.py        # NEW — comprehensive center isolation tests

frontend/
├── src/
│   ├── auth/
│   │   └── ProtectedRoute.jsx          # MODIFIED — explicitly block superadmin from center-scoped routes
│   └── ...                             # Other frontend files unchanged
```

**Structure Decision**: This is a hardening feature — no new files beyond test files. All changes are modifications to existing backend CRUD/service functions and frontend route guards to close identified isolation gaps.

## Complexity Tracking

> Not applicable — Constitution Check has no violations.

## Identified Isolation Gaps

The following gaps were found during codebase audit. Each gap maps to a specific file and function:

| # | Gap | File | Function | Fix |
|---|-----|------|----------|-----|
| G1 | `delete_class_session` has no `center_id` parameter — any admin can delete any class by ID | `backend/app/crud/class_session.py` | `delete_class_session()` | Add `center_id` param, scope lookup |
| G2 | `unenroll_student` has no `center_id` scoping — unenrollment is not center-gated | `backend/app/crud/class_session.py` | `unenroll_student()` | Add `center_id` param, scope lookup |
| G3 | `check_scheduling_conflicts` queries all centers — false conflicts across tenants | `backend/app/services/schedule_service.py` | `check_scheduling_conflicts()` | Add `center_id` filter to base_query |
| G4 | `enroll_student` has no cross-entity validation — student from Center B could be enrolled in Center A's class | `backend/app/crud/class_session.py` | `enroll_student()` | Validate student.center_id == center_id |
| G5 | Auth login does not check center `is_active` — deactivated center users can still log in | `backend/app/api/auth.py` | `login()` | Check center.is_active before issuing tokens |
| G6 | `get_current_user` does not check center `is_active` — deactivated center users with valid JWT can access data | `backend/app/core/deps.py` | `get_current_user()` | Load center, check is_active |
| G7 | Frontend `ProtectedRoute` doesn't explicitly block superadmin | `frontend/src/auth/ProtectedRoute.jsx` | component | Already handled (redirects to /system/centers) — verify only |
