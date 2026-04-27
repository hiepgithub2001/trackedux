# API Contracts: Piano Center Management System

**Phase**: 1 — Design & Contracts  
**Date**: 2026-04-27  
**Base URL**: `/api/v1`  
**Auth**: Bearer JWT token in `Authorization` header

> **Session policy (Phase 1, clarification 2026-04-27)**: admin/staff sessions persist until manual logout. The access token is issued with a long lifetime (recommend 30 days) and the refresh token is rotated only on explicit logout. No idle-timeout enforcement, no account lockout. Phase 2 (parent portal) will revisit this.

---

## Authentication

### POST `/api/v1/auth/login`

Login and receive JWT tokens.

**Request**:
```json
{
  "username": "string",
  "password": "string"
}
```

**Response 200**:
```json
{
  "access_token": "string",
  "refresh_token": "string",
  "token_type": "bearer",
  "user": {
    "id": "uuid",
    "username": "string",
    "full_name": "string",
    "role": "admin | staff | parent",
    "language": "vi | en"
  }
}
```

**Response 401**: `{ "detail": "Invalid credentials" }`

### POST `/api/v1/auth/refresh`

Refresh access token.

**Request**:
```json
{
  "refresh_token": "string"
}
```

**Response 200**: Same as login response.

### POST `/api/v1/auth/logout`

Invalidate refresh token.

**Response 200**: `{ "detail": "Logged out" }`

### GET `/api/v1/auth/me`

Get current user profile.

**Response 200**: User object (same as login response `user` field).

---

## Students

### GET `/api/v1/students`

List students with filtering and sorting.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `status` | string | Filter by enrollment_status |
| `skill_level` | string | Filter by skill level |
| `search` | string | Search by name/nickname (unaccented) |
| `sort_by` | string | Field to sort by (name, skill_level, enrolled_at) |
| `sort_order` | string | asc / desc |
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Items per page (default: 20, max: 100) |

**Response 200**:
```json
{
  "items": [
    {
      "id": "uuid",
      "name": "string",
      "nickname": "string | null",
      "age": "integer | null",
      "skill_level": "string",
      "enrollment_status": "trial | active | paused | withdrawn",
      "parent_name": "string",
      "active_package": {
        "remaining_sessions": "integer",
        "payment_status": "paid | unpaid"
      } | null,
      "enrolled_at": "date"
    }
  ],
  "total": "integer",
  "page": "integer",
  "page_size": "integer"
}
```

**RBAC**: Staff sees all fields except `parent_contact` details (hidden in detail view).

### GET `/api/v1/students/{id}`

Get student detail.

**Response 200**:
```json
{
  "id": "uuid",
  "name": "string",
  "nickname": "string | null",
  "date_of_birth": "date | null",
  "age": "integer | null",
  "skill_level": "string",
  "personality_notes": "string | null",
  "learning_speed": "string | null",
  "current_issues": "string | null",
  "enrollment_status": "trial | active | paused | withdrawn",
  "enrolled_at": "date",
  "parent": {
    "id": "uuid",
    "full_name": "string",
    "phone": "string (admin only)",
    "address": "string | null (admin only)"
  },
  "active_package": { "..." } | null,
  "classes": [{ "..." }],
  "created_at": "datetime",
  "updated_at": "datetime"
}
```

### POST `/api/v1/students`

Create a new student. **Role**: Admin, Staff.

**Request**:
```json
{
  "name": "string (required)",
  "nickname": "string | null",
  "date_of_birth": "date | null",
  "age": "integer | null",
  "skill_level": "string (required)",
  "personality_notes": "string | null",
  "learning_speed": "string | null",
  "current_issues": "string | null",
  "enrollment_status": "trial (default)",
  "parent_id": "uuid (required)"
}
```

**Response 201**: Created student object.

### PATCH `/api/v1/students/{id}`

Update student fields. **Role**: Admin, Staff.

**Request**: Partial student object (only fields to update).

**Response 200**: Updated student object.

### PATCH `/api/v1/students/{id}/status`

Change enrollment status (creates audit trail). **Role**: Admin.

**Request**:
```json
{
  "status": "trial | active | paused | withdrawn",
  "reason": "string | null"
}
```

**Response 200**: Updated student with new status.

---

## Parents

### GET `/api/v1/parents`

