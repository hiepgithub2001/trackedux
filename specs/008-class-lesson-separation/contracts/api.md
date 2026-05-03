# API Contracts: Class / Lesson Separation (008)

**Base URL**: `/api/v1`  
**Auth**: All endpoints require `Authorization: Bearer <token>` (existing JWT scheme).  
**Multi-tenancy**: `center_id` is derived from the authenticated user; never passed as a query param.

---

## Classes

### `GET /classes`
List all classes for the current center.

**Query params**: `is_active=true|false`, `teacher_id=<uuid>`  
**Response 200**:
```json
[
  {
    "id": "uuid",
    "name": "Piano Beginner Group A",
    "teacher_id": "uuid",
    "teacher_name": "Nguyen Van A",
    "tuition_fee_per_lesson": 150000,
    "lesson_kind_id": "uuid|null",
    "lesson_kind_name": "string|null",
    "is_active": true,
    "enrolled_count": 5,
    "enrolled_students": [{"id": "uuid", "name": "string"}],
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
]
```
> `tuition_fee_per_lesson` is `null` for non-admin roles.

---

### `POST /classes`
Create a class (admin only).

**Request**:
```json
{
  "name": "Piano Beginner Group A",
  "teacher_id": "uuid",
  "tuition_fee_per_lesson": 150000,
  "lesson_kind_id": "uuid|null",
  "student_ids": ["uuid"]
}
```
**Response 201**: ClassResponse (same as GET item shape).  
**Response 409**: Scheduling conflict (if any student conflicts).

---

### `GET /classes/{class_id}`
Get class detail.  
**Response 200**: ClassResponse.  
**Response 404**: Not found.

---

### `PUT /classes/{class_id}`
Update class (admin only).  
**Request**: Partial update (same fields as POST, all optional).  
**Response 200**: Updated ClassResponse.

---

### `DELETE /classes/{class_id}`
Soft-delete class (`is_active = false`). Admin only.  
**Response 200**: `{"detail": "Class deactivated"}`.

---

### `POST /classes/{class_id}/enroll`
Enroll a student (admin only). 409 on time-overlap conflict.

**Request**: `{"student_id": "uuid", "enrolled_since": "YYYY-MM-DD|null"}`  
**Response 200**: `{"detail": "Student enrolled"}`.

---

### `DELETE /classes/{class_id}/enroll/{student_id}`
Unenroll a student (admin only).  
**Request body (optional)**: `{"unenrolled_at": "YYYY-MM-DD|null"}`  
**Response 200**: `{"detail": "Student unenrolled"}`.

---

## Lessons

### `GET /lessons`
List lessons for the current center.

**Query params**: `class_id=<uuid>`, `teacher_id=<uuid>`, `is_active=true|false`  
**Response 200**:
```json
[
  {
    "id": "uuid",
    "class_id": "uuid|null",
    "class_name": "string|null",
    "teacher_id": "uuid",
    "title": "string|null",
    "start_time": "HH:MM",
    "duration_minutes": 60,
    "day_of_week": 0,
    "specific_date": "YYYY-MM-DD|null",
    "rrule": "FREQ=WEEKLY;BYDAY=MO;COUNT=10|null",
    "is_active": true,
    "created_at": "ISO8601",
    "updated_at": "ISO8601"
  }
]
```

---

### `POST /lessons`
Create a lesson (admin only).

**Request**:
```json
{
  "class_id": "uuid|null",
  "teacher_id": "uuid",
  "title": "string|null",
  "start_time": "HH:MM",
  "duration_minutes": 60,
  "specific_date": "YYYY-MM-DD|null",
  "rrule": "FREQ=WEEKLY;BYDAY=MO;COUNT=10|null"
}
```
> Exactly one of `specific_date` / `rrule` must be provided.

**Response 201**: LessonResponse.  
**Response 409**: Scheduling conflict.  
**Response 422**: Validation error (e.g. both/neither of `specific_date`/`rrule`).

---

