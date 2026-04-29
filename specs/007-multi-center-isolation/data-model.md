# Data Model: Multi-Center Data Isolation

**Date**: 2026-04-29 | **Branch**: `007-multi-center-isolation`

## Overview

No schema changes are needed. All models already have `center_id` foreign keys. This document serves as the authoritative reference for how center scoping is applied to each entity.

## Entity Center Scoping Map

| Entity | Table | Has `center_id` FK | Indexed | Scoping Strategy |
|--------|-------|-------------------|---------|------------------|
| Center | `centers` | N/A (is the tenant) | N/A | Root entity |
| User | `users` | ✅ (nullable for superadmin) | ✅ | `center_id` from JWT user |
| Student | `students` | ✅ | ✅ | Direct filter |
| Teacher | `teachers` | ✅ | ✅ | Direct filter |
| ClassSession | `class_sessions` | ✅ | ✅ | Direct filter |
| ClassEnrollment | `class_enrollments` | ✅ | — | Via class_session + student |
| AttendanceRecord | `attendance_records` | ✅ | ✅ | Direct filter |
| TuitionPayment | `tuition_payments` | ✅ | ✅ | Direct filter |
| TuitionLedgerEntry | `tuition_ledger_entries` | ✅ | ✅ | Direct filter |
| LessonKind | `lesson_kinds` | ✅ | ✅ | Direct filter |
| StudentStatusHistory | `student_status_history` | ✅ | — | Via student |
| TeacherAvailability | `teacher_availabilities` | ❌ | — | Implicit via teacher.center_id |

## Cross-Entity Validation Rules

### Rule 1: Student ↔ ClassSession Center Match

When enrolling a student in a class, verify:
```
student.center_id == class_session.center_id == current_user.center_id
```

**Enforcement point**: `enroll_student()` in `backend/app/crud/class_session.py`

### Rule 2: Teacher ↔ ClassSession Center Match

When assigning a teacher to a class, verify:
```
teacher.center_id == current_user.center_id
```

**Enforcement point**: Already enforced — `create_class_session()` and `update_class_session()` accept `center_id` and create the class with it. The teacher dropdown in the frontend only shows center-scoped teachers. However, no server-side validation exists to reject a teacher_id from another center.

**Fix needed**: Add server-side teacher center validation in `create_class_session()`.

### Rule 3: Scheduling Conflict Scope

Scheduling conflicts must only consider classes within the same center:
```
ClassSession.center_id == current_user.center_id
```

**Enforcement point**: `check_scheduling_conflicts()` in `backend/app/services/schedule_service.py`

## State Transitions

### Center Lifecycle

```
active → deactivated (by superadmin)
deactivated → active (by superadmin, re-activation)
```

**Impact on users**: When a center is deactivated:
1. New logins are blocked (check center.is_active at login)
2. Existing sessions are blocked on next API request (check center.is_active in get_current_user)
3. Center data is preserved (not deleted)

## No Migration Required

All `center_id` columns, foreign keys, and indexes were created in migration `013_multi_tenant_centers.py`. No additional database changes are needed for this feature.
