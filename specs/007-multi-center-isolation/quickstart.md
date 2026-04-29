# Quickstart: Multi-Center Data Isolation

**Date**: 2026-04-29 | **Branch**: `007-multi-center-isolation`

## What This Feature Does

Closes all remaining data isolation gaps in the multi-center (multi-tenant) system. After implementation, each center's data is completely invisible to other centers at every layer: database queries, API responses, and frontend routing.

## Key Changes

1. **Auth middleware** (`deps.py`): Checks center `is_active` on every API request
2. **Login flow** (`auth.py`): Blocks login for deactivated centers
3. **Class CRUD** (`class_session.py`): Adds center_id to delete, unenroll, and cross-entity enrollment validation
4. **Schedule service** (`schedule_service.py`): Scopes conflict detection to current center
5. **Frontend routing** (`ProtectedRoute.jsx`): Verified — already blocks superadmin correctly

## Testing Locally

```bash
# 1. Start backend
cd backend && uvicorn app.main:app --reload

# 2. Start frontend
cd frontend && npm run dev

# 3. Create two centers via superadmin
# Login as superadmin → /system/centers → Create Center A and Center B

# 4. Test isolation
# Login as Center A admin → create students, teachers, classes
# Login as Center B admin → verify none of Center A's data is visible
# Attempt API calls with Center A's resource IDs while logged in as Center B → expect 404
```

## Files Modified

| File | Change Type | Description |
|------|-------------|-------------|
| `backend/app/core/deps.py` | Modified | Add center is_active check in `get_current_user()` |
| `backend/app/api/auth.py` | Modified | Add center is_active check at login |
| `backend/app/api/classes.py` | Modified | Pass center_id to delete and unenroll |
| `backend/app/crud/class_session.py` | Modified | Add center_id to `delete_class_session()`, `unenroll_student()`, cross-center enrollment validation |
| `backend/app/services/schedule_service.py` | Modified | Add center_id filter to `check_scheduling_conflicts()` |
| `frontend/src/auth/ProtectedRoute.jsx` | Verified | Already handles superadmin redirect — no change needed |

## No Migration Needed

All database columns and indexes already exist from migration `013_multi_tenant_centers.py`.
