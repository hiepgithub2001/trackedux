# Research: Multi-Tenant Edu-Center Scalability System

**Phase**: 0 | **Date**: 2026-04-28 | **Plan**: [plan.md](./plan.md)

All unknowns from the Technical Context are resolved below.

---

## Decision 1 — Multi-Tenancy Strategy: Shared Database, Shared Schema (Row-Level Tenancy)

**Decision**: Use shared database, shared schema (single PostgreSQL database) with a `center_id` foreign key column added to every tenant-scoped table. All queries for tenant-scoped resources MUST include a `WHERE center_id = <current_user.center_id>` filter applied at the service/CRUD layer — never optional, never overridable by the caller.

**Rationale**:
- The existing codebase uses a single PostgreSQL instance with no database-per-tenant infrastructure (no connection pool per tenant, no database switcher).
- The scale (tens of centers, each with ~50 classes and ~100 packages) does not justify the operational overhead of schema-per-tenant or database-per-tenant.
- Row-level tenancy is the simplest extension of the existing pattern: add one UUID FK column to each relevant table, filter in CRUD functions, and validate in API middleware.
- Supabase Row Level Security (RLS) was considered but rejected: the project owns its own DB filtering logic, and RLS adds a Postgres-specific abstraction that complicates the existing SQLAlchemy async pattern.

**Alternatives rejected**:
- **Schema-per-tenant** (PostgreSQL `search_path`): Requires dynamic connection string manipulation and Alembic multi-schema migrations — significant complexity for no benefit at this scale.
- **Database-per-tenant**: Operational overhead (N connection pools), not feasible in a single-server deployment.

---

## Decision 2 — System Admin Role: New `superadmin` Role vs. Elevated `admin`

**Decision**: Introduce a new `superadmin` role value in the `users.role` column (alongside existing `admin`, `staff`, `parent`). The `superadmin` role is NOT bound to any center (`center_id = NULL`). A single `superadmin` account is pre-seeded in the database (via Alembic seed or a management CLI command). Regular `admin` users are center-scoped and manage day-to-day operations of their own center.

**Rationale**:
- The existing `role` column is a `String(20)` — adding `superadmin` requires no schema change beyond the new role value.
- Separating `superadmin` from `admin` preserves the current RBAC semantics: center `admin` users continue to operate as today.
- Existing `require_role(...)` dependency factory can be extended with `require_role('superadmin')` guards on system-admin-only endpoints.
- A `center_id IS NULL` check provides a secondary safety net: a `superadmin` user can never accidentally filter against a center.

**Alternatives rejected**:
- **Separate `superadmins` table**: Additional join on every auth middleware call, unnecessary complexity when the `users` table + a new role value suffices.
- **Promoting one center `admin` to have cross-center visibility**: Violates the spec's strict "center account cannot see other centers" requirement and creates confusion.

---

## Decision 3 — Center Entity: New `centers` Table

**Decision**: Add a new `centers` table with columns: `id` (UUID PK), `name` (String 200, NOT NULL, UNIQUE), `code` (String 20, computed short code for display, NOT NULL, UNIQUE), `registered_by_id` (UUID FK → `users.id`, nullable, the superadmin who created it), `is_active` (Boolean, NOT NULL, default `true`), `created_at`, `updated_at`.

The `center_id` FK is added to these existing tables: `users`, `students`, `teachers`, `class_sessions`, `class_enrollments`, `packages`, `payment_records`, `attendance`, `renewal_reminders`, `lesson_kinds`, `student_status_history`.

Tables NOT receiving `center_id`: `centers` itself (it IS a center), and any purely cross-cutting tables (none currently exist).

**Rationale**:
- A first-class `Center` entity is needed as the anchor FK for all tenant-scoped data.
- The `code` field provides the human-readable "Center ID" shown in the System Admin UI (e.g., `CTR-001`). It is auto-generated at creation time from a sequential counter, not user-supplied.
- `registered_by_id` allows audit tracing of which superadmin created each center without a separate audit log table.

**Alternatives rejected**:
- **Embedding center metadata into the `users` table**: Conflates identity with organization; makes the center list query awkward (scan users where role = 'admin', one per center).
- **Using a UUID as the human-readable Center ID directly**: UUIDs are unwieldy for display; a short `code` field is more user-friendly.

---

## Decision 4 — Existing Data Migration: Assign to a Default "Legacy" Center

**Decision**: The Alembic migration (`013_multi_tenant_centers.py`) will:
1. Create the `centers` table.
2. Insert one row: the "Legacy Center" (the existing single tenant) with a well-known code `CTR-001`.
3. Add `center_id` column (nullable initially) to all tenant-scoped tables.
4. `UPDATE` all existing rows to `center_id = <legacy-center-id>`.
5. Apply `NOT NULL` constraint to `center_id` on all affected tables.
6. Add FK constraints with `ON DELETE RESTRICT`.
7. Add `center_id` to the `users` table (nullable for `superadmin`, NOT NULL for all other roles).

**Rationale**:
- There is production data to preserve (unlike spec 003 which explicitly sanctioned data loss).
- Migrating all existing rows to a "Legacy Center" is the only safe path that keeps the existing single-tenant center operational without any data re-entry.
- Making `center_id` nullable only during the migration window (then constraining to NOT NULL) follows standard zero-downtime migration practice.

**Alternatives rejected**:
- **Drop and recreate tables**: Rejected because this feature has live data that must be preserved.
- **Leaving `center_id` nullable permanently**: Creates a footgun — any missed filter silently leaks all legacy data.

---

## Decision 5 — Center Admin Credential Delivery

**Decision**: When the System Admin creates a new center, the system **auto-generates a temporary password** (random 12-character alphanumeric string), creates the center admin `User` record, and **returns the temporary password in the API response (shown once)**. The System Admin is responsible for securely transmitting the credentials to the center. The center admin is **not** forced to change the password on first login in Phase 1 (this is a Phase 2 enhancement).

**Rationale**:
- Email delivery requires an SMTP integration that does not exist in the current codebase. Adding it is out of scope for this feature.
- "Show once" is a well-established pattern (used by AWS IAM, GitHub PATs, etc.) that works without external services.
- The superadmin UI will display the generated credentials in a modal immediately after center creation, with a "copy to clipboard" button and a warning that it will not be shown again.

**Alternatives rejected**:
- **Email delivery**: Requires SMTP/SendGrid integration — out of scope.
- **Fixed default password**: Security risk; predictable credentials if code leaks.
- **Force password change on first login**: Deferred to Phase 2 to keep this spec focused.

---

## Decision 6 — Session Invalidation on Center Deactivation

**Decision**: Deactivation is enforced at the **authentication middleware level** (existing `get_current_user` dependency). The middleware already checks `user.is_active`. Deactivating a center will set `is_active = false` on the center's admin `User` record(s). On the next request by the deactivated user, the middleware rejects the token with HTTP 401. No active session termination list or token blocklist is needed.

**Rationale**:
- The existing `get_current_user` dependency already reads `user.is_active` from the database on every request (no in-memory user cache). Flipping `is_active = false` is immediately effective.
- Token TTL is 30 days, but the DB check makes it functionally synchronous — the user is rejected on their next API call (within milliseconds of deactivation, in practice).
- A token blocklist would add Redis infrastructure that doesn't currently exist in the project.

**Alternatives rejected**:
- **Token blocklist (Redis)**: Introduces new infrastructure dependency; unnecessary given the DB-per-request auth check pattern already in place.
- **Short token TTL**: Would require changing the existing access token TTL from 30 days, breaking existing sessions.

**Output**: All NEEDS CLARIFICATION resolved. Proceeding to Phase 1.
