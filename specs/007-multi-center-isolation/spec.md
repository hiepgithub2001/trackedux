# Feature Specification: Multi-Center Data Isolation

**Feature Branch**: `007-multi-center-isolation`  
**Created**: 2026-04-29  
**Status**: Draft  
**Input**: User description: "We need to separate data (student, teacher, classes, tuition, ...) from different centers."

## Clarifications

### Session 2026-04-29

- Q: When a center is deactivated while its admin is logged in, what happens to active sessions? → A: Block access on next API request by checking the center's `is_active` flag during authentication. Existing JWT tokens are not immediately revoked; the deactivation takes effect the next time any API call is made.
- Q: When a center admin attempts to access a resource belonging to another center, should the system return 404 or 403? → A: Return 404 Not Found to hide resource existence from other tenants and prevent enumeration attacks.
- Q: Do staff users have the same center isolation as admin users, or different permissions? → A: Staff has identical center isolation as admin. Intra-center permission differentiation (e.g., restricting staff from financial data) is out of scope and will be managed in a future spec.

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Center Admin Sees Only Their Own Students, Teachers, and Classes (Priority: P1)

A center administrator logs in and navigates through the application — viewing students, teachers, classes, schedules, attendance, and tuition pages. Every data record they see belongs exclusively to their own center. They have no awareness that other centers or their data exist. If two centers happen to have a student with the same name, each center admin only sees their own record.

**Why this priority**: Data isolation is the core security guarantee. If center A can see center B's students or financial data, the entire multi-tenant system is unsafe. This is the foundational requirement that makes multi-center operation viable.

**Independent Test**: Create two centers (Center A and Center B). Add students, teachers, classes, and tuition records under each. Log in as Center A's admin and verify every page shows only Center A's data. Log in as Center B's admin and verify the same for Center B.

**Acceptance Scenarios**:

1. **Given** two centers exist, each with their own students, **When** Center A's admin navigates to the Students page, **Then** they see only Center A's students — none of Center B's records appear.
2. **Given** two centers exist, each with their own teachers, **When** Center A's admin navigates to the Teachers page, **Then** they see only Center A's teachers.
3. **Given** two centers exist, each with their own classes, **When** Center A's admin navigates to the Classes page, **Then** they see only classes belonging to Center A (taught by Center A's teachers, containing Center A's students).
4. **Given** two centers exist, each with tuition payments and ledger entries, **When** Center A's admin navigates to the Tuition page, **Then** they see only Center A's student balances and payment history.
5. **Given** two centers exist, each with attendance records, **When** Center A's admin navigates to the Attendance page, **Then** they see only attendance records for Center A's classes and students.
6. **Given** two centers exist with a student named "Nguyễn Văn A" in each, **When** each center admin views their Students page, **Then** each admin sees exactly one "Nguyễn Văn A" — their own center's record.

---

### User Story 2 — Center Admin Creates Records Scoped to Their Center (Priority: P1)

When a center administrator creates a new student, teacher, class, or records a tuition payment, the new record is automatically associated with their center. The admin does not need to select a center manually — the system infers it from their login session. The newly created record is immediately visible to that center's admin and invisible to other centers.

**Why this priority**: Equally critical to reading isolated data is ensuring writes are properly scoped. If a center admin creates a student that accidentally belongs to another center, data integrity is broken.

**Independent Test**: Log in as Center A's admin, create a new student, then log in as Center B's admin and confirm the student is not visible. Log back in as Center A and confirm the student is present.

**Acceptance Scenarios**:

1. **Given** Center A's admin is logged in, **When** they create a new student, **Then** the student is automatically assigned to Center A and appears in Center A's student list.
2. **Given** Center A's admin created a student, **When** Center B's admin views their student list, **Then** Center A's new student does not appear.
3. **Given** Center A's admin is logged in, **When** they create a new teacher, **Then** the teacher is assigned to Center A and only visible within Center A.
4. **Given** Center A's admin is logged in, **When** they create a new class, **Then** only Center A's teachers are available for assignment, and the class is scoped to Center A.
5. **Given** Center A's admin is logged in, **When** they record a tuition payment, **Then** only Center A's students appear in the student selection, and the payment is scoped to Center A.

---

### User Story 3 — Schedule and Dashboard Show Center-Scoped Data (Priority: P2)

The weekly schedule calendar and the dashboard display data filtered to the logged-in user's center. The schedule shows only classes belonging to the center. The dashboard metrics (active students count, class count, attendance rates, tuition balances) reflect only the center's own data.

**Why this priority**: Schedule and dashboard are the most frequently visited pages. Showing cross-center data here would be immediately confusing and would violate tenant isolation in the most visible way.

**Independent Test**: Create two centers with different class counts and student counts. Log in as each center admin and verify the dashboard numbers match only that center's data. Verify the schedule calendar shows only that center's classes.

**Acceptance Scenarios**:

1. **Given** Center A has 5 active students and Center B has 10, **When** Center A's admin views the dashboard, **Then** the active students metric shows 5.
2. **Given** Center A has 3 classes and Center B has 7, **When** Center A's admin views the schedule, **Then** only 3 classes appear on the calendar.
3. **Given** Center A has recent attendance records, **When** Center A's admin views the dashboard, **Then** the attendance summary reflects only Center A's data.
4. **Given** Center A has tuition balances, **When** Center A's admin views the dashboard, **Then** the financial summary reflects only Center A's tuition data.

---

### User Story 4 — Superadmin Cannot Access Center-Scoped Data Directly (Priority: P3)

The system administrator (superadmin) can manage centers (create, activate, deactivate) but cannot directly view or modify center-scoped data (students, teachers, classes, tuition, attendance). The superadmin's navigation shows only the System Admin console, not the center-specific operational pages.

