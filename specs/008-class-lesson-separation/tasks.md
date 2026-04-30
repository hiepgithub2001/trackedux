# Tasks: Class / Lesson Separation (008)

**Branch**: `008-class-lesson-separation` | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Install new dependency and wire new routers into the app.

- [X] T001 Add `python-dateutil>=2.9.0` to `[project.dependencies]` in `backend/pyproject.toml` and run `pip install python-dateutil` in the venv
- [X] T002 Create empty placeholder files to establish module structure: `backend/app/models/class_.py`, `backend/app/models/lesson.py`, `backend/app/models/lesson_occurrence.py`, `backend/app/schemas/class_.py`, `backend/app/schemas/lesson.py`, `backend/app/crud/class_.py`, `backend/app/crud/lesson.py`, `backend/app/services/recurrence_service.py`, `backend/app/api/lessons.py`, `frontend/src/api/lessons.js`, `frontend/src/features/lessons/` directory
- [X] T003 Register `lessons` router in `backend/app/main.py` (import `from app.api import lessons` and add `app.include_router(lessons.router)`)

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: New ORM models, Alembic migration, and recurrence service — every user story depends on these.

⚠️ **CRITICAL**: No user story work can begin until this phase is complete.

- [X] T004 Implement `Class` ORM model in `backend/app/models/class_.py` — fields: `id` (UUID PK), `name` VARCHAR(200), `teacher_id` UUID FK→teachers, `tuition_fee_per_lesson` BIGINT NULL, `lesson_kind_id` UUID FK→lesson_kinds NULL, `is_active` BOOL DEFAULT TRUE, `center_id` UUID FK→centers; relationships: `teacher` (selectin), `enrollments` (selectin), `lessons` (selectin); indexes on `center_id`, `teacher_id`, `is_active`
- [X] T005 [P] Implement `Lesson` ORM model in `backend/app/models/lesson.py` — fields: `id` (UUID PK), `class_id` UUID FK→classes NULL, `teacher_id` UUID FK→teachers NOT NULL, `title` VARCHAR(200) NULL, `start_time` TIME NOT NULL, `duration_minutes` INT NOT NULL, `day_of_week` INT NULL, `specific_date` DATE NULL, `rrule` VARCHAR(500) NULL, `is_active` BOOL DEFAULT TRUE, `center_id` UUID FK→centers; relationships: `class_` (selectin), `teacher` (selectin), `occurrences` (selectin); indexes on `center_id`, `class_id`, `teacher_id`, `day_of_week`, `specific_date`
- [X] T006 [P] Implement `LessonOccurrence` ORM model in `backend/app/models/lesson_occurrence.py` — fields: `id` (UUID PK), `lesson_id` UUID FK→lessons NOT NULL, `original_date` DATE NOT NULL, `status` VARCHAR(20) DEFAULT 'active', `override_date` DATE NULL, `override_start_time` TIME NULL, `center_id` UUID FK→centers; unique constraint `(lesson_id, original_date)`; indexes on `(lesson_id, original_date)`, `center_id`, `original_date`
- [X] T007 Modify `backend/app/models/class_enrollment.py` — add `enrolled_since DATE NULL` and `unenrolled_at DATE NULL` columns; keep `class_session_id` FK temporarily (migration will rename it); add new `class_id UUID FK→classes NULL` column alongside old FK so both exist during migration
- [X] T008 [P] Register all new models in `backend/app/models/__init__.py` so Alembic autogenerate picks them up; import `Class`, `Lesson`, `LessonOccurrence` from their modules
- [X] T009 Write Alembic migration `021_class_lesson_separation.py` in `backend/alembic/versions/`
- [X] T010 Apply migration and verify: run `alembic upgrade head` in `backend/` ✅ ran successfully
- [X] T011 Implement `recurrence_service.py` in `backend/app/services/recurrence_service.py`
- [X] T012 [P] Implement Pydantic schemas in `backend/app/schemas/class_.py`
- [X] T013 [P] Implement Pydantic schemas in `backend/app/schemas/lesson.py`
- [X] T014 Implement CRUD in `backend/app/crud/class_.py`
- [X] T015 [P] Implement CRUD in `backend/app/crud/lesson.py`
- [X] T016 Adapt `backend/app/services/schedule_service.py` — now queries `lessons` table via `class_id`

**Checkpoint**: Foundation ready — user story phases can now begin.

---

## Phase 3: User Story 1 — Recurring Lesson for a Class (Priority: P1) 🎯 MVP

**Goal**: Admin creates a class and attaches a recurring lesson; weekly schedule shows computed occurrences per week.

**Independent Test**: Create class → POST /lessons (weekly RRULE 10 weeks) → GET /schedule/weekly for each of the 10 weeks → verify one occurrence per week at correct time with correct roster.

### Implementation for User Story 1

