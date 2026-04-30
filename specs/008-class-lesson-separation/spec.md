# Feature Specification: Separate Class from Lesson

**Feature Branch**: `008-class-lesson-separation`
**Created**: 2026-04-30
**Status**: Draft
**Input**: User description: "Should we separate class from lesson. We create class X. We create a lesson like an Outlook appointment (recurring, time, etc.) and then add class. This way one class can have a flexible schedule. Recurring lessons should auto-create single lesson instances."

## Clarifications

### Session 2026-04-30

- Q: How are occurrences of a recurring lesson surfaced — materialized as records, or computed on demand? → A: **Computed at read time** from the recurrence rule for every week (current and future). No scheduled materialization job runs. The full series is never pre-created.
- Q: How are per-occurrence actions (attendance, cancel, reschedule) persisted then? → A: Persisted records are created **only when an admin takes an action that mutates an occurrence**, keyed on (lesson, occurrence date). Otherwise an occurrence exists purely as a virtual entity derived from the lesson's recurrence rule.
- Q: How should future weeks render on the schedule view? → A: Computed from the recurrence rule at read time, with **no default forward horizon cap** — admins can navigate to any future week.
- Q: When a recurring lesson is created mid-week, when does it first appear on the schedule? → A: Immediately. Because the schedule view computes at read time, any current-week occurrence whose date has not yet passed shows up as soon as the recurring lesson is saved — no waiting for a job.
- Q: Can admins cancel or reschedule an occurrence in a future week before it has been "acted on"? → A: Yes — overrides are allowed on any virtual occurrence the recurrence rule produces (no horizon cap by default). The override is persisted as a record (keyed on lesson + original date) at the moment the admin acts; until then, the occurrence remains virtual.
- Q: How do per-occurrence overrides interact with a later **series** edit on the same dates? → A: Per-occurrence overrides **win** and are preserved through series edits. A pre-canceled date stays canceled; a rescheduled override keeps its overridden date and time. Admins must explicitly un-override (revert) the date to re-sync it with the series.
- Q: What is the default end for a recurring lesson and the schedule view's forward visibility? → A: **NEVER** — recurring lessons default to no end date, and the schedule view has no default forward horizon cap. Admins can optionally set a fixed end date or end count on a per-lesson basis.
- Q: What edit scopes does the reschedule/edit feature offer for recurring lessons? → A: **Two modes only, Outlook-style:** (1) **This occurrence** — edits or cancels the single occurrence at a given date, persisted as a per-occurrence override; (2) **Series** — edits the recurrence rule itself (time, day, pattern, end), applying to every virtual occurrence in the series. Persisted records (attendance, per-occurrence overrides) always win over rule changes. There is no separate "this and future" mode — admins who want to change the schedule going forward should either edit the series (past attended occurrences are preserved automatically) or end the current series and create a new one.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Schedule a recurring lesson series for a class (Priority: P1)

A center admin defines class "Piano Beginner Group A" once — name, teacher, students, per-lesson tuition. Separately the admin creates a lesson appointment ("every Monday 8:00–9:00 from May 4 for 10 weeks") and attaches the class. The schedule view immediately shows 10 individual lesson occurrences (computed from the recurrence rule at read time) that accept attendance, exactly as today's recurring class would.

**Why this priority**: This is the core capability. Without it, the class/lesson separation delivers no user-visible value.

**Independent Test**: Create a class, create a recurring lesson and attach the class, navigate the weekly schedule across multiple weeks, confirm an occurrence appears each week at the right time with the correct roster, mark attendance on one occurrence and confirm it persists with the existing fee deduction behavior.

**Acceptance Scenarios**:

1. **Given** a class with 5 enrolled students and no lessons attached, **When** the admin creates a weekly recurring lesson for 10 weeks and attaches the class, **Then** the schedule view shows one occurrence per configured date for all 10 weeks (computed from the recurrence rule at read time; no occurrence records are persisted yet).
2. **Given** a recurring lesson exists for a class, **When** the admin opens the weekly schedule for any week within the recurrence range, **Then** exactly one occurrence appears at the configured time with the class's roster.
3. **Given** an occurrence has been marked with per-student attendance and tuition deductions, **When** the admin returns to that occurrence on a later day, **Then** the recorded attendance and ledger entries are unchanged.

