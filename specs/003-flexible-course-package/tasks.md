# Tasks: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Input**: Design documents from `/specs/003-flexible-course-package/`
**Prerequisites**: plan.md ✅, spec.md ✅, research.md ✅, data-model.md ✅, contracts/ ✅, quickstart.md ✅

**Tests**: Not explicitly requested in spec — test tasks omitted. Tests can be added later.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Database migration and new model files that all user stories depend on

- [x] T001 Create Alembic migration `012_flexible_course_package.py` in `backend/alembic/versions/012_flexible_course_package.py` — create `lesson_kinds` table with unique index on `LOWER(TRIM(name))`, seed initial lesson kinds (Beginner, Elementary, Intermediate, Advanced), add `tuition_fee_per_lesson BIGINT` column to `class_sessions` with CHECK constraints (> 0, <= 100000000), drop `skill_level` column from `students`, drop `renewal_reminders` table, drop `payment_records` table, drop `packages` table, recreate `packages` with new schema (add `class_session_id` FK, `lesson_kind_id` FK, rename `total_sessions` → `number_of_lessons`, add CHECK constraints), recreate `payment_records` (FK → new packages), recreate `renewal_reminders` (FK → new packages). Include full downgrade.
- [x] T002 [P] Create LessonKind model in `backend/app/models/lesson_kind.py` — UUID PK, `name` VARCHAR(100) NOT NULL, `name_normalized` VARCHAR(100) NOT NULL UNIQUE, `created_at`/`updated_at` timestamps. Add import to `backend/app/models/__init__.py`.
- [x] T003 [P] Update Package model in `backend/app/models/package.py` — drop `package_type` and `total_sessions` columns, add `class_session_id` UUID FK → `class_sessions.id` (ON DELETE RESTRICT, NOT NULL), `lesson_kind_id` UUID FK → `lesson_kinds.id` (ON DELETE RESTRICT, NOT NULL), `number_of_lessons` INTEGER NOT NULL with CHECK (> 0, <= 500). Update `price` CHECK (> 0, <= 1000000000). Add relationships: `class_session` (selectin), `lesson_kind` (selectin). Keep existing `student`, `payments` relationships.
- [x] T004 [P] Update ClassSession model in `backend/app/models/class_session.py` — add `tuition_fee_per_lesson` BIGINT column (nullable, CHECK > 0, CHECK <= 100000000). Add `packages` relationship (back_populates from Package).
- [x] T005 [P] Update Student model in `backend/app/models/student.py` — drop `skill_level` column entirely. No replacement column needed (skill context goes in `personality_notes` free-text).

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Backend CRUD, schemas, and utility functions that MUST be complete before user story UI work begins

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

- [x] T006 [P] Create LessonKind CRUD in `backend/app/crud/lesson_kind.py` — implement `find_or_create_lesson_kind(db, name: str) -> LessonKind` using INSERT ON CONFLICT DO NOTHING + SELECT pattern for atomic concurrent-safe creation; implement `list_lesson_kinds(db, search: str | None) -> list[LessonKind]` with optional case-insensitive substring match; implement `normalize_lesson_kind_name(name: str) -> str` utility (trim, collapse whitespace, lowercase).
- [x] T007 [P] Create display ID utility in `backend/app/crud/class_session.py` — add `compute_display_ids(classes: list[ClassSession]) -> dict[UUID, str]` function that groups classes by `(TeacherFirstName, Weekday3, HHMM)`, sorts by `created_at`, assigns disambiguator `-{N}` suffix starting at 2 for collisions. Use `DAY_ABBR = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]`. Add `compute_single_display_id(cs: ClassSession, all_classes: list[ClassSession]) -> str` convenience wrapper.
- [x] T008 [P] Update Package schemas in `backend/app/schemas/package.py` — replace `PackageCreate` with new fields: `student_id` UUID, `class_session_id` UUID, `number_of_lessons` int (ge=1, le=500), `lesson_kind_name` str (min_length=1, max_length=100), `tuition_fee` int (ge=1, le=1000000000). Replace `PackageResponse` to drop `package_type`/`total_sessions`, add `class_session_id` UUID, `class_display_id` str, `lesson_kind_id` UUID, `lesson_kind_name` str, `number_of_lessons` int. Keep `PaymentRecordCreate` and `PaymentRecordResponse` unchanged.
- [x] T009 [P] Update ClassSession schemas in `backend/app/schemas/class_session.py` — add `tuition_fee_per_lesson: int | None` to `ClassSessionCreate` (optional, with ge=1 le=100000000 when provided), to `ClassSessionUpdate`, and to `ClassSessionResponse`. Add `display_id: str` and `enrolled_count: int` to `ClassSessionResponse`.
- [x] T010 [P] Update Student schemas in `backend/app/schemas/student.py` — remove `skill_level` from `StudentCreate` (drop the required field), `StudentUpdate`, `StudentResponse`, and `StudentListItem`.
- [x] T011 Update Package CRUD in `backend/app/crud/package.py` — rewrite `create_package(db, data)` to: (1) find-or-create lesson kind via `lesson_kind.find_or_create_lesson_kind`, (2) verify student exists, (3) verify class exists, (4) verify student is enrolled in class via `class_enrollments` table query (raise HTTPException 422 with display_id-aware message if not), (5) deactivate existing active package for student, (6) create Package with `class_session_id`, `lesson_kind_id`, `number_of_lessons`, `remaining_sessions=number_of_lessons`, `price=tuition_fee`. Update `list_packages` to eager-load `class_session` (with teacher) and `lesson_kind` relationships, and accept optional `class_session_id` filter. Update `get_package_by_id` to eager-load new relationships.
- [x] T012 Update ClassSession CRUD in `backend/app/crud/class_session.py` — add `update_class_session(db, class_id, data)` function. Add `delete_class_session(db, class_id)` function that checks for referencing packages (active or historical) and raises HTTPException 409 if any exist. Update `create_class_session` to accept and store `tuition_fee_per_lesson`. Update `list_class_sessions` and `get_class_session_by_id` to return enriched data including display_id computation.

