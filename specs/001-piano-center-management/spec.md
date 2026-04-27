# Feature Specification: Piano Center Management System

**Feature Branch**: `001-piano-center-management`  
**Created**: 2026-04-27  
**Status**: Draft  
**Input**: User description: "Web application (PWA) for managing a piano learning center — student CRM, class scheduling, attendance tracking, tuition management, teacher assignment, and parent portal. Bilingual (Vietnamese/English). Phase 1: Operations management. Phase 2: Parent portal, reports, teacher notes, auto-notifications."

## Clarifications

### Session 2026-04-27

- Q: Does removing the student limit apply to all class types or only Group? → A: Group is unlimited; 1:1 stays at exactly 1 student; Pair stays at exactly 2 *(superseded below)*
- Q: Since class type won't be based on student count, should classes still have a type or label field? → A: No type field — a class has a name, teacher, time slot, and student list only; no classification based on student count
- Q: How is session duration tracked for overlap conflict detection? → A: Each class stores its own duration in minutes; overlap is computed as a start-to-end time range
- Q: Does the system record the monetary amount of each tuition package? → A: Admin sets a price (VND) per package at assignment time; stored in the Package entity
- Q: What is the expected session management behavior for admin/staff login? → A: Sessions persist until manual logout; no idle timeout or account lockout required for Phase 1
- Q: How are makeup sessions visually distinguished from regular sessions on the calendar? → A: Makeup sessions display with a distinct visual marker (e.g., "Makeup" label or badge) on the calendar

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Manages Students (Priority: P1)

An admin logs into the system and registers a new student, entering their name (nickname), age, parent name, current skill level, personality notes, learning speed, and current issues. The admin can update the student's enrollment status (trial / active / paused / withdrawn) at any time and sort/filter students by skill level or status.

**Why this priority**: Student data is the foundation of all other features — scheduling, attendance, and tuition all depend on having students in the system.

**Independent Test**: Can be fully tested by creating, editing, and searching students, verifying all fields persist correctly.

**Acceptance Scenarios**:

1. **Given** admin is logged in, **When** they click "Add Student" and fill in required fields, **Then** the student appears in the student list with correct information
2. **Given** a student exists, **When** admin updates their status to "paused," **Then** the student's status reflects the change and they no longer appear in active class rosters
3. **Given** multiple students exist, **When** admin sorts by skill level, **Then** students are ordered correctly
4. **Given** a staff member is logged in, **When** they view a student profile, **Then** parent contact details and tuition information are hidden

---

### User Story 2 - Admin Creates Classes and Schedules (Priority: P1)

An admin creates a class with a name, assigns a teacher, assigns any number of students to the class, and sets a recurring weekly time slot. The system displays the schedule in a calendar view (weekly). The system prevents booking a student into overlapping time slots and notifies the admin of conflicts. Classes have no type classification based on student count.

**Why this priority**: Scheduling is the core operational workflow — without it, the center cannot function day-to-day.

**Independent Test**: Can be fully tested by creating classes with different types, assigning students and teachers, and verifying calendar display and conflict detection.

**Acceptance Scenarios**:

1. **Given** admin is on the scheduling screen, **When** they create a new class with a name, teacher, student(s), and time slot, **Then** the class appears on the weekly calendar
2. **Given** a student is already booked at 17:00 Monday, **When** admin tries to assign them to another class at 17:00 Monday, **Then** the system displays a conflict notification and prevents the booking
3. **Given** a class exists with 3 students, **When** admin adds more students, **Then** each student is added successfully with no upper limit enforced

---

### User Story 3 - Teacher/Admin Takes Attendance (Priority: P1)

Before or after each session, the teacher or admin marks attendance for each student: present, absent, or absent with prior notice. For absent students requesting a makeup session, the system allows scheduling a makeup class. Makeup sessions are deducted from the student's active package. The system tracks attendance history and shows remaining sessions in the current package.

**Why this priority**: Attendance is directly tied to package consumption and tuition — it drives the business model.

**Independent Test**: Can be fully tested by marking attendance for various states and verifying package session counts decrease correctly.

**Acceptance Scenarios**:

