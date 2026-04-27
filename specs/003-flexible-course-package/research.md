# Research: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Feature**: 003-flexible-course-package
**Date**: 2026-04-27
**Status**: Complete

## Research Summary

Five technical unknowns were identified during Technical Context analysis. All have been resolved. No external dependencies or new libraries are required — all changes use the existing tech stack.

---

## Decision 1: Display ID Derivation Strategy

**Question**: Should the class display ID (`{TeacherFirstName}-{Weekday3}-{HHMM}[-{N}]`) be computed at query time or stored as a materialized column?

**Decision**: Compute at query time in the application layer (Python).

**Rationale**:
- The display ID depends on mutable values from **two tables** (teacher `full_name` from `teachers`, plus `day_of_week` and `start_time` from `class_sessions`). A stored column would require database triggers on both tables.
- FR-003 mandates that the display ID reflects current values — any caching/materialization introduces staleness risk.
- At the current scale (~50 classes, ~10 teachers), computing display IDs in Python after loading classes with their teacher relationship (already eager-loaded via `lazy="selectin"`) adds negligible overhead.
- The disambiguator suffix (`-{N}`) requires a group-by across all classes sharing the same base ID. This is trivially done in Python with `itertools.groupby` or a `defaultdict` over the loaded result set.

**Implementation approach**:
```python
# In crud/class_session.py or a utility module
DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def compute_display_ids(classes: list[ClassSession]) -> dict[uuid.UUID, str]:
    """Compute display IDs for a list of classes, handling disambiguators."""
    from collections import defaultdict
    
    # Group by base ID components
    groups = defaultdict(list)
    for cs in classes:
        teacher_first = cs.teacher.full_name.split()[0] if cs.teacher else "Unknown"
        base = f"{teacher_first}-{DAY_ABBR[cs.day_of_week]}-{cs.start_time.strftime('%H%M')}"
        groups[base].append(cs)
    
    result = {}
    for base, members in groups.items():
        members.sort(key=lambda c: c.created_at)
        for i, cs in enumerate(members):
            result[cs.id] = base if i == 0 else f"{base}-{i + 1}"
    return result
```

**Alternatives considered**:
1. **Stored `display_id` column with triggers** — Requires `AFTER UPDATE` triggers on both `teachers` and `class_sessions`, plus a trigger for `AFTER INSERT` on `class_sessions` to handle disambiguator reflow. High maintenance burden, error-prone cascading logic.
2. **PostgreSQL generated column** — Cannot reference columns from other tables (`teachers.full_name`). Not viable.
3. **Materialized view** — Over-engineering for ~50 rows. Refresh timing is another moving part.

---

## Decision 2: Lesson Kind Uniqueness Enforcement

**Question**: How should case-insensitive uniqueness of lesson kind names be enforced, given concurrent inline-create requirements (SC-008)?

**Decision**: Database-level functional unique index on `LOWER(TRIM(name))`, combined with application-layer normalization and an `INSERT ... ON CONFLICT` find-or-create pattern.

**Rationale**:
- SC-008 requires that two concurrent inline-creates of the same name converge to a single row. Only a database constraint can guarantee this under concurrent transactions.
- PostgreSQL supports functional indexes: `CREATE UNIQUE INDEX uq_lesson_kind_name ON lesson_kinds (LOWER(TRIM(name)))`.
- The application normalizes (trim + collapse whitespace) before insert. The find-or-create pattern:
  ```sql
  INSERT INTO lesson_kinds (id, name, name_normalized)
  VALUES ($1, $2, LOWER(TRIM($2)))
  ON CONFLICT (name_normalized) DO NOTHING
  RETURNING id;
  -- If no row returned, SELECT by name_normalized
  ```

**Implementation approach**:
- Model: `LessonKind` with `name` (display form) and `name_normalized` (lowercase/trimmed, unique).
- CRUD: `find_or_create_lesson_kind(db, name: str) -> LessonKind` — normalize, attempt insert, handle conflict.
- The `ON CONFLICT DO NOTHING` + subsequent `SELECT` pattern avoids exceptions and is idempotent.

**Alternatives considered**:
1. **Application-only uniqueness check** (SELECT + INSERT) — Susceptible to TOCTOU race conditions. Two concurrent requests could both find "no match" and both insert, creating duplicates.
2. **Advisory locks** — Over-engineering. The database unique index is simpler and more robust.

---

## Decision 3: Package Table Rebuild Strategy

**Question**: What migration strategy should be used to restructure the `packages` table given that existing data is not preserved?

**Decision**: Drop dependent tables (`renewal_reminders`, `payment_records`) → drop `packages` → recreate all three with new schemas in a single migration.

**Rationale**:
- Spec clarification explicitly states: "Existing course packages (and their dependent records that block schema changes) are dropped and the table is rebuilt under the new flexible model."
- The `payment_records` and `renewal_reminders` tables have FK references to `packages`. Dropping `packages` without first dropping these would fail due to FK constraints.
- Recreating all three in the same migration keeps the operation atomic and the schema consistent.

