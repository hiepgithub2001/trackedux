# Implementation Plan: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Branch**: `003-flexible-course-package` | **Date**: 2026-04-27 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/003-flexible-course-package/spec.md`

## Summary

A feature that restructures course packages from fixed-type presets (12/24/36) to a flexible model where admin enters an arbitrary lesson count, links packages to specific classes, and categorises them by an admin-managed "Lesson Kind" vocabulary. It also introduces a new "Classes" navigation tab with human-readable display IDs, per-lesson pricing on classes, and auto-fill tuition calculation on the package form. The `skill_level` field is removed from Student.

The architecture reuses the existing FastAPI backend + React/Vite frontend. Changes span: new `LessonKind` entity, restructured `Package` schema, new `tuition_fee_per_lesson` on `ClassSession`, new backend endpoints, a new frontend `classes` feature module, and a reworked package creation form in the `tuition` module.

## Technical Context

**Language/Version**:
- Backend: Python 3.11+ (`backend/pyproject.toml` requires-python `>=3.11`)
- Frontend: Node 20+ (Vite 8 / React 19 toolchain)

**Primary Dependencies**:
- Backend: FastAPI ≥ 0.115, SQLAlchemy 2 (async) + asyncpg, Pydantic 2, Alembic 1.13+, python-jose (JWT), passlib[bcrypt], python-multipart
- Frontend: React 19, Vite 8, Ant Design 6, `@fullcalendar/react` (daygrid + timegrid), `@tanstack/react-query` 5, `react-i18next` 17, `react-router-dom` 7, axios, dayjs, `vite-plugin-pwa`

**Storage**: PostgreSQL 16+ (async via asyncpg). Migrations managed by Alembic with sequential numbering (`001_…`, `002_…`). Next migration: `012_…`.

**Testing**:
- Backend: pytest, pytest-asyncio, httpx async client, testcontainers[postgres]
- Frontend: Playwright (E2E, already configured via `playwright.config.js`)

**Target Platform**: Linux server (backend), modern browsers + installable PWA on Android/iOS/desktop (frontend). Vietnamese-language primary users.

**Project Type**: Web application (frontend + backend separation)

**Performance Goals**:
- Class listing / package endpoints: p95 < 200 ms for ≤ 100 classes
- Lesson kind typeahead: < 100 ms response
- Package creation (with inline lesson kind create): < 500 ms

**Constraints**:
- Online-only for Phase 1 (no offline data cache; PWA is installability + asset cache only)
- All money stored as `BIGINT` VND (no decimals)
- Bilingual UI (vi / en), no untranslated strings
- Sessions never time out (spec 001 clarification)
- Package table is dropped and rebuilt — no data migration

**Scale/Scope**:
- Initial: ~30 students, ~50 classes, ~100 packages over time
- ~3 new/modified entities, ~10 new/modified REST endpoints, ~2 new/modified frontend feature modules

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project constitution (`.specify/memory/constitution.md`) currently contains only template placeholders (no ratified principles). No constitutional gates can be enforced.

| Gate | Status | Notes |
|------|--------|-------|
| Constitutional principles | **N/A — Unfilled** | `constitution.md` is the unedited template. Recommend running `/speckit-constitution` to ratify principles before further work. |
| Spec clarifications complete | ✅ Pass | Session 2026-04-27 resolved all ambiguities; all integrated into spec. |
| Tech stack matches existing repo | ✅ Pass | Plan reuses existing backend/frontend stacks; no new framework introduced. |
| Destructive migration acceptable | ✅ Pass | Spec explicitly states no production data; package table drop is sanctioned. |
| Dependency on spec 001 | ✅ Pass | Spec 001 classes, enrollment, attendance, and auth infrastructure are already implemented in the codebase. |

**Action item (advisory, not blocking)**: Ratify the constitution to enable real gate enforcement on subsequent specs.

## Project Structure

### Documentation (this feature)

