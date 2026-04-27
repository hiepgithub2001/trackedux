---
description: "Task list for Student & Parent Info Restructure"
---

# Tasks: Student & Parent Info Restructure

**Input**: Design documents from `/specs/002-student-parent-info-restructure/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/student-api.md

**Tests**: No automated tests requested in spec; manual verification tasks included in US3 + Polish.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3)
- File paths are absolute or repo-relative

## Path Conventions

- Backend: `backend/app/...`, `backend/alembic/versions/...`
- Frontend: `frontend/src/...`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Confirm the dev environment is ready for backend + frontend changes.

- [X] T001 Verify backend dev environment is ready: PostgreSQL reachable, `alembic current` runs cleanly from `backend/`, frontend dev server boots via `npm run dev` in `frontend/`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend data layer changes that all user stories depend on. Adds the `contact` JSONB column, migrates existing parent data, removes the `parent_id` FK, and updates the API contract.

**⚠️ CRITICAL**: No user story work can begin until this phase is complete.

- [X] T002 [P] Update `Student` model in `backend/app/models/student.py`: add `contact: Mapped[dict | None] = mapped_column(JSONB, nullable=True)` (import `JSONB` from `sqlalchemy.dialects.postgresql`); remove `parent_id` column and the `parent = relationship("Parent", ...)` line
- [X] T003 [P] Update `Parent` model in `backend/app/models/parent.py`: remove the `students = relationship("Student", back_populates="parent", lazy="selectin")` line (no FK from students anymore)
- [X] T004 Update Pydantic schemas in `backend/app/schemas/student.py`: add `ContactInfo` model (fields: `name`, `relationship`, `phone`, `phone_secondary`, `email`, `address`, `zalo_id`, `notes` — all `str | None = None`); update `StudentCreate` (remove `parent_id`, add `contact: ContactInfo | None = None`); update `StudentUpdate` (add `contact: ContactInfo | None = None`); update `StudentResponse` (remove `parent_id`, add `contact: ContactInfo | None = None`); update `StudentListItem` (rename `parent_name` → `contact_name`)
- [X] T005 Update student CRUD in `backend/app/crud/student.py`: remove all `selectinload(Student.parent)` calls in `get_student_by_id` and `list_students`; ensure `create_student` writes the `contact` dict from `data.contact.model_dump() if data.contact else None`; ensure `update_student` writes `contact` similarly when present in the update payload
- [X] T006 Update students API in `backend/app/api/students.py`: replace `parent_name=s.parent.full_name if s.parent else None` with `contact_name=(s.contact or {}).get('name') if s.contact else None` in the list endpoint; verify `StudentResponse.model_validate(student)` still works for `contact`
- [X] T007 [P] Create Alembic migration `backend/alembic/versions/010_student_contact.py`: upgrade adds `contact JSONB NULL` to `students`, runs `UPDATE students s SET contact = jsonb_build_object('name', p.full_name, 'relationship', 'parent', 'phone', p.phone, 'phone_secondary', p.phone_secondary, 'email', null, 'address', p.address, 'zalo_id', p.zalo_id, 'notes', p.notes) FROM parents p WHERE p.id = s.parent_id`, drops `students_parent_id_fkey`, drops `ix_students_parent_id`, drops `parent_id` column; downgrade adds back `parent_id UUID` (best-effort) and drops `contact`
- [X] T008 Apply migration: run `cd backend && alembic upgrade head` and confirm `students` table has the new `contact` column with migrated data via `psql` spot-check

**Checkpoint**: Backend now exposes `contact` as a JSON object on student endpoints; `parent_id` is gone from the schema. Foundation ready — user story implementation can now begin.

---

## Phase 3: User Story 1 - Edit Student with Contact Section (Priority: P1) 🎯 MVP

**Goal**: Staff opening an existing student record see a collapsible "Contact Information" section inline (no tab/modal) and can edit and save contact data alongside student data in one form submission.

**Independent Test**: Open `/students/<id>/edit`, confirm a collapsed "Contact Information" panel exists, expand it, edit a field (e.g., phone), click Save, then refresh the page and confirm the new value persists.

### Implementation for User Story 1

- [X] T009 [US1] In `frontend/src/features/students/StudentForm.jsx`: import `Collapse` from `antd`; remove the `parent_id` `<Form.Item>` (Select + ParentFormModal trigger), the `listParents` query, and the `ParentFormModal` import + state (`isParentModalOpen`)
- [X] T010 [US1] In `frontend/src/features/students/StudentForm.jsx`: add a `<Collapse>` panel with header "Contact Information" (i18n: `students.contactInfo`), `defaultActiveKey={[]}` (collapsed by default); inside the panel add `<Form.Item>` fields for `contact.name`, `contact.relationship` (Select with options: parent, guardian, self, other — values free-text), `contact.phone`, `contact.phone_secondary`, `contact.email`, `contact.address`, `contact.zalo_id`, `contact.notes`. Use Ant Design `Form.Item name={['contact', 'name']}` (array path) for nested form values
- [X] T011 [US1] In `frontend/src/features/students/StudentForm.jsx`: update the edit-mode `useEffect` to populate contact subfields via `form.setFieldsValue({ ...student, contact: student.contact || {}, date_of_birth: ... })`; ensure null `student.contact` resolves to an empty object so the form doesn't crash
- [X] T012 [US1] In `frontend/src/features/students/StudentForm.jsx`: configure the Collapse to programmatically open when `form.getFieldError(['contact', ...])` is non-empty after submit failure — track active key in component state and set it on `onFinishFailed`
- [X] T013 [P] [US1] In `frontend/src/features/students/StudentDetail.jsx`: replace any old `parent_id` / `parent.full_name` rendering with display of `student.contact.name`, `student.contact.phone`, `student.contact.email`, `student.contact.relationship`, etc. (show "—" for null fields)
- [X] T014 [P] [US1] Add i18n keys in `frontend/src/i18n/en.json` and `frontend/src/i18n/vi.json` under `students`: `contactInfo`, `contactName`, `relationship`, `relationshipParent`, `relationshipGuardian`, `relationshipSelf`, `relationshipOther`, `email` (keep existing `phone`, `phoneSecondary`, `address`, `zaloId`, `notes`)

**Checkpoint**: User Story 1 is fully functional. Editing an existing student's contact info via the inline collapsible section works end-to-end and persists.

---

## Phase 4: User Story 2 - Add a New Student with Contact Section (Priority: P2)

**Goal**: Staff creating a new student see the same collapsible "Contact Information" section inline and can submit the full record (including contact info) in a single form action.

**Independent Test**: Navigate to `/students/new`, fill the student fields, expand the contact section, fill phone + email, click Save, and confirm the new student appears in the list with the correct `contact_name`.

### Implementation for User Story 2

- [X] T015 [US2] In `frontend/src/features/students/StudentForm.jsx`: confirm `initialValues` include `contact: {}` so the create-mode form starts with an empty contact object (the same form component already handles both create and edit modes)
- [X] T016 [US2] Verify `frontend/src/api/students.js` `createStudent` and `updateStudent` pass through the `contact` object unchanged (axios serializes nested objects as JSON automatically — no client-side change required if the wrapper just forwards the payload). Read the file and confirm; only edit if a transform strips fields
- [X] T017 [US2] In `frontend/src/features/students/StudentList.jsx`: rename references to `parent_name` → `contact_name` in the list table column (header label can remain "Parent" or change to "Contact" — use i18n key `students.contact` or similar)

**Checkpoint**: Both create and edit flows use the same inline collapsible contact section. User Stories 1 and 2 both work independently.

---

## Phase 5: User Story 3 - Data Layer Verification (Priority: P3)

**Goal**: Confirm `contact` is stored as embedded JSON on the `students` table and migrated parent records are preserved with no data loss.

**Independent Test**: Connect to the database and run `SELECT id, name, contact FROM students LIMIT 5;` — confirm `contact` is a JSON object with `name`, `phone`, `relationship='parent'`, etc., for migrated records.

### Implementation for User Story 3

- [X] T018 [US3] Verify migration data integrity: from `backend/`, run `psql $DATABASE_URL -c "SELECT COUNT(*) FROM students WHERE contact IS NOT NULL"` and compare to `psql $DATABASE_URL -c "SELECT COUNT(*) FROM parents p JOIN (the pre-migration student-parent link)"` — confirm 100% of pre-migration students with parents now have `contact` populated. Document the verification commands in a comment at the top of `backend/alembic/versions/010_student_contact.py`
- [X] T019 [US3] Verify API contract: `curl http://localhost:8000/students/<id>` returns a `contact` object embedded in the response (not a separate `parent_id` field). `curl http://localhost:8000/students` list response contains `contact_name` for each item (not `parent_name`)

