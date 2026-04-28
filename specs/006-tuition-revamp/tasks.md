# Tasks: Tuition Revamp — Balance-Based Fee Tracking

**Input**: Design documents from `/specs/006-tuition-revamp/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/api.md

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Web app**: `backend/app/`, `frontend/src/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Remove legacy package system and create new tuition data infrastructure

- [X] T001 Create TuitionPayment ORM model in `backend/app/models/tuition_payment.py` with fields: id (UUID PK), student_id (FK→students), amount (BigInteger, >0), payment_date (Date), payment_method (String(50), nullable), notes (Text, nullable), recorded_by (FK→users), center_id (FK→centers), created_at. Add indexes on student_id, center_id, payment_date. Add relationship to Student.
- [X] T002 [P] Create TuitionLedgerEntry ORM model in `backend/app/models/tuition_ledger_entry.py` with fields: id (UUID PK), student_id (FK→students), entry_type (String(20): "payment"|"class_fee"), amount (BigInteger, >0), balance_after (BigInteger), payment_id (FK→tuition_payments, nullable), attendance_id (FK→attendance_records, nullable, unique partial index where NOT NULL), class_session_id (FK→class_sessions, nullable), entry_date (Date), description (String(200)), center_id (FK→centers), created_at. Add composite index on (student_id, created_at). Add relationships to Student, TuitionPayment, AttendanceRecord, ClassSession.
- [X] T003 Add `balance` field (BigInteger, default=0, server_default="0") to Student model in `backend/app/models/student.py`
- [X] T004 Update `backend/app/models/__init__.py`: remove Package and PaymentRecord imports, add TuitionPayment and TuitionLedgerEntry imports
- [X] T005 Remove `package_id` column and Package relationship from AttendanceRecord model in `backend/app/models/attendance.py`
- [X] T006 Create Alembic migration `backend/alembic/versions/016_tuition_revamp.py`: (1) drop FK constraint attendance_records.package_id→packages, (2) drop column attendance_records.package_id, (3) drop table payment_records, (4) drop table packages, (5) create table tuition_payments, (6) create table tuition_ledger_entries with partial unique index on attendance_id, (7) add column students.balance BigInteger default 0. Also drop renewal_reminders table if it references packages.

**Checkpoint**: Database schema is ready. Legacy package tables are gone. New tuition tables exist. All models compile.

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core backend services that ALL user stories depend on

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [X] T007 Create Pydantic schemas in `backend/app/schemas/tuition.py`: (1) TuitionPaymentCreate (student_id: UUID required, amount: int >0 ≤1B, payment_date: date optional default today, payment_method: str optional, notes: str optional), (2) TuitionPaymentResponse (id, student_id, student_name, amount, payment_date, payment_method, notes, recorded_by, balance_after, created_at), (3) StudentBalanceResponse (student_id, student_name, total_paid, total_fees, balance), (4) LedgerEntryResponse (id, entry_type, amount, balance_after, description, entry_date, class_display_id nullable, created_at), (5) StudentLedgerResponse (student_id, student_name, current_balance, entries: list[LedgerEntryResponse])
- [X] T008 Rewrite tuition service in `backend/app/services/tuition_service.py`: implement (1) `record_payment(db, student_id, data, recorded_by, center_id)` — create TuitionPayment, create ledger entry with type="payment", update student.balance atomically, return payment with balance_after; (2) `get_student_balances(db, center_id, balance_filter)` — query students with aggregated total_paid and total_fees from ledger entries, return list of StudentBalanceResponse; (3) `get_student_ledger(db, student_id, center_id, from_date, to_date)` — query ledger entries ordered by created_at, return StudentLedgerResponse with all entries
- [X] T009 Rewrite attendance service in `backend/app/services/attendance_service.py`: remove all Package imports and remaining_sessions logic. For each attendance record: (1) look up class_session.tuition_fee_per_lesson, (2) if student marked "present" and fee > 0: create TuitionLedgerEntry with type="class_fee", deduct fee from student.balance, (3) if status changed from "present" to non-present: create reversal ledger entry (type="class_fee", positive amount added back), restore student.balance, (4) if status changed from non-present to "present": create debit ledger entry, deduct from balance. Use class session display_id as ledger description. Keep renewal_reminder_triggered in response for backward compatibility (set to False always). Add balance_after and fee_deducted to response dict.
- [X] T010 Delete legacy files: `backend/app/models/package.py`, `backend/app/models/payment_record.py`, `backend/app/models/renewal_reminder.py`, `backend/app/schemas/package.py`, `backend/app/crud/package.py`, `backend/app/api/packages.py`
- [X] T011 Update `backend/app/api/__init__.py`: remove packages_router import and include_router call, add tuition_router import and include_router call
- [X] T012 Delete legacy frontend file `frontend/src/api/packages.js`

