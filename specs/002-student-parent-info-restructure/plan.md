# Implementation Plan: Student & Parent Info Restructure

**Branch**: `002-student-parent-info-restructure` | **Date**: 2026-04-27 | **Spec**: [spec.md](./spec.md)  
**Input**: Feature specification from `specs/002-student-parent-info-restructure/spec.md`

## Summary

Replace the separate `parents` table and tab-based UI with an inline collapsible "Contact Information" section in the student form, and store contact data as a `contact` JSONB column on the `students` table. The `contact` JSON supports both parent/guardian contacts and adult self-paying students via a nullable `name` field and an optional `relationship` field. Eliminates the FK relationship between students and parents, simplifying the data model and user flow in a single coordinated change across backend and frontend.

## Technical Context

**Language/Version**: Python 3.11 (backend), JavaScript/React 19 (frontend)  
**Primary Dependencies**: FastAPI 0.115, SQLAlchemy 2.0 (async), Alembic, Pydantic v2 (backend); Ant Design 6, React Query 5, React Router 7 (frontend)  
**Storage**: PostgreSQL with `asyncpg` driver; JSONB column for contact data  
**Testing**: pytest + pytest-asyncio (backend); Playwright (frontend E2E)  
**Target Platform**: Linux server (backend), modern web browser (frontend)  
**Project Type**: Web application (backend API + frontend SPA)  
**Performance Goals**: Standard web app — form save completes within 2 seconds  
**Constraints**: Migration must be non-destructive; all existing parent data must be preserved in the new `contact` JSON column  
**Scale/Scope**: Single-center deployment; student count expected in the hundreds

## Constitution Check

The constitution template is unfilled (placeholder content only). No gates to enforce. Proceeding without violations.

## Project Structure

### Documentation (this feature)

```text
specs/002-student-parent-info-restructure/
├── plan.md              # This file
├── research.md          # Phase 0 output
├── data-model.md        # Phase 1 output
├── contracts/           # Phase 1 output
│   └── student-api.md
└── tasks.md             # Phase 2 output (/speckit-tasks)
```

### Source Code (repository root)

```text
backend/
├── app/
│   ├── models/
│   │   └── student.py          # Add contact JSONB; remove parent_id FK + relationship
│   ├── schemas/
│   │   └── student.py          # Add ContactInfo schema; update StudentCreate/Update/Response/ListItem
│   ├── crud/
│   │   └── student.py          # Remove selectinload(parent); read contact from JSON field
│   └── api/
│       └── students.py         # Update contact_name extraction from JSON
└── alembic/
    └── versions/
        └── 010_student_contact.py   # Add column, migrate data (relationship="parent"), drop FK

frontend/
└── src/
    └── features/
        └── students/
            ├── StudentForm.jsx        # Replace parent dropdown+modal → collapsible Contact section
            └── ParentFormModal.jsx    # Delete (no longer used)
```

**Structure Decision**: Web application (Option 2). Frontend and backend are separate directories at repo root.