1. **Given** a class is scheduled today, **When** admin marks a student as "present," **Then** one session is deducted from their active package and the attendance record is saved
2. **Given** a student is marked "absent with notice," **When** admin schedules a makeup session, **Then** the makeup session appears on the calendar with a "Makeup" label and will deduct from the package when attended
3. **Given** a student has 2 sessions remaining, **When** they attend a class, **Then** the system shows 1 session remaining and triggers a renewal reminder
4. **Given** a class has 3 students and 1 is absent, **When** the class time arrives, **Then** the class still runs for the remaining 2 students

---

### User Story 4 - Admin Manages Tuition Packages (Priority: P1)

An admin assigns a tuition package to a student (12, 24, 36 sessions, or a custom number). The system tracks payment status (paid / unpaid), remaining sessions, and payment history. When a student has approximately 2 sessions remaining, the system triggers a renewal reminder. Students can continue attending after package expiration but are marked as owing.

**Why this priority**: Revenue tracking is essential for business sustainability; the center needs to know who has paid and who owes.

**Independent Test**: Can be fully tested by creating packages, recording payments, and verifying reminder triggers and owing status.

**Acceptance Scenarios**:

1. **Given** admin is viewing a student's profile, **When** they assign a 24-session package and mark it as paid, **Then** the package appears with 24 remaining sessions and "paid" status
2. **Given** a student has 2 sessions remaining, **When** the system processes this, **Then** a renewal reminder is generated
3. **Given** a student's package has 0 sessions remaining, **When** they attend another class, **Then** attendance is recorded, session count goes negative, and the student is flagged as "owing"
4. **Given** admin creates a custom package of 18 sessions, **When** saved, **Then** the package functions identically to standard packages
5. **Given** admin views the tuition management screen, **When** filtering by "unpaid," **Then** only students with outstanding balances are shown

---

### User Story 5 - Admin Manages Teachers (Priority: P2)

An admin adds teachers to the system with their name, contact info, and available time slots. Teachers are assigned to specific classes. The schedule shows which teacher is responsible for each session.

**Why this priority**: Teacher assignment is important for operations but can be manually tracked initially if needed.

**Independent Test**: Can be fully tested by creating teachers, setting availability, assigning them to classes, and verifying calendar reflects assignments.

**Acceptance Scenarios**:

1. **Given** admin is on the teacher management screen, **When** they add a new teacher with name and availability, **Then** the teacher appears in the teacher list
2. **Given** a teacher is available Monday 16:00-20:00, **When** admin assigns them to a class at 17:00, **Then** the assignment succeeds
3. **Given** a teacher is assigned to a class, **When** viewing the calendar, **Then** the teacher's name appears on the class slot

---

### User Story 6 - Dashboard Overview (Priority: P2)

An admin or staff member views a dashboard showing: total active students, today's sessions count, today's absences, students nearing package end, and current month's revenue (admin only). Quick action buttons allow adding a student or creating a trial class.

**Why this priority**: The dashboard provides at-a-glance operational awareness but is not required for core workflows.

**Independent Test**: Can be fully tested by verifying dashboard metrics match actual data in the system.

**Acceptance Scenarios**:

1. **Given** there are 25 active students, **When** admin views the dashboard, **Then** "Total active students" shows 25
2. **Given** 3 students are absent today, **When** viewing the dashboard, **Then** "Absences today" shows 3
3. **Given** a staff member views the dashboard, **When** looking at revenue section, **Then** it is hidden from their view
4. **Given** admin clicks "Add Student," **Then** they are navigated to the student creation form

---

### User Story 7 - Parent Portal (Priority: P3)

A parent logs into a separate portal using their own credentials. They can view their child's class schedule, attendance history, teacher comments/notes per session, current package details (sessions remaining), and payment status. Parents cannot modify any data.

**Why this priority**: Phase 2 feature — adds transparency for parents but is not required for center operations.

**Independent Test**: Can be fully tested by logging in as a parent and verifying read-only access to their child's data.

**Acceptance Scenarios**:

1. **Given** a parent is logged in, **When** they view their child's profile, **Then** they see schedule, attendance history, and current package info
2. **Given** a teacher has written a note for today's session, **When** the parent checks the portal, **Then** the note is visible under the session date
3. **Given** a parent is logged in, **When** they attempt to modify any data, **Then** no edit controls are available

---

### User Story 8 - Teacher Session Notes (Priority: P3)

After each session, a teacher logs a note: what was taught, student progress, and assigned homework. These notes are visible to admin and (in Phase 2) to parents through the parent portal.

**Why this priority**: Phase 2 feature — enhances communication but can be handled informally initially.