---

### User Story 2 - Add a one-off lesson alongside a recurring series (Priority: P1)

The admin needs an extra Saturday makeup session for "Piano Beginner Group A" without touching the regular Monday recurring lesson. The admin creates a non-recurring lesson on the Saturday date and attaches the same class. Both Monday and Saturday occurrences appear on that week's schedule.

**Why this priority**: Flexible scheduling is the explicit motivator for separating class from lesson; one-off lessons are the simplest test of that flexibility.

**Independent Test**: With a class that already has a recurring weekly lesson, add a one-time lesson on a different day, confirm both appear on the week view for the affected week, and confirm attendance can be marked independently on each.

**Acceptance Scenarios**:

1. **Given** a class with a recurring Monday lesson, **When** the admin creates a one-time lesson on a Saturday and attaches the same class, **Then** the week view shows both the Monday and Saturday occurrences for that class.
2. **Given** a one-time and a recurring lesson both exist for a class, **When** the admin marks attendance on the one-time lesson, **Then** the recurring lesson's occurrences are unaffected.

---

### User Story 3 - Modify or cancel a single occurrence of a recurring series (Priority: P2)

A national holiday lands on a Monday. The admin opens the affected occurrence within the recurring lesson and either cancels it or moves it to Tuesday at the same time. Other Mondays in the series remain untouched.

**Why this priority**: Real-world schedules need exceptions. Without per-occurrence overrides, recurring lessons are too rigid to adopt and admins fall back to creating manual one-offs.

**Independent Test**: Create a 10-week recurring lesson, cancel occurrence #5, open the affected week and confirm it is missing or shown as canceled while occurrences #1–4 and #6–10 are unchanged. Repeat for reschedule (move to a different day/time).

**Acceptance Scenarios**:

1. **Given** a 10-week recurring lesson, **When** the admin cancels the occurrence on 2026-05-04, **Then** that occurrence no longer accepts attendance and the schedule view does not surface it as a regular class, while all other occurrences remain.
2. **Given** a 10-week recurring lesson, **When** the admin reschedules the 2026-05-04 occurrence to 2026-05-05 at the same time, **Then** the week view shows the lesson on Tuesday for that week only and Mondays in other weeks are unchanged.

---

### User Story 4 - Edit the recurring series (Priority: P3)

The teacher's availability changes and the lesson must move from 8:00 to 9:00. The admin opens the recurring lesson, selects "Series" edit, and changes the start time. The new time applies to every future occurrence. Past occurrences with attendance keep their original time and recorded data — those records win over the rule change.

**Why this priority**: Less frequent than per-occurrence edits but still important to avoid recreating series for routine changes.

**Independent Test**: Create a recurring lesson, mark attendance on the first 3 occurrences, edit the **series** to a new time, and confirm occurrences #1–3 retain the original time and attendance while all future occurrences reflect the new time.

**Acceptance Scenarios**:

1. **Given** a recurring lesson with 3 past occurrences containing attendance and 9 future occurrences, **When** the admin selects **"Series"** and changes the start time, **Then** the 3 past attended occurrences keep their original time and records, and the 9 future virtual occurrences reflect the new time.
2. **Given** a recurring lesson with a per-occurrence reschedule already applied to date X, **When** the admin selects **"Series"** and changes the start time, **Then** date X keeps its overridden time/date, and all other future virtual occurrences reflect the new time.

---

### Edge Cases

