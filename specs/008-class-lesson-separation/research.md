# Research: Class / Lesson Separation (008)

**Feature branch**: `008-class-lesson-separation`
**Date**: 2026-04-30

---

## 1. Recurrence Engine Selection

**Decision**: Use the `python-dateutil` library (`rrule`) for recurrence expansion.

**Rationale**:
- Already a transitive dependency of many Python projects; lightweight to add.
- `rrule` directly models RFC 5545 (iCalendar) recurrence — WEEKLY, DAILY, COUNT, UNTIL — which covers the spec's committed v1 patterns (weekly with optional end count or end date).
- Expansion is on-demand (called per weekly request, never stored), so no materialization concern.
- Parsing an RRULE string (e.g. `RRULE:FREQ=WEEKLY;BYDAY=MO;COUNT=10`) keeps the DB column simple (String) and interoperable with calendar tools.

**Alternatives considered**:
- `recurrence` (Django-centric, not applicable).
- Custom bitmask field (simpler but no built-in expansion logic; would require manual implementation of UNTIL/COUNT).
- Celery + materialization job (ruled out by spec: read-time-only model, no scheduler required).

---

## 2. Recurrence Rule Storage Format

**Decision**: Store the recurrence rule as an RFC 5545 RRULE string in a `String(500)` column on `Lesson`, plus two index-friendly denormalized columns (`day_of_week INT`, `start_time TIME`) for conflict-detection queries.

**Rationale**:
- RRULE string is human-readable, debuggable, and parse-expandable at any future date.
- Denormalized columns allow existing `schedule_service.check_scheduling_conflicts` query patterns to keep working without full RRULE expansion on every conflict check.
- Single source of truth: RRULE string; denormalized columns are always derived from it on write and enforced consistent.

**Alternatives considered**:
- Separate columns per field (`freq`, `interval`, `byday`, `count`, `until`) — more columns to migrate but arguably more queryable; rejected because the RRULE string is more extensible and canonical.
- JSON blob — less interoperable and harder to validate.

---

## 3. Virtual Occurrence Computation

**Decision**: Compute occurrences in a pure Python helper `compute_occurrences(lesson, week_start, week_end) → list[VirtualOccurrence]` called at API read time. Overlay persisted `LessonOccurrence` records (by `original_date` key) to apply cancellations, reschedules, and attendance state.

**Rationale**:
- Bounded per request: expanding weekly occurrences touches at most 1–2 dates (weekly recurrence → at most 1 per week; daily → 7).
- No new background jobs, no database writes on read.
- Overlay pattern is O(#persisted overrides) which is small and decreasing with time (no open-ended accumulation of virtual records).

**Alternatives considered**:
- Materialization on create (ruled out by spec).
- Lazy materialization on first read and cache (adds write complexity, stale-cache risk).

---

## 4. Conflict Detection — Lesson-Based

**Decision**: Extend `check_scheduling_conflicts` to accept a `Lesson` (or equivalent parameters) and expand it to concrete date-time ranges per week, then check against other `Lesson` occurrences that share a teacher or an enrolled student.

**Rationale**:
- Current service checks `ClassSession.day_of_week` (integer) + `start_time` across all active sessions. The new `Lesson` has equivalent fields (`day_of_week`, `start_time`, `duration_minutes`), so the existing query structure is reusable.
- For per-occurrence reschedule conflicts: an additional check at override-save time covers a single concrete date rather than a recurring pattern.

**Alternatives considered**:
- Interval-tree or calendar engine for conflict detection — overkill for the small cardinality (a few lessons per teacher per day per center).

---

## 5. Migration Strategy — ClassSession → Class + Lesson

**Decision**: Data migration via an Alembic migration script (migration `021`):
1. For each existing `ClassSession` row, create one `Class` row (name, teacher, tuition fee) and one `Lesson` row (recurrence rule derived from `day_of_week` + `start_time` + `duration_minutes` + `is_recurring`/`recurring_pattern`).
2. Copy enrollments to `ClassEnrollment` pointing at the new `Class`.
3. Update `AttendanceRecord.lesson_id` (new FK) and `TuitionLedgerEntry.lesson_id` to point at the new `Lesson`.
4. Keep old `class_sessions` table with `is_migrated` flag for backward safety; drop in a subsequent migration after smoke testing.

**Rationale**:
- Zero-downtime for admins: existing data is preserved; the weekly schedule renders immediately on deploy (FR-008, SC-002).
- Alembic migration is atomic (all-or-nothing in Postgres transaction).

**Alternatives considered**:
- Application-layer shim that reads `ClassSession` as a `Lesson` — adds permanent technical debt.
- Manual admin re-entry — explicitly rejected by spec.

---

## 6. Occurrence Override Storage

**Decision**: New table `lesson_occurrences` (composite unique key: `lesson_id + original_date`), with fields:
- `status` (`active`, `canceled`)
- `override_date DATE` (NULL = not rescheduled; non-NULL = rescheduled to this date)
- `override_start_time TIME` (NULL = use lesson's start_time)
- Attendance foreign keys

**Rationale**:
- Keying on `(lesson_id, original_date)` implements the spec rule "per-occurrence overrides win over series edits" — the key is immutable, only the overriding fields change.
- `override_date` supports the reschedule-to-different-day use case without losing the original date (needed for reporting and the "undo override" operation).

---

## 7. Edit Scopes — "This Occurrence" vs "Series"

**Decision**: Implement as two separate API operations:
- `PATCH /lessons/{lesson_id}/occurrences/{original_date}` — creates/updates a `LessonOccurrence` record for that date (this-occurrence scope).
- `PATCH /lessons/{lesson_id}` with body `{scope: "series", ...}` — updates the `Lesson.rrule` and denormalized fields; does not touch existing `LessonOccurrence` records.

**Rationale**:
- Clean REST separation; no ambiguous `scope` field in the same endpoint.
- Series edit never rewrites occurrence records (spec requirement); the API boundary makes this explicit.

---

## 8. Frontend — Schedule View Adaptation

**Decision**: Pass `week_start` as a query parameter from FullCalendar's navigation callbacks to the `/schedule/weekly` endpoint. The API already accepts `week_start`; FullCalendar fires `datesSet` on navigation — wire it to `setWeekStart(info.start)` which invalidates the React Query cache for that week.

**Rationale**:
- FullCalendar's `datesSet` callback fires after every navigation (next/prev/today) — a single hook point covers all navigation paths.
- React Query key `['schedule', weekStart, teacherFilter]` ensures each week is independently cached and refetched on demand.

---

## 9. Recurrence Pattern Scope (v1)

**Decision**: v1 supports **weekly** recurrence only (RRULE `FREQ=WEEKLY`), with `BYDAY` (day of week), optional `COUNT` (end after N occurrences), and optional `UNTIL` (end on a specific date). One-off lessons are represented as a `Lesson` with `specific_date` set (no RRULE).

**Rationale**:
- Covers 100% of current `ClassSession` data (all sessions are weekly or one-off).
- Simpler API contract for v1; daily/bi-weekly/monthly can be added later by extending the RRULE field without schema changes.