**Independent Test**: Can be fully tested by a teacher creating session notes and verifying visibility to admin and parents.

**Acceptance Scenarios**:

1. **Given** a class session has ended, **When** the teacher opens the session record, **Then** they can enter lesson content, progress notes, and homework
2. **Given** a note has been saved, **When** admin views the student's profile under "Notes" tab, **Then** the session note is visible with date

---

### User Story 9 - Monthly Reports (Priority: P3)

At month's end, the system generates reports showing: total revenue, new student count, student retention/dropout rate, and attendance rate (percentage). Revenue is displayed as a bar chart.

**Why this priority**: Phase 2 feature — valuable for business analysis but not urgent for day-to-day operations.

**Independent Test**: Can be fully tested by populating data for a month and verifying report accuracy.

**Acceptance Scenarios**:

1. **Given** it is the end of April, **When** admin opens the monthly report, **Then** revenue, new students, attendance rate, and dropout rate are displayed
2. **Given** report data exists, **When** viewing revenue section, **Then** a bar chart shows monthly revenue over time

---

### User Story 10 - Automated Notifications (Priority: P3)

The system sends automated reminders via Zalo or SMS to parents: before upcoming classes (schedule reminder) and when tuition payment is due or overdue.

**Why this priority**: Phase 2 feature — automates communication that staff currently handles manually.

**Independent Test**: Can be fully tested by triggering reminder conditions and verifying notification delivery.

**Acceptance Scenarios**:

1. **Given** a class is scheduled for tomorrow, **When** the reminder time is reached, **Then** the parent receives a notification via Zalo/SMS
2. **Given** a student has 2 sessions remaining, **When** the reminder triggers, **Then** the parent receives a payment due notification

---

### Edge Cases

- What happens when a student is transferred between classes mid-package? Sessions remain from the same package, only the class assignment changes.
- How does the system handle a student enrolled in multiple classes simultaneously? Each class session deducts from the same active package.
- What happens when a teacher is sick and a class needs reassignment? Admin can reassign a different teacher to the session.
- What if a parent has multiple children at the center? They see all children under one portal login.
- What happens when a custom package is created with 0 sessions? System rejects it; minimum is 1 session.

## Requirements *(mandatory)*

### Functional Requirements

**Authentication & Authorization**
- **FR-001**: System MUST support role-based access with three roles: Admin, Staff, and Parent; admin/staff sessions persist until manual logout (no idle timeout for Phase 1)
- **FR-002**: Admin MUST have full access to all features including tuition and parent contact information
- **FR-003**: Staff MUST have access to student management, scheduling, and attendance but MUST NOT see tuition details or parent phone numbers/addresses
- **FR-004**: Parents MUST only have read-only access to their own child's data through a separate portal
- **FR-005**: System MUST support bilingual interface (Vietnamese and English) with user-selectable language

**Student Management**
- **FR-006**: System MUST store student records including: name (nickname), age, parent name, current skill level, personal notes (personality, learning speed, current issues), and enrollment status
- **FR-007**: System MUST support enrollment statuses: Trial, Active, Paused, Withdrawn
- **FR-008**: System MUST allow sorting and filtering students by skill level, status, and name
- **FR-009**: System MUST maintain a complete history of student status changes

**Teacher Management**
- **FR-010**: System MUST store teacher records including: name, contact information, and weekly availability slots
- **FR-011**: System MUST allow assigning teachers to specific class sessions

**Class & Scheduling**
- **FR-012**: Classes MUST have a name, an assigned teacher, a start time, a duration (in minutes), and an unrestricted list of enrolled students; no type classification based on student count
- **FR-013**: System MUST display schedules in a weekly calendar view
- **FR-014**: System MUST prevent scheduling a student into overlapping time slots (checked as start-time + duration range) and display a conflict notification
- **FR-015**: System MUST allow recurring weekly schedules
- **FR-016**: Classes MUST continue running regardless of individual student absences

**Attendance**
- **FR-017**: System MUST support attendance states: Present, Absent, Absent with Notice
- **FR-018**: System MUST allow scheduling makeup sessions for absent students; makeup sessions MUST be visually distinguished on the calendar with a "Makeup" label or badge
- **FR-019**: Makeup sessions MUST be deducted from the student's active package
- **FR-020**: System MUST maintain complete attendance history per student
- **FR-021**: System MUST display remaining sessions in the active package after each attendance record

