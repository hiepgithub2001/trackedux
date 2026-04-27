# Implementation Plan: Piano Center Management System

**Branch**: `001-piano-center-management` | **Date**: 2026-04-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/001-piano-center-management/spec.md`

## Summary

A bilingual (Vietnamese/English) Progressive Web App for managing a piano learning center: student CRM, class scheduling with conflict detection, attendance + makeup tracking, tuition packages with renewal reminders, teacher management, dashboard, and (Phase 2) parent portal, teacher notes, monthly reports, and Zalo/SMS notifications.

This plan refresh integrates the **2026-04-27 clarification session** outcomes:

- Class types (1:1 / pair / group) are removed entirely. A class is just a name + teacher + start time + duration + unrestricted student list.
- Each class stores its own duration (minutes); overlap detection uses `[start, start + duration)` as a range.
- Each Package stores a `price` (VND `BIGINT`) set by admin at assignment time; payment history references that amount.
- Admin/staff sessions persist until manual logout (no idle timeout, no lockout for Phase 1).
- Makeup sessions render with a distinct "Makeup" badge on the calendar (already supported by `is_makeup` flag, frontend needs a visual marker).

The architecture is a Web Application: a Python FastAPI backend with PostgreSQL and a React/Vite SPA frontend, both already scaffolded under `backend/` and `frontend/`. The plan focuses on aligning the existing codebase with the new clarifications.

## Technical Context

**Language/Version**:
- Backend: Python 3.11+ (`backend/pyproject.toml` requires-python `>=3.11`)
- Frontend: Node 20+ (Vite 8 / React 19 toolchain)

**Primary Dependencies**:
- Backend: FastAPI ≥ 0.115, SQLAlchemy 2 (async) + asyncpg, Pydantic 2, Alembic 1.13+, python-jose (JWT), passlib[bcrypt], python-multipart
- Frontend: React 19, Vite 8, Ant Design 6, `@fullcalendar/react` (daygrid + timegrid), `@tanstack/react-query` 5, `react-i18next` 17, `react-router-dom` 7, axios, dayjs, `vite-plugin-pwa`

**Storage**: PostgreSQL 16+ (async via asyncpg). Migrations managed by Alembic with sequential numbering (`001_…`, `002_…`).

**Testing**:
- Backend: pytest, pytest-asyncio, httpx async client, testcontainers[postgres]
- Frontend: Playwright (E2E, already configured via `playwright.config.js`); component tests with Vitest + Testing Library when added

**Target Platform**: Linux server (backend), modern browsers + installable PWA on Android/iOS/desktop (frontend). Vietnamese-language primary users.

**Project Type**: Web application (frontend + backend separation)

**Performance Goals**:
- Student list / schedule endpoints: p95 < 200 ms for 100 active students
- Calendar rendering: < 1 s for a full week of sessions
- Attendance batch save: < 500 ms for a single class

**Constraints**:
- Online-only for Phase 1 (no offline data cache; PWA is installability + asset cache only)
- All money stored as `BIGINT` VND (no decimals)
- Bilingual UI (vi / en), no untranslated strings (SC-010)
- Sessions never time out for Phase 1 (clarification 2026-04-27)
- No upper bound on students per class (clarification 2026-04-27)

**Scale/Scope**:
- Initial: ~30 students, 5–10 staff/admin, ~50 weekly sessions
- Designed to scale to ≥ 100 students (SC-006)
- ~10 entities, ~30 REST endpoints, ~6 frontend feature modules (students, schedule, attendance, tuition, teachers, dashboard)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`.specify/memory/constitution.md`) currently contains only template placeholders (no ratified principles). No constitutional gates can be enforced.

| Gate | Status | Notes |
|------|--------|-------|
| Constitutional principles | **N/A — Unfilled** | `constitution.md` is the unedited template. Recommend running `/speckit-constitution` to ratify principles before further work. |
| Spec clarifications complete | ✅ Pass | Session 2026-04-27 resolved 5 critical ambiguities; all integrated into spec. |
| Tech stack matches existing repo | ✅ Pass | Plan reuses existing backend/frontend stacks; no new framework introduced. |
| Phase scoping (P1 vs P2) | ✅ Pass | Spec clearly marks Phase 2 features (parent portal, notes, reports, notifications). |

**Action item (advisory, not blocking)**: Ratify the constitution to enable real gate enforcement on subsequent specs.

## Project Structure

### Documentation (this feature)

```text
specs/001-piano-center-management/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 — already exists, kept as-is
├── data-model.md        # Phase 1 — updated for clarifications
├── quickstart.md        # Phase 1 — kept; manual smoke flow
├── contracts/
│   ├── api.md           # Phase 1 — REST endpoint contracts (updated)
│   └── ui.md            # Phase 1 — UI contracts (updated for makeup badge)
├── checklists/          # Generated by /speckit-checklist as needed
├── spec.md              # Source of truth (with clarifications)
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                # FastAPI app entrypoint
│   ├── core/                  # Config, security (JWT, hashing), deps
│   ├── db/                    # Async engine, session factory
│   ├── models/                # SQLAlchemy models
│   │   ├── user.py
│   │   ├── parent.py
│   │   ├── student.py
│   │   ├── student_status_history.py
│   │   ├── teacher.py
│   │   ├── teacher_availability.py
│   │   ├── class_session.py            # ← drop class_type, drop max_students; require name
│   │   ├── class_enrollment.py
│   │   ├── package.py                  # already has price (BIGINT VND)
│   │   ├── payment_record.py
│   │   ├── attendance.py
│   │   └── renewal_reminder.py
│   ├── schemas/                # Pydantic request/response models
│   ├── crud/                   # DB access layer
│   ├── services/               # Business logic (overlap detection, package math)
│   ├── api/                    # FastAPI routers (one per feature)
│   └── scripts/                # Seed / utility scripts
├── alembic/
│   └── versions/               # 001_*.py … sequential migrations
└── tests/
    ├── unit/
    ├── integration/            # DB-backed (testcontainers)
    └── contract/               # OpenAPI drift checks

