# Research: Tuition Revamp — Balance-Based Fee Tracking

**Date**: 2026-04-28 | **Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

## Research Topics

### 1. Balance Computation Strategy: Cached Field vs. Aggregate Query

**Decision**: Use a **cached `balance` field on Student** plus ledger entries as the source of truth.

**Rationale**:
- Aggregate queries (`SUM(credits) - SUM(debits)` across ledger entries) are O(n) per student and degrade as history grows. For a Tuition page listing 200 students, this means 200 subqueries or a complex GROUP BY.
- A cached `balance` field on the Student model provides O(1) reads for the list view. The field is updated atomically when a ledger entry is created (within the same DB transaction).
- The ledger entries table serves as the audit trail and the source of truth for reconciliation. The cached balance can be recomputed from ledger entries if needed (admin tool, future feature).
- This is the standard pattern for financial ledger systems: "write to the journal, cache the running total."

**Alternatives considered**:
- **Pure aggregate query**: Simpler schema but performance degrades. Rejected for list-view latency concerns (SC-004: ≤2s for 200 students).
- **Materialized view**: PostgreSQL-native but adds operational complexity (refresh scheduling). Over-engineered for this scale.

### 2. Ledger Entry Design: Separate Table vs. Unified Event Log

**Decision**: Use a **single `tuition_ledger_entries` table** with a `type` discriminator (`payment` | `class_fee`).

**Rationale**:
- A single table simplifies the chronological ledger query (one `SELECT ... ORDER BY created_at` with no UNION).
- The `type` field distinguishes credits from debits.
- Each entry stores: student_id, type, amount (always positive — the sign is determined by type), balance_after (running balance snapshot), description, and FK references to either the TuitionPayment or the AttendanceRecord that caused it.
- The `balance_after` field enables efficient ledger display without re-summing from the beginning.

**Alternatives considered**:
- **Two separate tables** (payment_entries + fee_entries): More normalized but requires UNION for chronological view. Rejected for query simplicity.
- **Event sourcing**: Full event-sourced balance. Over-engineered for this use case.

### 3. Attendance → Balance Deduction: Inline vs. Event-Driven

**Decision**: **Inline deduction** within the `mark_batch_attendance` service function, in the same database transaction.

**Rationale**:
- The current attendance service already modifies the package inline (decrementing `remaining_sessions`). We replace that inline logic with balance deduction + ledger entry creation.
- Transactional consistency: the attendance record, ledger entry, and balance update are committed atomically — no inconsistency risk from failed async events.
- At this scale (~10 attendance events/day), there's no performance reason to defer to background workers.

**Alternatives considered**:
- **Background task / event bus**: Decouple attendance from balance. Rejected — adds complexity, risk of lost events, and eventual consistency issues for a low-volume operation. Can be introduced later if scale demands.

### 4. Migration Strategy: Drop + Rebuild

**Decision**: Single Alembic migration (`016_tuition_revamp.py`) that drops legacy tables and creates new ones.

**Rationale**:
- Per clarification Q1: the system is pre-production, so no data preservation needed.
- The migration:
  1. Drops FK constraints from `attendance_records.package_id` → `packages`
  2. Drops `attendance_records.package_id` column
  3. Drops `payment_records` table
  4. Drops `packages` table
  5. Creates `tuition_payments` table
  6. Creates `tuition_ledger_entries` table
  7. Adds `balance` column to `students` (default 0)
- Order matters: FKs must be dropped before the referenced tables.

**Alternatives considered**:
- **Keep old tables read-only**: Adds schema noise for no benefit (pre-production). Rejected.
- **Soft-delete via rename**: `packages` → `packages_legacy`. Still noise. Rejected.

### 5. Dashboard Metric Replacement

**Decision**: Replace `expiring_packages` metric with `students_with_negative_balance`. Replace `monthly_revenue` source from `PaymentRecord` to `TuitionPayment`.

**Rationale**:
- `expiring_packages` (packages with ≤2 remaining sessions) has no equivalent in the new model. The closest useful metric is "students who owe money" (negative balance).
- `monthly_revenue` is still relevant but needs to query `tuition_payments` instead of `payment_records`.
- The dashboard response shape changes: `expiring_packages` → `students_owing`.

### 6. Frontend Architecture: Rewrite vs. Modify TuitionPage

**Decision**: **Rewrite** `TuitionPage.jsx` and create new `PaymentForm.jsx` + `StudentLedger.jsx` components. Delete `PackageForm.jsx`.

**Rationale**:
- The current TuitionPage is structured around package listing (columns: student, class, lessons, remaining, price, payment status, actions). The new page is structured around student balances (columns: student name, total paid, total fees, balance, actions).
- The form changes from "Assign Package" (5 fields: student, class, lessons, kind, fee) to "Add Payment" (4 fields: student, amount, date, method/notes).
- The new StudentLedger component is entirely new functionality — a detail view showing the chronological journal.
- Given the fundamental data model change, modifying the existing components would be more complex than a clean rewrite.

**Alternatives considered**:
- **Incremental modification**: Patch existing components. Rejected — the column structure, data shape, and actions are all different, making modifications error-prone and harder to review.

## All NEEDS CLARIFICATION Resolved

No outstanding unknowns remain. All technical decisions have been made with rationale documented.
