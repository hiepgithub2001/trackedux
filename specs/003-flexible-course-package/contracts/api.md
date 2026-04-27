# API Contracts: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Feature**: 003-flexible-course-package
**Date**: 2026-04-27
**Base URL**: `/api/v1`

---

## New Endpoints

### GET `/lesson-kinds`

List all lesson kinds from the vocabulary. Supports optional search for typeahead.

**Auth**: Any authenticated user (admin, staff)
**Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `search` | `string` | No | Case-insensitive substring match against lesson kind names. Returns all if omitted. |

**Response** `200 OK`:
```json
[
  {
    "id": "uuid",
    "name": "Beginner",
    "created_at": "2026-04-27T10:00:00Z"
  },
  {
    "id": "uuid",
    "name": "Advanced",
    "created_at": "2026-04-27T10:00:00Z"
  }
]
```

**Notes**: Lesson kinds have no lifecycle management — no POST/PUT/DELETE endpoints for standalone CRUD. New lesson kinds are created inline during package creation only.

---

### DELETE `/classes/{class_id}`

Delete a class session. Admin only. Blocked if any package references this class.

**Auth**: Admin only
**Path Parameters**: `class_id` (UUID)

**Response** `200 OK`:
```json
{ "detail": "Class deleted" }
```

**Error** `409 Conflict`:
```json
{
  "detail": "Cannot delete class with associated packages. Deactivate referencing packages first."
}
```

**Error** `404 Not Found`:
```json
{ "detail": "Class not found" }
```

---

## Modified Endpoints

### GET `/classes`

**Changes**: Response includes `tuition_fee_per_lesson`, `display_id`, and `enrolled_count`.

**New Query Parameters**: None (existing: `teacher_id`, `day_of_week`, `is_active`).

**Response** `200 OK` — Updated shape per item:
```json
{
  "id": "uuid",
  "teacher_id": "uuid",
  "name": "Piano Basics",
  "day_of_week": 0,
  "start_time": "17:30",
  "duration_minutes": 60,
  "end_time": "18:30",
  "is_recurring": true,
  "is_makeup": false,
  "is_active": true,
  "teacher_name": "Jane Doe",
  "display_id": "Jane-Mon-1730",
  "enrolled_count": 3,
  "tuition_fee_per_lesson": 200000,
  "enrolled_students": [
    { "id": "uuid", "name": "Alice" }
  ],
  "created_at": "...",
  "updated_at": "..."
}
```

**Role-based visibility**:
- `tuition_fee_per_lesson`: Visible to admin only. Returns `null` for staff/parent.

---

### POST `/classes`

**Changes**: Request body adds optional `tuition_fee_per_lesson`.

**Request body** (updated):
```json
{
  "teacher_id": "uuid",
  "name": "Piano Basics",
  "day_of_week": 0,
  "start_time": "17:30",
  "duration_minutes": 60,
  "is_recurring": true,
  "student_ids": ["uuid"],
  "tuition_fee_per_lesson": 200000
}
```

**Validation** (new field):
- `tuition_fee_per_lesson`: Optional on create (nullable for backward compat). When provided: positive integer, max 100,000,000 VND.

---

### PUT `/classes/{class_id}`

**Changes**: Update body adds optional `tuition_fee_per_lesson`.

**Request body** (updated):
```json
{
  "name": "Piano Basics Updated",
  "day_of_week": 1,
  "start_time": "18:00",
  "duration_minutes": 45,
  "is_active": true,
  "tuition_fee_per_lesson": 250000
}
```

**Note**: Currently this endpoint doesn't exist in the codebase. It needs to be created as part of this feature.

---

### GET `/classes/{class_id}`

**Changes**: Response includes `tuition_fee_per_lesson`, `display_id`, and `enrolled_count` (same shape as list endpoint).

---

### GET `/packages`

**Changes**: Response shape restructured. Drops `package_type`; adds class and lesson kind info.

**New Query Parameters**:

| Param | Type | Required | Description |
|-------|------|----------|-------------|
| `class_session_id` | `UUID` | No | Filter by class |