frontend/
├── src/
│   ├── main.jsx
│   ├── App.jsx
│   ├── api/                    # axios client, query hooks
│   ├── auth/                   # Login, token storage, route guards
│   ├── components/             # Shared UI building blocks
│   ├── features/
│   │   ├── students/
│   │   ├── teachers/
│   │   ├── schedule/           # ← FullCalendar wrapper; render makeup badge
│   │   ├── attendance/
│   │   ├── tuition/
│   │   └── dashboard/
│   ├── i18n/                   # vi.json, en.json (react-i18next)
│   ├── pwa/                    # manifest, service-worker hooks
│   ├── routes/                 # React Router config
│   └── styles/
├── public/
├── tests/                      # Playwright E2E specs (under playwright.config.js)
└── vite.config.js
```

**Structure Decision**: Adopting the existing two-tree layout (`backend/` + `frontend/`). No restructuring is needed — the directories above already exist. The plan focuses on three categories of change against this layout: (1) drop class typing, (2) ensure duration-based overlap is enforced, (3) add a makeup visual marker in the schedule feature.

## Phase 0 — Research (already complete)

`research.md` is the authoritative record of technology decisions; the 2026-04-27 clarifications did not invalidate any of those choices. Re-using as-is. Summary of unchanged decisions:

| # | Decision | Status |
|---|----------|--------|
| 1 | React + Vite + PWA | Unchanged |
| 2 | FastAPI backend | Unchanged |
| 3 | PostgreSQL + SQLAlchemy async | Unchanged |
| 4 | Alembic with sequential numbering | Unchanged |
| 5 | react-i18next for bilingual UI | Unchanged |
| 6 | JWT auth + RBAC | Refined: refresh tokens still issued, but Phase 1 session persists until manual logout (no idle timeout) |
| 7 | FullCalendar | Unchanged; needs an `eventContent` renderer for the makeup badge |
| 8 | Online-only PWA shell | Unchanged |
| 9 | React Query + Context | Unchanged |
| 10 | Zalo + SMS (deferred to Phase 2) | Unchanged |
| 11 | pytest + Playwright | Unchanged |
| 12 | Two-tree project layout | Unchanged |
| 13 | Ant Design | Unchanged |
| 14 | OpenAPI auto-docs | Unchanged |

No `NEEDS CLARIFICATION` markers remain in the technical context.

## Phase 1 — Design & Contracts

### 1. Data model deltas (recorded in `data-model.md`)

| Entity | Change | Reason |
|--------|--------|--------|
| `ClassSession` | Drop `class_type` enum; drop `max_students`; rename `title` → `name` and make it `NOT NULL`; store both `start_time` (TIME) and `duration_minutes` (INTEGER, NOT NULL, > 0). `end_time` becomes a derived value (`start_time + duration_minutes`). | Clarifications: no type classification; explicit duration field. |
| `ClassEnrollment` | Drop the "cannot exceed `max_students`" rule. Keep the `(class_session_id, student_id) UNIQUE` rule (no duplicate enrollment). | Clarifications: unrestricted enrollment. |
| `Package` | No structural change — `price BIGINT VND` already present. Document explicitly that `price` is admin-set at assignment time and must be `> 0`. | Clarification reinforces existing field. |
| `User` / auth | No schema change. Document that for Phase 1 the access token is issued long-lived (e.g., 30 days) and the refresh-token rotation behaves as "until manual logout"; no per-request idle TTL is enforced. | Clarification: sessions persist until manual logout. |
| `AttendanceRecord` / `ClassSession` | No schema change for makeup visual marker — `ClassSession.is_makeup` already exists. Frontend gets a UI contract addition. | Clarification: visual marker. |

The PostgreSQL `class_type` enum and any check constraints derived from it are dropped via a new Alembic migration: `010_drop_class_type_and_max_students.py`.

### 2. API contract deltas (recorded in `contracts/api.md`)

| Endpoint | Change |
|----------|--------|
| `POST /api/v1/classes` | Request body drops `class_type` and `end_time`; adds required `name` (string) and required `duration_minutes` (integer ≥ 1). |
| `GET /api/v1/classes` (query) | Drop `class_type` filter. |
| `GET /api/v1/classes/{id}` (response) | Drop `class_type`, `max_students`. Add `name`, `duration_minutes`. |
| `POST /api/v1/classes/{id}/enroll` | Remove the `422 Class at max capacity` response. Only `409 Time conflict` remains. |
| `GET /api/v1/schedule/weekly` (response) | Drop `class_type`. Keep `is_makeup` (already present). Each session entry includes `name`, `start_time`, `duration_minutes`, `end_time` (derived). |
| `POST /api/v1/auth/login` (response) | Document long-lived token semantics for Phase 1 (no idle timeout). No request shape change. |

### 3. UI contract deltas (recorded in `contracts/ui.md`)

| Surface | Change |
|---------|--------|
| Class create/edit form | Replace the "Class type" dropdown with a free-text "Class name" field. Replace "End time" with "Duration (minutes)" numeric input (default 60). Student picker has no upper bound. |
| Weekly calendar (`schedule` feature) | Each session card renders the class `name`. If `is_makeup` is `true`, render an additional Ant Design `Tag` labelled "Makeup" (use `color="orange"` for visibility) above the time range. |
| Conflict toast | Wording stays the same; the displayed range now uses `start_time + duration_minutes`. |
| Login page | No "Stay signed in" checkbox required — sessions stay logged in by default. Document the long-lived behaviour in the user help text. |

### 4. Quickstart

`quickstart.md` is unchanged in shape (start backend, run migrations, seed, start frontend, log in as admin). The smoke-flow steps that involve creating a class need to be updated to match the new form (name + duration), tracked in the Phase 2 task list.

### 5. Agent context update

`CLAUDE.md` already has the SPECKIT block pointing at `specs/001-piano-center-management/plan.md`; no change needed.

## Post-Design Constitution Re-check

| Gate | Status | Notes |
|------|--------|-------|
| Constitutional principles | **N/A — Unfilled** | Same as pre-check. No new violations introduced. |
| Backwards compatibility | ⚠ Migration required | Dropping the `class_type` column is destructive — see Complexity Tracking below. |
| Spec drift | ✅ Pass | Spec, data model, and contracts are now mutually consistent. |
| Test coverage plan | ✅ Pass | Existing test layout (unit / integration / contract / E2E) covers the modified surfaces. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Destructive schema change (drop `class_type` enum + `max_students` column from `ClassSession`) | The clarification explicitly removes count-based class typing; keeping the column would create persistent ambiguity in the data model. | Keeping the column nullable was considered, but it would leave a "ghost" field in OpenAPI / forms, and existing client code reads `class_type` to label cards — soft-deprecation would prolong the inconsistency without payoff. The dataset is small (no production data yet), so a clean drop is cheaper. |
| Long-lived auth tokens (no idle timeout) | Clarification: sessions persist until manual logout. | Idle-timeout enforcement is the safer default, but the user explicitly opted out for Phase 1 (small internal staff only). Document the trade-off and revisit in Phase 2 alongside the parent portal, which will need stricter session handling. |

---

## Outputs

| Phase | Artifact | Status |
|-------|----------|--------|
| 0 | `research.md` | Already exists; unchanged |
| 1 | `data-model.md` | Updated — drops `class_type`/`max_students`, requires `name` + `duration_minutes` |
| 1 | `contracts/api.md` | Updated — class endpoints reflect new shape |
| 1 | `contracts/ui.md` | Updated — adds makeup-badge contract and class-form change |
| 1 | `quickstart.md` | Unchanged shape; minor narrative tweaks deferred to `/speckit-tasks` |
| 1 | `CLAUDE.md` SPECKIT block | Unchanged (already points to this plan) |
