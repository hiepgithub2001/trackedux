# Feature Specification: Student & Parent Info Restructure

**Feature Branch**: `002-student-parent-info-restructure`  
**Created**: 2026-04-27  
**Status**: Draft  
**Input**: User description: "Re-organize student's info: collapse contact info panel instead of separate tab, store contact data as student metadata"

## Clarifications

### Session 2026-04-27

- Q: What should the embedded contact JSON field be named, and should it support adult/self-paying students? → A: Field renamed from `parents_infor` to `contact`. Name field is nullable. Includes phone, email, and other contact fields. Supports both parent/guardian contacts and self-paying adult students.
- Q: Should the `contact` JSON include a `relationship` field to indicate who the contact person is relative to the student? → A: Yes — add an optional `relationship` field (free-text, e.g., "parent", "guardian", "self", "other").

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View and Edit Contact Info Within Student Form (Priority: P1)

An admin or staff member opens a student's record to view or update contact information. Instead of navigating to a separate tab, they see a collapsible "Contact Information" section directly within the student form. They can expand it to view details, make edits, and save everything in one submission.

**Why this priority**: This is the core UX change requested. Eliminating the tab navigation reduces clicks and keeps all student-related data in one cohesive form, directly addressing the primary complaint.

**Independent Test**: Open any student record, confirm a collapsible contact section exists in the form, expand it, edit a field, save, and verify the data persists.

**Acceptance Scenarios**:

1. **Given** a staff member is on the student detail/edit page, **When** they view the page, **Then** a collapsed "Contact Information" section is visible without navigating to another tab.
2. **Given** the contact section is collapsed, **When** the user clicks the section header, **Then** the section expands to reveal all contact fields inline.
3. **Given** the contact section is expanded, **When** the user clicks the section header again, **Then** the section collapses, hiding the fields.
4. **Given** a staff member fills in contact info and clicks Save, **When** the form is submitted, **Then** both student data and contact data are saved together successfully.

---

### User Story 2 - Add a New Student with Contact Info in One Form (Priority: P2)

A staff member creates a new student record. The student creation form includes the collapsible contact section so all information can be entered in a single workflow without switching tabs.

**Why this priority**: The add-student workflow should mirror the edit workflow for consistency. Eliminating the tab during creation reduces confusion and data-entry errors.

**Independent Test**: Navigate to the add-student page, expand the contact section, fill in fields, submit, and confirm the new student record contains all contact info.

**Acceptance Scenarios**:

1. **Given** a staff member is on the new student form, **When** they open the page, **Then** the contact section is present and collapsible within the same form.
2. **Given** a staff member enters student details and expands the contact section to add contact info, **When** they submit the form, **Then** a single student record is created containing both student and contact data.
3. **Given** a staff member submits the form without expanding the contact section, **When** the form is saved, **Then** the student record is created with contact fields left empty (contact info is optional).
4. **Given** an adult student who pays their own tuition, **When** a staff member creates or edits the student record, **Then** the contact section can be filled with the student's own phone/email without requiring a parent name.

---

### User Story 3 - System Stores Contact Info as Student Metadata (Priority: P3)

Contact information is stored as part of the student's own record rather than in a separate linked table. This means querying a student record returns all associated contact info without requiring a separate lookup.

**Why this priority**: This is a data-layer change that enables the UX simplification. It is testable independently by verifying the data structure returned when fetching a student record.

**Independent Test**: Fetch a student record via the system's data layer and confirm contact fields are embedded in the student record, not in a separate relational table requiring a join.

**Acceptance Scenarios**:

1. **Given** a student record exists with contact info, **When** the student record is retrieved, **Then** contact information is accessible as fields within the student record (no separate parent table lookup required).
2. **Given** existing student records with parent data in a separate table, **When** the migration is applied, **Then** all parent data is moved into the corresponding student record's `contact` field without data loss.
3. **Given** a student with no contact info on file, **When** the record is retrieved, **Then** the contact field is null or empty within the student record.

---

### Edge Cases

- What happens when a student record has existing parent data stored in the old separate table — it is migrated automatically as part of deployment.
- How does the collapsible section behave if contact fields contain validation errors on submit? — The section stays expanded and errors are shown inline.
- What happens if a user partially fills out contact fields and navigates away — partial data is lost (no draft persistence); the form resets on reload.
- What if a student has no parent/guardian (e.g., adult self-paying student) — the name field is optional, so the contact section can be completed with phone/email only.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The student detail/edit page MUST display a collapsible "Contact Information" section inline, replacing any existing separate tab for parent/guardian data.
- **FR-002**: The student creation form MUST include the same collapsible contact section so both student and contact info can be entered in one workflow.
- **FR-003**: The collapsible section MUST default to a collapsed state when the form loads.
- **FR-004**: Users MUST be able to toggle the contact section open and closed by clicking the section header.
- **FR-005**: All contact fields (name, relationship, phone, secondary phone, email, address, Zalo ID, notes) MUST be available within the collapsible section.
- **FR-006**: Saving the student form MUST persist both student data and contact data in a single operation.
- **FR-007**: Contact information MUST be stored as a `contact` JSON field within the student record, not in a separate relational table.
- **FR-008**: The system MUST migrate any existing parent data from the separate table into the student record's `contact` field without data loss.
- **FR-009**: All contact fields MUST be optional — submitting a student form with an empty or partially filled contact section MUST be allowed. The contact name field specifically MUST allow null to support adult self-paying students.
- **FR-010**: If contact fields contain invalid data, the form MUST display validation errors inline within the collapsible section and keep the section expanded so errors are visible.
- **FR-011**: The contact section MUST include an email field in addition to phone number(s), address, Zalo ID, and notes.

### Key Entities

- **Student**: Core record representing an enrolled student. Now includes contact information as an embedded `contact` JSON field rather than a foreign key to a separate parent record.
- **Contact Metadata** (`contact` JSON field within Student): Covers both parent/guardian contacts and self-paying adult students. Fields: name (nullable), relationship (nullable, e.g., "parent", "guardian", "self", "other"), phone, email, secondary phone, address, Zalo ID, notes. All fields optional.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Staff can view and edit contact information without leaving the student detail page — measured by zero tab navigations required for contact data access.
- **SC-002**: The student form (create and edit) loads with the contact section present in under 2 seconds on standard connections.
- **SC-003**: 100% of existing parent records are migrated into student contact metadata with no data loss, verified by record count comparison before and after migration.
- **SC-004**: Form submission saves both student and contact data in a single action — staff complete the full student record (including contact info) in fewer steps than the previous tab-based flow.
- **SC-005**: Contact info fields are accessible within the student record without an additional lookup — retrieval of a student record returns contact fields in one operation.
- **SC-006**: Adult student records can be saved with a null contact name and valid phone or email — zero validation errors for name-absent contact submissions.

## Assumptions

- The existing parent data (in the separate table) maps 1-to-1 with students — each student has at most one parent/guardian record migrated into the `contact` field.
- Contact fields are a superset of the current parent table fields, with email added as a new field.
- The separate parent tab's removal is a breaking UX change and no backwards-compatible tab fallback is needed.
- All staff users who can view/edit student records will have access to the new collapsible contact section — no additional permission changes are required.
- The migration from the separate parent table to student contact metadata is a one-time, non-reversible operation applied as part of this feature's deployment.
- The `parents` table is retained (not dropped) because it contains user account linkage for parent logins — this feature only removes the FK from `students` to `parents`.