**Checkpoint**: Backend compiles, all legacy package code removed, tuition service and modified attendance service are ready. No API routes serving tuition yet.

---

## Phase 3: User Story 5 — Remove Legacy Package Assignment Flow (Priority: P1) 🎯

**Goal**: Ensure the old "Assign Package" UI is completely gone and replaced by the new balance-centric tuition page structure. This is the foundational UI change.

**Independent Test**: Open the Tuition page — no "Assign Package" button, no PackageForm, no package-related columns.

### Implementation for User Story 5

- [X] T013 [US5] Delete `frontend/src/features/tuition/PackageForm.jsx`
- [X] T014 [US5] Create tuition API client in `frontend/src/api/tuition.js`: export functions `listBalances(params)` → GET /tuition/balances, `recordPayment(data)` → POST /tuition/payments, `listPayments(params)` → GET /tuition/payments, `getStudentLedger(studentId, params)` → GET /tuition/ledger/{studentId}
- [X] T015 [US5] Rewrite `frontend/src/features/tuition/TuitionPage.jsx` with new balance-centric layout: (1) replace package data fetching with `listBalances()` call, (2) replace table columns to: Student Name, Total Paid (VND formatted), Total Fees (VND formatted), Current Balance (VND formatted, green if >0, red if <0), Actions, (3) replace "Assign Package" button with "Add Payment" button (admin only), (4) remove all package-related state, modals, and handlers, (5) add balance filter dropdown (All/Positive/Zero/Negative), (6) admin-only visibility for financial columns. Use Ant Design Table, Tag, Button, Select components.
- [X] T016 [US5] Update i18n files `frontend/src/i18n/en.json` and `frontend/src/i18n/vi.json`: remove all `package.*` keys and `tuition.createPackage`, `tuition.packageType`, `tuition.assignPackage` keys. Add new tuition keys: `tuition.addPayment`, `tuition.totalPaid`, `tuition.totalFees`, `tuition.balance`, `tuition.studentLedger`, `tuition.paymentMethod`, `tuition.paymentDate`, `tuition.amount`, `tuition.owing`, `tuition.credit`, `tuition.filterBalance`. Add dashboard key: `dashboard.studentsOwing`.

**Checkpoint**: Tuition page shows student balance list. No package references remain in the UI. "Add Payment" button visible (but form not yet built). 

---

## Phase 4: User Story 1 — Admin Records a Tuition Payment (Priority: P1)

**Goal**: Admin can click "Add Payment", fill out the form, and record a payment that increases a student's balance.

**Independent Test**: Log in as admin → Tuition page → click "Add Payment" → select student, enter 2,000,000 VND → save → student's balance increases to 2,000,000 VND.

### Implementation for User Story 1