- A recurring lesson is edited via **"Series"** scope (start time, duration, day of week, pattern) — past occurrences with attendance and any per-occurrence overrides MUST NOT be retroactively changed; only virtual (unrecorded) occurrences reflect the new rule.
- A class is detached from a lesson while future occurrences with attendance exist — the lesson must remain visible in history; future-occurrence behavior follows an explicit rule (e.g., lesson is auto-canceled or kept as an empty appointment).
- A student enrolls in the class mid-series — they appear on the roster only for occurrences from the enrollment date forward; past occurrences' rosters are unchanged.
- A student is removed from the class mid-series — past attendance for that student remains; future occurrences omit them.
- A teacher conflict arises (two lessons overlap for the same teacher) when creating or moving a lesson — the system MUST reject the change with an actionable error.
- A student conflict arises (the student is enrolled in another class whose lesson overlaps) — the system MUST reject the conflicting enrollment or lesson change.
- Migration of existing classes: every existing recurring class definition under the current model MUST continue to render and be operable on the weekly schedule the day after deploy, with no admin action required.
- A recurring lesson with no end date — supported as the **default**. The schedule view computes one week at a time at read time, so navigating arbitrarily far into the future remains responsive (each request is bounded work).
- An occurrence is canceled or rescheduled (mode "this occurrence"), then the series is later edited (mode "Series") — the per-occurrence override wins for that date (cancellation stays canceled; reschedule keeps its overridden date and time); the admin must explicitly un-override the date to re-sync it with the series.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST allow admins to create a class with name, teacher, enrolled students, and per-lesson tuition fee, independent of any schedule.
- **FR-002**: System MUST allow admins to create a lesson with either (a) a single date and time, or (b) a recurrence rule (e.g., weekly on a given day) independent of any class. The recurrence MUST default to **no end date** (open-ended); admins MAY optionally set a fixed end date or end count per lesson.
- **FR-003**: System MUST allow admins to attach exactly one class to a lesson; the class's roster and tuition policy applies to every occurrence of that lesson.
- **FR-004**: System MUST treat each occurrence of a recurring lesson as an independently addressable single occurrence — capable of holding attendance, supporting cancellation, and supporting reschedule — without affecting sibling occurrences in the same series.
- **FR-004a**: System MUST compute occurrences from the recurrence rule **at read time** for the requested week, regardless of how far that week is in the future. The full series MUST NOT be pre-materialized at lesson creation, and no scheduled background job is required to make occurrences visible. Each weekly request MUST be bounded work (compute only that week's occurrences from the rule) so unbounded recurrence does not impact request performance.
- **FR-004b**: System MUST persist a per-occurrence record only when an admin takes an action that mutates that occurrence — specifically: marking attendance, canceling the occurrence, or rescheduling/overriding it. The persisted record MUST be keyed on (lesson, occurrence date) so subsequent reads reflect the override.
- **FR-005**: System MUST preserve current attendance behavior at the occurrence level: per-student status (`present`, `absent`, `absent_with_notice`), `charge_fee` flag, and atomic tuition ledger update on the occurrence's date.
- **FR-006**: System MUST detect and reject scheduling conflicts at lesson creation, attachment, edit, or per-occurrence reschedule: a teacher MUST NOT be assigned to overlapping occurrences; a student MUST NOT be enrolled in classes whose occurrences overlap.
- **FR-007**: System MUST support exactly **two edit scopes** for recurring lessons, mirroring Outlook's classic dialog: **"this occurrence"** and **"series"**.
  - **This occurrence**: edits or cancels a single dated occurrence; persisted as a per-occurrence override keyed on (lesson, original date). MUST work on any virtual or persisted occurrence the recurrence rule produces — including arbitrarily far in the future.
  - **Series**: edits the recurrence rule itself (time, duration, day-of-week, recurrence pattern, end date/count); applies to every virtual occurrence the new rule produces. Persisted records — attendance and per-occurrence overrides — MUST always win over the new rule (they are not retroactively rewritten). Past occurrences with recorded attendance are therefore preserved automatically.
  - There is no "this and future" scope; admins who need a future-only change should edit the series (past attended dates remain locked) or end the current series and create a new one.
- **FR-008**: System MUST preserve all attendance records, tuition ledger entries, and class enrollments belonging to existing class definitions when this feature is deployed; existing weekly schedules MUST continue to render correctly with no admin action required.
- **FR-009**: System MUST scope all classes, lessons, and occurrences to a single center; users MUST NOT see or modify data from other centers (preserves current multi-center isolation guarantees).
- **FR-010**: System MUST display all occurrences (recurring + one-off, reflecting cancellations and reschedules) for a given week on the weekly schedule view, scoped to the user's center.
- **FR-011**: System MUST allow a class to have zero, one, or many lessons attached over its lifetime, including overlapping series (e.g., a regular weekly series + a separate makeup series).
- **FR-012**: System MUST allow open-ended recurring lessons (no end date) by default — there is no system-imposed forward visibility cap. The schedule view computes one week at a time at read time, so navigating arbitrarily far ahead is supported and bounded only by the requested week. (Operational sanity caps such as input validation on date fields are an implementation detail for planning.)
- **FR-013**: System MUST retain attendance, fees, and notes recorded on a canceled occurrence as a historical record, but MUST NOT permit new actions on a canceled occurrence unless the cancellation is reversed.

### Key Entities *(include if feature involves data)*

- **Class**: A named cohort with a teacher, an enrolled student set, and a per-lesson tuition fee. Has no inherent schedule. Lives within a single center.
- **Lesson**: A schedulable definition that specifies start time, duration, and either a single date or a recurrence rule. Optionally attached to one Class. Lives within a single center.
- **Lesson Occurrence**: A concrete single-date instance derived from a Lesson — the unit at which attendance, tuition deductions, cancellations, and reschedules act. May carry per-occurrence overrides relative to its parent's recurrence rule.
- **Attendance Record**: Per-student record on a Lesson Occurrence (carried over from current behavior; tied to the occurrence's date).
- **Tuition Ledger Entry**: Per-attendance fee transaction (carried over; linked to the attendance record).
- **LessonKind** (existing, out of scope): An append-only vocabulary for classifying lessons by category. Remains functional and is not renamed or repurposed by this feature.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A center admin can create a class and attach a 10-week recurring lesson in under 2 minutes end-to-end.
- **SC-002**: 100% of existing classes render correctly on the weekly schedule the day after deployment, with no manual migration step required from admins.
- **SC-003**: 100% of attendance records and tuition ledger entries that existed before deployment remain queryable and unchanged for all historical dates.
- **SC-004**: A center admin can cancel a single occurrence of a recurring lesson and verify the change on the schedule view in under 30 seconds.
- **SC-005**: A center admin can add a one-off lesson to an existing class without modifying the class's recurring lesson, in under 1 minute.
- **SC-006**: Time to mark attendance for a class on a given date is no slower than today's flow (no perceptible regression in the attendance experience).
- **SC-007**: Multi-center isolation is preserved — no test scenario exposes one center's classes, lessons, occurrences, or attendance to another center.

## Assumptions

- A lesson has at most one class attached. A class can have many lessons over its lifetime, including concurrent series. (User's wording "add class" was singular; one-class-per-lesson keeps the roster and tuition policy unambiguous per occurrence.)
- The center's local time zone applies to lesson times. Cross-time-zone scheduling is not introduced by this feature.
- "Recurring" minimally covers weekly with a fixed end date or end count. Daily, monthly, and custom recurrence (e.g., every other Tuesday) are not committed for v1 and may be added later based on demand.
- Materialization follows a **read-time-only model**: occurrences are computed from the recurrence rule whenever the schedule is read, **with no default forward horizon cap** — open-ended recurring lessons surface for any future week the admin navigates to. Persisted occurrence records are created lazily, only when an admin takes an action that mutates an occurrence (attendance, cancel, reschedule). No scheduled background job is required. Each weekly request computes only that week's occurrences from the rule, so unbounded recurrence does not degrade performance.
- Existing `ClassSession` data will be migrated automatically at deploy time into the new Class + Lesson structure. Admins are not required to recreate anything. The migration preserves all attendance, ledger, and enrollment records.
- The existing `LessonKind` vocabulary is unrelated to scheduled lessons in this feature and remains a separate, append-only classifier.
- Naming: the user-facing term "Lesson" is reused for the new scheduling concept, distinct from `LessonKind`. The UI must distinguish them clearly to avoid admin confusion.
- Per-occurrence cancellation is a soft state (the occurrence remains queryable as canceled) so that historical reporting is preserved.
