# Feature Specification: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Feature Branch**: `003-flexible-course-package`
**Created**: 2026-04-27
**Status**: Draft
**Input**: User description: "1. Admin create and manage kinds of lesson (beginner, advanced, ...), these all should be customized by Admin. 2. For course package creation, I think we should make it more flexible. It means we just fill out student, number of lessons, kinds of lesson (beginner, advanced, ... which customized by Admin), and tuition fee instead of fixing 12, 24, 36, ..."

## Clarifications

### Session 2026-04-27

- Q: Should the existing free-text `skill_level` field on Student be unified with the new admin-managed Lesson Kind list, kept as an independent free-text field, or removed? → A: Remove `skill_level` as a structured field on Student. Skill-level context (if needed) is captured informally inside the existing free-text student notes field; the notes input shows a placeholder hint such as "e.g., currently at intermediate level, struggles with sight-reading". Lesson Kind is referenced by Course Package only — not by Student.
- Q: How should pre-existing packages be assigned a Lesson Kind during migration? → A: No migration. Existing course packages (and their dependent records that block schema changes) are dropped and the table is rebuilt under the new flexible model. The system is treated as having no production package data worth preserving for this feature.
- Q: Should admin be able to edit `number_of_lessons`, `lesson_kind`, or `tuition_fee` on an already-active package after creation? → A: No. Editing an active package's lessons/kind/fee is out of scope for this feature. Corrections are made by deactivating the package and assigning a new one (consistent with spec 001's "one active package per student" replacement semantics).
- Q: When creating a course package, can the admin choose an existing lesson kind AND/OR create a new lesson kind on the fly? → A: Both. The lesson kind input on the package form behaves as a typeahead/combobox: as the admin types (e.g., "Be…"), matching lesson kinds from the dedicated Lesson Kinds table are suggested. The admin can either pick a suggestion or, if no match exists, submit the typed name to create a new lesson kind inline; the new kind is persisted to the same Lesson Kinds table and immediately linked to the package being created.
- Q: How does the system manage the lifecycle of lesson kinds (rename, deactivate, reactivate, delete) and what happens when a typed name matches a deactivated kind? → A: There is **no lifecycle management** of lesson kinds. The Lesson Kinds table is a passive, append-only vocabulary of words: there is no admin UI to rename, deactivate, reactivate, or delete a lesson kind, and lesson kinds have no active/inactive state. Kinds are added to the table only by the inline-create flow in the package creation form (or by an initial seeded set at deployment).
- Q: Should the system have a "Classes" listing tab, and how should classes be uniquely identified for human use? → A: Yes — add a "Classes" navigation tab listing all classes at the center. Each class displays a human-readable unique ID derived from `teacher first name + weekday (3-letter) + time (HHMM)`, with a sequential disambiguator suffix `-{N}` when multiple classes would otherwise share the same combination (e.g., "Jane-Mon-1730" and "Jane-Mon-1730-2"). The display ID is derived from the class's current values; if any of those values change, the displayed ID updates accordingly. The internal stable identifier (UUID, from spec 001) remains the durable foreign-key target — references between entities use UUIDs, never display IDs.
- Q: Should classes carry their own price? → A: Yes — each class has a `tuition_fee_per_lesson` field (positive integer in VND, ceiling 100,000,000 VND for typo protection). It is set when the class is created or edited via the existing class CRUD plus the new Classes tab. Admin sees and edits the fee; staff and parents do not see it (consistent with the existing role-based access model).
- Q: Should the course package reference a class? → A: Yes — every course package MUST reference exactly one class (by the class's stable identifier). The package creation form gains a "class" input alongside student, number of lessons, lesson kind, and tuition fee. Packages cannot be saved without a class.
- Q: How is the package's `tuition_fee` determined when a class is selected on the package form? → A: Auto-populate the package fee from `class.tuition_fee_per_lesson × number_of_lessons` whenever the admin picks a class and enters a lesson count, but allow the admin to override the auto-filled value before saving. The stored `tuition_fee` on the package is whatever the admin confirmed (the auto-filled default or the manually overridden value). Auto-fill recomputes whenever class or lesson count changes, *unless* the admin has manually edited the fee field — in which case the manual value is preserved (a "reset to auto-fill" affordance is offered for convenience).
- Q: When the admin assigns a course package for a student to a class, what should the system do about the student's enrollment in that class? → A: Validate, don't auto-enroll. The package save MUST be rejected if the chosen student is not already enrolled in the chosen class (per the spec 001 `Class.enrolled_students` relationship). The admin must enroll the student first via the existing class-management flow from spec 001, then return to the package form. There is no auto-enroll side-effect on package save.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Admin Views the Classes Catalog (Priority: P1)

An admin opens a new "Classes" tab in the main navigation and sees a list of all classes at the center. Each row shows the class's human-readable unique display ID (derived from teacher first name + weekday + time, with a numeric suffix when multiple classes share the same combination), the teacher, the weekday and time, the class duration (from spec 001), the number of currently enrolled students, and the tuition fee per lesson (in VND, admin-only column). Admin can sort/filter the list, click a class row to open its detail/edit view, edit `tuition_fee_per_lesson`, and create a new class from this tab.

**Why this priority**: The Classes tab is the foundation that the flexible package flow (Story 2) depends on — package creation requires picking an existing class. The tab also gives admin a clear catalog of what the center offers so they can reason about pricing and capacity.

**Independent Test**: Can be fully tested by logging in as admin, opening the Classes tab, verifying every class appears with an auto-generated human-readable display ID and a `tuition_fee_per_lesson`, editing a fee, creating a new class, and verifying that the disambiguator suffix appears when two classes share the same (teacher, weekday, time).

**Acceptance Scenarios**:

1. **Given** the admin is logged in, **When** they click the "Classes" tab, **Then** they see a list of all classes with columns for display ID, teacher, weekday, time, duration, enrolled count, and `tuition_fee_per_lesson`.
2. **Given** two classes are both taught by Jane on Monday at 17:30, **When** the admin views the Classes tab, **Then** the two rows display IDs "Jane-Mon-1730" and "Jane-Mon-1730-2" (the suffix "-2" is assigned by creation order at the moment of collision).
3. **Given** the admin opens the "Create class" form, **When** they save without entering a `tuition_fee_per_lesson`, **Then** the system rejects the save and indicates the field is required (positive integer VND, within configured ceiling).
4. **Given** the admin edits a class's `tuition_fee_per_lesson` from 200,000 to 250,000 VND, **When** they save, **Then** the new fee is reflected in the Classes tab and is the new default for any subsequently created package against this class. Existing packages already saved against this class keep their previously stored `tuition_fee`.
5. **Given** a staff (non-admin) user views the Classes tab, **When** the page renders, **Then** they see all class rows but the `tuition_fee_per_lesson` column is hidden (per role-based access from spec 001).
6. **Given** a class's teacher is renamed (e.g., "Jane" → "Janet") in the system, **When** the admin returns to the Classes tab, **Then** the display ID for that class reflects the new teacher name (the display ID is derived from current values, not frozen at creation).
7. **Given** a class's weekday or start time is changed, **When** the change is saved, **Then** the display ID is recomputed and disambiguator suffixes are reassigned among any new collisions; references from existing packages still resolve correctly because they use the stable UUID.

---

### User Story 2 - Admin Creates a Flexible Course Package (Priority: P1)

When assigning a course package to a student, the admin sees a simplified form with five inputs: student (selected from existing students), class (typeahead by class display ID, with teacher/schedule shown for context), number of lessons (any positive integer the admin types in), lesson kind (typeahead combobox — pick a suggestion or type a brand-new name to add it to the vocabulary inline), and tuition fee (in VND, auto-filled from `class.tuition_fee_per_lesson × number_of_lessons` but editable). There are no preset buttons for "12 / 24 / 36"; the admin types the count they want each time. On save, the package is created with the entered values; if the admin added a new lesson kind inline, that kind is also persisted to the Lesson Kinds vocabulary atomically with the package. The package then behaves identically to existing packages for attendance deduction, payment tracking, and renewal reminders.

**Why this priority**: This is the headline change the user requested. It removes a hard-coded constraint that no longer matches how the center sells packages, anchors each package to a specific class (so attendance tracking, scheduling, and revenue analysis line up correctly), and uses the class's per-lesson rate as the default price while still letting admin negotiate per-package adjustments.

**Independent Test**: Can be fully tested by creating a package for a student against a specific class with an arbitrary lesson count (e.g., 8, 18, 50), verifying auto-fill of the tuition fee, verifying override behavior, verifying inline create of a new lesson kind, and verifying the package displays correctly with class info attached.

**Acceptance Scenarios**:

1. **Given** the admin opens the "Assign package" form, **When** the form renders, **Then** they see exactly five required inputs (student, class, number of lessons, lesson kind, tuition fee) and no preset buttons for 12/24/36.
2. **Given** the admin picks class "Jane-Mon-1730" (whose `tuition_fee_per_lesson` is 200,000 VND) and enters number of lessons = 18, **When** the lesson count field loses focus, **Then** the tuition fee field auto-populates with 3,600,000 VND (200,000 × 18) and remains editable.
3. **Given** the admin then manually changes the tuition fee from 3,600,000 to 3,200,000 VND (negotiated discount) and **subsequently** changes the number of lessons from 18 to 20, **When** the lesson count blurs, **Then** the tuition fee stays at the manually-entered 3,200,000 (auto-fill does not overwrite a manual edit). A "reset to auto-fill" affordance MAY be offered.
4. **Given** the admin selects a class (auto-fill = 4,000,000 VND) and saves without touching the fee, **When** the package is saved, **Then** the stored tuition fee is exactly the auto-fill value (4,000,000 VND).
5. **Given** the admin types a brand-new lesson kind name (e.g., "Jazz Foundations") that does not match any existing kind, **When** they confirm and save the package, **Then** "Jazz Foundations" is added to the Lesson Kinds vocabulary and the package is linked to it (both writes succeed atomically; either-or-neither persistence).
6. **Given** the admin enters number of lessons = 0 (or negative or non-integer), **When** they attempt to save, **Then** the system rejects with a clear validation error and does not create a package.
7. **Given** the admin enters tuition fee = 0 or negative, **When** they attempt to save, **Then** the system rejects with a clear validation error.
8. **Given** the admin leaves the class input empty, **When** they attempt to save, **Then** the system rejects and indicates a class is required.
9. **Given** the admin selects student=Bob and class="Jane-Mon-1730" but Bob is not currently enrolled in that class, **When** they attempt to save, **Then** the system rejects the save with a clear message ("Bob is not enrolled in Jane-Mon-1730 — enroll the student in the class first") and offers a quick link to the class enrollment flow. No package is created.
10. **Given** Bob is then enrolled in "Jane-Mon-1730" via the existing class-management flow, **When** the admin returns to the package form and saves with the same inputs, **Then** the package is created successfully.
11. **Given** a package with 18 lessons exists for Alice in class "Jane-Mon-1730", **When** Alice is marked present at a session of that class, **Then** her remaining session count drops to 17 (existing attendance behavior preserved).
12. **Given** the admin views the tuition management screen, **When** packages are listed, **Then** each row shows the class display ID and the lesson kind alongside the existing fields (student, total/remaining sessions, price, payment status).

---

### User Story 3 - Class & Lesson Kind Visible Across Package Views (Priority: P2)

Wherever a course package is displayed — student profile, tuition management list, package detail view, parent portal package info, dashboard "students nearing package end" — both the linked class display ID (with teacher and schedule) and the lesson kind associated with the package are shown. This gives admin, staff, and parents immediate context: parents see which class they paid for; admin sees the routing; staff sees the schedule for attendance.

**Why this priority**: The data is captured by Stories 1 and 2; surfacing it consistently is a small but meaningful UX improvement that turns stored fields into useful information. Lower priority because the feature is functional without it.

**Independent Test**: Can be fully tested by creating packages of different lesson kinds linked to different classes for several students, then visiting each surface (student profile, tuition list, parent portal) and confirming both the class display ID and the lesson kind label appear next to package info.

**Acceptance Scenarios**:

1. **Given** a student has an active "Advanced" package linked to class "Jane-Mon-1730", **When** an admin opens the student's profile, **Then** the active package section displays both "Jane-Mon-1730" (with teacher/schedule tooltip) and "Advanced" as the lesson kind.
2. **Given** a parent is logged into the parent portal, **When** they view their child's package info, **Then** they see the class display ID (with teacher name and schedule) and the lesson kind alongside remaining sessions and payment status.
3. **Given** a class's teacher was renamed after a package was created, **When** the package is shown, **Then** the displayed class identifier reflects the **current** teacher name (because the display ID is always derived from current values, never stored on the package).

---

### Edge Cases

- **Class display ID — collision after teacher rename or reschedule**: If renaming/rescheduling causes a previously unique display ID to now collide with another class, both rows are shown with disambiguator suffixes; references from existing packages still resolve through the stable UUID, so no data is lost. The disambiguator number is assigned by creation order at the moment the collision arises.
- **Class display ID — special characters in teacher name**: Names with diacritics, spaces, or non-ASCII characters are kept as-is in the display ID; the format is human-readable, not URL-safe. (URL/slug forms are out of scope here.)
- **Editing `tuition_fee_per_lesson` on a class with active packages**: Existing packages keep their stored `tuition_fee` value (no retroactive change to historical packages). Only **future** packages created against that class use the new rate as the auto-fill default.
- **Deleting a class with active packages**: Hard delete is blocked when any active package references the class; admin must deactivate the packages first (using the existing one-active-package replacement flow). Inactive/historical packages also block deletion to preserve audit history; admin may "archive" the class (out of scope for this feature) or leave it as-is.
- **Class without students enrolled yet**: A class can be created and shown in the Classes tab with zero enrolled students. To assign a package against this class, the admin must first enroll a student in the class via the existing class-enrollment flow from spec 001 — package creation does not auto-enroll.
- **Package save with student not enrolled in chosen class**: Save is rejected; admin is shown the offending pair (student, class display ID) and a quick link to the class enrollment flow. After enrolling, the admin returns to the package form to save.
- **Student is unenrolled from a class while a package referencing that class is active**: This case is governed by the existing class-management flow from spec 001 (out of scope here); the active package is not automatically deactivated by un-enrollment.
- **Auto-fill — manual edit then class change**: If the admin manually edited the fee and later changes the selected class, the manually-entered value is preserved; auto-fill does not overwrite manual edits. A "reset to auto-fill" button MAY be provided.
- **Auto-fill — manual edit then lesson count change**: Same as above — manual fee is preserved across lesson count changes once the admin has touched the fee field.
- **Zero lesson kinds in the vocabulary**: When the table starts empty, the package form's typeahead returns no suggestions; the admin types a name and creates the first lesson kind inline. There is no setup screen to visit first.
- **Inline create matches an existing kind (case-insensitive)**: Existing kind is reused (no duplicate created); typeahead surface highlights the match before confirmation.
- **Whitespace-only or empty lesson kind / class / student / fee / lesson count**: Each rejected with a clear validation error.
- **Whitespace handling on inline create of lesson kind**: Trim leading/trailing whitespace; collapse internal whitespace; case-insensitive uniqueness compares the normalized form.
- **Typo-induced new lesson kinds**: A typo creates a permanent vocabulary entry (no rename/delete in this feature). Admins are expected to confirm carefully.
- **Very large lesson counts**: A reasonable upper bound is enforced (default 500 lessons per package); values above are rejected.
- **Decimal or non-numeric input for lesson count**: Rejected; only positive whole numbers accepted.
- **Currency overflow / unrealistic price**: Tuition fee values above 1,000,000,000 VND (package) or 100,000,000 VND (class per-lesson) are rejected.
- **Concurrent inline create of the same new lesson kind name**: Storage layer converges to a single row; second attempt sees the first one and reuses it (case-insensitive match).
- **Concurrent class creation with same (teacher, weekday, time)**: Storage layer assigns disambiguator suffixes deterministically by creation order; both rows persist with distinct display IDs.
- **Correcting a typo on an active package**: Active packages are not editable. Admin deactivates the bad package and assigns a new one (existing replacement flow from spec 001).

## Requirements *(mandatory)*

### Functional Requirements

**Class Catalog & Identification**

- **FR-001**: System MUST provide a "Classes" tab in the main navigation that lists all classes with columns for display ID, teacher, weekday, time, duration, enrolled student count, and (admin-only) `tuition_fee_per_lesson`. The list MUST be sortable and filterable by at least teacher and weekday.
- **FR-002**: System MUST compute a human-readable display ID for every class in the form `{TeacherFirstName}-{Weekday3}-{HHMM}[-{N}]` where `Weekday3` is one of {Mon, Tue, Wed, Thu, Fri, Sat, Sun} and `HHMM` is the start time in 24-hour `HHMM` form (e.g., "1730"). The optional `-{N}` suffix MUST be appended when multiple classes would otherwise produce the same base ID; `N` MUST be assigned in creation order starting at 2 (the first/oldest class with that base ID has no suffix).
- **FR-003**: The display ID MUST be derived from the class's current values; if the teacher's name, weekday, or time changes, the display ID MUST recompute accordingly. Foreign-key references between Class and other entities MUST use the class's stable internal identifier (UUID), not the display ID, so external references survive renames/reschedules.
- **FR-004**: System MUST add a `tuition_fee_per_lesson` field on Class (positive integer in VND, configured ceiling 100,000,000 VND for typo protection, required on save). Zero, negative, decimal, and non-numeric values MUST be rejected with a clear message.
- **FR-005**: System MUST hide `tuition_fee_per_lesson` from staff and parents in line with existing role-based access rules; only admin sees the value and can edit it.
- **FR-006**: System MUST block hard-deletion of a class when any course package (active or historical) references it. Admin MUST first deactivate referencing packages (or archive them via a future feature) before the class can be deleted.

**Lesson Kinds Vocabulary (no management UI)**

- **FR-007**: System MUST maintain a separate, dedicated Lesson Kinds table (persistent vocabulary) that stores distinct lesson kind names referenced by course packages.
- **FR-008**: System MUST NOT provide any UI to rename, deactivate, reactivate, or delete a lesson kind in this feature. The vocabulary is append-only by design; lesson kinds have no active/inactive state.
- **FR-009**: System MUST allow new lesson kinds to be added to the vocabulary in exactly two ways: (a) via an initial seeded set at first deployment, and (b) inline through the package creation form (FR-014b).
- **FR-010**: Lesson kind names MUST be unique within the vocabulary, enforced case-insensitively after trimming and whitespace normalization.

**Flexible Course Package**

- **FR-011**: System MUST present a single course package creation form whose required inputs are: student, class, number of lessons, lesson kind, and tuition fee (VND).
- **FR-012**: System MUST NOT offer fixed presets such as 12 / 24 / 36 in the package creation form. The number of lessons MUST be entered as a free-form positive integer.
- **FR-013**: System MUST validate the number of lessons as a positive integer within a reasonable upper bound (default ceiling: 500). Zero, negative, decimal, and non-numeric values MUST be rejected with a clear message.
- **FR-014**: System MUST require a lesson kind on package creation; saving without a lesson kind (neither selected nor typed) MUST be rejected.
- **FR-014a**: The lesson kind input on the package creation form MUST behave as a typeahead/combobox: as the admin types, it MUST show suggestions from the Lesson Kinds vocabulary that match the typed substring (case-insensitive).
- **FR-014b**: When the admin types a name that does not match any existing lesson kind, the system MUST allow the admin to add it inline; the new kind MUST be persisted to the Lesson Kinds vocabulary atomically with the package save (either both writes succeed or neither).
- **FR-014c**: When the typed name case-insensitively matches an existing lesson kind, the system MUST reuse that existing kind (by stable identifier) and MUST NOT create a duplicate row.
- **FR-015**: System MUST require a class on package creation (referenced by the class's stable UUID, not its display ID); saving without a class MUST be rejected.
- **FR-015a**: The class input on the package creation form MUST behave as a typeahead/combobox keyed by class display ID, also showing teacher name and schedule for disambiguation in the suggestion list.
- **FR-015b**: System MUST reject the package save if the chosen student is not currently enrolled in the chosen class (per the `Class.enrolled_students` relationship from spec 001). The error message MUST identify both the student and the class display ID and MUST offer a quick navigation affordance to the existing class-enrollment flow. The package form MUST NOT auto-enroll the student as a side-effect of saving.
- **FR-016**: System MUST auto-populate the package's `tuition_fee` field as `class.tuition_fee_per_lesson × number_of_lessons` whenever the admin selects a class and a positive lesson count, **provided the admin has not manually edited the fee field**. Once the admin manually edits the fee, the auto-fill MUST NOT overwrite the manual value on subsequent class or lesson-count changes; a "reset to auto-fill" affordance MAY be provided to restore default behavior.
- **FR-017**: The stored `tuition_fee` on the package MUST be whatever value the admin confirms on save (auto-filled default or manual override), independent of the class's `tuition_fee_per_lesson` at any later time. Editing a class's `tuition_fee_per_lesson` later MUST NOT modify any historical package's stored fee.
- **FR-018**: System MUST validate `tuition_fee` as a positive integer in VND within a reasonable upper bound (default ceiling: 1,000,000,000 VND). Zero, negative, and non-numeric values MUST be rejected with a clear message.
- **FR-019**: System MUST associate every newly created package with exactly one class (by UUID) and exactly one lesson kind (by stable identifier).
- **FR-020**: System MUST preserve the existing package behaviors defined in spec 001 for attendance deduction (one session per "present" mark in the linked class), renewal reminders, payment status tracking, ability to go negative on remaining sessions, and replacement of the prior active package on assignment.
- **FR-021**: System MUST display the class display ID (and the lesson kind label) on every surface that shows package information: student profile (active package section), tuition management list, package detail view, dashboard "students nearing package end" if applicable, and parent portal package info.
- **FR-022**: System MUST drop and rebuild the course package data store as part of rolling out this feature; no migration of pre-existing packages is performed. (Acceptable because the feature is being introduced before any production rollout that would require preserving package history.)
- **FR-023**: System MUST treat newly created packages as immutable in their core fields (`student`, `class`, `number_of_lessons`, `lesson_kind`, `tuition_fee`); admin corrections are made by deactivating the package and creating a replacement.
- **FR-024**: System MUST hide `tuition_fee` from staff and parents in line with existing role-based access rules; only admin sees the price.
- **FR-025**: Package creation (and therefore inline lesson kind creation) MUST remain restricted to admin role only, consistent with the role-based access model from spec 001.

### Key Entities *(include if data involves)*

- **Class** (existing entity from spec 001, modified): A scheduled lesson slot taught by an assigned teacher at a specific weekday/time/duration with enrolled students. New attributes added by this feature: `tuition_fee_per_lesson` (positive integer VND, required). New computed/displayed attribute: `display_id` (string, derived from teacher first name + weekday + time + optional disambiguator suffix). The internal stable identifier (UUID) from spec 001 remains the foreign-key target for all references.
- **Lesson Kind** (new): A passive, append-only vocabulary entry representing a name used to classify a course package (e.g., "Beginner", "Intermediate", "Advanced", "Jazz Foundations"). Attributes: stable identifier, unique name (case-insensitive, trimmed/normalized), timestamps. No active/inactive state, no description, no admin lifecycle controls. Referenced by Course Package only.
- **Course Package** (existing entity, restructured): A purchased bundle of sessions assigned to a student against a specific class. Restructured by this feature: the fixed `package_type` enum ('12'/'24'/'36'/'custom') is removed in favor of a free `number_of_lessons` integer; new required FK to Class (by UUID); new required FK to Lesson Kind (by stable identifier). The course package data store is rebuilt with no data migration. All other attributes (student link, total/remaining sessions, price in VND, payment status, active flag, started/expired dates, reminder status) are preserved in the new schema.
- **Student** (existing entity, modified): The free-text `skill_level` field is removed. Skill-level context, when relevant, is captured informally inside the existing free-text student notes field; the notes input shows a placeholder hint suggesting that admins/staff may include phrases like "currently at intermediate level" if useful. Student does not reference Lesson Kind.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Admin can navigate to the Classes tab and locate any specific class by display ID in under 10 seconds.
- **SC-002**: Admin can assign a course package to a student in under 60 seconds using only the five-input form (student, class, number of lessons, lesson kind, tuition fee), including the case where they add a brand-new lesson kind inline. The auto-filled tuition fee MUST appear within 200 ms of the admin entering both class and lesson count (so they don't have to wait to confirm).
- **SC-003**: 100% of newly created course packages reference a valid class (by UUID) and a valid lesson kind at the moment of creation.
- **SC-004**: Wherever a package is displayed (student profile, tuition list, parent portal, package detail), both the class display ID and the lesson kind label are visible without the user needing extra clicks.
- **SC-005**: Zero hard-coded references to "12", "24", or "36" remain in the package creation flow after this feature ships.
- **SC-006**: After rollout, the application contains no structured `skill_level` field on Student; any prior UI that exposed `skill_level` is replaced by the existing free-text notes field with an updated placeholder hint.
- **SC-007**: After rollout, the application exposes no UI to rename, deactivate, reactivate, or delete a lesson kind. The Lesson Kinds vocabulary grows only via inline-create or initial seed.
- **SC-008**: Two concurrent inline-creates of the same brand-new lesson kind name converge to a single row (no duplicate names, even case-insensitive duplicates).
- **SC-009**: Two concurrent class creations with the same (teacher, weekday, time) converge to two rows with deterministically-assigned disambiguator suffixes (no duplicate display IDs).
- **SC-010**: Editing a class's `tuition_fee_per_lesson` MUST NOT change the stored `tuition_fee` on any historical package; verified by creating a package, editing the class fee, and confirming the package's stored fee is unchanged.
- **SC-011**: 100% of saved course packages reference a (student, class) pair where the student is enrolled in the class. There is no auto-enroll path that bypasses the existing class-management flow; verified by attempting to save a package for a non-enrolled student and confirming the save is rejected.

## Assumptions

- **No data migration**: The course package data store is dropped and rebuilt under the new flexible schema. Existing packages, payments, attendance records that reference packages, and renewal reminders that depend on packages are not preserved. Acceptable because the feature is being introduced before any production rollout that would require keeping historical package data.
- **Class data preserved**: Existing Class records from spec 001 are preserved across this feature; the only schema change to Class is the addition of `tuition_fee_per_lesson` (NULL initially for legacy rows, then admin sets the value before the class can be referenced by a new package). This avoids dropping the Class table.
- **Class display ID format**: `{TeacherFirstName}-{Weekday3}-{HHMM}[-{N}]` with English weekday abbreviations. Bilingual rendering of the weekday is out of scope here.
- **Class display ID is derived, not stored**: Display IDs are computed from current teacher name, weekday, and time at every render. References between entities use UUIDs; display IDs are for human use only.
- **Disambiguator stability**: The `-{N}` suffix is assigned by creation order at the moment of collision. If a class is later rescheduled away from a colliding slot, its base ID may once again be unique; the disambiguator is dropped on the recomputed display. Numbering for remaining colliders may reflow accordingly.
- **Seeded lesson kinds at first deployment**: The system seeds a starter list of lesson kinds (Beginner, Elementary, Intermediate, Advanced) so the package form's typeahead is useful on day one. Once seeded, no UI manages them; further entries grow organically from inline-create.
- **Lesson kind names are immutable once created**: There is no rename in this feature. A typo (e.g., "Begnner") becomes a permanent vocabulary entry until a future cleanup feature is built.
- **No lifecycle states on lesson kinds**: Lesson kinds have no `is_active`/`deactivated_at` field. Every entry in the table is always selectable as a suggestion.
- **Student `skill_level` removed**: The structured `skill_level` field on Student is removed. Any UI that previously displayed or filtered by `skill_level` is replaced by surfacing the existing free-text student notes field, with a placeholder hint encouraging admins/staff to include skill-level context when useful.
- **Active packages are immutable**: After save, the admin cannot edit `student`, `class`, `number_of_lessons`, `lesson_kind`, or `tuition_fee` on an active package. Corrections are made by deactivating the package and assigning a new one.
- **Auto-fill semantics**: Tuition-fee auto-fill applies only when the admin has not manually edited the fee field; manual edits are preserved across class/lesson-count changes. A "reset to auto-fill" affordance MAY be provided.
- **Enrollment is a precondition, not a side-effect**: The student must be enrolled in the chosen class via the existing spec 001 class-management flow **before** a package can be assigned. The package form validates this and rejects the save otherwise; it does not auto-enroll. This keeps a single, auditable path for enrollment changes and avoids invisible side-effects from the package form.
- **Reasonable input ceilings**: Lessons per package capped at 500; package tuition fee capped at 1,000,000,000 VND; class tuition_fee_per_lesson capped at 100,000,000 VND. These are typo-protection ceilings, not business limits, and are configurable later if needed.
- **Role-based access**: Class management, package creation, and inline lesson-kind creation are admin-only. Staff and parents are read-only consumers of the class display ID and lesson kind label where it appears (and only where their existing visibility allows). Per-lesson and total tuition fees remain hidden from staff/parents per the existing rules from spec 001.
- **Currency**: VND only, integer (no decimals), consistent with the existing tuition implementation.
- **One active package per student**: This invariant from spec 001 still holds; assigning a new flexible package deactivates the prior active package.
- **Localization**: Lesson kind names and class display IDs are entered/displayed as a single string each. Bilingual rendering is out of scope for this feature.
- **Dependency on spec 001**: This feature builds on the Course Package, Class, Student, and role infrastructure delivered in spec 001 (`001-piano-center-management`), and supersedes spec 001's fixed-package-type design.