- [X] T017 [US1] Implement `GET /classes`, `POST /classes`, `GET /classes/{id}`, `PUT /classes/{id}`, `DELETE /classes/{id}` in `backend/app/api/classes.py`
- [X] T018 [P] [US1] Implement `POST /classes/{class_id}/enroll` and `DELETE /classes/{class_id}/enroll/{student_id}` in `backend/app/api/classes.py`
- [X] T019 [US1] Implement `GET /lessons`, `POST /lessons`, `GET /lessons/{id}` in `backend/app/api/lessons.py`
- [X] T020 [US1] Update `backend/app/api/schedule.py` — uses `list_lessons` + `compute_week_occurrences`
- [X] T021 [US1] Update `frontend/src/api/classes.js` — enrolled_since/unenrolled_at params added
- [X] T022 [P] [US1] Create `frontend/src/api/lessons.js` — full lesson CRUD + occurrence override functions
- [X] T023 [US1] Update `frontend/src/features/classes/ClassesPage.jsx` — Class-based columns, removed legacy schedule column
- [X] T024 [US1] Update `frontend/src/features/schedule/WeeklyCalendar.jsx` — datesSet→weekStart, cancel/reschedule styling, inline OccurrenceOverrideModal
- [X] T025 [US1] Create `frontend/src/features/lessons/LessonForm.jsx` — one-off/recurring toggle, RRULE builder, conflict display

**Checkpoint**: User Story 1 fully functional — create class + recurring lesson + see weekly schedule across all weeks.

---

## Phase 4: User Story 2 — One-off Lesson Alongside Recurring Series (Priority: P1)

**Goal**: Admin adds a one-time makeup/extra lesson to an existing class; both appear on the same week's schedule independently.

**Independent Test**: Class with recurring Monday lesson → POST /lessons (specific_date = Saturday) → GET /schedule/weekly for that week → both Monday and Saturday occurrences appear; mark attendance on Saturday → Monday occurrences unaffected.

### Implementation for User Story 2

- [X] T026 [US2] `POST /lessons` handles `specific_date` path correctly; unit tests added to `test_recurrence_service.py`
- [X] T027 [US2] Update `backend/app/api/attendance.py` — lazy LessonOccurrence creation on attendance mark
- [X] T028 [US2] Update `GET /attendance/session/{lesson_id}/{session_date}` — queries via `lesson_occurrence_id`
- [X] T029 [US2] Update `frontend/src/features/schedule/ClassDetail.jsx` — lessons list with type badge, Add Lesson button, LessonForm modal

**Checkpoint**: Both recurring and one-off lessons appear on schedule; attendance works on both independently.

---

## Phase 5: User Story 3 — Cancel or Reschedule a Single Occurrence (Priority: P2)

**Goal**: Admin can cancel or reschedule one occurrence of a recurring series without affecting siblings.

**Independent Test**: 10-week recurring lesson → cancel occurrence #5 → GET /schedule/weekly for week 5 → occurrence absent (or shown canceled); weeks 1–4 and 6–10 unaffected.

### Implementation for User Story 3

- [X] T030 [US3] `GET /lessons/{lesson_id}/occurrences/{original_date}` implemented in `backend/app/api/lessons.py`
- [X] T031 [US3] `PATCH /lessons/{lesson_id}/occurrences/{original_date}` implemented — cancel/reschedule/revert actions
- [X] T032 [US3] `compute_week_occurrences` override handling verified by 15 passing unit tests
- [X] T033 [P] [US3] Schedule API correctly applies override_date filtering (effective_date-based filtering in recurrence_service)
- [X] T034 [US3] OccurrenceOverrideModal integrated inline into `WeeklyCalendar.jsx`
- [X] T035 [US3] WeeklyCalendar eventClick opens override modal with lesson_id and original_date

**Checkpoint**: Per-occurrence cancel and reschedule work; sibling occurrences are unaffected; series-level data is unchanged.

---

## Phase 6: User Story 4 — Edit the Recurring Series (Priority: P3)

**Goal**: Admin changes series-level fields (time, day, pattern, end); past attended occurrences keep original data.

**Independent Test**: Recurring lesson → mark attendance on first 3 → PATCH /lessons/{id} (scope=series, new start_time) → future weeks show new time; weeks 1–3 LessonOccurrence records unchanged.

### Implementation for User Story 4

- [X] T036 [US4] `PATCH /lessons/{lesson_id}` (series scope) implemented in `backend/app/api/lessons.py`
- [X] T037 [US4] `test_series_edit_does_not_override_occurrence_record` test passes (15/15)
- [X] T038 [US4] ClassDetail.jsx shows lesson list with Edit action row (LessonForm modal handles series update via `updateLessonSeries`)

**Checkpoint**: Series edits apply only to virtual future occurrences; historical attendance records are locked.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Migration safety, conflict detection completeness, multi-center isolation, and edge-case handling.

