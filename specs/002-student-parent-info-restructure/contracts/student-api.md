# API Contract: Students (Updated)

**Feature**: 002-student-parent-info-restructure  
**Date**: 2026-04-27  
**Updated**: 2026-04-27 (clarifications: `parents_infor` → `contact`, added `email` + `relationship`, `full_name` → `name`)  
**Base path**: `/students`

---

## Breaking Changes

| Change                        | Before                                  | After                                           |
|-------------------------------|-----------------------------------------|-------------------------------------------------|
| `StudentCreate.parent_id`     | Required `UUID`                         | **Removed**                                     |
| `StudentCreate.contact`       | Not present                             | Optional nested `ContactInfo` object            |
| `StudentUpdate.contact`       | Not present                             | Optional nested `ContactInfo` object            |
| `StudentResponse.parent_id`   | `UUID`                                  | **Removed**                                     |
| `StudentResponse.contact`     | Not present                             | `ContactInfo \| null`                           |
| `StudentListItem.contact_name`| `parent_name` from JOIN                 | `contact_name` from `contact.name` (JSON field) |

---

## ContactInfo Schema

```json
{
  "name": "string | null",
  "relationship": "string | null",
  "phone": "string | null",
  "phone_secondary": "string | null",
  "email": "string | null",
  "address": "string | null",
  "zalo_id": "string | null",
  "notes": "string | null"
}
```

All fields optional. Entire `contact` object is also optional (can be omitted or `null`).  
`relationship` examples: `"parent"`, `"guardian"`, `"self"`, `"other"`.

---

## POST /students — Create Student

**Request body** (changed):

```json
{
  "name": "Nguyễn Minh Tuấn",
  "nickname": "Tuấn",
  "date_of_birth": "2015-03-10",
  "age": 10,
  "skill_level": "Beginner",
  "enrollment_status": "trial",
  "personality_notes": null,
  "learning_speed": "Normal",
  "current_issues": null,
  "contact": {
    "name": "Nguyễn Văn A",
    "relationship": "parent",
    "phone": "0901234567",
    "phone_secondary": null,
    "email": "nguyen.van.a@example.com",
    "address": "123 Đường Lê Lợi",
    "zalo_id": "0901234567",
    "notes": null
  }
}
```

**Adult self-paying student** (contact name null, relationship "self"):

```json
{
  "name": "Trần Thị Bình",
  "skill_level": "Intermediate",
  "enrollment_status": "active",
  "contact": {
    "name": null,
    "relationship": "self",
    "phone": "0912345678",
    "email": "binh@example.com"
  }
}
```

**Response** `201 Created` — see GET /students/{id} response shape.

---

## PATCH /students/{id} — Update Student

**Request body** (changed):

```json
{
  "contact": {
    "name": "Nguyễn Văn A",
    "relationship": "parent",
    "phone": "0909999999",
    "email": "new.email@example.com"
  }
}
```

The entire `contact` JSON object is replaced when provided. Send all desired fields, not just changed ones.

---

## GET /students/{id} — Get Student Detail

**Response** (changed):

```json
{
  "id": "uuid",
  "name": "Nguyễn Minh Tuấn",
  "nickname": "Tuấn",
  "date_of_birth": "2015-03-10",
  "age": 10,
  "skill_level": "Beginner",
  "enrollment_status": "trial",
  "enrolled_at": "2026-01-15",
  "personality_notes": null,
  "learning_speed": "Normal",
  "current_issues": null,
  "contact": {
    "name": "Nguyễn Văn A",
    "relationship": "parent",
    "phone": "0901234567",
    "phone_secondary": null,
    "email": null,
    "address": "123 Đường Lê Lợi",
    "zalo_id": "0901234567",
    "notes": null
  },
  "created_at": "2026-01-15T08:00:00Z",
  "updated_at": "2026-04-27T10:00:00Z"
}
```

---

## GET /students — List Students

**Response item** (changed — `contact_name` sourced from JSON):

```json
{
  "id": "uuid",
  "name": "Nguyễn Minh Tuấn",
  "nickname": "Tuấn",
  "age": 10,
  "skill_level": "Beginner",
  "enrollment_status": "trial",
  "enrolled_at": "2026-01-15",
  "contact_name": "Nguyễn Văn A"
}
```

---

## Deprecated/Removed Endpoints

| Endpoint          | Status   | Reason                                            |
|-------------------|----------|---------------------------------------------------|
| `GET /parents`    | Retained | Still used for parent user account management     |
| `POST /parents`   | Retained | Still used for creating parent login accounts     |
| `GET /parents/{id}` | Retained | Still used for parent user account lookup       |
| `PATCH /parents/{id}` | Retained | Still used for updating parent account details |