```text
specs/003-flexible-course-package/
├── plan.md              # This file (/speckit-plan output)
├── research.md          # Phase 0 — technology decisions
├── data-model.md        # Phase 1 — entity definitions
├── quickstart.md        # Phase 1 — manual smoke flow
├── contracts/
│   ├── api.md           # Phase 1 — REST endpoint contracts
│   └── ui.md            # Phase 1 — UI contracts
└── tasks.md             # Phase 2 output (/speckit-tasks — NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── main.py                # FastAPI app entrypoint (unchanged)
│   ├── core/                  # Config, security (JWT, hashing), deps (unchanged)
│   ├── db/                    # Async engine, session factory (unchanged)
│   ├── models/
│   │   ├── __init__.py                 # ← add LessonKind import
│   │   ├── student.py                  # ← drop skill_level column
│   │   ├── class_session.py            # ← add tuition_fee_per_lesson (BIGINT VND)
│   │   ├── class_enrollment.py         # (unchanged)
│   │   ├── lesson_kind.py              # ← NEW: LessonKind model
│   │   ├── package.py                  # ← restructured: drop package_type, add class_session_id FK, lesson_kind_id FK, rename total_sessions→number_of_lessons
│   │   ├── payment_record.py           # (unchanged)
│   │   ├── attendance.py               # (unchanged)
│   │   └── renewal_reminder.py         # (unchanged)
│   ├── schemas/
│   │   ├── class_session.py            # ← add tuition_fee_per_lesson to create/response; add display_id to response
│   │   ├── lesson_kind.py              # ← NEW: LessonKind schemas
│   │   ├── package.py                  # ← restructured: new create/response shapes
│   │   └── student.py                  # ← drop skill_level from all schemas
│   ├── crud/
│   │   ├── class_session.py            # ← add display_id derivation logic, fee queries
│   │   ├── lesson_kind.py              # ← NEW: find-or-create, list, search
│   │   └── package.py                  # ← restructured: enrollment validation, class+kind linking
│   ├── services/
│   │   └── tuition_service.py          # ← updated for new package shape
│   ├── api/
│   │   ├── __init__.py                 # ← register lesson_kinds router
│   │   ├── classes.py                  # ← add tuition_fee fields; add display_id to list response
│   │   ├── packages.py                 # ← restructured endpoints with enrollment checks
│   │   ├── lesson_kinds.py             # ← NEW: GET /lesson-kinds (list + search)
│   │   └── students.py                 # ← drop skill_level references
│   └── scripts/                        # Seed script for initial lesson kinds
├── alembic/
│   └── versions/
│       └── 012_flexible_course_package.py  # NEW: drop+rebuild packages, add lesson_kinds, add tuition_fee_per_lesson to class_sessions, drop skill_level from students
└── tests/
    ├── unit/                           # Tests for display_id derivation, lesson kind normalization
    ├── integration/                    # Tests for package create with enrollment check, inline kind create
    └── contract/                       # OpenAPI drift checks

frontend/
├── src/
│   ├── api/                            # ← add lesson-kinds hooks, update packages hooks, update classes hooks
│   ├── features/
│   │   ├── classes/                    # ← NEW: ClassesPage (list), ClassDetail (enhanced)
│   │   ├── schedule/                   # ← ClassForm: add tuition_fee_per_lesson input
│   │   ├── tuition/                    # ← TuitionPage: restructured package form with class picker, kind typeahead, auto-fill fee
│   │   └── students/                   # ← drop skill_level from forms and detail views
│   ├── i18n/
│   │   ├── vi.json                     # ← add classes, lesson-kind, package-form translations
│   │   └── en.json                     # ← same
│   └── routes/
│       └── index.jsx                   # ← add /classes route
└── tests/                              # Playwright E2E specs
```

**Structure Decision**: Extending the existing two-tree layout (`backend/` + `frontend/`). No restructuring — the plan adds files within existing directory conventions. The `classes` frontend feature is new (currently class management is within `schedule`); the `tuition` module is restructured.

## Phase 0 — Research

### Research Tasks

