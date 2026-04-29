# API Isolation Contract: Multi-Center Data Isolation

**Date**: 2026-04-29 | **Branch**: `007-multi-center-isolation`

## Contract Overview

This document defines the isolation guarantees that every API endpoint MUST enforce. No new endpoints are added — this contract specifies behavioral changes to existing endpoints.

## Universal Isolation Rules

### Rule 1: Every center-scoped endpoint MUST call `get_center_id(current_user)`

This extracts the `center_id` from the authenticated user's JWT and raises 403 for superadmin users.

**Already enforced on**: All endpoints in `students.py`, `teachers.py`, `classes.py`, `attendance.py`, `tuition.py`, `schedule.py`, `dashboard.py`, `lesson_kinds.py`.

### Rule 2: Every query MUST include `WHERE center_id = :center_id`

Resource lookups by ID must include center_id in the WHERE clause. This ensures:
- Listing endpoints return only center-scoped results
- Single-resource endpoints return 404 (not 403) for cross-center IDs

### Rule 3: Every write MUST assign `center_id` from the authenticated user

New records created via POST endpoints must have `center_id` set from `get_center_id()`, never from request body.

## Endpoint-Specific Changes

### `DELETE /api/v1/classes/{class_id}` — Gap G1

**Current behavior**: Deletes any class by ID regardless of center.
**Required behavior**: Only delete if `class_session.center_id == current_user.center_id`. Return 404 otherwise.

```
Before: delete_class_session(db, class_id)
After:  delete_class_session(db, class_id, center_id)
```

### `DELETE /api/v1/classes/{class_id}/enroll/{student_id}` — Gap G2

**Current behavior**: Unenrolls any student from any class.
**Required behavior**: Only unenroll if the class belongs to the current user's center. Return 404 otherwise.

```
Before: unenroll_student(db, class_id, student_id)
After:  unenroll_student(db, class_id, student_id, center_id)
```

### `POST /api/v1/classes/{class_id}/enroll` — Gap G4

**Current behavior**: Enrolls any student in any class (no cross-center check).
**Required behavior**: Verify `student.center_id == center_id` before enrolling. Return 404 if student not found in center.

### `POST /api/v1/classes` — Gap G3 (scheduling)

**Current behavior**: `check_scheduling_conflicts()` queries all centers.
**Required behavior**: Pass `center_id` to `check_scheduling_conflicts()` and filter queries.

```
Before: check_scheduling_conflicts(db, teacher_id, day, time, duration, students)
After:  check_scheduling_conflicts(db, teacher_id, day, time, duration, students, center_id=center_id)
```

### `POST /api/v1/auth/login` — Gap G5

**Current behavior**: Only checks `user.is_active`, not `center.is_active`.
**Required behavior**: After user validation, load center and check `center.is_active`. Return 401 "Center is deactivated" if inactive.

### All authenticated endpoints — Gap G6

**Current behavior**: `get_current_user()` checks `user.is_active` only.
**Required behavior**: Also load center (via `user.center_id`) and check `center.is_active`. Return 401 if center inactive. Skip check for superadmin (no center_id).

## Error Response Contract

| Scenario | HTTP Status | Response Body |
|----------|-------------|---------------|
| Access resource from another center | 404 | `{"detail": "<Entity> not found"}` |
| Superadmin accessing center-scoped endpoint | 403 | `{"detail": "Superadmin accounts cannot access center-scoped resources directly."}` |
| User from deactivated center | 401 | `{"detail": "Center is deactivated"}` |
| Login to deactivated center | 401 | `{"detail": "Center is deactivated"}` |
| Cross-center enrollment attempt | 404 | `{"detail": "Student not found"}` |
