# Data Model: Class / Lesson Separation (008)

**Feature branch**: `008-class-lesson-separation`
**Date**: 2026-04-30

---

## Entity Overview

```
Center
  ├── Class (1–N)
  │     ├── ClassEnrollment (join: Class ↔ Student, with enrolled_since)
  │     └── Lesson (N — a class can have many lessons over its lifetime)
  │           ├── LessonOccurrence (0–N, lazy-persisted on admin action)
  │           │     └── AttendanceRecord (N — per student per occurrence)
  │           │           └── TuitionLedgerEntry (0–1 per attendance)
  │           └── [virtual occurrences] ← computed from Lesson.rrule at read time
  └── Teacher
```

---

## New Tables

### `classes`

Replaces the "cohort + schedule" responsibility of `ClassSession`. Holds only the cohort definition; schedule lives in `lessons`.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `name` | VARCHAR(200) NOT NULL | e.g. "Piano Beginner Group A" |
| `teacher_id` | UUID FK→teachers NOT NULL | |
| `tuition_fee_per_lesson` | BIGINT NULL | Admin-only visible; NULL = no fee |
| `lesson_kind_id` | UUID FK→lesson_kinds NULL | Optional classification |
| `is_active` | BOOLEAN NOT NULL DEFAULT TRUE | Soft-delete flag |
| `center_id` | UUID FK→centers NOT NULL | Multi-tenant scoping |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

**Indexes**: `(center_id)`, `(teacher_id)`, `(is_active)`

---

### `lessons`

A schedulable definition. May be recurring (has `rrule`) or one-off (has `specific_date`).

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `class_id` | UUID FK→classes NULL | NULL = unattached lesson (future flexibility) |
| `teacher_id` | UUID FK→teachers NOT NULL | Denormalized for conflict queries |
| `title` | VARCHAR(200) NULL | Optional override label; if NULL, inherit from `Class.name` |
| `start_time` | TIME NOT NULL | Local time; timezone from center config |
| `duration_minutes` | INT NOT NULL CHECK > 0 | |
| `day_of_week` | INT NULL CHECK 0–6 | 0=Monday. NULL for one-off lessons |
| `specific_date` | DATE NULL | Set for one-off lessons; NULL for recurring |
| `rrule` | VARCHAR(500) NULL | RFC 5545 RRULE string (e.g. `FREQ=WEEKLY;BYDAY=MO;COUNT=10`). NULL for one-off |
| `is_active` | BOOLEAN NOT NULL DEFAULT TRUE | |
| `center_id` | UUID FK→centers NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

**Indexes**: `(center_id)`, `(class_id)`, `(teacher_id)`, `(day_of_week)`, `(specific_date)`

**Validation rules** (application-layer):
- Exactly one of `{rrule, specific_date}` must be set (not both, not neither).
- If `rrule` is set, `day_of_week` must also be set (derived from RRULE's `BYDAY`; stored for query efficiency).
- `duration_minutes` > 0.

---

### `lesson_occurrences`

Persisted lazily — only when an admin takes a mutating action (attendance, cancel, reschedule). Virtual occurrences exist in memory only.

| Column | Type | Notes |
|--------|------|-------|
| `id` | UUID PK | |
| `lesson_id` | UUID FK→lessons NOT NULL | |
| `original_date` | DATE NOT NULL | The date this occurrence falls on per the recurrence rule (immutable key) |
| `status` | VARCHAR(20) NOT NULL DEFAULT 'active' | `active` or `canceled` |
| `override_date` | DATE NULL | Non-NULL = occurrence rescheduled to this date |
| `override_start_time` | TIME NULL | Non-NULL = occurrence time overridden |
| `center_id` | UUID FK→centers NOT NULL | |
| `created_at` | TIMESTAMPTZ NOT NULL | |
| `updated_at` | TIMESTAMPTZ NOT NULL | |

**Unique constraint**: `(lesson_id, original_date)` — enforces one override record per (lesson, date) pair.

**Indexes**: `(lesson_id, original_date)`, `(center_id)`, `(original_date)`

---

## Modified Tables

### `class_enrollments` ← rename-extended

Currently links `class_session_id` → `student_id`. After migration: links `class_id` → `student_id`.

| Column change | Before | After |
|--------------|--------|-------|
| FK source | `class_session_id` | `class_id` (rename + re-FK) |
| Added | — | `enrolled_since DATE NULL` — for mid-series enrollment cutoff |
| Added | — | `unenrolled_at DATE NULL` — for mid-series removal cutoff |

**Existing unique constraint** `uq_enrollment_class_student`: update to reference `class_id`.

---

### `attendance_records` ← re-keyed

Currently keyed on `class_session_id + session_date`. After migration: keyed on `lesson_id + session_date` (via the `LessonOccurrence`).

| Column change | Before | After |
|--------------|--------|-------|
| FK | `class_session_id` FK→class_sessions | `lesson_occurrence_id` FK→lesson_occurrences |
| Removed | `class_session_id` | (migrated away; dropped after migration) |

> **Migration note**: Each existing `AttendanceRecord(class_session_id, session_date)` maps to a `LessonOccurrence` created during migration.

---

### `tuition_ledger_entries` ← FK updated

| Column change | Before | After |
|--------------|--------|-------|
| FK | `class_session_id` FK→class_sessions | `lesson_id` FK→lessons (optional; NULL for payment entries) |

---

## State Transitions

### LessonOccurrence.status

```
[virtual] ──(admin marks attendance)──► active (persisted)
[virtual] ──(admin cancels)──────────► canceled (persisted)
[virtual] ──(admin reschedules)──────► active + override_date set (persisted)
active    ──(admin cancels)──────────► canceled
canceled  ──(admin un-cancels/reverts)► active
active    ──(admin reverts override)──► active, override_date = NULL
```

### Class.is_active

```
TRUE ──(admin deactivates)──► FALSE
FALSE ──(admin reactivates)─► TRUE
```

---

## Occurrence Computation Algorithm

```python
def compute_occurrences(lesson: Lesson, week_start: date, week_end: date) -> list[VirtualOccurrence]:
    if lesson.specific_date:
        # One-off: appears in the week it falls in
        if week_start <= lesson.specific_date <= week_end:
            return [VirtualOccurrence(lesson, lesson.specific_date)]
        return []
    # Recurring: expand RRULE for the week
    rule = rrulestr(lesson.rrule, dtstart=datetime.combine(lesson.rrule_start, lesson.start_time))
    dates = rule.between(
        datetime.combine(week_start, time.min),
        datetime.combine(week_end, time.max),
        inc=True,
    )
    return [VirtualOccurrence(lesson, d.date()) for d in dates]
```

Overlay: for each `VirtualOccurrence`, look up `LessonOccurrence(lesson_id, original_date)` from a pre-loaded dict; if found, apply `status` / `override_date` / `override_start_time`.

---

## Invariants

1. A `LessonOccurrence` for date X under lesson L **always wins** over L's recurrence rule for date X (even after a series edit).
2. A `ClassEnrollment` with `enrolled_since = D` causes the student to appear on roster only for occurrences with `effective_date >= D`.
3. A `ClassEnrollment` with `unenrolled_at = D` causes the student to be omitted for occurrences with `effective_date >= D`.
4. A `Class` with `is_active = FALSE` hides all its lessons and occurrences from the schedule view (but they remain queryable for history).
5. `center_id` is non-nullable on every new table and propagated from the parent `Class`/`Lesson` on insert; queries always filter by `center_id`.