**Checkpoint**: Foundation ready — backend models, schemas, CRUD, and migration all in place. User story implementation can now begin.

---

## Phase 3: User Story 1 — Admin Views the Classes Catalog (Priority: P1) 🎯 MVP

**Goal**: Admin opens a "Classes" tab and sees all classes with human-readable display IDs, per-lesson fees, and can create/edit/delete classes from this view.

**Independent Test**: Log in as admin → click Classes tab → verify display IDs, fee column, sorting/filtering → edit a fee → create a new class → verify disambiguator when two classes share (teacher, weekday, time). Log in as staff → verify fee column is hidden.

### Implementation for User Story 1

- [x] T013 [US1] Create LessonKinds API router in `backend/app/api/lesson_kinds.py` — GET `/lesson-kinds` endpoint accepting optional `?search=` query param, returns list of `{id, name, created_at}`. Register router in `backend/app/api/__init__.py`.
- [x] T014 [US1] Update Classes API in `backend/app/api/classes.py` — modify `_class_to_response` to include `display_id`, `enrolled_count`, and `tuition_fee_per_lesson` (null for non-admin users by checking `current_user.role`). Add PUT `/classes/{class_id}` endpoint for updating class (including `tuition_fee_per_lesson`). Add DELETE `/classes/{class_id}` endpoint that returns 409 if packages reference the class. Update POST to accept `tuition_fee_per_lesson`. Pass `current_user` to response builder for role-based fee visibility.
- [x] T015 [P] [US1] Update frontend API hooks in `frontend/src/api/classes.js` — add `updateClass(classId, data)` function, add `deleteClass(classId)` function. Update `fetchClasses` response shape to include `display_id`, `enrolled_count`, `tuition_fee_per_lesson`.
- [x] T016 [P] [US1] Create frontend API hooks in `frontend/src/api/lessonKinds.js` — export `fetchLessonKinds(search)` function calling GET `/api/v1/lesson-kinds?search=`.
- [x] T017 [US1] Update ClassForm to add fee input in `frontend/src/features/schedule/ClassForm.jsx` — add Ant Design `InputNumber` for `tuition_fee_per_lesson` with VND formatting (thousand separators), `min={1}`, `max={100000000}`, `addonAfter="VND"`, required field. Wire to class create/update API. ID: `class-form-tuition-fee-per-lesson`.
- [x] T018 [US1] Create ClassesPage component in `frontend/src/features/classes/ClassesPage.jsx` — Ant Design Table with columns: Display ID, Teacher (sortable, filterable), Weekday (sortable, filterable as dropdown), Time (sortable), Duration, Enrolled count (sortable), Fee/Lesson (admin-only, VND formatted, sortable). Click row navigates to `/classes/{id}`. "Create Class" button (admin-only) navigates to `/classes/new`. Empty state message. Use `@tanstack/react-query` to fetch from `/api/v1/classes`. Conditionally hide fee column for non-admin users using auth context.
- [x] T019 [US1] Update ClassDetail to show display ID and fee in `frontend/src/features/schedule/ClassDetail.jsx` — display `display_id` as bold header. Show `tuition_fee_per_lesson` with VND formatting (admin-only). Add "Edit" button that opens edit mode or navigates to edit form. Add "Delete" button (admin-only) that calls DELETE endpoint with confirmation modal, showing 409 error if packages reference the class.
- [x] T020 [US1] Add Classes route and navigation in `frontend/src/routes/index.jsx` and `frontend/src/components/Layout.jsx` — add `/classes` route pointing to `ClassesPage`. Add "Classes" / "Lớp học" nav item in sidebar between Schedule and Attendance, using appropriate Ant Design icon (e.g., `AppstoreOutlined`).
- [x] T021 [US1] Add i18n translations for Classes tab in `frontend/src/i18n/en.json` and `frontend/src/i18n/vi.json` — add keys: `nav.classes`, `classes.title`, `classes.displayId`, `classes.teacher`, `classes.weekday`, `classes.time`, `classes.duration`, `classes.enrolled`, `classes.feePerLesson`, `classes.createClass`, `classes.noClasses`, `classes.deleteConfirm`, `classes.deleteBlocked`.