- [X] T017 [US1] Create tuition API router in `backend/app/api/tuition.py`: (1) POST `/tuition/payments` — admin-only, validate request body with TuitionPaymentCreate schema, call `tuition_service.record_payment()`, return TuitionPaymentResponse (201), (2) GET `/tuition/payments` — admin-only, optional query params student_id/from_date/to_date, return list of payments, (3) GET `/tuition/balances` — admin-only, optional balance_filter param, call `tuition_service.get_student_balances()`, return list of StudentBalanceResponse
- [X] T018 [US1] Create `frontend/src/features/tuition/PaymentForm.jsx`: Ant Design Modal form with fields: (1) Student select (searchable, required — fetch from students API), (2) Amount input (number, required, min 1, VND formatting), (3) Payment Date picker (required, defaults to today), (4) Payment Method select (optional: cash/bank_transfer/other), (5) Notes textarea (optional). On submit: call `recordPayment()` API, show success message, close modal, refresh balance list. Validation: amount > 0, student required. Use i18n keys for labels.
- [X] T019 [US1] Wire PaymentForm into TuitionPage.jsx: import PaymentForm, add modal open state, connect "Add Payment" button click to open modal, on form success call `refetch()` on the balances query to refresh the table.

**Checkpoint**: Full payment recording flow works end-to-end. Admin can record payments. Student balances update in real-time on the Tuition list.

---

## Phase 5: User Story 2 — Balance Deduction on Class Attendance (Priority: P1)

**Goal**: When teacher/admin marks a student "present", the class fee is deducted from the student's balance and logged in their ledger.

**Independent Test**: Record a payment for student (2,000,000 VND) → go to Attendance page → mark student "present" at class with fee 200,000 VND → verify balance becomes 1,800,000 VND on Tuition page. Then change status to "absent" → balance restores to 2,000,000 VND.

### Implementation for User Story 2

- [X] T020 [US2] Verify and finalize attendance service deduction logic in `backend/app/services/attendance_service.py`: ensure (1) new attendance record with status="present" creates class_fee ledger entry and deducts from student.balance, (2) existing record changed present→absent creates reversal entry and restores balance, (3) existing record changed absent→present creates debit entry and deducts balance, (4) class with null/0 tuition_fee_per_lesson skips balance logic, (5) class display_id is used as ledger description (e.g., "Jane-Mon-1730"), (6) balance_after and fee_deducted included in response. Write edge case handling for concurrent access (SELECT FOR UPDATE on student row).
- [X] T021 [US2] Update attendance API response in `backend/app/api/attendance.py`: include `balance_after` and `fee_deducted` fields in the batch attendance response. For non-admin roles (teacher/staff), set these to null to hide financial details (FR-025).
- [X] T022 [US2] Remove `package_remaining` from attendance response in `backend/app/api/attendance.py` and any frontend code that references it. Ensure the attendance page frontend still functions correctly after removing the package-related response fields.

**Checkpoint**: Attendance marking deducts from balance. Ledger entries are created. Status changes correctly reverse/apply deductions.

---

## Phase 6: User Story 3 — Admin Views Student Tuition Overview (Priority: P1)

**Goal**: Admin sees a balance list on the Tuition page and can click a student to view their chronological ledger with running balance.

**Independent Test**: With a student who has payments and attendance records, view the Tuition page → verify correct Total Paid, Total Fees, Balance columns → click student → see chronological ledger with entries like "2026-04-01 | Payment | +2,000,000 | Balance: 2,000,000".

### Implementation for User Story 3

