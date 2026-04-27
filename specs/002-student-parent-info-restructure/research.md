# Research: Student & Parent Info Restructure

**Feature**: 002-student-parent-info-restructure  
**Date**: 2026-04-27

## Decision 1: JSON Storage Strategy

**Decision**: Use PostgreSQL `JSONB` column named `contact` on the `students` table (via SQLAlchemy `JSONB` dialect type).

**Rationale**: The parent fields are a fixed, small set of attributes (name, phone, address, zalo_id, notes). They will always be queried together with the student. JSONB avoids a JOIN, keeps the student record self-contained, and is natively supported by SQLAlchemy 2.0 and PostgreSQL. The `JSONB` type (vs plain `JSON`) provides indexing capability if needed later.

**Alternatives considered**:
- Separate `parents` table (current state) — rejected: requires JOIN, adds complexity for a 1:1 relationship.
- `hstore` — rejected: doesn't support nested types or mixed value types cleanly.

---

## Decision 2: Migration Approach

**Decision**: A single Alembic migration (`010_student_contact.py`) that:
1. Adds `parents_infor JSONB NULL` column to `students`.
2. Runs a SQL `UPDATE` to copy data from `parents` into `students.parents_infor` via a JOIN.
3. Drops the `parent_id` foreign key and column from `students`.

The `parents` table itself is **retained** because `parents.user_id` links parents to user accounts (login credentials). Dropping it would break authentication for parent users.

**Rationale**: Data integrity during migration is guaranteed by the SQL UPDATE before the FK drop. The `parents` table is not removed because it serves the auth system.

**Alternatives considered**:
- Drop `parents` table entirely — rejected: `parents.user_id` is a FK to `users`; dropping it would break parent login functionality.
- Two-phase migration (add column now, drop FK later) — rejected: unnecessary complexity for a non-production-critical migration.

---

## Decision 3: Frontend — Collapsible Section Implementation

**Decision**: Use Ant Design `Collapse` component with a single panel titled "Thông tin phụ huynh / Parent Info". The panel is collapsed by default. All parent fields from the existing `ParentFormModal` are moved inline into this panel within the `StudentForm`.

**Rationale**: Ant Design `Collapse` is already available in the project (antd ^6.3.6). It matches the existing design language. No new dependencies needed.

**Alternatives considered**:
- Custom accordion — rejected: unnecessary when antd Collapse fits exactly.
- Always-visible parent section — rejected: user explicitly requested collapsible to reduce visual clutter.

---

## Decision 4: Parent Fields in Student API

**Decision**: `StudentCreate` adds an optional `contact` field (a `ContactInfo` nested Pydantic model). `StudentUpdate` adds the same optional field. `StudentResponse` includes `contact` as a `ContactInfo | None`. The `parent_id` field is removed from all schemas. `ContactInfo` includes: `name` (nullable), `relationship` (nullable free-text), `phone`, `phone_secondary`, `email` (new), `address`, `zalo_id`, `notes`.

**Rationale**: Mirrors the database change. Pydantic v2 handles nested models natively. The `ParentInfo` schema reuses the same fields from the old `ParentCreate` schema.

**Alternatives considered**:
- Flatten contact fields directly on `StudentCreate` with prefixes (e.g., `contact_name`) — rejected: harder to evolve, less clear structure.

---

## Decision 5: `ParentFormModal` disposition

**Decision**: Delete `ParentFormModal.jsx`. It is only used by `StudentForm.jsx`. After the inline collapsible section is added, the modal is unreferenced.

**Rationale**: The spec explicitly removes the separate tab/modal pattern. Keeping unused components creates maintenance burden.

**Alternatives considered**:
- Keep modal for other potential uses — rejected: no other current consumer; YAGNI applies.