**Why this priority**: Clear role separation prevents the superadmin from accidentally viewing or modifying a center's data. This is important for trust and compliance, but the center isolation (P1/P2) must work correctly first.

**Independent Test**: Log in as superadmin and attempt to navigate to any center-scoped page (students, teachers, classes, etc.). Verify the system blocks access or redirects to the System Admin console.

**Acceptance Scenarios**:

1. **Given** the superadmin is logged in, **When** they attempt to access the Students page, **Then** the system denies access and redirects them to the System Admin console.
2. **Given** the superadmin is logged in, **When** they view the navigation, **Then** they see only the System Admin menu items (Center Management), not operational pages (Students, Teachers, Classes, etc.).
3. **Given** the superadmin is logged in, **When** they attempt to call any center-scoped API directly, **Then** the system returns a 403 Forbidden error.

---

### Edge Cases

- When a center is deactivated while its admin is logged in, access is blocked on the next API request (center `is_active` check during auth). Existing JWT tokens are not immediately revoked.
- When a center admin’s JWT token is used to access an API endpoint with a different center’s resource ID, the system returns 404 Not Found (does not reveal resource existence to other tenants).
- How does the system handle concurrent record creation across two centers — do they ever interfere?
- What happens when a student is enrolled in a class — does the system verify both belong to the same center?
- What happens if lesson kinds (course types) are created with the same name in two different centers — are they kept separate?
- How does the system handle a center admin trying to assign a teacher from another center to their class?

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST filter all data queries (students, teachers, classes, attendance, tuition, schedules, lesson kinds) by the logged-in user's `center_id`.
- **FR-002**: System MUST automatically assign the logged-in user's `center_id` to every new record created through the application (students, teachers, classes, payments, attendance records, lesson kinds).
- **FR-003**: System MUST prevent a center admin from accessing, viewing, or modifying records belonging to another center, even if they know the record’s ID. Cross-center access attempts MUST return 404 Not Found (not 403 Forbidden) to prevent resource enumeration.
- **FR-004**: System MUST enforce cross-entity center consistency — when enrolling a student in a class, both the student and the class must belong to the same center.
- **FR-005**: System MUST enforce cross-entity center consistency — when assigning a teacher to a class, both the teacher and the class must belong to the same center.
- **FR-006**: System MUST block superadmin accounts from accessing center-scoped API endpoints (students, teachers, classes, tuition, attendance), returning a clear permission error.
- **FR-007**: System MUST display only center-scoped navigation for center admins and staff — no visibility of system administration features or other centers.
- **FR-008**: System MUST scope dashboard metrics (student count, class count, attendance rates, tuition balances) to the logged-in user's center.
- **FR-009**: System MUST scope the weekly schedule calendar to only show classes belonging to the logged-in user's center.
- **FR-010**: System MUST ensure lesson kinds (course types) are isolated per center — each center manages its own vocabulary independently.
- **FR-011**: System MUST handle deactivated centers gracefully — users of a deactivated center MUST be unable to log in, and active sessions MUST be blocked on the next API request by checking the center's `is_active` flag during authentication (no immediate token revocation required).

### Key Entities

- **Center**: A tenant representing one educational center. All operational data (students, teachers, classes, etc.) belongs to exactly one center.
- **Student**: A learner enrolled at a specific center. Always scoped to one `center_id`. Cannot be shared across centers.
- **Teacher**: An instructor at a specific center. Always scoped to one `center_id`. Cannot teach at another center through the system.
- **Class Session**: A recurring or one-off class at a specific center. Teacher and enrolled students must belong to the same center.
- **Attendance Record**: A per-student, per-class attendance entry. Scoped to the center of the class.
- **Tuition Payment / Ledger Entry**: Financial records for a student. Scoped to the student's center.
- **Lesson Kind**: A vocabulary entry for classifying courses. Each center has its own independent set of lesson kinds.
- **User**: A system account (superadmin, admin, staff, parent). Non-superadmin users are always bound to one center.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A center admin logged into Center A sees zero records from Center B across all pages (students, teachers, classes, tuition, attendance, schedule, dashboard) — verified by end-to-end tests with two populated centers.
- **SC-002**: A new record created by Center A's admin is immediately visible in Center A and never appears in Center B — verified across all entity types.
- **SC-003**: Cross-center resource access attempts (using another center’s record IDs in API calls) return 404 Not Found 100% of the time — no data leakage, no existence confirmation to other tenants.
- **SC-004**: Dashboard metrics for each center reflect only that center's own data — student counts, class counts, attendance rates, and tuition balances are independently accurate.
- **SC-005**: Superadmin cannot access any center-scoped operational page or API endpoint — all attempts are blocked with appropriate error messaging.

## Assumptions

- The system already has a `Center` model with `center_id` foreign keys on most core models (students, teachers, class sessions, attendance, tuition, lesson kinds). This spec focuses on ensuring complete and consistent enforcement of center-based data isolation at all layers (database queries, API routes, frontend navigation, and cross-entity validation).
- There is no requirement for cross-center data sharing (e.g., a student attending classes at two different centers). Each center operates as a fully independent tenant.
- The superadmin role is limited to center lifecycle management (create, activate, deactivate). The superadmin does not need aggregate reporting across centers in this scope.
- Existing user roles (admin, staff) within a center retain their current permissions — this spec does not modify intra-center role-based access control. Staff and admin have identical center isolation behavior; differentiating staff permissions is explicitly deferred to a future spec.
- The frontend already has center management pages (`/system/centers`) for the superadmin. This spec is about ensuring the operational pages are properly isolated, not about creating new center management UI.
