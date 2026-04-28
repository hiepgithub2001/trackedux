# Quickstart: Tuition Revamp — Balance-Based Fee Tracking

**Date**: 2026-04-28 | **Branch**: `006-tuition-revamp`

## What Changed

The tuition system shifts from a **package-based model** (buy N lessons → decrement on attendance) to a **balance-based model** (record payments → auto-deduct class fee on attendance).

### Before (Package Model)
1. Admin "Assigns Package" to a student: selects class, enters N lessons, sets total fee
2. Student attends class → `remaining_sessions` decrements
3. When remaining_sessions ≤ 2 → renewal reminder triggered
4. Payment recorded against the package

### After (Balance Model)
1. Admin records a "Payment" for a student: enters amount in VND
2. Payment increases the student's unified balance
3. Student attends class → `tuition_fee_per_lesson` deducted from balance (ledger entry created)
4. Balance can go negative (student owes money)
5. Admin views student balance list and chronological ledger

## Key Concepts

- **Balance**: A single number per student — sum of all payments minus sum of all class fee deductions. Can be positive (credit), zero, or negative (owes money).
- **Ledger Entry**: An individual event that affects the balance. Two types:
  - `payment` (credit): money received, balance goes up
  - `class_fee` (debit): attended a class, balance goes down by `tuition_fee_per_lesson`
- **No packages**: Students attend classes by enrollment alone. There is no "remaining sessions" concept.

## Development Setup

```bash
# Switch to feature branch
git checkout 006-tuition-revamp

# Run the migration (drops packages/payment_records, creates tuition tables)
cd backend
alembic upgrade head

# Start backend
uvicorn app.main:app --reload

# Start frontend (separate terminal)
cd frontend
npm run dev
```

## Testing the New Flow

1. **Login as admin**
2. **Record a payment**: Tuition page → "Add Payment" → select student → enter amount → save
3. **Verify balance**: Student appears in the Tuition list with updated balance
4. **Mark attendance**: Attendance page → select class → mark student "present" → save
5. **Verify deduction**: Return to Tuition page → student's balance decreased by the class fee
6. **View ledger**: Click on student row → see chronological ledger with payment and class fee entries

## API Quick Reference

| Action | Endpoint | Method |
|--------|----------|--------|
| Record payment | `/tuition/payments` | POST |
| List payments | `/tuition/payments` | GET |
| List student balances | `/tuition/balances` | GET |
| Student ledger detail | `/tuition/ledger/{student_id}` | GET |
| Mark attendance (triggers deduction) | `/attendance/batch` | POST |
| Dashboard metrics | `/dashboard` | GET |

## Files to Know

| File | Purpose |
|------|---------|
| `backend/app/models/tuition_payment.py` | TuitionPayment ORM model |
| `backend/app/models/tuition_ledger_entry.py` | TuitionLedgerEntry ORM model |
| `backend/app/services/tuition_service.py` | Payment recording, balance queries, ledger |
| `backend/app/services/attendance_service.py` | Modified: deducts from balance instead of package |
| `backend/app/api/tuition.py` | New API routes for tuition |
| `frontend/src/features/tuition/TuitionPage.jsx` | Rewritten: student balance list |
| `frontend/src/features/tuition/PaymentForm.jsx` | New: record payment form |
| `frontend/src/features/tuition/StudentLedger.jsx` | New: student ledger detail view |
