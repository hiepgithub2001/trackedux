# Tasks: Multi-Tenant Edu-Center Scalability System

**Input**: Design documents from `/specs/004-edu-center-scalability/`  
**Prerequisites**: plan.md ✅ | spec.md ✅ | research.md ✅ | data-model.md ✅ | contracts/api.md ✅ | contracts/ui.md ✅ | quickstart.md ✅

**Organization**: Tasks grouped by user story to enable independent implementation and testing.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies on incomplete tasks)
- **[Story]**: User story this task belongs to ([US1], [US2], [US3])

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Extend the project structure to support multi-tenancy without touching existing feature code.

- [ ] T001 Create `backend/app/models/center.py` — empty file with module docstring (will be filled in Phase 2)
- [ ] T002 Create `backend/app/schemas/center.py` — empty file with module docstring
- [ ] T003 Create `backend/app/crud/center.py` — empty file with module docstring
- [ ] T004 Create `backend/app/services/center_service.py` — empty file with module docstring
- [ ] T005 Create `backend/app/api/system/__init__.py` — empty module init
- [ ] T006 Create `backend/app/api/system/centers.py` — empty file with module docstring
- [ ] T007 [P] Create `frontend/src/features/system/CenterListPage.jsx` — empty component placeholder
- [ ] T008 [P] Create `frontend/src/features/system/CenterFormPage.jsx` — empty component placeholder
- [ ] T009 [P] Create `frontend/src/api/centers.js` — empty file with module comment
- [ ] T010 [P] Create `frontend/src/auth/SuperadminRoute.jsx` — empty component placeholder

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core multi-tenancy infrastructure that MUST be complete before any user story can be implemented. This phase adds the `centers` table, `center_id` FK columns across all 11 tenant tables, the `superadmin` role, and backend CRUD-layer isolation — all transparently, without breaking the current single-tenant behavior.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete. The Alembic migration must run successfully and all CRUD filters must be in place before testing any feature.