**Migration steps** (`012_flexible_course_package.py`):
```
upgrade():
  1. CREATE TABLE lesson_kinds (id, name, name_normalized, created_at, updated_at)
     + UNIQUE INDEX on name_normalized
  2. ALTER TABLE class_sessions ADD COLUMN tuition_fee_per_lesson BIGINT
     + CHECK (tuition_fee_per_lesson > 0 AND tuition_fee_per_lesson <= 100000000)
  3. ALTER TABLE students DROP COLUMN skill_level
  4. DROP TABLE renewal_reminders
  5. DROP TABLE payment_records
  6. DROP TABLE packages
  7. CREATE TABLE packages (new schema with class_session_id FK, lesson_kind_id FK)
  8. CREATE TABLE payment_records (same as before, FK → new packages)
  9. CREATE TABLE renewal_reminders (same as before, FK → new packages)
  10. INSERT seed lesson kinds (Beginner, Elementary, Intermediate, Advanced)

downgrade():
  Reverse all steps (recreate old packages schema, re-add skill_level, drop lesson_kinds, etc.)
```

**Alternatives considered**:
1. **Column-by-column ALTER** — More migration steps, same data loss, higher error risk, no benefit since there's no production data to preserve.
2. **Rename old table + create new** — Keeps a ghost table around for no reason.

---

## Decision 4: Auto-fill Fee UX Strategy

**Question**: How should the frontend implement the "auto-fill tuition fee unless manually edited" behavior?

**Decision**: Frontend-only logic using React state (`isManualFeeEdit` flag) with `useEffect` watching `selectedClass` and `numberOfLessons`.

**Rationale**:
- The computation is a simple multiplication: `tuition_fee_per_lesson × number_of_lessons`.
- No server round-trip is needed — the class's `tuition_fee_per_lesson` is already available from the class selection response.
- SC-002 requires the auto-fill to appear within 200 ms — local computation is instantaneous.

**Implementation approach**:
```jsx
const [selectedClass, setSelectedClass] = useState(null);
const [numberOfLessons, setNumberOfLessons] = useState(null);
const [tuitionFee, setTuitionFee] = useState(null);
const [isManualFeeEdit, setIsManualFeeEdit] = useState(false);

useEffect(() => {
  if (!isManualFeeEdit && selectedClass?.tuition_fee_per_lesson && numberOfLessons > 0) {
    setTuitionFee(selectedClass.tuition_fee_per_lesson * numberOfLessons);
  }
}, [selectedClass, numberOfLessons, isManualFeeEdit]);

// When user manually edits fee:
const handleFeeChange = (value) => {
  setTuitionFee(value);
  setIsManualFeeEdit(true);
};

// Reset button:
const handleResetFee = () => {
  setIsManualFeeEdit(false);
  // useEffect will recompute
};
```

**Alternatives considered**:
1. **Server-side computation on each change** — Unnecessary network latency for a multiplication. Violates SC-002's 200 ms requirement under poor network conditions.
2. **Debounced server call** — Same issues as #1, plus added complexity.

---

## Decision 5: Class Deletion Guard

**Question**: How should the system prevent deletion of a class that has associated packages (FR-006)?

**Decision**: Both application-level check (for friendly error messages) and database-level `ON DELETE RESTRICT` FK constraint (for safety).

**Rationale**:
- FR-006 requires blocking deletion when any package (active or historical) references the class.
- Application check: Before `DELETE`, query `SELECT EXISTS(SELECT 1 FROM packages WHERE class_session_id = ?)`. If true, return HTTP 409 with a human-readable message.
- DB constraint: `packages.class_session_id` FK uses `ON DELETE RESTRICT` (the default for FK constraints, and already the behavior for the existing `student_id` FK).
- Belt-and-suspenders: even if the application check is bypassed (e.g., direct DB access), the FK constraint prevents data corruption.

**Implementation approach**:
```python
# In api/classes.py (new endpoint)
@router.delete("/{class_id}")
async def delete_class(class_id: UUID, db: DbSession, current_user: CurrentUser):
    if current_user.role != "admin":
        raise HTTPException(403, "Admin access required")
    
    has_packages = await has_packages_for_class(db, class_id)
    if has_packages:
        raise HTTPException(409, "Cannot delete class with associated packages. Deactivate packages first.")
    
    await delete_class_session(db, class_id)
    return {"detail": "Class deleted"}
```

**Alternatives considered**:
1. **DB-only constraint** — Correct but produces a raw IntegrityError that maps to a generic 500 unless caught and parsed. Poor UX.
2. **Application-only check** — Susceptible to race conditions (package created between check and delete). The DB constraint is the safety net.

---

## Technology Decisions Summary

| # | Decision | Status |
|---|----------|--------|
| 1 | Compute display ID at query time (Python) | ✅ Resolved |
| 2 | Database unique index for lesson kind names (case-insensitive) | ✅ Resolved |
| 3 | Drop + rebuild packages/payments/reminders in single migration | ✅ Resolved |
| 4 | Frontend-only auto-fill fee with `isManualFeeEdit` flag | ✅ Resolved |
| 5 | Application + DB dual guard for class deletion | ✅ Resolved |

No `NEEDS CLARIFICATION` markers remain.
