# Implementation Plan: Class / Lesson Separation

**Branch**: `008-class-lesson-separation` | **Date**: 2026-04-30 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/008-class-lesson-separation/spec.md`

---

## Summary

Separate the monolithic `ClassSession` (which fuses cohort + schedule) into two independent entities — **Class** (cohort, roster, tuition) and **Lesson** (schedule, recurrence rule) — connected via a FK. Lesson occurrences remain **virtual** (computed at read time via `python-dateutil` RRULE expansion) and are lazily persisted as `LessonOccurrence` records only when an admin takes a mutating action (attendance, cancel, reschedule). Existing `ClassSession` data is migrated automatically in Alembic migration `021` with zero admin intervention required.

---

## Technical Context

**Language/Version**: Python 3.12 (backend), Node 20 + React 18 (frontend)
**Primary Dependencies**: FastAPI 0.115+, SQLAlchemy 2.0 async, Alembic 1.13+, asyncpg, Pydantic 2, `python-dateutil` 2.9+ (new), Ant Design 5, FullCalendar 6, React Query 5
**Storage**: PostgreSQL (asyncpg driver); all new tables follow UUID PK + TimestampMixin + center_id pattern
**Testing**: pytest 8 + pytest-asyncio + testcontainers[postgres] (backend); Playwright (E2E)
**Target Platform**: Linux server (Docker/Compose); frontend served via Vite dev server / static build
**Project Type**: Web application (React SPA + FastAPI REST API + PostgreSQL)
**Performance Goals**: Weekly schedule API response ≤ 200ms p95 for up to 50 lessons per center per week; occurrence expansion is O(1) per lesson per week (bounded work per request — FR-004a)
**Constraints**: No background jobs introduced; multi-center isolation preserved (center_id on every new table); attendance + ledger records must survive migration intact
**Scale/Scope**: Tens of centers; ~10–50 classes per center; weekly schedule query bounded to one week at a time

---

## Constitution Check

*Constitution template is unpopulated (placeholder only — no ratified principles). No gates to evaluate. Re-check after Phase 1 design is complete.*

> **Post-Phase 1 re-evaluation**: No constitution violations identified. The design:
> - Adds no unnecessary abstractions (YAGNI: two new tables, one new service).
> - Preserves existing multi-center isolation pattern (`center_id` on all new tables).
> - Does not introduce background jobs (spec-mandated read-time-only model).
> - Migration is atomic via Alembic and preserves all historical data.

---

## Project Structure

### Documentation (this feature)

```text
specs/008-class-lesson-separation/
├── plan.md              ← this file
├── research.md          ← Phase 0 output
├── data-model.md        ← Phase 1 output
├── quickstart.md        ← Phase 1 output
├── contracts/
│   └── api.md           ← Phase 1 output
└── tasks.md             ← Phase 2 output (/speckit-tasks — NOT created here)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   ├── class_.py               # NEW — Class ORM model
│   │   ├── lesson.py               # NEW — Lesson ORM model
│   │   ├── lesson_occurrence.py    # NEW — LessonOccurrence ORM model
│   │   ├── class_enrollment.py     # MODIFY — re-FK to classes.id + enrolled_since/unenrolled_at
│   │   ├── attendance.py           # MODIFY — lesson_occurrence_id FK replaces class_session_id
│   │   └── tuition_ledger_entry.py # MODIFY — lesson_id FK replaces class_session_id
│   ├── schemas/
│   │   ├── class_.py               # NEW — Pydantic schemas (Create, Update, Response)
│   │   └── lesson.py               # NEW — Pydantic schemas + OccurrenceOverride
│   ├── crud/
│   │   ├── class_.py               # NEW — Class CRUD
│   │   └── lesson.py               # NEW — Lesson + occurrence CRUD
│   ├── services/
│   │   ├── recurrence_service.py   # NEW — compute_occurrences(), rrule helpers
│   │   └── schedule_service.py     # MODIFY — adapt conflict check to Lesson model
│   ├── api/
│   │   ├── classes.py              # REPLACE — new Class endpoints
│   │   ├── lessons.py              # NEW — Lesson + occurrence endpoints
│   │   ├── schedule.py             # MODIFY — weekly expansion via recurrence_service
│   │   └── attendance.py           # MODIFY — lesson_id param replaces class_session_id
│   └── main.py                     # MODIFY — register lessons router
└── alembic/versions/
    └── 021_class_lesson_separation.py   # NEW — migration