| # | Unknown / Question | Resolution |
|---|-------------------|------------|
| 1 | Display ID derivation strategy — compute at query time vs. store a materialized column? | **Decision**: Compute at query time. **Rationale**: The display ID depends on mutable values (teacher name, day, time) and must reflect current values per FR-003. A materialized column would require triggers on teacher rename and class reschedule — excessive complexity for ~50 classes. The derivation is a simple string concatenation with a window function for disambiguator, easily done in Python after loading the class + teacher. **Alternatives rejected**: (a) Stored `display_id` column with trigger-based updates — complex to maintain, error-prone on cascading renames; (b) Database-generated column — PostgreSQL generated columns can't reference other tables. |
| 2 | Lesson Kind uniqueness enforcement — database-level UNIQUE vs. application check? | **Decision**: Database-level `UNIQUE` constraint on a `LOWER(TRIM(name))` functional index, plus application-layer normalization before insert. **Rationale**: Concurrent inline-creates (SC-008) require database-level uniqueness to avoid race conditions. The application normalizes whitespace and lowercases before querying, then does `INSERT ... ON CONFLICT DO NOTHING` + `SELECT` (find-or-create pattern). **Alternatives rejected**: Application-only check — susceptible to TOCTOU races under concurrency. |
| 3 | Package table rebuild strategy — `DROP TABLE` + `CREATE TABLE` vs. rename+recreate? | **Decision**: The migration will: (1) drop `renewal_reminders` (FK → packages), (2) drop `payment_records` (FK → packages), (3) drop `packages`, (4) recreate `packages` with new schema, (5) recreate `payment_records` with FK, (6) recreate `renewal_reminders` with FK. **Rationale**: Spec clarification explicitly sanctions full data loss. Dropping dependent tables avoids FK constraint issues. **Alternatives rejected**: Column-by-column ALTER — more migrations, same data loss, more error-prone. |
| 4 | Auto-fill fee UX — when to trigger recomputation? | **Decision**: Frontend `useEffect` watches `selectedClass` and `numberOfLessons`; if both are set and `isManualFeeEdit` is false, recompute `tuitionFee = class.tuition_fee_per_lesson * numberOfLessons`. Once user types in the fee field, set `isManualFeeEdit = true`. A "reset" button sets it back to false and triggers recompute. **Rationale**: Matches the spec's "auto-fill unless manually edited" semantics exactly. **Alternatives rejected**: Server-side computation on each keystroke — unnecessary latency for a multiplication. |
| 5 | Class deletion guard — how to check for referencing packages? | **Decision**: Before deleting a class, query `SELECT COUNT(*) FROM packages WHERE class_session_id = ?`. If > 0, return 409. **Rationale**: Simple, correct, no performance concern at this scale. **Alternatives rejected**: Database-level `ON DELETE RESTRICT` — also correct, but the error message would be a raw DB error rather than a friendly API response. We'll add both (DB constraint for safety + application check for UX). |

**Output**: `research.md` generated — all unknowns resolved.

## Phase 1 — Design & Contracts

### 1. Data Model (recorded in `data-model.md`)

| Entity | Change Type | Summary |
|--------|-------------|---------|
| `LessonKind` | **NEW** | Append-only vocabulary table: `id` (UUID PK), `name` (String 100, NOT NULL), `name_normalized` (String 100, UNIQUE functional index on `LOWER(TRIM(name))`), `created_at`, `updated_at`. No `is_active` flag. |
| `ClassSession` | **MODIFIED** | Add `tuition_fee_per_lesson` (BIGINT, nullable initially for legacy rows, CHECK > 0 when NOT NULL, ceiling 100,000,000 VND). Display ID is a computed property, not stored. |
| `Package` | **RESTRUCTURED** | Drop `package_type` column. Add `class_session_id` (UUID FK → `class_sessions.id`, NOT NULL), `lesson_kind_id` (UUID FK → `lesson_kinds.id`, NOT NULL). Rename `total_sessions` → `number_of_lessons`. Keep `remaining_sessions`, `price` (renamed conceptually to `tuition_fee` but column name stays `price` for migration simplicity), `payment_status`, `is_active`, `reminder_status`, `started_at`, `expired_at`. Add FK constraint `ON DELETE RESTRICT` for both `class_session_id` and `lesson_kind_id`. |
| `Student` | **MODIFIED** | Drop `skill_level` column. The `personality_notes` field (Text, nullable) serves as the free-text notes field with updated placeholder. |
| `PaymentRecord` | **REBUILT** | Same schema as before (FK → new `packages` table). No structural change. |
| `RenewalReminder` | **REBUILT** | Same schema as before (FK → new `packages` table). No structural change. |

### 2. API Contracts (recorded in `contracts/api.md`)

| Endpoint | Method | Change |
|----------|--------|--------|
| `/api/v1/lesson-kinds` | GET | **NEW** — List all lesson kinds; optional `?search=` query param for typeahead (case-insensitive substring match). Returns `[{id, name, created_at}]`. |
| `/api/v1/classes` | GET | **MODIFIED** — Response includes `tuition_fee_per_lesson` (admin only; null for staff/parent), `display_id` (computed string), `enrolled_count` (integer). |
| `/api/v1/classes` | POST | **MODIFIED** — Request body adds optional `tuition_fee_per_lesson` (positive integer, ceiling 100M VND). |
| `/api/v1/classes/{id}` | PUT | **MODIFIED** — Update body adds optional `tuition_fee_per_lesson`. |
| `/api/v1/classes/{id}` | DELETE | **MODIFIED** — Returns 409 if any package (active or historical) references this class. |
| `/api/v1/packages` | GET | **MODIFIED** — Response shape: drop `package_type`; add `class_session_id`, `class_display_id`, `lesson_kind_id`, `lesson_kind_name`, `number_of_lessons`. Fee field visible to admin only. |
| `/api/v1/packages` | POST | **MODIFIED** — Request body: `{student_id, class_session_id, number_of_lessons, lesson_kind_name, tuition_fee}`. Inline lesson kind creation is atomic. Enrollment validation: 422 if student not enrolled in class. |
| `/api/v1/students` | GET/POST/PUT | **MODIFIED** — Drop `skill_level` from request/response schemas. |

