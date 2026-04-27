# API Contracts: Multi-Tenant Edu-Center Scalability System

**Phase**: 1 | **Date**: 2026-04-28 | **Plan**: [plan.md](../plan.md)

All endpoints are under `/api/v1/`. Auth header: `Authorization: Bearer <JWT>`.

---

## New: Center Management Endpoints (Superadmin Only)

### `POST /api/v1/system/centers`

Create a new edu-center and provision its administrator account.

**Authorization**: `superadmin` role required (HTTP 403 otherwise)

**Request body**:
```json
{
  "name": "Nhạc Viện Bình Thạnh",
  "admin_email": "admin@binhThanh.edu.vn",
  "admin_full_name": "Nguyễn Thị Mai",
  "admin_username": "binhThanh_admin"
}
```

| Field | Type | Required | Validation |
|-------|------|----------|------------|
| `name` | string | ✅ | 1–200 chars; must be unique (case-insensitive) |
| `admin_email` | string | ✅ | Valid email format; must be unique across all users |
| `admin_full_name` | string | ✅ | 1–200 chars |
| `admin_username` | string | ✅ | 3–100 chars, alphanumeric + underscore; must be unique |

**Response `201 Created`**:
```json
{
  "center": {
    "id": "uuid",
    "name": "Nhạc Viện Bình Thạnh",
    "code": "CTR-002",
    "is_active": true,
    "created_at": "2026-04-28T06:00:00Z"
  },
  "admin_credentials": {
    "username": "binhThanh_admin",
    "temporary_password": "Xk9mQ3nR7pLw",
    "note": "Store this password securely. It will not be shown again."
  }
}
```

**Error responses**:
- `400` — missing/invalid fields
- `409` — center name already taken OR admin email/username already in use

---

### `GET /api/v1/system/centers`

List all registered edu-centers.

**Authorization**: `superadmin` role required

**Query params**:
- `?search=<string>` — case-insensitive substring filter on `name` or `code`
- `?is_active=true|false` — filter by status (default: all)

**Response `200 OK`**:
```json
[
  {
    "id": "uuid",
    "name": "Nhạc Viện Bình Thạnh",
    "code": "CTR-002",
    "is_active": true,
    "admin_email": "admin@binhThanh.edu.vn",
    "admin_username": "binhThanh_admin",
    "registered_at": "2026-04-28T06:00:00Z"
  }
]
```

---

### `GET /api/v1/system/centers/{center_id}`

Get a single center's details.

**Authorization**: `superadmin` role required

**Response `200 OK`**: Same shape as one item in the list response above.

**Error**: `404` if center not found.

---

### `PATCH /api/v1/system/centers/{center_id}`

Update a center's name or active status.

**Authorization**: `superadmin` role required

**Request body** (all fields optional):
```json
{
  "name": "New Center Name",
  "is_active": false
}
```

**Behavior**:
- When `is_active` changes to `false`: also sets `is_active = false` on all `User` records with `center_id = <center_id>` (immediate effect via DB-per-request auth check — see Research Decision 6).
- When `is_active` changes to `true`: re-activates the center's admin user(s).

**Response `200 OK`**: Updated center object.

**Error**: `404` if not found; `409` if new name conflicts.

---

## Modified: Authentication (`/api/v1/auth/login`)

**Change**: The `UserResponse` returned in the login response now includes `center_id` and `center_code` fields (null for superadmin).

**Response addition**:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "user": {
    "id": "uuid",
    "username": "...",
    "role": "admin",
    "center_id": "uuid-of-center",
    "center_code": "CTR-001",
    "full_name": "...",
    "language": "vi",
    "is_active": true
  }
}
```

---

## Modified: All Tenant-Scoped Endpoints

The following endpoints are **unchanged in their request/response shape** but now enforce tenant isolation invisibly:

| Endpoint group | Isolation enforcement |
|---------------|----------------------|
| `GET/POST /api/v1/students` | Filtered by `center_id` of authenticated user |
| `GET/POST /api/v1/teachers` | Filtered by `center_id` of authenticated user |
| `GET/POST /api/v1/classes` | Filtered by `center_id` of authenticated user |
| `GET/POST /api/v1/packages` | Filtered by `center_id` of authenticated user |
| `GET/POST /api/v1/attendance` | Filtered by `center_id` of authenticated user |
| `GET /api/v1/lesson-kinds` | Filtered by `center_id` of authenticated user |
| `GET /api/v1/dashboard` | Filtered by `center_id` of authenticated user |

**No new request parameters are added** to these endpoints. The `center_id` is derived from the authenticated user's JWT payload / DB record — callers cannot override it.

---

## Security Rules

1. Any request from a `superadmin` user to a tenant-scoped endpoint (students, classes, etc.) returns `403` — superadmin does NOT have access to any center's operational data.
2. Any request from a non-`superadmin` user to `/api/v1/system/centers` returns `403`.
3. All `center_id` filters are applied in the CRUD layer, never in the API handler directly, to prevent accidental omission.
