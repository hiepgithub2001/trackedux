# Implementation Plan: Multi-Tenant Edu-Center Scalability System

**Branch**: `004-edu-center-scalability` | **Date**: 2026-04-28 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `/specs/004-edu-center-scalability/spec.md`

## Summary

A feature that converts the existing single-tenant Piano Center Management System into a multi-tenant platform. A new `superadmin` role manages edu-centers through a dedicated system console. Each edu-center is provisioned as an isolated tenant with a unique Center Code (`CTR-NNN`), and all operational data (students, teachers, classes, packages, etc.) is scoped to its center via a `center_id` FK on every tenant table. Center admin accounts continue to use the existing app UI/UX, transparently scoped to their center only.

The architecture extends the existing FastAPI backend + React/Vite frontend with: a new `centers` table, `center_id` FK columns on all tenant-scoped tables, a new `superadmin` role, a dedicated `/system` route subtree for the superadmin console, and row-level filtering in all CRUD functions.

## Technical Context

**Language/Version**:
- Backend: Python 3.11+ (`backend/pyproject.toml` requires-python `>=3.11`)
- Frontend: Node 20+ (Vite 8 / React 19 toolchain)

**Primary Dependencies**:
- Backend: FastAPI ≥ 0.115, SQLAlchemy 2 (async) + asyncpg, Pydantic 2, Alembic 1.13+, python-jose (JWT), passlib[bcrypt], python-multipart, pydantic-settings
- Frontend: React 19, Vite 8, Ant Design 6, `@tanstack/react-query` 5, `react-i18next` 17, `react-router-dom` 7, axios, dayjs, `vite-plugin-pwa`

**Storage**: PostgreSQL 16+ (async via asyncpg). Migrations managed by Alembic with sequential numbering. Next migration: `013_…`.

**Testing**:
- Backend: pytest, pytest-asyncio, httpx async client, testcontainers[postgres]
- Frontend: Playwright (E2E, already configured via `playwright.config.js`)

**Target Platform**: Linux server (backend), modern browsers + installable PWA on Android/iOS/desktop (frontend). Vietnamese-language primary users.

**Project Type**: Web application (frontend + backend separation)

**Performance Goals**:
- Center list endpoint (superadmin): p95 < 200 ms for ≤ 100 centers
- All existing tenant-scoped endpoints: p95 regression budget ≤ 20 ms (cost of added `center_id` filter)
- Center creation (including provisioning admin user): < 1 s

**Constraints**:
- Existing data MUST be preserved — all current rows migrate to `CTR-001 Legacy Center`
- `center_id` filter is NON-OPTIONAL in all CRUD layer functions that query tenant-scoped tables
- No email/SMTP integration in this phase — credentials delivered via "show once" API response
- Sessions never time out (inherited from spec 001 clarification)
- Bilingual UI (vi / en), no untranslated strings
- `superadmin` has NO access to any center's operational data

**Scale/Scope**:
- Initial: 1 superadmin, ≤ 100 centers, each with existing scale (~30 students, ~50 classes)
- ~1 new entity (`Center`), `center_id` FK on ~11 tables, ~4 new REST endpoints, ~2 new frontend feature modules (`/system` console + route guard)

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`.specify/memory/constitution.md`) contains only template placeholders (no ratified principles). No constitutional gates can be enforced.

| Gate | Status | Notes |
|------|--------|-------|
| Constitutional principles | **N/A — Unfilled** | `constitution.md` is the unedited template. Recommend running `/speckit-constitution` to ratify. |
| Spec clarifications complete | ✅ Pass | All 6 research decisions resolved in `research.md`; no [NEEDS CLARIFICATION] markers remain. |
| Tech stack matches existing repo | ✅ Pass | Plan reuses existing backend/frontend stacks; no new framework introduced. |
| Destructive migration acceptable | ✅ Pass (safe) | All existing rows are migrated to Legacy Center (`CTR-001`), not dropped. |
| Data isolation correctness | ✅ Pass | Row-level `center_id` filtering at CRUD layer; superadmin blocked from operational endpoints. |
| Dependency on prior specs | ✅ Pass | Spec 001–003 auth, RBAC, class, and package infrastructure are already in the codebase. |

**Action item (advisory, not blocking)**: Ratify the constitution to enable real gate enforcement on subsequent specs.

## Project Structure

### Documentation (this feature)