- [X] T023 [US3] Add ledger API endpoint to `backend/app/api/tuition.py`: GET `/tuition/ledger/{student_id}` — admin-only, optional from_date/to_date query params, call `tuition_service.get_student_ledger()`, return StudentLedgerResponse with chronological entries and running balance.
- [X] T024 [US3] Create `frontend/src/features/tuition/StudentLedger.jsx`: Component that displays a student's chronological tuition ledger. Use Ant Design Drawer or Modal triggered from TuitionPage row click. Show: (1) student name + current balance at top, (2) Table/Timeline of ledger entries sorted by date, each showing: date, type icon (↑ payment / ↓ class fee), description (class display ID for fees, "Payment - method" for payments), amount with sign (+/-), running balance after entry. (3) Color coding: payment entries in green, class_fee entries in orange/red, negative balance_after in red. (4) Optional date range filter. Use i18n keys for labels. Fetch data via `getStudentLedger(studentId)`.
- [X] T025 [US3] Wire StudentLedger into TuitionPage.jsx: add row click handler or "View Ledger" action button per student row, manage selected student state, render StudentLedger component with selected student_id, handle drawer/modal close.
- [X] T026 [US3] Add balance status filter to TuitionPage.jsx: add Ant Design Select dropdown above the table with options All/Positive (balance>0)/Zero (balance=0)/Negative (balance<0). Pass `balance_filter` query param to `listBalances()` API call. Add color-coded Ant Design Tag for balance in the table: green Tag for positive, red Tag for negative, default Tag for zero.

**Checkpoint**: Full tuition overview works. Admin can see all student balances, filter by status, and drill into any student's ledger with complete payment and class fee history.

---

## Phase 7: User Story 4 — Parent Sees Their Child's Tuition Status (Priority: P2)

**Goal**: Parent can view their child's balance and simplified payment/attendance history without seeing per-lesson fee amounts.

**Independent Test**: Log in as parent → view child's profile → see Total Paid, Classes Attended count, Current Balance. See payment/attendance history without fee amounts.

### Implementation for User Story 4

- [X] T027 [US4] Add parent-scoped ledger endpoint logic to `backend/app/api/tuition.py`: in GET `/tuition/ledger/{student_id}`, if current user is parent role, verify student belongs to parent's children (via student.contact or parent relationship), strip amount fields from response (set to null), keep entry_type, description, entry_date, and balance_after. Return 403 if student is not the parent's child.
- [X] T028 [US4] Add parent balance endpoint to `backend/app/api/tuition.py`: GET `/tuition/my-child/{student_id}/balance` — parent-only, return simplified response: { student_name, total_paid, classes_attended (count of class_fee entries), current_balance }. Verify student belongs to parent.
- [X] T029 [US4] Add parent tuition view to frontend: in the student profile or parent dashboard view, add a tuition summary card showing Total Paid, Classes Attended, and Current Balance with appropriate color coding. If balance < 0, show a warning banner "Additional payment needed". Use i18n keys. Hide per-lesson fee breakdowns. This may be integrated into existing parent views rather than a separate page.

**Checkpoint**: Parents can see their child's financial status. No per-lesson fees exposed. Negative balance shows warning.

---

## Phase 8: Polish & Cross-Cutting Concerns

**Purpose**: Dashboard updates, final cleanup, and cross-cutting improvements

- [X] T030 [P] Update dashboard service in `backend/app/services/dashboard_service.py`: (1) replace `expiring_packages` query (Package.remaining_sessions≤2) with `students_owing` query (Student.balance < 0), (2) replace monthly revenue source from PaymentRecord to TuitionPayment, (3) remove Package and PaymentRecord imports, (4) update response key from `expiring_packages` to `students_owing`
- [X] T031 [P] Update dashboard API in `backend/app/api/dashboard.py` and frontend dashboard component: update response shape to use `students_owing` instead of `expiring_packages`. Update the frontend dashboard card that shows "Expiring Packages" to show "Students Owing" count instead, with appropriate i18n keys and styling (red color for count > 0).
- [X] T032 [P] Remove package-related i18n keys in `frontend/src/i18n/en.json` and `frontend/src/i18n/vi.json`: delete entire `"package": { ... }` section. Clean up any remaining references to package terminology in other i18n sections.
- [X] T033 [P] Remove any remaining package references across the codebase: grep for "package", "Package", "remaining_sessions", "payment_record", "PaymentRecord" across both backend and frontend. Remove or update any stale imports, comments, or dead code. Verify SC-006: zero references to "Assign Package", "remaining_sessions", or package-based deduction logic remain.
- [X] T034 VND currency formatting utility: ensure consistent VND formatting across the frontend (e.g., "2.000.000 ₫" or "2,000,000 VND"). Add or update a shared formatter in `frontend/src/utils/` if one doesn't exist. Verify all balance/amount displays use it (TuitionPage, PaymentForm, StudentLedger, Dashboard).
- [X] T035 Run quickstart.md validation: follow the steps in `specs/006-tuition-revamp/quickstart.md` end-to-end to verify the complete flow works — record payment, verify balance, mark attendance, verify deduction, view ledger.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 completion — BLOCKS all user stories
- **User Story 5 (Phase 3)**: Depends on Phase 2 — foundational UI change, RECOMMENDED before other stories
- **User Story 1 (Phase 4)**: Depends on Phase 2 + Phase 3 (needs TuitionPage with "Add Payment" button)
- **User Story 2 (Phase 5)**: Depends on Phase 2 only (attendance service is independent of UI)
- **User Story 3 (Phase 6)**: Depends on Phase 4 (needs tuition API router) + Phase 5 (needs ledger entries from attendance)
- **User Story 4 (Phase 7)**: Depends on Phase 6 (extends existing ledger endpoint with parent access)
- **Polish (Phase 8)**: Depends on all user stories being complete