List parents. **Role**: Admin.

### GET `/api/v1/parents/{id}`

Get parent detail. **Role**: Admin.

### POST `/api/v1/parents`

Create parent. **Role**: Admin.

**Request**:
```json
{
  "full_name": "string (required)",
  "phone": "string (required)",
  "phone_secondary": "string | null",
  "address": "string | null",
  "notes": "string | null"
}
```

### PATCH `/api/v1/parents/{id}`

Update parent. **Role**: Admin.

---

## Teachers

### GET `/api/v1/teachers`

List teachers. **Role**: Admin, Staff.

### GET `/api/v1/teachers/{id}`

Get teacher detail with availability. **Role**: Admin, Staff.

**Response 200**:
```json
{
  "id": "uuid",
  "full_name": "string",
  "phone": "string | null",
  "email": "string | null",
  "is_active": "boolean",
  "availability": [
    {
      "day_of_week": "integer (0-6)",
      "start_time": "HH:MM",
      "end_time": "HH:MM"
    }
  ],
  "classes": [{ "..." }]
}
```

### POST `/api/v1/teachers`

Create teacher. **Role**: Admin.

### PATCH `/api/v1/teachers/{id}`

Update teacher. **Role**: Admin.

### PUT `/api/v1/teachers/{id}/availability`

Replace availability slots. **Role**: Admin.

**Request**:
```json
{
  "slots": [
    {
      "day_of_week": "integer (0-6)",
      "start_time": "HH:MM",
      "end_time": "HH:MM"
    }
  ]
}
```

---

## Classes & Scheduling

### GET `/api/v1/classes`

List classes with optional filters.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `teacher_id` | uuid | Filter by teacher |
| `day_of_week` | integer | 0-6 |
| `is_active` | boolean | Active only |

> Note (clarification 2026-04-27): the `class_type` filter is removed — classes have no type classification.

### GET `/api/v1/classes/{id}`

Get class detail with enrolled students.

**Response 200** (excerpt):
```json
{
  "id": "uuid",
  "name": "string",
  "teacher": { "id": "uuid", "full_name": "string" },
  "day_of_week": 0,
  "start_time": "HH:MM",
  "duration_minutes": 60,
  "end_time": "HH:MM",
  "is_recurring": true,
  "is_makeup": false,
  "students": [{ "id": "uuid", "name": "string" }]
}
```
`end_time` is derived (`start_time + duration_minutes`), returned for client convenience.

### POST `/api/v1/classes`

Create a class session. **Role**: Admin.

**Request**:
```json
{
  "teacher_id": "uuid (required)",
  "name": "string (required)",
  "day_of_week": "integer 0-6 (required)",
  "start_time": "HH:MM (required)",
  "duration_minutes": "integer >= 1 (required)",
  "is_recurring": "boolean (default: true)",
  "student_ids": ["uuid"]
}
```

**Response 409**: `{ "detail": "Scheduling conflict", "conflicts": [...] }` if student or teacher has overlapping sessions. Overlap is computed against the half-open range `[start_time, start_time + duration_minutes)`.

### PATCH `/api/v1/classes/{id}`

Update class. **Role**: Admin.

### POST `/api/v1/classes/{id}/enroll`

Add student to class. **Role**: Admin.

**Request**:
```json
{
  "student_id": "uuid"
}
```

**Response 409**: Time overlap conflict with another class the student is already enrolled in.

> Note (clarification 2026-04-27): the previous `422 Class at max capacity` response is removed — classes have no upper bound on student count.

### DELETE `/api/v1/classes/{id}/enroll/{student_id}`

Remove student from class. **Role**: Admin.

### GET `/api/v1/schedule/weekly`

Weekly calendar view data.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `week_start` | date | Start of the week (Monday) |
| `teacher_id` | uuid | Filter by teacher |

**Response 200**:
```json
{
  "week_start": "date",
  "week_end": "date",
  "sessions": [
    {
      "id": "uuid",
      "name": "string",
      "teacher": { "id": "uuid", "full_name": "string" },
      "students": [{ "id": "uuid", "name": "string" }],
      "day_of_week": "integer",
      "start_time": "HH:MM",
      "duration_minutes": "integer",
      "end_time": "HH:MM (derived)",
      "date": "date",
      "is_makeup": "boolean",
      "attendance_marked": "boolean"
    }
  ]
}
```