frontend/
└── src/
    ├── api/
    │   ├── classes.js              # MODIFY — Class API calls
    │   └── lessons.js              # NEW — Lesson + occurrence API calls
    └── features/
        ├── schedule/
        │   └── WeeklyCalendar.jsx  # MODIFY — week navigation, canceled/rescheduled display
        ├── classes/
        │   ├── ClassesPage.jsx     # MODIFY — list Classes
        │   └── ClassDetail.jsx     # MODIFY — class + lesson list + occurrence actions
        └── lessons/
            ├── LessonForm.jsx      # NEW — create/edit lesson with RRULE builder
            └── OccurrenceOverrideModal.jsx  # NEW — cancel/reschedule/revert
```

**Structure Decision**: Web application (Option 2 from template). Existing `backend/` + `frontend/` layout is retained. New source files follow established naming conventions (`snake_case` for Python modules, `PascalCase.jsx` for React components).

---

## Complexity Tracking

> No Constitution violations — table omitted.

---

## Phase Roadmap

> The phases below are an implementation guide for `/speckit-tasks`. They reflect dependency order and parallelization opportunities.

### Phase A — Data Layer (Backend)
1. Add `python-dateutil` to `pyproject.toml`.
2. Create `Class`, `Lesson`, `LessonOccurrence` ORM models.
3. Modify `ClassEnrollment`, `AttendanceRecord`, `TuitionLedgerEntry` models.
4. Write Alembic migration `021` (schema + data migration from `class_sessions`).
5. Apply migration; verify all existing data is preserved.

### Phase B — Service Layer (Backend)
1. Create `recurrence_service.py` (`compute_occurrences`, `VirtualOccurrence`, RRULE helpers).
2. Adapt `schedule_service.check_scheduling_conflicts` to work with `Lesson` model.
3. Create `attendance_service` updates (accept `lesson_occurrence_id`).

### Phase C — API Layer (Backend)
1. New Pydantic schemas (`class_.py`, `lesson.py`).
2. New CRUD modules (`crud/class_.py`, `crud/lesson.py`).
3. Replace `api/classes.py` with Class endpoints.
4. New `api/lessons.py` (Lesson CRUD + occurrence override endpoints).
5. Update `api/schedule.py` to use `recurrence_service`.
6. Update `api/attendance.py` to use `lesson_id`.
7. Register new router in `main.py`.

### Phase D — Frontend
1. New/updated API client files (`classes.js`, `lessons.js`).
2. Update `WeeklyCalendar.jsx` — week navigation, canceled/rescheduled event rendering.
3. Update `ClassesPage.jsx` + `ClassDetail.jsx`.
4. New `LessonForm.jsx` (RRULE builder: weekly + optional COUNT/UNTIL).
5. New `OccurrenceOverrideModal.jsx` (cancel / reschedule / revert).

### Phase E — Testing & Migration Verification
1. Backend unit tests: `recurrence_service`, conflict detection, occurrence overlay.
2. Backend integration tests: all new API endpoints (pytest + testcontainers).
3. Migration smoke test: seed `class_sessions` → run migration → verify schedule renders.
4. Frontend E2E (Playwright): User Stories 1–4 from spec.

---

## Key Design Decisions (summary from research.md)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Recurrence engine | `python-dateutil` rrule | RFC 5545 compliant, on-demand expansion, no job required |
| Recurrence storage | RRULE string + `day_of_week` denormalized | Canonical + queryable for conflict detection |
| Occurrence persistence | Lazy (only on admin action) | Spec mandate; bounded DB growth |
| Override key | `(lesson_id, original_date)` | Immutable anchor; override always wins over rule |
| Edit scopes | Two separate PATCH operations | Clean REST boundary; series edit never touches occurrence records |
| Migration | Alembic `021` data migration | Atomic, zero-admin, preserves all history |
| Frontend week nav | FullCalendar `datesSet` → React Query key | Single hook covers all navigation paths |