### 3. UI Contracts (recorded in `contracts/ui.md`)

| Surface | Change |
|---------|--------|
| **Classes tab** (NEW) | New nav item between Schedule and Attendance. Table columns: Display ID, Teacher, Weekday, Time, Duration, Enrolled, Fee/Lesson (admin only). Sortable by teacher, weekday. Click row → class detail. "Create Class" button (admin only). |
| **Class create/edit form** | Add `tuition_fee_per_lesson` field: Ant Design `InputNumber` with VND formatting, required, positive integer, max 100,000,000. Admin-only visibility. |
| **Package creation form** | Five inputs: Student (Select), Class (AutoComplete by display ID), Number of Lessons (InputNumber, positive int, max 500), Lesson Kind (AutoComplete typeahead with inline-create), Tuition Fee (InputNumber with VND formatting, auto-fill logic). No 12/24/36 presets. |
| **Tuition list** | Add columns: Class (display ID), Lesson Kind. Hide fee from staff. |
| **Student forms** | Drop `skill_level` field. Update `personality_notes` placeholder to hint about skill level context. |
| **Student detail** | Drop `skill_level` display. |
| **Student list** | Drop `skill_level` column. |

### 4. Quickstart

```text
1. Start backend:  cd backend && uvicorn app.main:app --reload
2. Run migrations: cd backend && alembic upgrade head
3. Seed data:      cd backend && python -m app.scripts.seed
4. Start frontend: cd frontend && npm run dev
5. Log in as admin (admin@piano.vn / admin123)
6. Navigate to Classes tab → verify all classes show display IDs and per-lesson fees
7. Create a new class with tuition_fee_per_lesson = 200000 VND
8. Navigate to Tuition → Assign Package:
   - Pick a student enrolled in the class
   - Pick the class (typeahead by display ID)
   - Enter number_of_lessons = 10
   - Verify auto-fill: tuition_fee = 2,000,000 VND
   - Type a new lesson kind name → verify inline create
   - Save → verify package appears in list with class display ID + lesson kind
9. Take attendance → verify remaining sessions decrement
```

### 5. Agent context update

The `AGENTS.md` SPECKIT block needs to be updated to point to this plan.

## Post-Design Constitution Re-check

| Gate | Status | Notes |
|------|--------|-------|
| Constitutional principles | **N/A — Unfilled** | Same as pre-check. No new violations introduced. |
| Backwards compatibility | ⚠ Destructive migration | Package table is dropped and rebuilt. Sanctioned by spec clarification (no production data). |
| Spec drift | ✅ Pass | Spec, data model, and contracts are mutually consistent. |
| Test coverage plan | ✅ Pass | Existing test layout (unit / integration / contract / E2E) covers the modified surfaces. |

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|--------------------------------------|
| Destructive schema rebuild (drop + recreate `packages`, `payment_records`, `renewal_reminders`) | Spec explicitly removes fixed `package_type` enum and introduces required FKs to `class_sessions` and `lesson_kinds`. In-place ALTER would require nullable FKs, data backfill logic, and enum removal — all for zero rows worth preserving. | Column-by-column ALTER was considered but produces more migration steps, same data loss, and higher error risk for no benefit since there's no production data. |
| Computed display ID (no stored column) | Display ID must reflect current teacher name/schedule per FR-003. A stored column would need triggers on teacher and class updates. | Materialized column with triggers — complex, fragile, unnecessary at this scale (~50 classes). |
| Case-insensitive functional index on `lesson_kinds.name` | Required to satisfy SC-008 (concurrent inline-create convergence). | Application-only uniqueness check — susceptible to race conditions. |

---

## Outputs

| Phase | Artifact | Status |
|-------|----------|--------|
| 0 | `research.md` | Generated — 5 decisions documented |
| 1 | `data-model.md` | Generated — 3 new/modified entities |
| 1 | `contracts/api.md` | Generated — 8 endpoint contracts |
| 1 | `contracts/ui.md` | Generated — 6 UI surface contracts |
| 1 | `quickstart.md` | Generated — 9-step smoke flow |
| 1 | `AGENTS.md` SPECKIT block | Updated to point to this plan |