**Checkpoint**: Classes tab fully functional — admin can view, create, edit fees, delete classes. Staff sees all columns except fee. Display IDs compute correctly with disambiguator suffixes.

---

## Phase 4: User Story 2 — Admin Creates a Flexible Course Package (Priority: P1) 🎯 MVP

**Goal**: Admin assigns a course package with 5 inputs (student, class, number of lessons, lesson kind, tuition fee) — no fixed presets. Auto-fill fee from class rate × lesson count. Inline lesson kind creation. Enrollment validation.

**Independent Test**: Create a package with arbitrary lesson count (8, 18, 50) → verify auto-fill → override fee → verify override persists → type new lesson kind → verify inline create → attempt package for non-enrolled student → verify rejection with link to enrollment. Verify attendance still decrements remaining sessions.

**Depends on**: User Story 1 (classes with display IDs and fees must exist)

### Implementation for User Story 2

- [x] T022 [US2] Update Packages API in `backend/app/api/packages.py` — rewrite `create_package_endpoint` to use new `PackageCreate` schema (student_id, class_session_id, number_of_lessons, lesson_kind_name, tuition_fee). Compute `class_display_id` for response/error messages. Return 422 with enrollment-specific message if student not enrolled. Rewrite `get_packages` response to use new `PackageResponse` shape with `class_display_id` and `lesson_kind_name`. Hide `price` from non-admin users. Add optional `class_session_id` query filter.
- [x] T023 [US2] Update attendance service in `backend/app/services/attendance_service.py` — verify `remaining_sessions` decrement still works with the restructured Package model (column renamed from `total_sessions` reference to `number_of_lessons`, but `remaining_sessions` column name unchanged). Update any references to `package_type` or `total_sessions` if they exist.
- [x] T024 [US2] Update tuition service in `backend/app/services/tuition_service.py` — verify `record_payment` still works with restructured Package model. No structural change expected but validate import paths and relationship loads.
- [x] T025 [P] [US2] Update frontend packages API hooks in `frontend/src/api/packages.js` — update `createPackage(data)` to send new shape: `{student_id, class_session_id, number_of_lessons, lesson_kind_name, tuition_fee}`. Update `fetchPackages` response parsing for new fields (`class_display_id`, `lesson_kind_name`, `number_of_lessons`). Add optional `class_session_id` filter param.
- [x] T026 [US2] Create PackageForm component in `frontend/src/features/tuition/PackageForm.jsx` — modal/drawer with 5 inputs: (1) Student `Select` with search-by-name (fetches from `/students`), (2) Class `AutoComplete` with typeahead by display_id (fetches from `/classes`, each option shows display_id + teacher + weekday/time), (3) Number of Lessons `InputNumber` min=1 max=500 precision=0, (4) Lesson Kind `AutoComplete` with typeahead (fetches from `/lesson-kinds?search=`, shows "Create new: {typed}" option when no exact match), (5) Tuition Fee `InputNumber` with VND formatting min=1 max=1000000000. Implement auto-fill logic: `useEffect` watches `selectedClass` and `numberOfLessons`, computes `fee = class.tuition_fee_per_lesson * numberOfLessons` when `isManualFeeEdit` is false. On manual fee edit, set `isManualFeeEdit=true`. Optional "Reset to auto-fill" button. Client-side enrollment pre-check: if student not in `class.enrolled_students`, show inline warning with link to class enrollment. On save, call POST `/packages`. Element IDs per ui.md contract.
- [x] T027 [US2] Update TuitionPage in `frontend/src/features/tuition/TuitionPage.jsx` — replace existing package creation form/flow with `PackageForm` component (modal trigger: "Assign Package" button). Update table columns: drop "Package Type", add "Class" (`class_display_id`), add "Lesson Kind" (`lesson_kind_name`), rename "Sessions" → "Lessons" (`number_of_lessons`), keep "Remaining" (`remaining_sessions`), keep "Fee" (admin-only), keep "Payment Status", keep "Status". Remove any references to 12/24/36 presets. Hide fee column from non-admin.
- [x] T028 [US2] Add i18n translations for package form in `frontend/src/i18n/en.json` and `frontend/src/i18n/vi.json` — add keys: `package.class`, `package.lessonKind`, `package.numberOfLessons`, `package.tuitionFee`, `package.assignPackage`, `package.resetAutoFill`, `package.notEnrolled`, `package.createKindOption`, `lessonKind.title`.