---

## Attendance

### GET `/api/v1/attendance`

List attendance records with filters.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `student_id` | uuid | Filter by student |
| `class_session_id` | uuid | Filter by class |
| `date_from` | date | Start date range |
| `date_to` | date | End date range |
| `status` | string | Filter by attendance status |

### POST `/api/v1/attendance/batch`

Mark attendance for a class session (batch). **Role**: Admin, Staff.

**Request**:
```json
{
  "class_session_id": "uuid",
  "session_date": "date",
  "records": [
    {
      "student_id": "uuid",
      "status": "present | absent | absent_with_notice",
      "notes": "string | null"
    }
  ]
}
```

**Response 200**:
```json
{
  "records": [
    {
      "student_id": "uuid",
      "status": "string",
      "package_remaining": "integer | null",
      "renewal_reminder_triggered": "boolean"
    }
  ]
}
```

### POST `/api/v1/attendance/{id}/makeup`

Schedule a makeup session for an absence. **Role**: Admin.

**Request**:
```json
{
  "date": "date",
  "start_time": "HH:MM",
  "end_time": "HH:MM",
  "teacher_id": "uuid"
}
```

---

## Packages & Tuition

### GET `/api/v1/packages`

List packages with filters.

**Query Parameters**:
| Param | Type | Description |
|-------|------|-------------|
| `student_id` | uuid | Filter by student |
| `payment_status` | string | paid / unpaid |
| `is_active` | boolean | Active packages only |

### POST `/api/v1/packages`

Create a package for a student. **Role**: Admin.

**Request**:
```json
{
  "student_id": "uuid (required)",
  "total_sessions": "integer (required, min: 1)",
  "package_type": "12 | 24 | 36 | custom",
  "price": "integer (VND, required)"
}
```

**Response 422**: `total_sessions` is 0 or negative.

### PATCH `/api/v1/packages/{id}/payment`

Record payment. **Role**: Admin.

**Request**:
```json
{
  "amount": "integer (VND)",
  "payment_date": "date",
  "payment_method": "string | null",
  "notes": "string | null"
}
```

### GET `/api/v1/tuition/owing`

List students with owing status (negative remaining sessions). **Role**: Admin.

### GET `/api/v1/tuition/expiring`

List students nearing package end (≤2 sessions remaining). **Role**: Admin.

---

## Dashboard

### GET `/api/v1/dashboard`

Dashboard metrics. **Role**: Admin, Staff (revenue hidden for Staff).

**Response 200**:
```json
{
  "active_students": "integer",
  "today_sessions": "integer",
  "today_absences": "integer",
  "expiring_packages": "integer",
  "monthly_revenue": "integer | null (admin only, VND)",
  "today_date": "date"
}
```

---

## Parent Portal (Phase 2)

### GET `/api/v1/portal/children`

List parent's children. **Role**: Parent.

### GET `/api/v1/portal/children/{id}`

Child detail with schedule, attendance, package info. **Role**: Parent (own children only).

### GET `/api/v1/portal/children/{id}/notes`

Session notes for a child. **Role**: Parent (own children only).

---

## Reports (Phase 2)

### GET `/api/v1/reports/monthly`

Monthly report data. **Role**: Admin.

**Query Parameters**: `month` (YYYY-MM)

**Response 200**:
```json
{
  "month": "string",
  "total_revenue": "integer (VND)",
  "new_students": "integer",
  "attendance_rate": "float (%)",
  "dropout_rate": "float (%)",
  "revenue_chart": [
    { "month": "string", "revenue": "integer" }
  ]
}
```

---

## Common Response Patterns

### Pagination Wrapper
```json
{
  "items": [],
  "total": "integer",
  "page": "integer",
  "page_size": "integer"
}
```

### Error Response
```json
{
  "detail": "string",
  "errors": [
    {
      "field": "string",
      "message": "string"
    }
  ]
}
```

### HTTP Status Codes
| Code | Usage |
|------|-------|
| 200 | Success |
| 201 | Created |
| 400 | Validation error |
| 401 | Unauthorized |
| 403 | Forbidden (wrong role) |
| 404 | Not found |
| 409 | Conflict (scheduling) |
| 422 | Unprocessable entity |
| 500 | Server error |
