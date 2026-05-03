# Quickstart: Class / Lesson Separation (008)

**Branch**: `008-class-lesson-separation`

---

## What's Changing

This feature separates the current `ClassSession` model (which fuses "cohort" + "schedule") into two independent entities:

- **Class** — the cohort: name, teacher, enrolled students, tuition fee.
- **Lesson** — the schedule: one-off date or recurring rule (RRULE), attached to a class.
- **LessonOccurrence** — lazily persisted override record for a single occurrence (cancel, reschedule, attendance).

Occurrences remain **virtual** (computed at read time from the RRULE) until an admin takes a mutating action.

---

## Developer Workflow

### 1. Install new dependency

```bash
cd backend
pip install python-dateutil
# Then add to pyproject.toml [project.dependencies]:
# "python-dateutil>=2.9.0",
```

### 2. Create and apply the migration

```bash
cd backend
alembic revision --autogenerate -m "021_class_lesson_separation"
# Review the generated migration, then:
alembic upgrade head
```

The migration:
- Creates `classes`, `lessons`, `lesson_occurrences` tables.
- Migrates existing `class_sessions` rows into `Class + Lesson` pairs.
- Re-points `class_enrollments`, `attendance_records`, and `tuition_ledger_entries` FKs.

### 3. Run backend

```bash
cd backend
uvicorn app.main:app --reload
```

### 4. Run frontend

```bash
cd frontend
npm run dev
```

---

## Key Files to Create / Modify

### Backend

| Path | Action |
|------|--------|
| `backend/app/models/class_.py` | **New** — `Class` ORM model |
| `backend/app/models/lesson.py` | **New** — `Lesson` ORM model |
| `backend/app/models/lesson_occurrence.py` | **New** — `LessonOccurrence` ORM model |
| `backend/app/models/class_enrollment.py` | **Modify** — re-FK to `classes.id` + add `enrolled_since`/`unenrolled_at` |
| `backend/app/models/attendance.py` | **Modify** — replace `class_session_id` with `lesson_occurrence_id` |
| `backend/app/models/tuition_ledger_entry.py` | **Modify** — replace `class_session_id` with `lesson_id` |
| `backend/app/schemas/class_.py` | **New** — Pydantic schemas for Class CRUD |
| `backend/app/schemas/lesson.py` | **New** — Pydantic schemas for Lesson CRUD + OccurrenceOverride |
| `backend/app/crud/class_.py` | **New** — CRUD for Class |
| `backend/app/crud/lesson.py` | **New** — CRUD for Lesson + OccurrenceOverride |
| `backend/app/services/recurrence_service.py` | **New** — `compute_occurrences()`, RRULE helpers |
| `backend/app/services/schedule_service.py` | **Modify** — adapt conflict check to `Lesson` model |
| `backend/app/api/classes.py` | **Replace** — new Class endpoints (replaces ClassSession CRUD) |
| `backend/app/api/lessons.py` | **New** — Lesson + occurrence endpoints |
| `backend/app/api/schedule.py` | **Modify** — use `recurrence_service` to expand weekly occurrences |
| `backend/app/api/attendance.py` | **Modify** — accept `lesson_id` instead of `class_session_id` |
| `backend/alembic/versions/021_class_lesson_separation.py` | **New** — migration script |

### Frontend

| Path | Action |
|------|--------|
| `frontend/src/api/classes.js` | **Modify** — new Class API calls; add `lessons.js` |
| `frontend/src/api/lessons.js` | **New** — Lesson + occurrence API calls |
| `frontend/src/features/schedule/WeeklyCalendar.jsx` | **Modify** — pass `week_start` from FullCalendar `datesSet`, render canceled/rescheduled occurrences |
| `frontend/src/features/classes/ClassesPage.jsx` | **Modify** — list Classes (not ClassSessions); link to Class detail + Lessons |
| `frontend/src/features/classes/ClassDetail.jsx` | **New or modify** — Class detail with lesson list and occurrence override actions |
| `frontend/src/features/lessons/LessonForm.jsx` | **New** — create/edit Lesson with RRULE builder |
| `frontend/src/features/lessons/OccurrenceOverrideModal.jsx` | **New** — cancel/reschedule/revert a single occurrence |

---

## Testing

```bash
# Backend unit + integration tests
cd backend
pytest tests/

# Frontend
cd frontend
npm test
```

Key test scenarios (from spec user stories):
1. Create class → create recurring lesson → verify weekly schedule across 10 weeks.
2. Create one-off lesson for same class → both appear in week view.
3. Cancel occurrence → verify it disappears from that week only.
4. Reschedule occurrence → appears on new date for that week only.
5. Series edit → verify past attended occurrences unchanged, future occurrences reflect new time.
6. Migration smoke test → all pre-existing `class_sessions` render correctly after `alembic upgrade head`.
