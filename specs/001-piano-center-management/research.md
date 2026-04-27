# Research: Piano Center Management System

**Phase**: 0 — Outline & Research  
**Date**: 2026-04-27  
**Status**: Complete

---

## 1. Frontend Framework

**Decision**: React (Vite) with PWA support  
**Rationale**: User-specified React JS. Vite provides fast HMR, native PWA plugin (`vite-plugin-pwa`), and is already proven in the reference project (veloxship). React's ecosystem offers mature libraries for calendar views, form handling, and i18n.  
**Alternatives considered**:
- Next.js — SSR overkill for a management app; the center does not need SEO-optimized pages
- Vue.js — viable, but user explicitly chose React

## 2. Backend Framework

**Decision**: Python FastAPI  
**Rationale**: User-specified. FastAPI provides automatic OpenAPI docs, async support with asyncpg, Pydantic validation, and dependency injection. Proven in veloxship reference project.  
**Alternatives considered**:
- Django REST Framework — heavier, sync-first, slower for this use case
- Flask — lacks built-in validation and async support

## 3. Database & ORM

**Decision**: PostgreSQL 16+ with SQLAlchemy (async) + asyncpg driver  
**Rationale**: User-specified PostgreSQL + SQLAlchemy. Async SQLAlchemy with asyncpg provides non-blocking DB operations. PostgreSQL handles relational data well (students → classes → packages → attendance).  
**Alternatives considered**:
- MySQL — less feature-rich for JSON columns and extensions
- MongoDB — poor fit for highly relational data model

## 4. Database Migration Strategy

**Decision**: Alembic with sequential numbered versions (001, 002, 003, ...)  
**Rationale**: User-specified numbered versioning. Alembic is the standard SQLAlchemy migration tool. Sequential numbering (instead of random hashes) improves readability and ordering, matching the veloxship pattern (`0001_init_extensions.py`, `0002_...`, etc.).  
**Migration naming convention**: `{NNN}_{description}.py` (e.g., `001_init_extensions.py`, `002_users_and_roles.py`, `003_students_teachers.py`)  
**Alternatives considered**:
- Auto-generated hash-based revisions — harder to track sequence
- Django-style migrations — wrong framework

## 5. Internationalization (i18n)

**Decision**: `react-i18next` for frontend, backend returns translation keys or pre-translated strings  
**Rationale**: User requires bilingual English + Vietnamese. `react-i18next` is the most mature React i18n library with namespace support, lazy loading, and pluralization. Translation files stored as JSON (`en.json`, `vi.json`).  
**Implementation approach**:
- Frontend: `react-i18next` with JSON translation files per locale
- Backend: Error messages and notification templates support both locales
- Default language: Vietnamese (primary users are Vietnamese staff)
- Language switcher in the UI header, persisted to `localStorage`

**Alternatives considered**:
- `react-intl` (FormatJS) — less flexible for dynamic key lookups
- Custom i18n — unnecessary when mature libraries exist

## 6. Authentication & Authorization

**Decision**: JWT-based auth with role-based access control (RBAC)  
**Rationale**: Three roles (Admin, Staff, Parent) with distinct permission levels. JWT provides stateless auth suitable for PWA. Access tokens (short-lived) + refresh tokens (long-lived) pattern from veloxship.  
**Implementation**:
- `python-jose` for JWT encoding/decoding
- `passlib[bcrypt]` for password hashing
- Roles stored in user model: `admin`, `staff`, `parent`
- Parent portal uses same auth system but separate login UI
- FastAPI dependency injection for permission checks

**Alternatives considered**:
- Session-based auth — stateful, harder with PWA offline scenarios
- OAuth2/OIDC — overkill for a single-center app

## 7. Calendar / Scheduling UI

**Decision**: `@fullcalendar/react` (FullCalendar)  
**Rationale**: Mature, well-documented React calendar component with weekly/daily views, drag-and-drop, event overlapping detection, and responsive design. Supports Vietnamese locale.  
**Alternatives considered**:
- `react-big-calendar` — less polished, fewer features
- Custom calendar — high effort, no benefit
- `react-scheduler` — less community support

## 8. PWA Strategy

**Decision**: `vite-plugin-pwa` with Workbox (same as veloxship)  
**Rationale**: Generates service worker, web manifest, and handles caching strategies. Online-first approach (no offline data caching for Phase 1). Install prompt for Android/iOS.  
**Implementation**:
- Service worker for asset caching only
- Online-only for API operations (Phase 1)
- Install banner with Vietnamese/English text
- Auto-update prompt when new version deployed

**Alternatives considered**:
- Manual service worker — more effort, same result
- `@vite-pwa/assets-generator` — useful for icon generation

## 9. State Management

**Decision**: React Query (TanStack Query) for server state, React Context for UI state  
**Rationale**: React Query handles API data fetching, caching, and background refetching. Lightweight Context handles language selection, theme, and auth state. No need for Redux/Zustand given the app's complexity.  
**Alternatives considered**:
- Redux Toolkit — heavier than needed
- Zustand — viable but React Query + Context covers all needs

## 10. Notification System (Phase 2)

**Decision**: Zalo OA API + Vietnamese SMS gateway (deferred to Phase 2)  
**Rationale**: User specified Zalo/SMS. Research deferred — Phase 1 builds the notification model and queue, Phase 2 integrates actual providers.  
**Notes**:
- Zalo Official Account API requires business verification
- SMS providers in Vietnam: eSMS, SpeedSMS, Twilio (international)
- Backend will have a notification service with pluggable providers

## 11. Testing Strategy

**Decision**: pytest (backend) + Vitest + Playwright (frontend)  
**Rationale**: Following veloxship patterns. pytest with async support for FastAPI testing. Vitest for React unit tests. Playwright for E2E flows.  
**Implementation**:
- Backend: `pytest` + `httpx` (async test client) + `testcontainers` for DB
- Frontend: `vitest` + `@testing-library/react` for components
- E2E: `playwright` for critical flows (login → schedule → attendance)
- Contract tests: OpenAPI spec drift detection

## 12. Project Structure Decision

**Decision**: Web application structure (frontend + backend separation)  
**Rationale**: Following veloxship reference project structure. Clear separation of concerns. Backend serves API only, frontend is an SPA.  
**Structure**: See plan.md for detailed directory layout.

## 13. CSS / UI Framework

**Decision**: Ant Design (antd) for component library  
**Rationale**: Ant Design provides a comprehensive enterprise-grade component library with built-in Vietnamese locale support, table/form components ideal for management apps, and excellent calendar/date-picker components. Consistent with the "management system" nature of the project.  
**Alternatives considered**:
- Material UI (MUI) — viable but less Vietnamese locale support
- Chakra UI — lighter, fewer enterprise components
- Custom CSS — too much effort for admin-style interfaces

## 14. API Documentation

**Decision**: FastAPI auto-generated OpenAPI (Swagger UI)  
**Rationale**: FastAPI generates OpenAPI docs automatically from Pydantic schemas. Available at `/docs` (Swagger UI) and `/redoc`. Zero additional effort.