**Checkpoint**: Full package creation flow works — admin can assign flexible packages with class + lesson kind + auto-fill fee. Enrollment validation rejects non-enrolled students. Attendance deduction verified. No 12/24/36 presets remain.

---

## Phase 5: User Story 3 — Class & Lesson Kind Visible Across Package Views (Priority: P2)

**Goal**: Wherever a package is displayed (student profile, tuition list, parent portal, dashboard), both the class display ID and lesson kind label are visible.

**Independent Test**: Create packages with different lesson kinds linked to different classes → visit student profile → verify class display ID and lesson kind shown → visit tuition list → verify same. Parent portal shows class + kind (when portal is implemented).

**Depends on**: User Story 2 (packages must have class + lesson kind data)

### Implementation for User Story 3

- [x] T029 [US3] Update StudentDetail to show package class and lesson kind in `frontend/src/features/students/StudentDetail.jsx` — in the active package section, display `class_display_id` (with teacher/schedule tooltip using Ant Design `Tooltip`) and `lesson_kind_name` alongside remaining sessions and payment status. Fetch active package data including class + kind fields.
- [x] T030 [US3] Update dashboard service in `backend/app/services/dashboard_service.py` — if "students nearing package end" widget exists, update its query to include `class_display_id` and `lesson_kind_name` in the returned data by joining through Package → ClassSession → Teacher and Package → LessonKind.
- [x] T031 [P] [US3] Update dashboard frontend in `frontend/src/features/dashboard/DashboardPage.jsx` — if "nearing package end" widget renders package info, add class display ID and lesson kind label columns/fields.

**Checkpoint**: Class and lesson kind info visible on all package display surfaces. All user stories complete.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Student model cleanup, seed data, and final validation

- [x] T032 [P] Update Student forms to drop skill_level in `frontend/src/features/students/StudentForm.jsx` — remove the `skill_level` Select input field. Update `personality_notes` textarea placeholder to `"e.g., currently at intermediate level, struggles with sight-reading"` (en) / `"VD: hiện ở trình độ trung cấp, gặp khó khăn với đọc bản nhạc"` (vi) using i18n key `student.notesPlaceholder`.
- [x] T033 [P] Update StudentDetail to drop skill_level in `frontend/src/features/students/StudentDetail.jsx` — remove `skill_level` display row from the detail view.
- [x] T034 [P] Update StudentList to drop skill_level in `frontend/src/features/students/StudentList.jsx` — remove `skill_level` table column.
- [x] T035 [P] Update Students API to drop skill_level in `backend/app/api/students.py` — remove any references to `skill_level` in response building, filtering, or sorting logic.
- [x] T036 [P] Update Student CRUD to drop skill_level in `backend/app/crud/student.py` — remove `skill_level` from query filters, sort options, and create/update operations.
- [x] T037 [P] Add i18n key for student notes placeholder in `frontend/src/i18n/en.json` and `frontend/src/i18n/vi.json` — add `student.notesPlaceholder` key with the updated hint text.
- [x] T038 Update seed script in `backend/app/scripts/seed.py` (or equivalent) — add seeding of lesson kinds (Beginner, Elementary, Intermediate, Advanced) if not already seeded by migration. Update any class seed data to include `tuition_fee_per_lesson`. Remove any `skill_level` references from student seed data. Remove any `package_type` references from package seed data.
- [x] T039 Run quickstart.md validation — execute the 9-step smoke test from `specs/003-flexible-course-package/quickstart.md` end-to-end. Verify all 12 checklist items pass.

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies — can start immediately
- **Foundational (Phase 2)**: Depends on Phase 1 (models must exist before CRUD/schemas reference them)
- **User Story 1 (Phase 3)**: Depends on Phase 2 — classes API + frontend
- **User Story 2 (Phase 4)**: Depends on Phase 2 AND Phase 3 (package form needs class display IDs and fees)
- **User Story 3 (Phase 5)**: Depends on Phase 4 (needs packages with class + kind data)
- **Polish (Phase 6)**: Can start after Phase 2 for student cleanup tasks (T032–T037); T038–T039 depend on all phases

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) — No dependencies on other stories
- **User Story 2 (P1)**: Depends on User Story 1 — package form requires classes with display IDs and `tuition_fee_per_lesson`
- **User Story 3 (P2)**: Depends on User Story 2 — displays package data that includes class + lesson kind

