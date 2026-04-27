# Data Model: Student & Parent Info Restructure

**Feature**: 002-student-parent-info-restructure  
**Date**: 2026-04-27  
**Updated**: 2026-04-27 (clarifications: renamed `parents_infor` → `contact`, added `email` and `relationship` fields)

## Changed Entity: Student

The `Student` entity absorbs contact information as embedded metadata. The FK to the `parents` table is removed.

### students table (after migration)

| Column            | Type         | Constraints                      | Notes                                |
|-------------------|--------------|----------------------------------|--------------------------------------|
| id                | UUID         | PK, default gen_random_uuid()    | Unchanged                            |
| name              | VARCHAR(200) | NOT NULL, indexed                | Unchanged                            |
| nickname          | VARCHAR(100) | NULLABLE                         | Unchanged                            |
| date_of_birth     | DATE         | NULLABLE                         | Unchanged                            |
| age               | INTEGER      | NULLABLE                         | Unchanged                            |
| skill_level       | VARCHAR(50)  | NOT NULL, indexed                | Unchanged                            |
| personality_notes | TEXT         | NULLABLE                         | Unchanged                            |
| learning_speed    | VARCHAR(50)  | NULLABLE                         | Unchanged                            |
| current_issues    | TEXT         | NULLABLE                         | Unchanged                            |
| enrollment_status | VARCHAR(20)  | NOT NULL, default 'trial'        | Unchanged                            |
| enrolled_at       | DATE         | NOT NULL                         | Unchanged                            |
| **contact**       | **JSONB**    | **NULLABLE**                     | **NEW — replaces parent_id FK**      |
| created_at        | TIMESTAMPTZ  | NOT NULL, default now()          | Unchanged                            |
| updated_at        | TIMESTAMPTZ  | NOT NULL, default now()          | Unchanged                            |
| ~~parent_id~~     | ~~UUID FK~~  | ~~NOT NULL, FK→parents.id~~      | **REMOVED**                          |

### contact JSON structure

```json
{
  "name": "Nguyễn Văn A",
  "relationship": "parent",
  "phone": "0901234567",
  "phone_secondary": "0909876543",
  "email": "nguyen.van.a@example.com",
  "address": "123 Đường Lê Lợi, Q1, TP.HCM",
  "zalo_id": "0901234567",
  "notes": "Liên hệ vào buổi chiều"
}
```

**Field notes**:
- All fields are optional (nullable strings).
- `name` is nullable to support adult self-paying students who have no separate guardian.
- `relationship` is free-text (e.g., "parent", "guardian", "self", "other"); nullable.
- `email` is a new field not present in the old `parents` table; migrated records will have `null` for this field.
- An absent contact section is stored as `NULL` in the column (not an empty object).

---

## Retained Entity: Parent (unchanged)

The `parents` table is kept as-is because `parents.user_id` links to `users` for login authentication. No structural changes to this table.

| Column           | Type         | Notes                         |
|------------------|--------------|-------------------------------|
| id               | UUID         | PK                            |
| user_id          | UUID         | FK→users.id, UNIQUE, NULLABLE |
| full_name        | VARCHAR(200) | NOT NULL                      |
| phone            | VARCHAR(20)  | NOT NULL, indexed             |
| phone_secondary  | VARCHAR(20)  | NULLABLE                      |
| address          | TEXT         | NULLABLE                      |
| zalo_id          | VARCHAR(100) | NULLABLE                      |
| notes            | TEXT         | NULLABLE                      |
| created_at       | TIMESTAMPTZ  | NOT NULL                      |
| updated_at       | TIMESTAMPTZ  | NOT NULL                      |

Note: The `students` relationship on `Parent` (ORM `back_populates`) is removed since `students.parent_id` no longer exists.

---

## Migration Plan

**File**: `backend/alembic/versions/010_student_contact.py`

**Upgrade steps**:
1. `ALTER TABLE students ADD COLUMN contact JSONB NULL`
2. Copy data from `parents` table into `contact` column (maps `full_name` → `name`, omits `email` and `relationship` since they don't exist in source):
   ```sql
   UPDATE students s
   SET contact = jsonb_build_object(
     'name', p.full_name,
     'relationship', 'parent',
     'phone', p.phone,
     'phone_secondary', p.phone_secondary,
     'email', null,
     'address', p.address,
     'zalo_id', p.zalo_id,
     'notes', p.notes
   )
   FROM parents p
   WHERE p.id = s.parent_id;
   ```
3. `ALTER TABLE students DROP CONSTRAINT students_parent_id_fkey`
4. `DROP INDEX IF EXISTS ix_students_parent_id`
5. `ALTER TABLE students DROP COLUMN parent_id`

**Downgrade steps** (best-effort — data may be lost if new students were created post-migration):
1. `ALTER TABLE students ADD COLUMN parent_id UUID NULL`
2. Restore FK if parents table still has matching records (not guaranteed)
3. `ALTER TABLE students DROP COLUMN contact`

---

## Pydantic Schemas

### ContactInfo (new, nested)

```python
class ContactInfo(BaseModel):
    name: str | None = None
    relationship: str | None = None  # e.g., "parent", "guardian", "self", "other"
    phone: str | None = None
    phone_secondary: str | None = None
    email: str | None = None
    address: str | None = None
    zalo_id: str | None = None
    notes: str | None = None
```

### StudentCreate (updated)

- Remove: `parent_id: UUID` (required field)
- Add: `contact: ContactInfo | None = None`

### StudentUpdate (updated)

- Add: `contact: ContactInfo | None = None`

### StudentResponse (updated)

- Remove: `parent_id: UUID`
- Add: `contact: ContactInfo | None = None`

### StudentListItem (updated)

- `parent_name: str | None` → renamed to `contact_name: str | None`, sourced from `student.contact.get('name')` instead of `student.parent.full_name`