**Response** `200 OK` — Updated shape per item:
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "student_name": "Alice",
  "class_session_id": "uuid",
  "class_display_id": "Jane-Mon-1730",
  "lesson_kind_id": "uuid",
  "lesson_kind_name": "Beginner",
  "number_of_lessons": 18,
  "remaining_sessions": 15,
  "price": 3600000,
  "payment_status": "partial",
  "is_active": true,
  "reminder_status": "none",
  "started_at": "2026-04-27",
  "expired_at": null,
  "created_at": "...",
  "updated_at": "..."
}
```

**Role-based visibility**:
- `price`: Visible to admin only. Returns `null` for staff/parent.

**Dropped fields**: `package_type`, `total_sessions` (replaced by `number_of_lessons`)

---

### POST `/packages`

**Changes**: Request body restructured. Supports atomic inline lesson kind creation.

**Auth**: Admin only

**Request body** (new):
```json
{
  "student_id": "uuid",
  "class_session_id": "uuid",
  "number_of_lessons": 18,
  "lesson_kind_name": "Beginner",
  "tuition_fee": 3600000
}
```

**Validation**:

| Field | Rule | Error |
|-------|------|-------|
| `student_id` | Required UUID, must exist | 404 "Student not found" |
| `class_session_id` | Required UUID, must exist | 404 "Class not found" |
| `number_of_lessons` | Required, positive integer, 1–500 | 422 validation error |
| `lesson_kind_name` | Required, 1–100 chars, not blank after trim | 422 validation error |
| `tuition_fee` | Required, positive integer, 1–1,000,000,000 VND | 422 validation error |
| Enrollment check | Student must be enrolled in the class | 422 `"Student {name} is not enrolled in {display_id}. Enroll the student first."` |

**Behavior**:
1. Normalize `lesson_kind_name` (trim, collapse whitespace).
2. Find existing lesson kind by `LOWER(normalized_name)`. If not found, create inline (atomic with package save).
3. Check that student is enrolled in the class via `class_enrollments`.
4. Deactivate any existing active package for the same student.
5. Create package with `remaining_sessions = number_of_lessons`.

**Response** `201 Created`: Same shape as GET `/packages` response item.

**Error** `422 Unprocessable Entity` (enrollment check):
```json
{
  "detail": "Student Alice is not enrolled in Jane-Mon-1730. Enroll the student in the class first."
}
```

---

### GET `/students`, POST `/students`, PUT `/students/{id}`, GET `/students/{id}`

**Changes**: Drop `skill_level` from all request and response schemas.

**StudentCreate** (updated):
```json
{
  "name": "Alice",
  "nickname": "Ali",
  "date_of_birth": "2015-03-15",
  "age": 11,
  "personality_notes": "Currently at intermediate level, struggles with sight-reading",
  "learning_speed": "average",
  "current_issues": null,
  "enrollment_status": "active",
  "contact": { "name": "Mom", "phone": "0901234567" }
}
```

**StudentResponse** / **StudentListItem**: `skill_level` field removed.

---

## Endpoint Summary

| Method | Endpoint | Status | Auth | Description |
|--------|----------|--------|------|-------------|
| GET | `/lesson-kinds` | NEW | Any | List/search lesson kinds |
| GET | `/classes` | MODIFIED | Any | List classes with display_id + fee |
| POST | `/classes` | MODIFIED | Admin | Create class with optional fee |
| PUT | `/classes/{id}` | NEW | Admin | Update class (including fee) |
| GET | `/classes/{id}` | MODIFIED | Any | Class detail with display_id + fee |
| DELETE | `/classes/{id}` | NEW | Admin | Delete class (blocked if packages exist) |
| GET | `/packages` | MODIFIED | Any | List packages with class + kind info |
| POST | `/packages` | MODIFIED | Admin | Create package with enrollment check |
| POST | `/packages/{id}/payments` | UNCHANGED | Admin | Record payment |
| GET | `/students` | MODIFIED | Any | Drop skill_level |
| POST | `/students` | MODIFIED | Admin | Drop skill_level |
| PUT | `/students/{id}` | MODIFIED | Admin | Drop skill_level |
| GET | `/students/{id}` | MODIFIED | Any | Drop skill_level |