- [ ] T011 Implement `Center` SQLAlchemy model in `backend/app/models/center.py` with columns: `id` (UUID PK), `name` (String 200, UNIQUE), `code` (String 20, UNIQUE), `registered_by_id` (UUID FK → users.id nullable), `is_active` (Boolean default True), `created_at`, `updated_at`
- [ ] T012 Add `center_id` FK column to `User` model in `backend/app/models/user.py` (UUID FK → centers.id, nullable; extend role String to accept `'superadmin'`)
- [ ] T013 [P] Add `center_id` FK column to `Student` model in `backend/app/models/student.py` (UUID FK → centers.id, NOT NULL at app layer)
- [ ] T014 [P] Add `center_id` FK column to `Teacher` model in `backend/app/models/teacher.py`
- [ ] T015 [P] Add `center_id` FK column to `ClassSession` model in `backend/app/models/class_session.py`
- [ ] T016 [P] Add `center_id` FK column to `ClassEnrollment` model in `backend/app/models/class_enrollment.py`
- [ ] T017 [P] Add `center_id` FK column to `Package` model in `backend/app/models/package.py`
- [ ] T018 [P] Add `center_id` FK column to `PaymentRecord` model in `backend/app/models/payment_record.py`
- [ ] T019 [P] Add `center_id` FK column to `Attendance` model in `backend/app/models/attendance.py`
- [ ] T020 [P] Add `center_id` FK column to `RenewalReminder` model in `backend/app/models/renewal_reminder.py`
- [ ] T021 [P] Add `center_id` FK column to `LessonKind` model in `backend/app/models/lesson_kind.py`
- [ ] T022 [P] Add `center_id` FK column to `StudentStatusHistory` model in `backend/app/models/student_status_history.py`
- [ ] T023 Update `backend/app/models/__init__.py` to import and export the new `Center` model
- [ ] T024 Write Alembic migration `backend/alembic/versions/013_multi_tenant_centers.py` with operations in order: (1) CREATE TABLE centers, (2) INSERT legacy center row with code `CTR-001`, (3) for each of 11 tenant tables: ADD COLUMN center_id NULLABLE → UPDATE all rows to legacy center id → SET NOT NULL → ADD FK CONSTRAINT → CREATE INDEX, (4) ADD center_id to users table with same nullable+update pattern, (5) INSERT superadmin user with `center_id=NULL`, `role='superadmin'`, `username='superadmin'`, bcrypt-hashed password `SuperAdmin@2026!`
- [ ] T025 Add `get_center_id(current_user)` helper and `require_superadmin()` dependency to `backend/app/core/deps.py` — `get_center_id` extracts `center_id` from user dict and raises HTTP 403 if user is superadmin (superadmin has no center); `require_superadmin` raises HTTP 403 if role is not `superadmin`
- [ ] T026 Add mandatory `center_id: UUID` parameter to all list/get/create functions in `backend/app/crud/student.py` and apply `WHERE students.center_id = :center_id` filter to every query
- [ ] T027 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/teacher.py`
- [ ] T028 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/class_session.py`
- [ ] T029 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/class_enrollment.py`
- [ ] T030 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/package.py`
- [ ] T031 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/payment_record.py`
- [ ] T032 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/attendance.py`
- [ ] T033 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/lesson_kind.py`
- [ ] T034 [P] Add mandatory `center_id: UUID` parameter and filter to all functions in `backend/app/crud/renewal_reminder.py`
- [ ] T035 Inject `center_id = get_center_id(current_user)` into every endpoint handler in `backend/app/api/students.py` and pass to CRUD functions (depends on T025, T026)
- [ ] T036 [P] Inject `center_id` into every endpoint handler in `backend/app/api/teachers.py` (depends on T025, T027)
- [ ] T037 [P] Inject `center_id` into every endpoint handler in `backend/app/api/classes.py` (depends on T025, T028)
- [ ] T038 [P] Inject `center_id` into every endpoint handler in `backend/app/api/packages.py` (depends on T025, T030)
- [ ] T039 [P] Inject `center_id` into every endpoint handler in `backend/app/api/attendance.py` (depends on T025, T032)
- [ ] T040 [P] Inject `center_id` into every endpoint handler in `backend/app/api/lesson_kinds.py` (depends on T025, T033)
- [ ] T041 [P] Inject `center_id` into every endpoint handler in `backend/app/api/dashboard.py` (depends on T025)
- [ ] T042 [P] Inject `center_id` into every endpoint handler in `backend/app/api/schedule.py` (depends on T025)
- [ ] T043 Add `center_id` and `center_code` fields to `UserResponse` schema in `backend/app/schemas/user.py` (both Optional/nullable for superadmin)
- [ ] T044 Run `alembic upgrade head` to apply migration `013_multi_tenant_centers` and verify it completes without errors — legacy center `CTR-001` exists, all existing rows have `center_id` set, superadmin user created

**Checkpoint**: Foundation ready — existing app continues to work for the legacy center admin; superadmin account exists; all CRUD functions now enforce `center_id` filtering. Run the existing Playwright E2E tests to confirm no regressions before proceeding.

---

## Phase 3: User Story 1 — System Admin Registers a New Edu-Center (Priority: P1) 🎯 MVP

**Goal**: The superadmin can log in, see the system console, and register a new edu-center with credentials delivered via a "show once" modal.

**Independent Test**: Log in as `superadmin / SuperAdmin@2026!` → redirected to `/system/centers` → create center `Nhạc Viện Demo` with admin `demo_admin` → modal shows `CTR-002` code and temporary password → center appears in list. (Steps A–B of quickstart.md)

### Implementation for User Story 1

- [ ] T045 [US1] Implement `Center` CRUD functions in `backend/app/crud/center.py`: `create_center(db, name, registered_by_id) → Center` (generates `code` as `CTR-{NNN}` using `SELECT COUNT(*)+1 FROM centers`), `list_centers(db, search, is_active) → list[Center]`, `get_center(db, center_id) → Center | None`, `patch_center(db, center_id, **kwargs) → Center`
- [ ] T046 [US1] Implement `create_center_with_admin` service in `backend/app/services/center_service.py`: atomically creates `Center` record + provisions `User` record with role=`admin`, center_id=new center's id, auto-generated 12-char alphanumeric password; returns `(center, admin_user, plain_password)` tuple
- [ ] T047 [US1] Implement `CenterCreate`, `CenterResponse`, `CenterListItem`, `CreateCenterResponse` (includes nested `admin_credentials` with `username`, `temporary_password`, `note`) Pydantic schemas in `backend/app/schemas/center.py`
- [ ] T048 [US1] Implement `POST /api/v1/system/centers` endpoint in `backend/app/api/system/centers.py`: requires superadmin role, validates name uniqueness + email/username uniqueness, calls `center_service.create_center_with_admin`, returns `CreateCenterResponse` with the temporary password
- [ ] T049 [US1] Implement `GET /api/v1/system/centers` endpoint in `backend/app/api/system/centers.py`: requires superadmin role, accepts `?search=` and `?is_active=` query params, returns list of `CenterListItem`
- [ ] T050 [US1] Register `system` router in `backend/app/api/__init__.py` with prefix `/system` and tag `System Admin`
- [ ] T051 [US1] Implement `createCenter(data)`, `listCenters(params)` API functions in `frontend/src/api/centers.js` (axios calls to `/api/v1/system/centers`)
- [ ] T052 [US1] Implement `SuperadminRoute` component in `frontend/src/auth/SuperadminRoute.jsx`: wraps children, reads `user.role` from `AuthContext`; if role is not `superadmin` redirects to `/` with "Access Denied" toast; if unauthenticated redirects to `/login`
- [ ] T053 [US1] Implement `CenterListPage` in `frontend/src/features/system/CenterListPage.jsx`: standalone layout (no app sidebar), shows Ant Design Table with columns Center Code, Center Name, Admin Username, Admin Email, Registered Date, Status badge, Actions column; "Add New Center" button in top-right; search input; calls `listCenters()`; uses React Query
- [ ] T054 [US1] Implement `CenterFormPage` in `frontend/src/features/system/CenterFormPage.jsx`: 4-field form (Center Name, Admin Full Name, Admin Username, Admin Email); on submit calls `createCenter()`; on success opens Ant Design Modal with Center Code, admin username, monospaced temporary password box with copy-to-clipboard button, ⚠️ warning text, "Done" button that navigates back to `/system/centers`; on 409 shows inline field errors
- [ ] T055 [US1] Add `/system` route subtree to `frontend/src/routes/index.jsx`: wrap in `<SuperadminRoute>`, children: `{ index: redirect to /system/centers }`, `{ path: 'centers', element: <CenterListPage> }`, `{ path: 'centers/new', element: <CenterFormPage> }`
- [ ] T056 [US1] Update post-login redirect in `frontend/src/auth/AuthContext.jsx` (or login page component): if `user.role === 'superadmin'` navigate to `/system/centers`; else continue with existing logic
- [ ] T057 [US1] Add i18n keys for system console to `frontend/src/i18n/vi.json` and `frontend/src/i18n/en.json`: keys for `system.centers.title`, `system.centers.addCenter`, `system.centers.code`, `system.centers.credentialsNote`, `system.centers.deactivate`, `system.centers.reactivate`, and form field labels

**Checkpoint**: At this point, User Story 1 is fully functional. Superadmin can log in, see the center console, create a new center, and receive the credentials. Verify with quickstart.md Steps A–B before proceeding.

---

## Phase 4: User Story 2 — Center Account Logs In with Isolated View (Priority: P2)

**Goal**: A provisioned center admin logs in with their credentials and sees the existing app UI scoped exclusively to their center's data. No cross-tenant data leaks.

**Independent Test**: Create center via superadmin → log in as center admin → navigate to all feature pages → verify data is empty (new center) → create one student → log in as legacy center admin → confirm new student does NOT appear. (Steps C–D of quickstart.md)

### Implementation for User Story 2

- [ ] T058 [US2] Update `frontend/src/auth/AuthContext.jsx`: persist `center_id` and `center_code` from the login response `user` object to localStorage and to the `user` state (the backend already returns these in `UserResponse` after T043)
- [ ] T059 [US2] Verify tenant isolation end-to-end by running the Playwright smoke script against quickstart.md Steps C–D: (a) log in as `demo_admin`, navigate to Students — expect empty list; (b) create one student; (c) log out, log in as legacy `admin` — confirm the new student does NOT appear in Students list. Capture any isolation failures as bugs to fix before proceeding.
- [ ] T060 [US2] Add `center_id` guard to `ProtectedRoute` component in `frontend/src/auth/ProtectedRoute.jsx`: if authenticated user has `role === 'superadmin'` and the requested route does NOT start with `/system`, redirect to `/system/centers` (prevents superadmin from accidentally accessing tenant pages)
- [ ] T061 [US2] Add navigation guard for `/system/*` paths in `frontend/src/routes/index.jsx`: if a non-superadmin user navigates to any `/system` path, `SuperadminRoute` (T052) handles the redirect — verify this guard fires correctly via browser test

**Checkpoint**: At this point, User Stories 1 AND 2 are both functional. A new center admin experiences the full existing app UX with their data isolated. Run the full isolation test (quickstart.md Steps C–D) before proceeding.

---

## Phase 5: User Story 3 — System Admin Views and Manages the Center List (Priority: P3)

**Goal**: The superadmin can view the full center list with search/filter and deactivate/reactivate centers. Deactivation immediately blocks the center admin's login.

**Independent Test**: Register two centers → confirm both appear in list → deactivate one → attempt login as deactivated center admin → confirm HTTP 401 / "Account is inactive" → reactivate → confirm login succeeds. (Steps E of quickstart.md)

### Implementation for User Story 3

- [ ] T062 [US3] Implement `GET /api/v1/system/centers/{center_id}` endpoint in `backend/app/api/system/centers.py`: superadmin only; returns single `CenterResponse`; 404 if not found
- [ ] T063 [US3] Implement `PATCH /api/v1/system/centers/{center_id}` endpoint in `backend/app/api/system/centers.py`: superadmin only; accepts `{ name?: string, is_active?: bool }`; when `is_active` changes to `false`, also sets `is_active = false` on all `User` records with `center_id` matching the target center (using `crud/user.py` bulk update); when `is_active` changes to `true`, re-activates those users; returns updated `CenterResponse`; 404 if not found; 409 if new name conflicts
- [ ] T064 [US3] Add `bulk_set_active_by_center(db, center_id, is_active)` function to `backend/app/crud/user.py` — `UPDATE users SET is_active = :is_active WHERE center_id = :center_id AND role != 'superadmin'`
- [ ] T065 [US3] Add `patchCenter(centerId, data)` API function to `frontend/src/api/centers.js` (PATCH `/api/v1/system/centers/{centerId}`)
- [ ] T066 [US3] Add deactivate/reactivate action to `CenterListPage` in `frontend/src/features/system/CenterListPage.jsx`: "Deactivate" button in Actions column (shown when `is_active = true`); "Reactivate" button (shown when `is_active = false`); clicking "Deactivate" opens Ant Design confirmation modal: "Are you sure you want to deactivate [Center Name]? Their admin account will be locked immediately."; on confirm calls `patchCenter(id, { is_active: false })`; on success updates list row status badge; "Reactivate" calls `patchCenter(id, { is_active: true })` directly (no confirmation modal)
- [ ] T067 [US3] Add search input to `CenterListPage` (already scaffolded in T053): wire `onChange` to filter the table by `name` or `code` substring (client-side filtering for ≤50 centers); add "All / Active / Inactive" radio group filter that passes `is_active` param to `listCenters()`
- [ ] T068 [US3] Add i18n keys for deactivate/reactivate actions to `frontend/src/i18n/vi.json` and `frontend/src/i18n/en.json`: `system.centers.deactivateConfirmTitle`, `system.centers.deactivateConfirmBody`, `system.centers.reactivateSuccess`, `system.centers.deactivateSuccess`

**Checkpoint**: All three user stories are complete. Run the full quickstart.md 25-step smoke flow to validate the entire feature end-to-end.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Error handling hardening, minor UX improvements, and i18n completeness across all stories.

- [ ] T069 [P] Add unit test for `code` generation logic (CTR-NNN sequential counter with race condition handling) in `backend/tests/unit/test_center_code_generation.py`
- [ ] T070 [P] Add integration test for center CRUD and tenant isolation in `backend/tests/integration/test_tenant_isolation.py`: create two centers, confirm student created in center A returns zero results when queried with center B's `center_id`
- [ ] T071 [P] Add integration test for center creation + admin provisioning in `backend/tests/integration/test_center_crud.py`: POST /system/centers, verify response shape, verify admin user exists in DB with correct center_id
- [ ] T072 [P] Add Playwright E2E spec for superadmin center-create flow in `frontend/tests/e2e/superadmin-center-create.spec.js`: steps A–B of quickstart.md automated
- [ ] T073 [P] Add Playwright E2E spec for tenant isolation in `frontend/tests/e2e/tenant-isolation.spec.js`: steps C–D of quickstart.md automated
- [ ] T074 Review all existing API endpoints for any that allow superadmin access to tenant data (e.g., does `GET /api/v1/students` with a superadmin token return an error or empty list?). Enforce HTTP 403 for superadmin on all non-system endpoints in `backend/app/core/deps.py`
- [ ] T075 [P] Ensure all new i18n keys are complete in both `frontend/src/i18n/vi.json` and `frontend/src/i18n/en.json` — no untranslated strings in either language
- [ ] T076 Run full quickstart.md 25-step smoke flow manually (or via Playwright) and confirm all steps pass

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately; all tasks create empty files
- **Foundational (Phase 2)**: Depends on Phase 1 (files exist) — **BLOCKS all user stories**; Alembic migration must complete before any feature work
- **User Story 1 (Phase 3)**: Depends on Phase 2 — superadmin role, centers table, and system router prerequisite
- **User Story 2 (Phase 4)**: Depends on Phase 2 (CRUD isolation already in place) + Phase 3 (center provisioning needed to create a test center account)
- **User Story 3 (Phase 5)**: Depends on Phase 2 + Phase 3 (list page scaffolded in T053, extends it)
- **Polish (Phase 6)**: Depends on Phases 3–5 all complete

### User Story Dependencies

| Story | Depends on | Can parallel with |
|-------|-----------|------------------|
| US1 (P1) | Phase 2 only | — |
| US2 (P2) | Phase 2 + US1 (needs a provisioned account to test) | US3 after Phase 2 |
| US3 (P3) | Phase 2 + US1 (extends CenterListPage from T053) | US2 after Phase 2 |

### Within Each Phase

- T013–T022 (model FK columns) run in parallel with each other
- T026–T034 (CRUD filter additions) run in parallel with each other
- T035–T042 (API endpoint injections) run in parallel with each other
- T048–T050 (system endpoints) run sequentially (share same router file)
- T051–T057 (frontend US1) run mostly in parallel except: T055 depends on T052–T054; T056 can run anytime

### Critical Path

```
T001–T010 (setup) → T011–T023 (models) → T024 (migration) → T025 (deps) 
→ T026–T042 (CRUD+API isolation) → T043 (schema) → T044 (verify migration)
→ [US1: T045–T057] → [US2: T058–T061] → [US3: T062–T068] → [Polish: T069–T076]
```

---

## Parallel Execution Examples

### Phase 2 — Model columns (run all together)

```
Task: "Add center_id FK to Student model in backend/app/models/student.py"     [T013]
Task: "Add center_id FK to Teacher model in backend/app/models/teacher.py"     [T014]
Task: "Add center_id FK to ClassSession in backend/app/models/class_session.py"[T015]
Task: "Add center_id FK to ClassEnrollment..."                                  [T016]
Task: "Add center_id FK to Package..."                                          [T017]
Task: "Add center_id FK to PaymentRecord..."                                    [T018]
Task: "Add center_id FK to Attendance..."                                       [T019]
Task: "Add center_id FK to RenewalReminder..."                                  [T020]
Task: "Add center_id FK to LessonKind..."                                       [T021]
Task: "Add center_id FK to StudentStatusHistory..."                             [T022]
```

### Phase 2 — CRUD isolation (run all together after T025)

```
Task: "Add center_id filter to crud/student.py"     [T026]
Task: "Add center_id filter to crud/teacher.py"     [T027]
Task: "Add center_id filter to crud/class_session.py" [T028]
... (T029–T034 same pattern)
```

### Phase 3 — Backend vs Frontend (run in parallel after T044)

```
Wave A (backend): T045 → T046 → T047 → T048 → T049 → T050
Wave B (frontend): T051, T052, T053, T054 (parallel) → T055 → T056 → T057
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup (empty files)
2. Complete Phase 2: Foundational (migration + CRUD isolation) — **verify no regressions on existing app**
3. Complete Phase 3: User Story 1 (superadmin creates centers)
4. **STOP and VALIDATE**: Log in as superadmin, create a center, confirm credentials appear
5. Demo to stakeholder if ready

### Incremental Delivery

1. Phase 1 + 2 → Foundation complete; existing app works transparently for legacy center
2. Phase 3 → Superadmin can onboard new edu-centers (**MVP delivery point**)
3. Phase 4 → Tenant isolation confirmed end-to-end
4. Phase 5 → Deactivation management complete
5. Phase 6 → Tests + polish

### Parallel Team Strategy

With two developers after Phase 2 completes:
- **Developer A**: Phase 3 backend (T045–T050) while Developer B does Phase 3 frontend (T051–T057)
- After Phase 3: Developer A does Phase 5 backend (T062–T065) while Developer B does Phase 4 (T058–T061) and Phase 5 frontend (T066–T068)

---

## Notes

- [P] tasks = different files, no dependencies on incomplete tasks in the same phase
- T044 is the key migration checkpoint — do not proceed past Phase 2 until migration runs cleanly
- The existing Playwright E2E suite should be run after T044 to confirm no regressions before writing new feature code
- Superadmin's `center_id = NULL` is intentional — any CRUD function receiving NULL must be rejected at the `get_center_id()` dep layer (T025), not silently queried
- `temporary_password` in the API response is returned **once only** — it is NOT stored in the DB (only the bcrypt hash is stored)
- Avoid: modifying the same CRUD file in parallel tasks within the same phase; cross-story dependencies that break story independence