### User Story Dependencies

- **US5 (Legacy Removal)**: Can start after Phase 2 — foundational UI restructure
- **US1 (Payment Recording)**: Can start after US5 (needs the new TuitionPage skeleton)
- **US2 (Attendance Deduction)**: Can start after Phase 2 — independent of UI stories
- **US3 (Tuition Overview)**: Needs US1 (tuition API router) + US2 (ledger entries exist)
- **US4 (Parent View)**: Needs US3 (extends ledger endpoint)

### Within Each User Story

- Models before services
- Services before API endpoints
- API endpoints before frontend components
- Core implementation before integration wiring

### Parallel Opportunities

- T001 and T002 can run in parallel (different model files)
- T013 and T014 can run in parallel (delete vs create, different files)
- US2 (Phase 5) can start in parallel with US1 (Phase 4) after US5 is complete — they touch different files (attendance_service vs tuition API)
- T030, T031, T032, T033, T034 can all run in parallel (different files/concerns)

---

## Parallel Example: Setup Phase

```bash
# Launch T001 and T002 together (different model files):
Task: "Create TuitionPayment model in backend/app/models/tuition_payment.py"
Task: "Create TuitionLedgerEntry model in backend/app/models/tuition_ledger_entry.py"
```

## Parallel Example: After Phase 3 (US5)

```bash
# Launch US1 and US2 in parallel (different backend areas):
Task: "T017 [US1] Create tuition API router in backend/app/api/tuition.py"
Task: "T020 [US2] Verify attendance service deduction in backend/app/services/attendance_service.py"
```

---

## Implementation Strategy

### MVP First (User Stories 5 + 1 + 2)

1. Complete Phase 1: Setup (new models, migration, remove legacy)
2. Complete Phase 2: Foundational (schemas, services, legacy deletion)
3. Complete Phase 3: US5 — Legacy UI removal, new TuitionPage skeleton
4. Complete Phase 4: US1 — Payment recording works end-to-end
5. Complete Phase 5: US2 — Attendance deduction works
6. **STOP and VALIDATE**: Core flow works — payments in, fees deducted on attendance

### Incremental Delivery

1. Setup + Foundational + US5 → New page structure, legacy gone
2. Add US1 → Admin can record payments (MVP!)
3. Add US2 → Attendance deducts from balance (core complete!)
4. Add US3 → Full ledger visibility for admin
5. Add US4 → Parent transparency
6. Polish → Dashboard, cleanup, formatting

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- Each user story should be independently completable and testable
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
- All financial amounts are in VND (integer, no decimals)
- Balance can be negative — no blocking logic
- Teachers trigger balance deduction but don't see financial data