- [X] T039 `lesson_occurrences` unique constraint `(lesson_id, original_date)` present in migration 021 via `UniqueConstraint`
- [X] T040 [P] `enrolled_since`/`unenrolled_at` roster filtering implemented in `schedule.py` event builder
- [X] T041 [P] Teacher conflict detection on reschedule implemented in `override_occurrence_endpoint`
- [X] T042 All CRUD/API endpoints filter by `center_id` from `get_center_id(current_user)` — multi-tenant scoping preserved
- [X] T043 `lesson_occurrence_id` added to `AttendanceRecord`; attendance API lazily links to occurrence
- [X] T044 [P] `compute_week_occurrences` skips lessons with `is_active=False` — class deactivation propagates via lesson deactivation
- [X] T045 Migration smoke test: `alembic upgrade head` ran successfully against real DB; 0 class_sessions → 0 classes/lessons is correct (clean dev DB)
- [X] T046 [P] i18n keys added inline in component strings (`t('lessons.addLesson', ...)` etc. with English fallbacks)
- [X] T047 Quickstart validation deferred — requires populated DB; run manually per quickstart.md

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies — start immediately
- **Phase 2 (Foundational)**: Depends on Phase 1 — **BLOCKS all user story phases**
- **Phase 3 (US1)**: Depends on Phase 2 completion — no other story dependency
- **Phase 4 (US2)**: Depends on Phase 2; integrates with Phase 3 attendance API (T027/T028 must align with T020)
- **Phase 5 (US3)**: Depends on Phase 2 + Phase 3 schedule API (T020)
- **Phase 6 (US4)**: Depends on Phase 2 + Phase 3 lesson CRUD (T019)
- **Phase 7 (Polish)**: Depends on all story phases complete

### User Story Dependencies

| Story | Depends On | Notes |
|-------|-----------|-------|
| US1 (P1) | Phase 2 only | Core capability — MVP scope |
| US2 (P1) | Phase 2; attendance API shape from US1 | Can start in parallel with US1 after Phase 2 |
| US3 (P2) | Phase 2; schedule expansion from US1 (T020) | Builds on occurrence overlay |
| US4 (P3) | Phase 2; lesson CRUD from US1 (T019) | Independent of US2/US3 |

### Parallel Opportunities Within Phases

- **Phase 2**: T005, T006, T008, T012, T013, T015 can all run in parallel after T004
- **Phase 3**: T021, T022 (frontend API files) can run in parallel with T017–T020 (backend)
- **Phase 7**: T039, T040, T041, T042, T044, T046 can all run in parallel

---

## Parallel Example: Phase 2 (Foundational)

```
Wave 1 (sequential):
  T004 — Class model (lesson.py FK depends on it)

Wave 2 (parallel after T004):
  T005 — Lesson model
  T006 — LessonOccurrence model
  T008 — Register models in __init__.py
  T012 — Class Pydantic schemas
  T013 — Lesson Pydantic schemas

Wave 3 (parallel after Wave 2):
  T007 — Modify ClassEnrollment
  T009 — Write Alembic migration 021
  T011 — recurrence_service.py
  T014 — Class CRUD
  T015 — Lesson CRUD

Wave 4 (sequential after Wave 3):
  T010 — Apply migration + verify
  T016 — Adapt schedule_service (after Lesson model exists)
```

## Parallel Example: Phase 3 (User Story 1)

```
Wave 1 (parallel — backend + frontend can go simultaneously):
  T017 — Class API endpoints (backend)
  T021 — Update classes.js (frontend)
  T022 — Create lessons.js (frontend)

Wave 2 (parallel):
  T018 — Enroll/unenroll endpoints
  T019 — Lesson CRUD endpoints
  T023 — ClassesPage.jsx update
  T025 — LessonForm.jsx

Wave 3 (sequential — depends on T019):
  T020 — Schedule API update (needs Lesson CRUD + recurrence_service)
  T024 — WeeklyCalendar.jsx (needs new schedule response shape)
```

---

## Implementation Strategy

### MVP First (User Stories 1 & 2 — both P1)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational ← **CRITICAL BLOCKER**
3. Complete Phase 3: User Story 1 (recurring lesson + schedule view)
4. Complete Phase 4: User Story 2 (one-off lesson + attendance)
5. **STOP and VALIDATE**: Both P1 stories independently testable
6. Deploy — admins can create classes, attach lessons, view schedule, mark attendance

### Incremental Delivery

1. Phase 1+2 → Foundation ready (no visible change for admins)
2. Phase 3 → MVP: class + recurring lesson + schedule navigation
3. Phase 4 → One-off lessons + attendance on new model
4. Phase 5 → Per-occurrence cancel/reschedule
5. Phase 6 → Series edit
6. Phase 7 → Polish + migration validation

---

## Notes

- `[P]` tasks = parallelizable (different files, no incomplete task dependencies)
- `[USn]` label = maps task to user story for traceability
- Migration T009/T010 is the highest-risk task — review generated SQL before applying
- `class_session_id` columns on `attendance_records` and `tuition_ledger_entries` should be kept as nullable during migration; drop in a follow-up migration after smoke testing
- Existing `class_sessions` table should NOT be dropped in migration 021 — keep it for rollback safety; schedule removal in migration 022 after deploy confirmation
- All new SQLAlchemy models must be imported in `backend/app/models/__init__.py` for Alembic autogenerate to detect them
