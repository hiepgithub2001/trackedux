# Research: Multi-Center Data Isolation

**Date**: 2026-04-29 | **Branch**: `007-multi-center-isolation`

## Research Summary

This feature is a hardening exercise — the multi-tenant infrastructure already exists. Research focused on auditing every code path that touches center-scoped data to identify isolation gaps.

## Decision Log

### D1: Center `is_active` Check Location

**Decision**: Check center `is_active` in `get_current_user()` dependency (auth middleware), not just at login.
**Rationale**: JWT tokens remain valid after center deactivation. Checking at the auth dependency layer means every API call is gated without modifying individual endpoints. This is the standard pattern for stateless JWT systems.
**Alternatives considered**:
- Token blacklisting: Adds infrastructure complexity (Redis/DB table for revoked tokens). Rejected — disproportionate for the deactivation frequency (~never).
- Per-endpoint check: Error-prone, easy to forget on new endpoints. Rejected.

### D2: Cross-Center Access Response Code

**Decision**: Return 404 Not Found for cross-center resource access.
**Rationale**: Prevents resource enumeration attacks. If Center A's admin gets a 403 for Center B's student ID, they learn the ID is valid. 404 reveals nothing.
**Alternatives considered**:
- 403 Forbidden: More informative but leaks resource existence. Rejected per spec clarification.

### D3: Cross-Entity Center Validation Strategy

**Decision**: Validate center_id match at the CRUD layer (not service or API layer).
**Rationale**: The CRUD layer is the last checkpoint before database writes. Validating here ensures no code path can bypass the check, even if called from multiple services. The validation is a simple comparison (`student.center_id == center_id`), not a separate DB query.
**Alternatives considered**:
- Database constraint (trigger): Would catch violations but with cryptic error messages. Rejected — application-layer validation provides user-friendly errors.
- API-layer validation: Would require duplicate validation if CRUD is called from multiple API endpoints. Rejected.

### D4: Schedule Conflict Center Scoping

**Decision**: Add `center_id` parameter to `check_scheduling_conflicts()` and filter the base query.
**Rationale**: Currently queries all active class sessions across all centers on a given day. With multiple centers, Teacher A at Center X and Teacher B at Center Y could have the "same" teacher_id collision (they won't since IDs are UUIDs, but student scheduling would cross centers). More importantly, the query returns more rows than necessary.
**Alternatives considered**:
- Rely on teacher/student center_id FK: Would technically prevent false positives via FK, but wastes query time scanning irrelevant centers. Rejected.

### D5: Frontend Superadmin Routing

**Decision**: The existing `ProtectedRoute` already redirects superadmin to `/system/centers`. No code change needed — only E2E test verification.
**Rationale**: `ProtectedRoute` checks `roles` and redirects superadmin to `/system/centers`. `SuperadminRoute` blocks non-superadmin from system pages. The routing is already correct.
**Alternatives considered**:
- Adding explicit superadmin blocking in Layout: Unnecessary since ProtectedRoute handles it before Layout renders. Rejected.

## No Unresolved Items

All NEEDS CLARIFICATION items from the spec were resolved during `/speckit-clarify`. No further research needed.