### `GET /lessons/{lesson_id}`
Get lesson detail.  
**Response 200**: LessonResponse.

---

### `PATCH /lessons/{lesson_id}`
Edit the recurring series (admin only).

**Request**:
```json
{
  "scope": "series",
  "start_time": "HH:MM",
  "duration_minutes": 60,
  "rrule": "FREQ=WEEKLY;BYDAY=TU;COUNT=10"
}
```
> `scope: "series"` is required. Existing `LessonOccurrence` records are NOT modified.

**Response 200**: Updated LessonResponse.  
**Response 409**: Scheduling conflict.

---

### `DELETE /lessons/{lesson_id}`
Soft-delete lesson. Admin only.  
**Response 200**: `{"detail": "Lesson deactivated"}`.

---

## Lesson Occurrences (Per-Occurrence Overrides)

### `GET /lessons/{lesson_id}/occurrences/{original_date}`
Get override record for one occurrence.  
**Response 200**:
```json
{
  "id": "uuid",
  "lesson_id": "uuid",
  "original_date": "YYYY-MM-DD",
  "status": "active|canceled",
  "override_date": "YYYY-MM-DD|null",
  "override_start_time": "HH:MM|null",
  "center_id": "uuid"
}
```
**Response 404**: No override record (occurrence is still virtual — treat as `active`).

---

### `PATCH /lessons/{lesson_id}/occurrences/{original_date}`
Cancel or reschedule a single occurrence (admin only). Creates or updates the override record.

**Request** (cancel):
```json
{"action": "cancel"}
```
**Request** (reschedule):
```json
{
  "action": "reschedule",
  "override_date": "YYYY-MM-DD",
  "override_start_time": "HH:MM|null"
}
```
**Request** (revert to series):
```json
{"action": "revert"}
```
**Response 200**: OccurrenceResponse.  
**Response 409**: Scheduling conflict (on reschedule).  
**Response 403**: Not admin.

---

## Schedule

### `GET /schedule/weekly`
Get weekly view (expanded occurrences). Existing endpoint — updated response shape.

**Query params**: `week_start=YYYY-MM-DD` (defaults to current Monday), `teacher_id=<uuid>`  
**Response 200**:
```json
{
  "week_start": "YYYY-MM-DD",
  "week_end": "YYYY-MM-DD",
  "sessions": [
    {
      "id": "uuid",
      "lesson_id": "uuid",
      "class_id": "uuid|null",
      "name": "string",
      "teacher": {"id": "uuid", "full_name": "string", "color": "string|null"},
      "students": [{"id": "uuid", "name": "string"}],
      "day_of_week": 0,
      "start_time": "HH:MM",
      "end_time": "HH:MM",
      "duration_minutes": 60,
      "date": "YYYY-MM-DD",
      "effective_date": "YYYY-MM-DD",
      "is_canceled": false,
      "is_rescheduled": false,
      "original_date": "YYYY-MM-DD|null",
      "attendance_marked": false,
      "occurrence_id": "uuid|null"
    }
  ]
}
```
> `effective_date` = `override_date` if rescheduled, else `original_date`.  
> Canceled occurrences are omitted from the response (or included with `is_canceled: true` — implementation decision for planning phase).

---

## Attendance (updated)

### `POST /attendance/batch`
Mark attendance for a lesson occurrence. *(Existing endpoint — request body updated.)*

**Request**:
```json
{
  "lesson_id": "uuid",
  "session_date": "YYYY-MM-DD",
  "records": [
    {"student_id": "uuid", "status": "present|absent|absent_with_notice", "charge_fee": true, "notes": "string|null"}
  ]
}
```
> `session_date` = the `effective_date` of the occurrence (i.e. `override_date` if rescheduled).

**Response 200**: `{"records": [...]}` (unchanged shape).

---

### `GET /attendance/session/{lesson_id}/{session_date}`
Get attendance for a lesson occurrence. *(Existing endpoint — path param updated from `class_session_id` to `lesson_id`.)*

**Response 200**: List of attendance records (unchanged shape).