```text
specs/004-edu-center-scalability/
├── plan.md              # This file (/speckit-plan output)
├── spec.md              # Feature specification
├── research.md          # Phase 0 — 6 decisions documented
├── data-model.md        # Phase 1 — entity definitions
├── quickstart.md        # Phase 1 — 25-step smoke flow
├── contracts/
│   ├── api.md           # Phase 1 — REST endpoint contracts
│   └── ui.md            # Phase 1 — UI contracts
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── __init__.py                     # ← add Center import
│   │   ├── center.py                       # ← NEW: Center model
│   │   ├── user.py                         # ← add center_id FK; extend role values
│   │   ├── student.py                      # ← add center_id FK
│   │   ├── teacher.py                      # ← add center_id FK
│   │   ├── class_session.py                # ← add center_id FK
│   │   ├── class_enrollment.py             # ← add center_id FK
│   │   ├── package.py                      # ← add center_id FK
│   │   ├── payment_record.py               # ← add center_id FK
│   │   ├── attendance.py                   # ← add center_id FK
│   │   ├── renewal_reminder.py             # ← add center_id FK
│   │   ├── lesson_kind.py                  # ← add center_id FK
│   │   └── student_status_history.py       # ← add center_id FK
│   ├── schemas/
│   │   ├── center.py                       # ← NEW: CenterCreate, CenterResponse, CredentialsResponse
│   │   └── user.py                         # ← add center_id, center_code to UserResponse
│   ├── crud/
│   │   ├── center.py                       # ← NEW: create_center, list_centers, get_center, patch_center
│   │   ├── user.py                         # ← add center_id param to create; ensure get_user_by_id unchanged
│   │   ├── student.py                      # ← add center_id filter to all list/get functions
│   │   ├── teacher.py                      # ← add center_id filter
│   │   ├── class_session.py                # ← add center_id filter
│   │   ├── class_enrollment.py             # ← add center_id filter
│   │   ├── package.py                      # ← add center_id filter
│   │   ├── payment_record.py               # ← add center_id filter
│   │   ├── attendance.py                   # ← add center_id filter
│   │   ├── lesson_kind.py                  # ← add center_id filter
│   │   └── renewal_reminder.py             # ← add center_id filter
│   ├── core/
│   │   └── deps.py                         # ← add get_center_id() dependency; add require_superadmin()
│   ├── api/
│   │   ├── __init__.py                     # ← register system router
│   │   ├── system/
│   │   │   ├── __init__.py                 # ← NEW: /system router prefix
│   │   │   └── centers.py                  # ← NEW: POST/GET/PATCH /system/centers
│   │   ├── students.py                     # ← inject center_id into all CRUD calls
│   │   ├── teachers.py                     # ← inject center_id
│   │   ├── classes.py                      # ← inject center_id
│   │   ├── packages.py                     # ← inject center_id
│   │   ├── attendance.py                   # ← inject center_id
│   │   ├── lesson_kinds.py                 # ← inject center_id
│   │   └── dashboard.py                    # ← inject center_id
│   └── services/
│       └── center_service.py               # ← NEW: orchestrates center creation + admin provisioning
├── alembic/
│   └── versions/
│       └── 013_multi_tenant_centers.py     # ← NEW: adds centers table, center_id FKs, migrates existing data
└── tests/
    ├── unit/
    │   └── test_center_code_generation.py  # Center code auto-increment logic
    ├── integration/
    │   ├── test_center_crud.py             # Create, list, patch center
    │   └── test_tenant_isolation.py        # Cross-center data access attempts return 0 results / 403
    └── contract/
        └── test_superadmin_endpoints.py    # OpenAPI contract for /system/centers

frontend/
├── src/
│   ├── auth/
│   │   ├── AuthContext.jsx                 # ← add center_id, center_code to user state
│   │   └── SuperadminRoute.jsx             # ← NEW: redirects non-superadmin to /
│   ├── features/
│   │   └── system/                         # ← NEW: superadmin console feature module
│   │       ├── CenterListPage.jsx          # Center list + search + deactivate
│   │       └── CenterFormPage.jsx          # Add center form + credentials modal
│   ├── api/
│   │   └── centers.js                      # ← NEW: createCenter, listCenters, patchCenter
│   ├── i18n/
│   │   ├── vi.json                         # ← add system, center management translations
│   │   └── en.json                         # ← same
│   └── routes/
│       └── index.jsx                       # ← add /system route subtree
└── tests/
    └── e2e/
        ├── superadmin-center-create.spec.js  # Full registration + credential display flow
        └── tenant-isolation.spec.js          # Center admin cannot see other center's data
```

**Structure Decision**: Extending the existing two-tree layout (`backend/` + `frontend/`). A new `system/` API sub-router groups superadmin-only endpoints under `/api/v1/system/`. The frontend gains a `features/system/` module with its own isolated layout (no standard app sidebar).

## Phase 0 — Research

### Research Tasks

| # | Unknown / Question | Resolution |
|---|-------------------|------------|
| 1 | Multi-tenancy strategy — shared DB vs. schema-per-tenant vs. DB-per-tenant? | **Row-level tenancy**: `center_id` FK on all tenant tables, CRUD-layer filtering. Shared DB. See `research.md` Decision 1. |
| 2 | System Admin role — new role value vs. separate table? | **New `superadmin` role** in existing `users.role` String column, `center_id = NULL`. See Decision 2. |
| 3 | Center entity design — what columns, what codes format? | **New `centers` table** with `code` = `CTR-NNN` auto-generated. See Decision 3. |
| 4 | Existing data migration strategy? | **Migrate to Legacy Center `CTR-001`** — all existing rows get `center_id` of the seeded legacy center. See Decision 4. |
| 5 | Center admin credential delivery? | **Show-once in API response** (no SMTP). See Decision 5. |
| 6 | Session invalidation on center deactivation? | **Immediate via DB-per-request auth check** — `is_active = false` on user; no token blocklist needed. See Decision 6. |