### Within Each User Story

- Models/migration before CRUD
- CRUD/schemas before API endpoints
- API endpoints before frontend components
- Backend before frontend (frontend consumes API)

### Parallel Opportunities

- **Phase 1**: T002, T003, T004, T005 can all run in parallel (different model files)
- **Phase 2**: T006, T007, T008, T009, T010 can all run in parallel (different files). T011 depends on T006. T012 depends on T007.
- **Phase 3**: T015 and T016 can run in parallel (different API files). T018 and T019 are independent frontend components.
- **Phase 4**: T025 can run in parallel with T022–T024 (frontend vs backend)
- **Phase 6**: T032, T033, T034, T035, T036, T037 can all run in parallel (different files, same concern)

---

## Parallel Example: Phase 1 (Setup)

```bash
# All model updates can run in parallel (different files):
Task: "Create LessonKind model in backend/app/models/lesson_kind.py"
Task: "Update Package model in backend/app/models/package.py"
Task: "Update ClassSession model in backend/app/models/class_session.py"
Task: "Update Student model in backend/app/models/student.py"
```

## Parallel Example: Phase 2 (Foundational)

```bash
# CRUD and schema tasks across different files:
Task: "Create LessonKind CRUD in backend/app/crud/lesson_kind.py"
Task: "Create display ID utility in backend/app/crud/class_session.py"
Task: "Update Package schemas in backend/app/schemas/package.py"
Task: "Update ClassSession schemas in backend/app/schemas/class_session.py"
Task: "Update Student schemas in backend/app/schemas/student.py"
```

## Parallel Example: Phase 6 (Polish)

```bash
# All student skill_level cleanup tasks across different files:
Task: "Update StudentForm to drop skill_level in frontend/src/features/students/StudentForm.jsx"
Task: "Update StudentDetail to drop skill_level in frontend/src/features/students/StudentDetail.jsx"
Task: "Update StudentList to drop skill_level in frontend/src/features/students/StudentList.jsx"
Task: "Update Students API in backend/app/api/students.py"
Task: "Update Student CRUD in backend/app/crud/student.py"
```

---

## Implementation Strategy

### MVP First (User Stories 1 + 2)

1. Complete Phase 1: Setup (migration + models)
2. Complete Phase 2: Foundational (CRUD, schemas, utilities)
3. Complete Phase 3: User Story 1 — Classes tab
4. **STOP and VALIDATE**: Test Classes tab independently
5. Complete Phase 4: User Story 2 — Flexible package creation
6. **STOP and VALIDATE**: Test package creation, auto-fill, enrollment check
7. Deploy/demo if ready (MVP complete)

### Incremental Delivery

1. Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Classes catalog works
3. Add User Story 2 → Test independently → Package creation works (MVP!)
4. Add User Story 3 → Test independently → Cross-surface visibility
5. Polish → Student cleanup, seed data, final validation
6. Each story adds value without breaking previous stories

---

## Notes

- [P] tasks = different files, no dependencies
- [Story] label maps task to specific user story for traceability
- US2 depends on US1 (class display IDs and fees must exist for package form)
- US3 depends on US2 (package data must include class + kind)
- The `skill_level` removal (Phase 6) is independent of all user stories and can be parallelized
- Migration (T001) should be tested immediately after creation by running `alembic upgrade head`
- Commit after each task or logical group
- Stop at any checkpoint to validate story independently