**Tuition & Packages**
- **FR-022**: System MUST support predefined packages (12, 24, 36 sessions) and custom session counts; admin sets the price (VND) for each package at assignment time
- **FR-023**: System MUST track payment status per package: Paid, Unpaid
- **FR-024**: System MUST allow students to continue attending after package expiration, recording negative session balance (owing status)
- **FR-025**: System MUST trigger a renewal reminder when a student has approximately 2 sessions remaining
- **FR-026**: System MUST maintain payment history (date paid, amount in VND, package details); amount is the price set by admin at assignment time
- **FR-027**: System MUST support reminder status tracking: Reminded once, Reminded twice

**Dashboard**
- **FR-028**: System MUST display operational metrics: total active students, today's sessions, today's absences, students nearing package end, current month revenue (admin only)
- **FR-029**: Dashboard MUST provide quick-action buttons for common tasks (add student, create trial class)

**Parent Portal (Phase 2)**
- **FR-030**: Parents MUST be able to view their child's class schedule and attendance history
- **FR-031**: Parents MUST be able to view teacher session notes and comments
- **FR-032**: Parents MUST be able to view current package info and payment status

**Teacher Notes (Phase 2)**
- **FR-033**: Teachers MUST be able to record per-session notes: lesson content, progress, and homework assigned
- **FR-034**: Session notes MUST be viewable by admin and (when parent portal is active) by the student's parent

**Reports (Phase 2)**
- **FR-035**: System MUST generate monthly reports with: total revenue, new student count, attendance rate (%), dropout/retention rate
- **FR-036**: Revenue MUST be displayed as a bar chart over time

**Notifications (Phase 2)**
- **FR-037**: System MUST send automated reminders via Zalo or SMS before upcoming classes
- **FR-038**: System MUST send automated payment reminders when tuition is due or overdue

### Key Entities

- **Student**: Represents a learner enrolled at the center. Has personal info, skill level, enrollment status, notes, and is linked to packages, classes, and a parent.
- **Parent**: Guardian of one or more students. Has contact info and portal login credentials.
- **Teacher**: Instructor who teaches classes. Has availability schedule and is assigned to class sessions.
- **Class**: A recurring session with a name, assigned teacher, enrolled students (no count limit), start time, and duration in minutes.
- **Package**: A purchased bundle of sessions (12/24/36/custom) assigned to a student. Stores session count, price (VND set by admin at assignment), remaining sessions, and payment status.
- **Attendance Record**: Per-student, per-session log of presence status. Links to package for session deduction.
- **Session Note**: Teacher's post-class entry documenting lesson, progress, and homework.
- **Notification**: An automated message sent to parents via Zalo/SMS for schedule or payment reminders.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can register a new student and have them scheduled in a class within 5 minutes
- **SC-002**: Daily attendance for all classes can be completed within 2 minutes per session
- **SC-003**: 100% of scheduling conflicts are detected and prevented before saving
- **SC-004**: Renewal reminders are triggered automatically with zero manual tracking required
- **SC-005**: Staff can view today's full schedule and identify absences within 30 seconds of opening the app
- **SC-006**: System supports at minimum 100 students without performance degradation (designed for growth beyond initial 30)
- **SC-007**: All operational tasks (attendance, scheduling, student lookup) achievable in 3 clicks or fewer
- **SC-008**: Parents can access their child's information within 1 minute of logging into the portal (Phase 2)
- **SC-009**: Monthly reports are generated automatically with no manual data compilation (Phase 2)
- **SC-010**: Interface is fully usable in both Vietnamese and English with no untranslated elements

## Assumptions

- The system is a Progressive Web App (PWA) built with web-oriented technologies, installable on mobile devices and desktops
- The initial user base is approximately 30 students but the system is designed to scale beyond this without hard limits
- The center operates on fixed weekly time slots (e.g., Monday 17:00, Wednesday 18:00) with recurring schedules
- One student has one active package at a time; a new package replaces the previous one
- Teachers are part-time or full-time staff managed by the admin; they do not self-register
- Zalo/SMS integration (Phase 2) will use third-party APIs available in the Vietnamese market
- The system requires internet connectivity to function (no offline-first requirement for Phase 1)
- Currency is Vietnamese Dong (VND) for all financial records
- A "session" is a single class meeting regardless of duration (typically 45-60 minutes)
- The parent portal (Phase 2) uses separate authentication from the admin/staff system
