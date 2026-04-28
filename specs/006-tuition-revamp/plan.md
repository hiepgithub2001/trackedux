# Implementation Plan: Tuition Revamp — Balance-Based Fee Tracking

**Branch**: `006-tuition-revamp` | **Date**: 2026-04-28 | **Spec**: [spec.md](./spec.md)
**Input**: Feature specification from `/specs/006-tuition-revamp/spec.md`

## Summary

Replace the existing package-based tuition model (buy N lessons → decrement on attendance) with a balance-based model (record payments → auto-deduct class fee on attendance). The "Assign Package" flow is removed entirely; the Tuition page becomes a student balance overview with an "Add Payment" action. When a teacher or admin marks a student "present", the class's `tuition_fee_per_lesson` is deducted from the student's unified balance and a ledger entry is created. The student's balance may go negative (center extends credit). A chronological ledger per student shows all payments (credits) and class fee deductions (debits) with running balance. All existing package data is dropped (pre-production; same approach as spec 003). The implementation uses the existing FastAPI + React/Ant Design stack with a new Alembic migration.

## Technical Context

**Language/Version**: Python 3.11+ (backend, matches `pyproject.toml: requires-python = ">=3.11"`), JavaScript/ES2020+ (frontend, React 19 + Vite 8).
**Primary Dependencies**: FastAPI, SQLAlchemy 2 (async), Alembic (migrations), Pydantic v2 (schemas); React, Ant Design 5, TanStack Query v5, react-i18n (frontend).
**Storage**: PostgreSQL via SQLAlchemy async + `asyncpg`. Tables affected: new `tuition_payments`, new `tuition_ledger_entries`, modified `attendance_records` (drop `package_id` FK), dropped `packages`, dropped `payment_records`.
**Testing**: Pytest + pytest-asyncio (backend), Playwright (frontend E2E).
**Target Platform**: Linux server (Docker), browser (Chromium/Firefox/Safari).
**Project Type**: Multi-stack web application (existing `backend/` + `frontend/` siblings).
**Performance Goals**: SC-002 → balance deduction within 1s of attendance save. SC-004 → Tuition page loads ≤2s for 200 students.
**Constraints**: VND only (integer, no decimals). Negative balance allowed. Payments append-only (no edit/delete). Teachers can mark attendance but cannot see financial details.
**Scale/Scope**: ~200 students per center, ~20 classes, ~10 attendance sessions/day. Delta: 1 new migration, 2 new models, 2 new services, 1 new API router, 1 refactored API router, 2 refactored frontend pages, 1 new frontend API module.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

The project's constitution at `.specify/memory/constitution.md` is currently the unfilled template (all placeholders, no ratified principles). There are therefore **no enforced project-level gates** to evaluate at this time.

In place of formal gates, this plan honors the patterns established in prior specs:
- **Data model evolution**: New Alembic migration drops legacy tables and adds new ones (same pattern as spec 003's `012_flexible_course_package.py`).
- **Role-based access**: Financial data hidden from non-admin roles (consistent with spec 001/003).
- **No premature abstraction**: Simple service-layer functions, no new architectural patterns.
- **Re-check after Phase 1 design**: PASS — the design introduces no constraints beyond what the spec mandates.

No Complexity Tracking entries are required.

## Project Structure

### Documentation (this feature)

```text
specs/006-tuition-revamp/
├── plan.md              # This file (/speckit-plan command output)
├── spec.md              # Feature spec (already authored by /speckit-specify)
├── research.md          # Phase 0 output (this command)
├── data-model.md        # Phase 1 output (this command)
├── quickstart.md        # Phase 1 output (this command)
├── contracts/           # Phase 1 output (this command)
│   └── api.md           # REST API contract: tuition payments, ledger, balance
├── checklists/
│   └── requirements.md  # Spec quality checklist (already authored)
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── api/
│   │   ├── tuition.py                  # NEW — tuition payments & ledger API routes
│   │   ├── attendance.py               # MODIFIED — remove package references from response
│   │   ├── packages.py                 # REMOVED — entire file deleted
│   │   ├── dashboard.py                # MODIFIED — use tuition balance metrics
│   │   └── __init__.py                 # MODIFIED — swap packages router for tuition router
│   ├── models/
│   │   ├── tuition_payment.py          # NEW — TuitionPayment ORM model
│   │   ├── tuition_ledger_entry.py     # NEW — TuitionLedgerEntry ORM model
│   │   ├── attendance.py               # MODIFIED — drop package_id FK
│   │   ├── package.py                  # REMOVED — entire file deleted
│   │   ├── payment_record.py           # REMOVED — entire file deleted
│   │   └── __init__.py                 # MODIFIED — swap imports
│   ├── schemas/
│   │   ├── tuition.py                  # NEW — Pydantic schemas for tuition
│   │   ├── package.py                  # REMOVED — entire file deleted
│   │   └── attendance.py               # MODIFIED — remove package-related fields
│   ├── services/
│   │   ├── tuition_service.py          # REWRITTEN — payment recording, balance computation, ledger queries
│   │   ├── attendance_service.py       # MODIFIED — deduct from balance instead of package.remaining_sessions
│   │   └── dashboard_service.py        # MODIFIED — replace package metrics with balance metrics
│   └── crud/
│       ├── package.py                  # REMOVED — entire file deleted
│       └── ...                         # Other CRUD files unchanged
├── alembic/
│   └── versions/
│       └── 016_tuition_revamp.py       # NEW — drop packages/payment_records, create tuition tables, modify attendance
└── tests/                              # Test updates follow source changes

frontend/
├── src/
│   ├── api/
│   │   ├── tuition.js                  # NEW — tuition API client (payments, ledger, balance)
│   │   └── packages.js                 # REMOVED — entire file deleted
│   ├── features/
│   │   └── tuition/
│   │       ├── TuitionPage.jsx         # REWRITTEN — student balance list + "Add Payment" button
│   │       ├── PaymentForm.jsx         # NEW — replaces PackageForm; records payment for a student
│   │       ├── StudentLedger.jsx       # NEW — chronological ledger detail view for a student
│   │       └── PackageForm.jsx         # REMOVED — entire file deleted
│   └── i18n/
│       └── vi.json                     # MODIFIED — add tuition balance keys, remove package keys
└── ...
```

**Structure Decision**: This is a multi-stack web project with existing `backend/` + `frontend/` siblings. The tuition revamp touches both stacks. Backend changes center on 2 new models, a rewritten tuition service, a modified attendance service, and a new Alembic migration. Frontend changes center on rewriting the TuitionPage, adding PaymentForm and StudentLedger components, and replacing the packages API client with a tuition API client.

## Complexity Tracking

> Not applicable — Constitution Check has no violations.
