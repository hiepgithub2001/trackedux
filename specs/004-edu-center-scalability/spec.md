# Feature Specification: Multi-Tenant Edu-Center Scalability System

**Feature Branch**: `004-edu-center-scalability`  
**Created**: 2026-04-28  
**Status**: Draft  
**Input**: User description: "I want to create a scalability system where support center operates. 1. We have one account like admin system who adds edu-center with basic info like Center Name, Center Account, etc. 2. After that, the system will create a center with unique ID managed by admin system; admin system can see a list of centers they helped register, but the account of the center which is created by admin system cannot see that — it can see as current UI/UX."

---

## User Scenarios & Testing *(mandatory)*

### User Story 1 — System Admin Registers a New Edu-Center (Priority: P1)

A privileged "System Admin" user (the single top-level operator) opens a dedicated admin console and creates a new edu-center by providing the center's name and an email address for the center account. The system provisions a new isolated center record with a unique ID and generates login credentials for the center administrator. The System Admin can immediately see the newly created center in their center list.

**Why this priority**: This is the foundational capability — without it no center can exist in the system and no other story is meaningful.

**Independent Test**: Can be tested end-to-end by logging in as the System Admin, filling the "Add Edu-Center" form, and verifying the center appears in the System Admin's center list with a unique identifier. No other story needs to be built.

**Acceptance Scenarios**:

1. **Given** the System Admin is logged in, **When** they navigate to the Center Management page and submit the "Add Edu-Center" form with a valid Center Name and center email, **Then** the system creates a new center record with a globally unique center ID, generates credentials for the center account, and displays the new center in the System Admin's center list.
2. **Given** the System Admin has already registered a center with a given name, **When** they attempt to register a second center with the exact same name, **Then** the system rejects the submission with a clear error message indicating the name is already in use.
3. **Given** the System Admin submits the form with a missing Center Name or invalid email, **When** the form is submitted, **Then** the system prevents submission and highlights the invalid fields with descriptive messages.
4. **Given** the form is successfully submitted, **When** the System Admin views the center list, **Then** each center entry displays at minimum: Center Name, unique Center ID, registration date, and center account email.

---

### User Story 2 — Center Account Logs In and Sees Its Own Isolated View (Priority: P2)

A center administrator uses the credentials created during registration to log in. Once authenticated, they land on the same product UI/UX as the current application (students, classes, tuition, attendance, etc.) but scoped exclusively to their center's data. They cannot see other centers, the System Admin console, or any list of co-registered centers.

**Why this priority**: Tenant isolation is the security guarantee of the entire system. Without isolation, data leakage makes the product unsafe to operate with multiple clients.

**Independent Test**: Can be tested by creating one center, logging in as that center's account, and verifying (a) only that center's data is accessible and (b) no navigation to the System Admin console or other centers is available.

**Acceptance Scenarios**:

1. **Given** a center account was provisioned by the System Admin, **When** the center administrator logs in with their credentials, **Then** they land on the standard product dashboard scoped to their center only.
2. **Given** the center administrator is logged in, **When** they browse students, classes, tuition, or any feature, **Then** every record returned belongs exclusively to their center.
3. **Given** the center administrator is logged in, **When** they attempt to access any System Admin functionality (center list, center creation, other centers' data), **Then** the system denies access with an appropriate permission error — no data from other centers is leaked.
4. **Given** two centers exist with overlapping data (e.g., same student name), **When** each center administrator views their own data, **Then** each sees only their own records; neither can see the other center's records.

---

### User Story 3 — System Admin Views and Manages the Center List (Priority: P3)

After registering multiple centers, the System Admin can view the full list of centers, inspect basic details of each, and perform basic management operations such as deactivating a center.

**Why this priority**: Operational visibility is needed once more than one center exists, but the core provisioning (P1) and isolation (P2) must work first.

**Independent Test**: Can be tested by registering two centers and then verifying the System Admin list shows both with correct metadata. Deactivation can be tested separately.

**Acceptance Scenarios**:

1. **Given** the System Admin has registered three centers, **When** they open the Center Management page, **Then** they see all three centers listed with Center Name, Center ID, registration date, and status (active/inactive).
2. **Given** the System Admin selects a center and triggers deactivation, **When** the action is confirmed, **Then** the center's status changes to "inactive" and the center account can no longer log in.
3. **Given** the center list contains many entries, **When** the System Admin uses the search or filter, **Then** the list narrows to matching centers within one second.

---

### Edge Cases

- What happens when the System Admin attempts to re-activate an already inactive center?
- What happens if a center account's email is used for a personal account elsewhere in the system?
- How does the system handle a center being deactivated while a center admin is currently logged in — are their active sessions immediately invalidated?
- What happens if the System Admin accidentally registers the same center twice (same name, different emails)?
- How are center IDs assigned if two centers are created simultaneously (race condition)?
- What happens to a center's data if the center is deactivated — is data preserved or deleted?

---

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST support a single privileged "System Admin" account that can create and manage edu-center records.
- **FR-002**: System MUST allow the System Admin to register a new edu-center by providing at minimum: Center Name (required, unique), and a center administrator email address (required, valid format).
- **FR-003**: System MUST assign a globally unique, immutable Center ID to every newly created edu-center at the time of registration.
- **FR-004**: System MUST automatically provision a center administrator account (with login credentials) when a new edu-center is registered.
- **FR-005**: System MUST display to the System Admin a list of all edu-centers they have registered, including Center Name, Center ID, registration date, and account status (active/inactive).
- **FR-006**: System MUST enforce strict data isolation: a center administrator account MUST only be able to read and write data belonging to their own center.
- **FR-007**: Center administrator accounts MUST NOT have access to the System Admin console, the center list, or any data about other centers.
- **FR-008**: Center administrator accounts MUST see the same product UI/UX as the current application (students, classes, tuition, attendance) scoped to their center.
- **FR-009**: System MUST allow the System Admin to deactivate a center account, preventing future logins for that center.
- **FR-010**: System MUST reject edu-center registration if the Center Name is already in use.
- **FR-011**: System MUST reject edu-center registration if any required field is missing or invalid (email format, name length).

### Key Entities

- **System Admin**: The single top-level operator account. Has access to the Center Management console. Does not manage day-to-day center data (students, classes, etc.) directly.
- **Edu-Center**: A tenant record representing one educational center. Attributes: unique Center ID (system-generated), Center Name (admin-provided, unique), registration date, status (active/inactive), associated center administrator account.
- **Center Administrator Account**: A login credential set (email + password) provisioned automatically when an edu-center is registered. Scoped to one center. Uses the same product UI as today.

---

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The System Admin can register a new edu-center and have it operational (with login credentials available) in under 2 minutes from form submission.
- **SC-002**: A center administrator account, once logged in, can access no data outside its own center — verified by attempting cross-center data access and receiving zero results or a permission denial.
- **SC-003**: The System Admin's center list loads and displays up to 50 registered centers within 2 seconds.
- **SC-004**: 100% of API responses involving center data correctly enforce tenant boundary — no cross-tenant data leak occurs in any tested scenario.
- **SC-005**: Center accounts see no System Admin UI elements — the product navigation and features match the current application experience exactly.
- **SC-006**: Deactivating a center account prevents all subsequent login attempts by that center within 5 seconds of the deactivation action.

---

## Assumptions

- The existing application is a single-tenant system (one center) and this feature transitions it to multi-tenant. The existing tenant's data will be migrated to become "Center 1" or equivalent during implementation.
- The System Admin account is a special role, not a regular center administrator. It is pre-seeded in the database rather than self-registerable.
- Center administrator accounts share the same authentication system as today (email + password); no external SSO is required for this phase.
- A center administrator's initial password is either auto-generated and displayed once to the System Admin, or sent to the center email — the delivery mechanism will be confirmed during planning.
- Mobile/PWA access by center administrators uses the same scoped view as the desktop browser.
- The System Admin does not manage students, classes, or tuition directly — those operations remain the responsibility of each center's own administrator.
- Data from other centers is never visible to a center admin even in aggregate/anonymized form.
- There is no self-service registration for edu-centers — all registrations go through the System Admin.