**Checkpoint**: All three user stories independently verified. Data layer correctly stores contact as embedded JSON.

---

## Phase 6: Polish & Cleanup

**Purpose**: Remove dead code, validate end-to-end, and ensure no regressions.

- [X] T020 Delete `frontend/src/features/students/ParentFormModal.jsx` (no longer referenced anywhere after T009)
- [X] T021 [P] Search the frontend for remaining references to `parent_id`, `parent_name`, `listParents`, `createParent` in student-related files and clean up: `grep -r "parent_id\|parent_name\|listParents\|createParent" frontend/src/features/students frontend/src/api/students.js`
- [X] T022 [P] Run linters: `cd backend && ruff check app/` and `cd frontend && npm run lint`
- [X] T023 End-to-end smoke test in browser at `http://localhost:5173`: (a) create new student with contact info filled (incl. relationship="self", null name); (b) edit an existing student, expand contact section, change a field, save; (c) confirm the student list shows the correct `contact_name`; (d) confirm the student detail page displays contact info

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: No dependencies
- **Phase 2 (Foundational)**: Depends on Phase 1 — BLOCKS all user stories
- **Phase 3 (US1)**: Depends on Phase 2 complete
- **Phase 4 (US2)**: Depends on Phase 2 complete; benefits from T009-T012 (StudentForm.jsx) being done since it shares the component
- **Phase 5 (US3)**: Depends on Phase 2 complete (especially migration in T008)
- **Phase 6 (Polish)**: Depends on Phases 3, 4, 5 (or any subset that's been completed)

### User Story Dependencies

- **US1 (P1)**: Independent — fully testable after Phase 2 + T009-T014
- **US2 (P2)**: Re-uses StudentForm.jsx changes from US1 (T009-T012); T015-T017 are small additions
- **US3 (P3)**: Independent verification — testable after Phase 2 only; no UI dependency

### Within Each Phase

- Tasks marked `[P]` operate on different files and can run in parallel
- Tasks not marked `[P]` either operate on the same file as a sibling task or have a hard dependency on a prior task in the same phase

---

## Parallel Opportunities

### Phase 2 Foundational

- T002 (`models/student.py`), T003 (`models/parent.py`), and T007 (`alembic/versions/010_student_contact.py`) are in different files and can run in parallel
- After T002 + T004 land, T005 (`crud/student.py`) and T006 (`api/students.py`) can run in parallel

### Phase 3 US1

- T013 (`StudentDetail.jsx`) and T014 (`i18n/*.json`) can run in parallel with T012 (form validation in `StudentForm.jsx`)

### Phase 6 Polish

- T021 (grep cleanup) and T022 (linters) can run in parallel

---

## Implementation Strategy

### MVP First (User Story 1)

1. Phase 1: Setup (T001)
2. Phase 2: Foundational (T002–T008) — backend data layer + migration
3. Phase 3: User Story 1 (T009–T014) — edit form with collapsible contact section
4. **STOP and VALIDATE**: Test edit flow end-to-end
5. Deploy/demo as MVP

### Incremental Delivery

1. MVP (Setup + Foundational + US1) → demo edit flow
2. Add US2 (T015–T017) → demo create flow
3. Add US3 verification (T018–T019) → confirm migration integrity
4. Polish (T020–T023) → cleanup + lint + smoke test

---

## Notes

- The `parents` table is **retained** because `parents.user_id` links to the auth `users` table. Only the FK from `students` to `parents` is dropped.
- The migration sets `relationship = "parent"` for all migrated records; this matches the prior assumption that the linked record was a parent/guardian.
- `email` is a new field; migrated records will have `email = null`.
- The Ant Design `Collapse` component supports controlled `activeKey`, which is needed for T012 (force-open on validation error).
- Avoid: editing `models/student.py` and `crud/student.py` simultaneously (T002 vs T005) — T005 depends on T002.