**Output**: `research.md` generated — 6 decisions documented.

## Phase 1 — Design & Contracts

### 1. Data Model (recorded in `data-model.md`)

| Entity | Change Type | Summary |
|--------|-------------|---------|
| `Center` | **NEW** | `id` (UUID PK), `name` (String 200, UNIQUE), `code` (String 20, UNIQUE, auto-generated `CTR-NNN`), `registered_by_id` (FK → users, nullable), `is_active` (Boolean), timestamps |
| `User` | **MODIFIED** | Add `center_id` (UUID FK → centers, nullable for superadmin); extend `role` to accept `superadmin` |
| `Student`, `Teacher`, `ClassSession`, `ClassEnrollment`, `Package`, `PaymentRecord`, `Attendance`, `RenewalReminder`, `LessonKind`, `StudentStatusHistory` | **MODIFIED** | Add `center_id` (UUID FK → centers, NOT NULL) on each |

### 2. API Contracts (recorded in `contracts/api.md`)

| Endpoint | Method | Change |
|----------|--------|--------|
| `/api/v1/system/centers` | POST | **NEW** — Create center + provision admin; returns credentials (show-once) |
| `/api/v1/system/centers` | GET | **NEW** — List all centers (superadmin only); optional `?search=`, `?is_active=` |
| `/api/v1/system/centers/{id}` | GET | **NEW** — Get single center details |
| `/api/v1/system/centers/{id}` | PATCH | **NEW** — Update name or deactivate/reactivate |
| `/api/v1/auth/login` | POST | **MODIFIED** — `UserResponse` adds `center_id`, `center_code` fields |
| All tenant endpoints | GET/POST/PUT/DELETE | **MODIFIED** — Invisible `center_id` filter added at CRUD layer |

### 3. UI Contracts (recorded in `contracts/ui.md`)

| Surface | Change |
|---------|--------|
| **`/system/centers`** (NEW) | Superadmin-only page: center list table with search, status badge, deactivate/reactivate actions |
| **`/system/centers/new`** (NEW) | Add center form (4 fields) + "show once" credentials modal on success |
| **Login page** | No visual change; post-login redirect updated: superadmin → `/system/centers` |
| **Existing app** | No visual change for center admin; all data transparently scoped to their center |
| **`SuperadminRoute`** (NEW) | Route guard redirecting non-superadmin users away from `/system` |

### 4. Quickstart (recorded in `quickstart.md`)

25-step smoke flow covering: superadmin login → create center → center admin login → data isolation verification → deactivation → reactivation.

### 5. Agent context update

`AGENTS.md` SPECKIT block updated to point to this plan.

## Post-Design Constitution Re-check

| Gate | Status | Notes |
|------|--------|-------|
| Constitutional principles | **N/A — Unfilled** | Same as pre-check. No new violations introduced. |
| Data preservation | ✅ Pass | Existing rows migrated safely to Legacy Center. |
| Tenant isolation completeness | ✅ Pass | `center_id` on all 11 tenant tables; CRUD-layer enforcement; superadmin blocked from operational endpoints. |
| Spec drift | ✅ Pass | Spec, data model, and contracts are mutually consistent. |
| Test coverage plan | ✅ Pass | Unit (code generation), integration (CRUD + isolation), contract (OpenAPI), E2E (Playwright) all scoped. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| `center_id` FK on 11 tables (schema-wide change) | Tenant isolation requires every tenant-scoped query to filter by center. Adding `center_id` to each table is the minimal correct approach. | Deriving `center_id` from join chains (e.g., `student → class_enrollment → class_session → center`) would require multi-join queries on every list endpoint and is error-prone — a missed join leaks cross-center data. |
| Denormalized `center_id` on child tables (attendance, payment_records, etc.) | Fast, safe isolation without multi-hop joins. Each table is independently filterable. | Normalizing through parent FK chains trades query simplicity for correctness risk; at this scale denormalization cost is negligible. |

---

## Outputs

| Phase | Artifact | Status |
|-------|----------|--------|
| 0 | `research.md` | ✅ Generated — 6 decisions documented |
| 1 | `data-model.md` | ✅ Generated — 1 new + 11 modified entities |
| 1 | `contracts/api.md` | ✅ Generated — 4 new + 1 modified + N transparent endpoint contracts |
| 1 | `contracts/ui.md` | ✅ Generated — 2 new surfaces + routing changes |
| 1 | `quickstart.md` | ✅ Generated — 25-step smoke flow |
| 1 | `AGENTS.md` SPECKIT block | ✅ Updated |
