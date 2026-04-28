# API Contract: Tuition Revamp

**Date**: 2026-04-28 | **Spec**: [spec.md](../spec.md) | **Plan**: [plan.md](../plan.md)

## Base URL

All endpoints are prefixed with `/api/v1` (existing API prefix).

## Authentication

All endpoints require Bearer token authentication (existing auth flow). Role-based access applies as noted per endpoint.

---

## Tuition Payments

### POST `/tuition/payments` — Record a Payment

**Access**: Admin only

**Request Body**:
```json
{
  "student_id": "uuid",
  "amount": 2000000,
  "payment_date": "2026-04-28",
  "payment_method": "cash",
  "notes": "April tuition"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `student_id` | UUID | Yes | Must exist in same center |
| `amount` | integer | Yes | > 0, ≤ 1,000,000,000 |
| `payment_date` | date (ISO) | No | Defaults to today |
| `payment_method` | string | No | One of: `cash`, `bank_transfer`, `other` |
| `notes` | string | No | Free text |

**Response** (201 Created):
```json
{
  "id": "uuid",
  "student_id": "uuid",
  "student_name": "Minh",
  "amount": 2000000,
  "payment_date": "2026-04-28",
  "payment_method": "cash",
  "notes": "April tuition",
  "recorded_by": "uuid",
  "balance_after": 3500000,
  "created_at": "2026-04-28T10:30:00Z"
}
```

**Errors**:
- `400`: Invalid amount or missing student_id
- `403`: Non-admin user
- `404`: Student not found

---

### GET `/tuition/payments` — List Payments

**Access**: Admin only

**Query Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| `student_id` | UUID | Filter by student |
| `from_date` | date | Filter payments from this date |
| `to_date` | date | Filter payments up to this date |

**Response** (200):
```json
[
  {
    "id": "uuid",
    "student_id": "uuid",
    "student_name": "Minh",
    "amount": 2000000,
    "payment_date": "2026-04-28",
    "payment_method": "cash",
    "notes": "April tuition",
    "created_at": "2026-04-28T10:30:00Z"
  }
]
```

---

## Student Tuition Balance

### GET `/tuition/balances` — List All Student Balances

**Access**: Admin only (staff sees no financial data; parents use student-specific endpoint)

**Query Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| `balance_filter` | string | One of: `positive`, `zero`, `negative`, `all` (default: `all`) |

**Response** (200):
```json
[
  {
    "student_id": "uuid",
    "student_name": "Minh",
    "total_paid": 5000000,
    "total_fees": 3000000,
    "balance": 2000000
  },
  {
    "student_id": "uuid",
    "student_name": "Lan",
    "total_paid": 1000000,
    "total_fees": 1400000,
    "balance": -400000
  }
]
```

---

### GET `/tuition/ledger/{student_id}` — Student Ledger Detail

**Access**: Admin (full detail), Parent (own child only, limited detail)

**Query Parameters**:

| Param | Type | Description |
|-------|------|-------------|
| `from_date` | date | Filter entries from this date |
| `to_date` | date | Filter entries up to this date |

**Response** (200):
```json
{
  "student_id": "uuid",
  "student_name": "Minh",
  "current_balance": 1800000,
  "entries": [
    {
      "id": "uuid",
      "entry_type": "payment",
      "amount": 2000000,
      "balance_after": 2000000,
      "description": "Payment - cash",
      "entry_date": "2026-04-01",
      "class_display_id": null,
      "created_at": "2026-04-01T09:00:00Z"
    },
    {
      "id": "uuid",
      "entry_type": "class_fee",
      "amount": 200000,
      "balance_after": 1800000,
      "description": "Jane-Mon-1730",
      "entry_date": "2026-04-03",
      "class_display_id": "Jane-Mon-1730",
      "created_at": "2026-04-03T18:00:00Z"
    }
  ]
}
```

**For parent role**: Same shape but `amount` fields are hidden (replaced with `null`). Only `entry_type`, `description`, `entry_date`, and `balance_after` are visible.

---

## Modified Endpoints

### POST `/attendance/batch` — Mark Attendance (Modified)

**Access**: Admin or Teacher

**Request Body**: Unchanged from current schema.

**Response** (200) — Modified:
```json
{
  "records": [
    {
      "student_id": "uuid",
      "status": "present",
      "balance_after": 1800000,
      "fee_deducted": 200000,
      "renewal_reminder_triggered": false
    }
  ]
}
```

**Changes from current**:
- `package_remaining` → removed
- `balance_after` → new (student's balance after deduction; `null` for non-admin/non-financial roles)
- `fee_deducted` → new (amount deducted; `null` for non-financial roles, `0` if class has no fee)
- `renewal_reminder_triggered` → kept for backward compatibility but may be removed in future

---

### GET `/dashboard` — Dashboard Metrics (Modified)

**Response** (200):
```json
{
  "active_students": 45,
  "today_sessions": 6,
  "running_sessions": 2,
  "today_absences": 3,
  "students_owing": 8,
  "monthly_revenue": 15000000,
  "today_date": "2026-04-28"
}
```

**Changes from current**:
- `expiring_packages` → replaced by `students_owing` (count of students with negative balance)
- `monthly_revenue` → now queries `tuition_payments` instead of `payment_records`

---

## Error Response Format

All errors follow the existing FastAPI format:
```json
{
  "detail": "Human-readable error message"
}
```
