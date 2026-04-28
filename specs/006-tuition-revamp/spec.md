# Feature Specification: Tuition Revamp — Balance-Based Fee Tracking

**Feature Branch**: `006-tuition-revamp`  
**Created**: 2026-04-28  
**Status**: Draft  
**Input**: User description: "Revamp how we manage tuition. Focus on the fee. 'Assign package' should now be only 'Add record payment' for people who pay tuition. For each student, track which classes they joined to count toward the fee. If the student's paid balance > 0, it decreases after each class they join."

## Clarifications

### Session 2026-04-28

- Q: How should existing package data be migrated to the new balance system? → A: Drop all package data and start fresh (no migration). The system is pre-production; same approach used in spec 003.
- Q: Who can mark attendance (and thereby trigger balance deduction)? → A: Both admin and teacher can mark attendance. Both roles trigger balance deduction when marking a student "present".
- Q: What information should each lesson log entry show in the student's ledger? → A: Standard detail — class name/display ID, session date, and fee amount deducted.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Records a Tuition Payment (Priority: P1)

An admin opens the Tuition page and clicks "Add Payment". They select a student (or the student's parent), enter the payment amount in VND, the payment date, an optional payment method (cash, transfer, etc.), and optional notes. On save, the payment is recorded and the student's **tuition balance** increases by the paid amount. The balance is visible on the Tuition list and the student's profile.

**Why this priority**: Recording incoming money is the most fundamental action in tuition management — the center needs to track who paid what and when. Everything else (balance deduction, fee history) depends on payments being recorded first.

**Independent Test**: Can be fully tested by logging in as admin, clicking "Add Payment", selecting a student, entering an amount, saving, and verifying the student's balance increases accordingly.

**Acceptance Scenarios**:

1. **Given** the admin is on the Tuition page, **When** they click "Add Payment", **Then** they see a form with inputs for: student, amount (VND), payment date (defaults to today), payment method (optional dropdown: cash, bank transfer, other), and notes (optional free text).
2. **Given** student Minh has a current balance of 0 VND, **When** admin records a payment of 2,000,000 VND for Minh, **Then** Minh's balance updates to 2,000,000 VND.
3. **Given** student Minh already has a balance of 500,000 VND, **When** admin records another payment of 1,000,000 VND, **Then** Minh's balance updates to 1,500,000 VND.
4. **Given** the admin enters amount = 0 or a negative number, **When** they attempt to save, **Then** the system rejects with a validation error.
5. **Given** the admin selects no student, **When** they attempt to save, **Then** the system rejects with a validation error.
6. **Given** a payment is successfully recorded, **When** the admin views the Tuition list, **Then** the student's row shows the updated balance.

---

### User Story 2 - Balance Deduction on Class Attendance (Priority: P1)

When a teacher or admin marks a student "present" at a class session, the system automatically logs that lesson into the student's tuition ledger and deducts the class's `tuition_fee_per_lesson` from the student's tuition balance. The student's balance may go negative (the center extends credit / the student owes money). If attendance is changed from "present" to "absent" (or vice versa), the deduction is reversed or applied accordingly.

**Why this priority**: This is the core business logic that connects attendance to tuition. Without it, the balance is just a static number and doesn't reflect actual class consumption.

**Independent Test**: Can be fully tested by recording a payment for a student, marking them present at a class with a known per-lesson fee, and verifying the balance decreases by exactly that fee amount.

**Acceptance Scenarios**:

1. **Given** student Minh has a balance of 2,000,000 VND and class "Jane-Mon-1730" has `tuition_fee_per_lesson` = 200,000 VND, **When** Minh is marked "present" at a session of that class, **Then** Minh's balance decreases to 1,800,000 VND.
2. **Given** student Minh has a balance of 100,000 VND and the class fee is 200,000 VND, **When** Minh is marked "present", **Then** Minh's balance decreases to -100,000 VND (negative balance is allowed — the student owes the center).
3. **Given** Minh was marked "present" (balance went from 2,000,000 to 1,800,000 VND), **When** the admin changes the status to "absent", **Then** Minh's balance is restored to 2,000,000 VND (the deduction is reversed).
4. **Given** Minh was marked "absent" (no deduction), **When** the admin changes the status to "present", **Then** the fee is deducted from the balance.
5. **Given** a class has no `tuition_fee_per_lesson` set (null), **When** a student is marked present, **Then** no balance deduction occurs (free class / fee not configured).
6. **Given** a student has no payment records (balance = 0), **When** they are marked present at a class with fee 200,000 VND, **Then** their balance becomes -200,000 VND.

---

### User Story 3 - Admin Views Student Tuition Overview (Priority: P1)

On the Tuition page, the admin sees a list of all students with their current tuition balance, total amount paid, total fees consumed (from attended classes), and balance status (positive/zero/negative). The admin can click on a student to see a detailed breakdown: a chronological ledger showing all payments (credits) and all class attendance deductions (debits), with running balance.

**Why this priority**: The admin needs a clear, at-a-glance view of each student's financial status — who has paid, who owes money, and where the money went. This is essential for daily operations and parent communication.

**Independent Test**: Can be fully tested by creating a student with payments and attendance records, then viewing the Tuition page and the student's detail ledger, verifying all numbers are correct and the running balance matches.

**Acceptance Scenarios**:

1. **Given** the admin opens the Tuition page, **When** the page loads, **Then** they see a table of students with columns: Student Name, Total Paid, Total Fees, Current Balance, and Actions.
2. **Given** student Minh has paid 5,000,000 VND total and attended 15 classes at 200,000 VND each (3,000,000 VND in fees), **When** the admin views the Tuition list, **Then** Minh's row shows: Total Paid = 5,000,000, Total Fees = 3,000,000, Balance = 2,000,000.
3. **Given** the admin clicks on student Minh's row, **When** the detail view opens, **Then** they see a chronological ledger with entries like: "2026-04-01 | Payment | +2,000,000 | Balance: 2,000,000" and "2026-04-03 | Class: Jane-Mon-1730 | -200,000 | Balance: 1,800,000".
4. **Given** a student has a negative balance, **When** the admin views the Tuition list, **Then** the balance is displayed in red with a visual indicator (e.g., warning icon or red tag).
5. **Given** a student has a positive balance, **When** the admin views the Tuition list, **Then** the balance is displayed in green.
6. **Given** an admin filters the list by "negative balance" or "owing", **When** the filter is applied, **Then** only students with negative balances are shown.

---

### User Story 4 - Parent Sees Their Child's Tuition Status (Priority: P2)

A parent logging into the system can see their child's current tuition balance and a simplified payment/attendance history. They see total paid, total fees consumed, and the current balance. They do NOT see the per-lesson fee amounts or other students' information.

**Why this priority**: Parents need transparency about their child's tuition status so they know when to make additional payments. However, this is lower priority than the admin workflows since the admin is the primary user managing tuition.

**Independent Test**: Can be fully tested by logging in as a parent, viewing the child's tuition info, and verifying the correct balance and history are shown without exposing sensitive fee details of other students.

**Acceptance Scenarios**:

1. **Given** a parent is logged in, **When** they view their child's profile or tuition section, **Then** they see: Total Paid, Number of Classes Attended, and Current Balance.
2. **Given** a parent is logged in, **When** they view their child's tuition history, **Then** they see payments they made and class attendance events, but NOT the per-lesson fee or other students' data.
3. **Given** the child's balance is negative, **When** the parent views it, **Then** they see a clear indication that additional payment is needed.

---

### User Story 5 - Remove Legacy Package Assignment Flow (Priority: P1)

The current "Assign Package" button and the PackageForm (which creates a bundle of N lessons with a fixed price) are replaced by the new "Add Payment" workflow. The concept of a "package" (with number_of_lessons, remaining_sessions, etc.) is retired. Students no longer need a "package" to attend classes — enrollment in a class (from the existing class enrollment flow) is sufficient. Tuition is tracked purely through the balance system.

**Why this priority**: This is the foundational architectural change that enables the new model. The old package system and the new balance system cannot coexist without confusion.

**Independent Test**: Can be fully tested by verifying that the "Assign Package" button no longer exists, the PackageForm is removed, and the attendance flow no longer references remaining_sessions or package-based deduction.

**Acceptance Scenarios**:

1. **Given** the admin opens the Tuition page, **When** the page loads, **Then** there is NO "Assign Package" button — only "Add Payment".
2. **Given** a student is enrolled in a class, **When** they are marked present, **Then** the balance deduction happens based on the class fee — NOT based on any "package" with remaining sessions.
3. **Given** the admin views the Tuition page, **When** they look at the student list, **Then** there are no columns for "Number of Lessons", "Remaining Sessions", or "Package Status" — these are replaced by balance-related columns.

---

### Edge Cases

- **Class with no tuition_fee_per_lesson**: If a class does not have a fee configured, attending it does not affect the student's balance. The admin is warned when viewing such classes.
- **Multiple class enrollments**: A student enrolled in multiple classes gets charged per each class they attend — each attendance event deducts the respective class's fee from the single unified balance.
- **Concurrent attendance marking**: If the same student's attendance is marked by two admins simultaneously, the balance updates must be consistent (no double deduction or missed deduction).
- **Retroactive attendance changes**: Changing a past attendance record (e.g., from absent to present for last week) triggers the appropriate balance adjustment.
- **Very large negative balance**: No hard limit on how negative a balance can go — the center decides operationally when to require payment.
- **Student with no enrollment**: A student not enrolled in any class has no attendance events, so their balance only changes via payments.
- **Deleting a payment record**: Out of scope for this feature. Payments are append-only. If a correction is needed, a negative adjustment entry can be added (future feature).
- **Migration of existing package data**: All existing package data, payment records linked to packages, and related attendance references are dropped. The system starts fresh with the new balance model. Acceptable because the system is pre-production (same approach used in spec 003).

## Requirements *(mandatory)*

### Functional Requirements

**Payment Recording**

- **FR-001**: System MUST provide an "Add Payment" action on the Tuition page that records a monetary payment for a specific student.
- **FR-002**: Payment recording form MUST include: student selection (required), amount in VND (required, positive integer), payment date (required, defaults to today), payment method (optional: cash, bank transfer, other), and notes (optional free text).
- **FR-003**: Each recorded payment MUST increase the student's tuition balance by the payment amount.
- **FR-004**: Payment records MUST be immutable once created (no edit/delete in this feature). The payment history serves as an audit trail.
- **FR-005**: System MUST store each payment with: student reference, amount, date, method, notes, recorded_by (admin user), and timestamp.

**Balance Management**

- **FR-006**: System MUST maintain a computed tuition balance for each student, calculated as: sum of all payments − sum of all attendance fee deductions.
- **FR-007**: The tuition balance MUST be allowed to go negative (the student owes the center money).
- **FR-008**: System MUST display the current balance for each student on the Tuition list page and the student's profile.

**Attendance-Driven Fee Deduction**

- **FR-009**: When a student is marked "present" at a class session (by either an admin or a teacher), the system MUST log that lesson into the student's tuition ledger and deduct the class's `tuition_fee_per_lesson` from the student's tuition balance.
- **FR-010**: When attendance status is changed from "present" to any non-present status (by either an admin or a teacher), the system MUST reverse the fee deduction (restore the amount to the balance).
- **FR-011**: When attendance status is changed from a non-present status to "present" (by either an admin or a teacher), the system MUST apply the fee deduction.
- **FR-012**: If a class has no `tuition_fee_per_lesson` configured (null/zero), marking attendance MUST NOT affect the student's balance.
- **FR-013**: Each attendance-related balance change MUST be recorded as a ledger entry displaying: the class name/display ID, the session date, and the fee amount deducted. The entry MUST also store references to the student, class, and attendance record for traceability.

**Tuition Overview & Ledger**

- **FR-014**: Tuition page MUST display a student list with columns: Student Name, Total Paid, Total Fees Consumed, Current Balance, and Actions.
- **FR-015**: Admin MUST be able to view a detailed ledger for any student showing all balance-affecting events (payments and attendance deductions) in chronological order with a running balance.
- **FR-016**: Admin MUST be able to filter the Tuition list by balance status (positive, zero, negative/owing).
- **FR-017**: Balance amounts MUST be displayed in VND format with proper currency formatting.

**Legacy Package Removal**

- **FR-018**: System MUST remove the "Assign Package" button and the PackageForm from the Tuition page.
- **FR-019**: System MUST remove package-related columns (Number of Lessons, Remaining Sessions, Package Payment Status) from the Tuition page.
- **FR-020**: Attendance marking MUST no longer reference or deduct from `Package.remaining_sessions`. Instead, it deducts from the student's tuition balance using the class fee.
- **FR-021**: The Package model, Package CRUD, Package API endpoints, and all associated payment records MUST be dropped and removed. No migration of existing data is performed. The system starts fresh with the new balance model.

**Role-Based Access**

- **FR-022**: Only admin users MUST be able to record payments and view full financial details (per-lesson fees, total amounts).
- **FR-023**: Parents MUST be able to see their own child's balance and payment history, but NOT per-lesson fee breakdowns or other students' data.
- **FR-024**: Staff MUST see attendance information but NOT financial details (fees, balances, payment amounts).
- **FR-025**: Teachers MUST be able to mark attendance (which triggers balance deduction), but MUST NOT see financial details (balances, payment amounts, per-lesson fees). The deduction happens transparently — teachers only see the attendance interface.

### Key Entities

- **TuitionPayment** (new, replaces PaymentRecord's package-centric model): A record of money received from/for a student. Key attributes: student reference, amount (VND), payment date, payment method, notes, recorded by, center reference. Not linked to a package — linked directly to a student.
- **TuitionLedgerEntry** (new): An individual balance-affecting event. Type is either "payment" (credit) or "class_fee" (debit). Visible attributes for class_fee entries: class name/display ID, session date, fee amount deducted. Internal attributes: student reference, type, amount, related payment or attendance record reference, running balance after entry, timestamp. This provides the audit trail for the student's balance.
- **Student** (existing, modified): Gains a computed property `tuition_balance` derived from the sum of ledger entries (or cached/materialized for performance). No new stored field needed if computed; alternatively, a cached `balance` field may be added for query performance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can record a payment for a student in under 30 seconds using the "Add Payment" form.
- **SC-002**: After marking a student "present" at a class, their tuition balance reflects the deduction within 1 second of the attendance save completing.
- **SC-003**: 100% of attendance-marking events for classes with a configured fee result in a corresponding ledger entry and balance adjustment.
- **SC-004**: The Tuition page loads the student list with current balances in under 2 seconds for up to 200 students.
- **SC-005**: The student ledger detail view displays a complete, accurate chronological history with running balance that reconciles to the current displayed balance (total paid − total fees = current balance, with no discrepancies).
- **SC-006**: Zero references to "Assign Package", "remaining_sessions", or package-based deduction logic remain in the tuition management UI after this feature ships.
- **SC-007**: Admin can identify all students with negative balances (owing money) in under 5 seconds using the filter on the Tuition page.

## Assumptions

- **No package concept going forward**: The "package" (a pre-purchased bundle of N lessons) is retired. Tuition is tracked purely as money-in (payments) vs. money-out (class attendance fees). Students do not need a package to attend classes — only enrollment.
- **Single unified balance per student**: Each student has one tuition balance across all their class enrollments. Money paid is pooled; attending any enrolled class deducts from the same balance.
- **Negative balance allowed**: The system does not block attendance when a student's balance is zero or negative. The center manages this operationally (reminders, parent communication). A future feature may add configurable alerts.
- **Class fee is the deduction unit**: The existing `tuition_fee_per_lesson` on ClassSession is used as the per-attendance deduction amount. No change to how class fees are set or managed.
- **Payments are student-level, not class-level**: A payment is associated with a student, not a specific class. The money goes into the student's unified balance.
- **Attendance integration**: The existing attendance marking flow (AttendancePage, mark_batch_attendance service) is modified to deduct from balance instead of decrementing `remaining_sessions`.
- **Payment records are append-only**: No editing or deleting of payment records in this feature. Corrections are made via future adjustment entries.
- **Existing enrollment flow unchanged**: Students are enrolled in classes via the existing class enrollment management from spec 001/003. This feature does not change enrollment.
- **Currency**: VND only, integer amounts (no decimals), consistent with the existing implementation.
- **Role-based visibility**: Financial data (fees, amounts, balances) follows existing role visibility rules — admin sees all, parents see own child only, staff sees no financial details.
- **Dashboard integration**: The existing dashboard metrics (e.g., "students nearing package end", monthly revenue) should be updated to reflect the new balance model (e.g., "students with negative balance", total payments this month).
- **No data migration**: All existing package data (packages, payment_records, package references in attendance) is dropped and the tables are rebuilt under the new balance model. No historical data is preserved. Acceptable because the system is pre-production (same approach used in spec 003).
