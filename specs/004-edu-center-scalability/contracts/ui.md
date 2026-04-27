# UI Contracts: Multi-Tenant Edu-Center Scalability System

**Phase**: 1 | **Date**: 2026-04-28 | **Plan**: [plan.md](../plan.md)

---

## New Surface: Superadmin Console (`/system`)

A completely separate route subtree, accessible ONLY when `user.role === 'superadmin'`. Center admin users are redirected away from any `/system` path.

### `/system` — Center List Page

**Route**: `/system/centers`  
**Default redirect**: `/system` → `/system/centers`

**Layout**: Standalone layout (no standard app sidebar/nav). Displays "TrackedUX System Admin" branding. No student/class/tuition nav links visible.

**Content**:
- Page heading: "Edu-Center Management"
- "Add New Center" primary button (top-right)
- Table columns:
  | Column | Sortable | Notes |
  |--------|----------|-------|
  | Center Code | ✅ | e.g., `CTR-001` |
  | Center Name | ✅ | |
  | Admin Username | — | |
  | Admin Email | — | |
  | Registered Date | ✅ | |
  | Status | — | Active / Inactive badge |
  | Actions | — | "Deactivate" / "Reactivate" button |
- Search input: filters table by name or code (client-side for ≤50 centers; server-side search param used for larger lists)
- Status filter: "All / Active / Inactive" toggle

**Deactivate flow**:
1. Click "Deactivate" → confirmation modal: "Are you sure you want to deactivate [Center Name]? Their admin account will be locked immediately."
2. Confirm → PATCH `/api/v1/system/centers/{id}` with `{is_active: false}`
3. Status badge updates to "Inactive"; button changes to "Reactivate"

---

### `/system/centers/new` — Add Edu-Center Form

**Trigger**: "Add New Center" button on center list page

**Form fields**:
| Field | Input type | Validation |
|-------|-----------|------------|
| Center Name | Text input | Required, 1–200 chars |
| Admin Full Name | Text input | Required, 1–200 chars |
| Admin Username | Text input | Required, 3–100 chars, alphanumeric + underscore |
| Admin Email | Email input | Required, valid email format |

**Submit behavior**:
1. POST `/api/v1/system/centers`
2. On success: show "Center Created" modal containing:
   - Center Code (e.g., `CTR-002`)
   - Admin Username
   - **Temporary Password** (shown in a monospaced box with "Copy" button)
   - ⚠️ Warning: "This password will not be shown again. Please copy it now."
   - "Done" button closes modal and navigates back to center list
3. On `409` error: inline field error highlighting (name conflict or username/email taken)
4. On other errors: toast notification

---

## Modified Surface: Login Page (`/login`)

**No visual changes.** The login page remains identical. The routing logic after login changes:

- If `user.role === 'superadmin'` → redirect to `/system/centers`
- If `user.role === 'admin'` or `'staff'` → redirect to `/` (existing dashboard, center-scoped)
- If `user.role === 'parent'` → redirect to `/portal` (unchanged)

---

## Modified Surface: Existing App (Center Admin View)

**No visual changes for center admin users.** The existing sidebar, navigation, and all feature pages remain identical. The only invisible change is that all data fetched from the API is silently scoped to the authenticated user's center.

**Access guard**: Any attempt by a center user to navigate to `/system/*` redirects to `/` with an "Access Denied" toast.

---

## Routing Changes

```diff
+ { path: '/system', element: <SuperadminRoute />, children: [
+   { index: true, element: <Navigate to="/system/centers" /> },
+   { path: 'centers', element: <CenterListPage /> },
+   { path: 'centers/new', element: <CenterFormPage /> },
+ ]}
```

`SuperadminRoute` is a new protected route component that redirects to `/` if `user.role !== 'superadmin'`.

---

## Component Changes

| Component | Change |
|-----------|--------|
| `AuthContext` | Add `center_id`, `center_code` to user state (from login response) |
| `ProtectedRoute` | Extend to accept `roles={['superadmin']}` guard |
| `Layout` | No change — superadmin uses a separate layout |
| All feature pages | No change — data scoping is transparent via API |
