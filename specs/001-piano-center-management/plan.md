# Implementation Plan: Piano Center Management System

**Branch**: `001-piano-center-management` | **Date**: 2026-04-27 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `specs/001-piano-center-management/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

A bilingual (Vietnamese/English) PWA for managing a piano learning center — student CRM, class scheduling, attendance tracking, tuition management, teacher assignment, and parent portal. Built with React (Vite) frontend and FastAPI (Python) backend, using PostgreSQL + SQLAlchemy for data persistence. Sequential Alembic migrations (001, 002, ...). Phase 1 covers core operations; Phase 2 adds parent portal, reports, teacher notes, and auto-notifications.

## Technical Context

**Language/Version**: Python 3.11+ (backend), JavaScript/ES2022 (frontend)  
**Primary Dependencies**: FastAPI, SQLAlchemy (async), asyncpg, Pydantic v2, python-jose, passlib (backend) — React 18, Vite, Ant Design, react-i18next, TanStack Query, FullCalendar, vite-plugin-pwa (frontend)  
**Storage**: PostgreSQL 16+ with asyncpg driver, Alembic migrations (sequential: 001, 002, ...)  
**Testing**: pytest + httpx + testcontainers (backend), Vitest + Testing Library + Playwright (frontend)  
**Target Platform**: PWA — web browsers (desktop + mobile), installable on Android/iOS  
**Project Type**: Web application (SPA frontend + REST API backend)  
**Performance Goals**: <200ms API response for CRUD, <1s initial page load, support 100+ students  
**Constraints**: Online-only (Phase 1), VND currency (integer storage), bilingual VI/EN  
**Scale/Scope**: ~30 students initial, designed for 100+, 18 pages/routes, 14 database entities

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Constitution is an unfilled template — no project-specific principles or gates defined. No violations to check.

**Pre-Phase 0**: ✅ PASS (no gates)  
**Post-Phase 1**: ✅ PASS (no gates)

## Project Structure

### Documentation (this feature)

```text
specs/001-piano-center-management/
├── plan.md              # This file (/speckit-plan command output)
├── research.md          # Phase 0 output (/speckit-plan command)
├── data-model.md        # Phase 1 output (/speckit-plan command)
├── quickstart.md        # Phase 1 output (/speckit-plan command)
├── contracts/           # Phase 1 output (/speckit-plan command)
│   ├── api.md           # REST API endpoint contracts
│   └── ui.md            # Page routes, layout, component contracts
└── tasks.md             # Phase 2 output (/speckit-tasks command - NOT created by /speckit-plan)
```

### Source Code (repository root)

```text
backend/
├── alembic/
│   ├── versions/            # Sequential migrations: 001_, 002_, ...
│   ├── env.py
│   └── script.py.mako
├── app/
│   ├── api/                 # FastAPI route handlers
│   │   ├── __init__.py
│   │   ├── auth.py          # Login, refresh, logout, me
│   │   ├── students.py      # CRUD + status change
│   │   ├── parents.py       # CRUD
│   │   ├── teachers.py      # CRUD + availability
│   │   ├── classes.py       # CRUD + enroll + conflict detection
│   │   ├── attendance.py    # Batch marking + makeup scheduling
│   │   ├── packages.py      # CRUD + payment recording
│   │   ├── dashboard.py     # Metrics aggregation
│   │   ├── schedule.py      # Weekly calendar data
│   │   └── portal.py        # Parent portal (Phase 2)
│   ├── core/                # Config, security, dependency injection
│   │   ├── config.py        # Pydantic Settings from .env
│   │   ├── security.py      # JWT creation, hashing, verification
│   │   └── deps.py          # FastAPI dependencies (get_db, get_current_user)
│   ├── crud/                # Database CRUD operations per entity
│   ├── db/                  # Engine, session factory
│   ├── models/              # SQLAlchemy ORM models (14 entities)
│   ├── schemas/             # Pydantic request/response schemas
│   ├── services/            # Business logic (attendance→package deduction, reminders)
│   ├── scripts/             # Seed data (admin user, sample data)
│   └── main.py              # FastAPI app with CORS, routers
├── tests/
│   ├── unit/
│   ├── integration/
│   └── contract/
├── alembic.ini
├── pyproject.toml
├── ruff.toml
└── .env.example

frontend/
├── public/                  # PWA icons, favicon, manifest assets
├── src/
│   ├── api/                 # Axios client, interceptors, API modules
│   ├── auth/                # AuthContext, ProtectedRoute, LoginPage
│   ├── components/          # Shared: Layout, Sidebar, Header, LanguageSwitcher
│   ├── features/
│   │   ├── students/        # StudentList, StudentForm, StudentDetail
│   │   ├── teachers/        # TeacherList, TeacherForm, TeacherDetail
│   │   ├── schedule/        # WeeklyCalendar, ClassForm, ClassDetail
│   │   ├── attendance/      # AttendanceList, AttendanceBatchForm
│   │   ├── tuition/         # PackageList, PackageForm, PaymentForm
│   │   ├── dashboard/       # DashboardPage, MetricCards
│   │   └── portal/          # ParentPortal (Phase 2)
│   ├── i18n/                # en.json, vi.json, i18n config
│   ├── lib/                 # Utilities (formatVND, dateHelpers)
│   ├── pwa/                 # InstallPrompt, ConnectionBanner, UpdatePrompt
│   ├── routes/              # Route definitions, role guards
│   ├── styles/              # Global CSS, theme variables
│   ├── App.jsx
│   └── main.jsx
├── e2e/                     # Playwright E2E tests
├── package.json
├── vite.config.js
└── .env.example
```

**Structure Decision**: Web application with `backend/` + `frontend/` separation, following the veloxship reference project pattern. Backend serves REST API only; frontend is a React SPA with PWA capabilities.

## Complexity Tracking

> No constitution violations to justify — constitution is an unfilled template.
