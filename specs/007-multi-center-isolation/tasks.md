# Tasks: Multi-Center Data Isolation

**Input**: Design documents from `/specs/007-multi-center-isolation/`
**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: Test tasks are included per the `Independent Test` criteria outlined in the spec user stories.
**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Test infrastructure for multi-center validation

- [X] T001 Create `backend/tests/test_center_isolation.py` scaffold with basic auth helpers for multi-center testing

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Fix core auth dependencies before any specific resource tests can pass.

- [X] T002 [P] Update `get_current_user` in `backend/app/core/deps.py` to load center and check `center.is_active` (Gap G6)
- [X] T003 [P] Update `login` in `backend/app/api/auth.py` to check `center.is_active` before issuing tokens (Gap G5)

**Checkpoint**: Foundation ready - Center deactivation handling works, enabling isolated tenant operations.

---

## Phase 3: User Story 1 - Center Admin Sees Only Their Own Students, Teachers, and Classes (Priority: P1) 🎯 MVP

**Goal**: Read operations strictly isolated by center.

**Independent Test**: Create two centers (Center A and Center B). Add students, teachers, classes, and tuition records under each. Log in as Center A's admin and verify every page shows only Center A's data.

### Tests for User Story 1

- [X] T004 [P] [US1] Integration test for isolated read access in `backend/tests/test_center_isolation.py` (verify 404 on cross-center lookup)

### Implementation for User Story 1

*Note: Listing and direct lookups are largely handled by existing `get_center_id` injection per spec audit. We need to patch the missing CRUD level cross-center 404 scopes.*

- [X] T005 [P] [US1] Add `center_id` param to `delete_class_session` in `backend/app/crud/class_session.py` and scope lookup (Gap G1)
- [X] T006 [P] [US1] Update `delete_class_endpoint` in `backend/app/api/classes.py` to pass `center_id` to CRUD
- [X] T007 [P] [US1] Add `center_id` param to `unenroll_student` in `backend/app/crud/class_session.py` and scope lookup (Gap G2)
- [X] T008 [P] [US1] Update `unenroll_student_endpoint` in `backend/app/api/classes.py` to pass `center_id` to CRUD

**Checkpoint**: Read/Delete operations are strictly isolated. No cross-center leakage.

---

## Phase 4: User Story 2 - Center Admin Creates Records Scoped to Their Center (Priority: P1)

**Goal**: Write operations and cross-entity relationships strictly isolated by center.

**Independent Test**: Log in as Center A's admin, create a new student, then log in as Center B's admin and confirm the student is not visible.

### Tests for User Story 2

- [X] T009 [P] [US2] Integration test for cross-center creation blocking (e.g. enrolling Center B student in Center A class) in `backend/tests/test_center_isolation.py`

### Implementation for User Story 2

- [X] T010 [P] [US2] Add cross-entity center validation in `enroll_student` in `backend/app/crud/class_session.py` (Gap G4)
- [X] T011 [P] [US2] Add server-side teacher center validation in `create_class_session` and `update_class_session` in `backend/app/crud/class_session.py` (Data Model Rule 2)

**Checkpoint**: Write operations cannot mix entities from different centers.

---

## Phase 5: User Story 3 - Schedule and Dashboard Show Center-Scoped Data (Priority: P2)

**Goal**: Aggregate queries and conflict detection strictly isolated by center.

**Independent Test**: Create two centers. Verify the dashboard numbers match only that center's data. Verify the schedule calendar shows only that center's classes.

### Tests for User Story 3

- [X] T012 [P] [US3] Integration test for isolated schedule conflict detection in `backend/tests/test_center_isolation.py`

### Implementation for User Story 3

- [X] T013 [P] [US3] Add `center_id` parameter to `check_scheduling_conflicts` in `backend/app/services/schedule_service.py` and filter base query (Gap G3)
- [X] T014 [P] [US3] Update `create_class` and `enroll_student_endpoint` in `backend/app/api/classes.py` to pass `center_id` to `check_scheduling_conflicts`

**Checkpoint**: Dashboards and schedules compute correctly per center.

---

## Phase 6: User Story 4 - Superadmin Cannot Access Center-Scoped Data Directly (Priority: P3)

**Goal**: Role separation enforced.

**Independent Test**: Log in as superadmin and attempt to navigate to any center-scoped page. Verify redirect. Call center APIs directly, verify 403.

### Tests for User Story 4

- [X] T015 [P] [US4] E2E test via Playwright verifying superadmin is redirected from operational pages to `/system/centers`

### Implementation for User Story 4

*Note: Backend `get_center_id` already throws 403 for superadmin. Frontend `ProtectedRoute.jsx` already redirects (Gap G7). No backend code changes needed. E2E test validates existing behavior.*

**Checkpoint**: Superadmin boundaries confirmed.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final verification.

- [X] T016 Run full test suite to verify no regressions in existing endpoints
- [ ] T017 Execute UI smoke test for Center Admin login and basic navigation (manual; deferred — requires running frontend + seeded centers)

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: Can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories.
- **User Stories (Phase 3+)**: All depend on Foundational phase completion. Proceed in priority order (P1 → P2 → P3).
- **Polish (Final Phase)**: Depends on all user stories being complete.

### Parallel Opportunities

- Foundational tasks T002 and T003 can be executed in parallel.
- All tasks marked [P] within a given Phase can run in parallel.
- Tests (T004, T009, T012, T015) can be authored in parallel with their corresponding implementation tasks.

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently
3. Add User Story 2 → Test independently
4. Add User Story 3 → Test independently
5. Add User Story 4 → Test independently
