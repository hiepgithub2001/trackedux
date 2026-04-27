# Quickstart: Multi-Tenant Edu-Center Scalability System

**Phase**: 1 | **Date**: 2026-04-28 | **Plan**: [plan.md](./plan.md)

---

## Prerequisites

```bash
# 1. Start backend
cd backend && uvicorn app.main:app --reload

# 2. Run migrations (includes 013_multi_tenant_centers)
cd backend && alembic upgrade head

# 3. Start frontend
cd frontend && npm run dev
```

---

## Smoke Flow

### A. Superadmin — Register a Center

1. Open `http://localhost:5173/login`
2. Log in as **superadmin** (credentials seeded by migration: `superadmin` / `SuperAdmin@2026!`)
3. Verify redirect to `/system/centers` (NOT the standard dashboard)
4. Verify no student/class/tuition nav links exist
5. The center list shows one entry: **CTR-001 — Legacy Center** (migrated from existing data)

### B. Superadmin — Create a New Center

6. Click **"Add New Center"**
7. Fill the form:
   - Center Name: `Nhạc Viện Demo`
   - Admin Full Name: `Trần Văn Bình`
   - Admin Username: `demo_admin`
   - Admin Email: `demo@nhacvien.vn`
8. Submit → verify success modal appears with:
   - Center Code: `CTR-002`
   - Admin Username: `demo_admin`
   - A temporary password displayed (e.g., `Xk9mQ3nR7pLw`)
9. Copy the password. Click "Done".
10. Verify `Nhạc Viện Demo / CTR-002` now appears in the center list with **Active** status.

### C. Center Admin — Isolated Login

11. Log OUT as superadmin
12. Log in as `demo_admin` with the temporary password copied in step 9
13. Verify redirect to `/` (standard dashboard — the existing app UI)
14. Verify the standard app navigation is present (Students, Classes, Tuition, etc.)
15. Verify NO link to `/system` or "Center Management" exists in the nav

### D. Tenant Isolation Verification

16. As `demo_admin`, navigate to **Students** → verify the list is empty (new center, no students yet)
17. Create one student: "Nguyễn Thị Test"
18. Log out. Log in as the original `admin` account (CTR-001 Legacy Center)
19. Navigate to **Students** → verify "Nguyễn Thị Test" does NOT appear (data isolated to CTR-002)
20. Log back in as superadmin → navigate to `/system/centers` → verify both centers visible

### E. Deactivation

21. As superadmin, click **"Deactivate"** on `Nhạc Viện Demo`
22. Confirm the modal. Verify status badge changes to **Inactive**.
23. Log out. Attempt to log in as `demo_admin` → verify login fails with "Account is inactive" error.
24. Log back in as superadmin → **Reactivate** the center
25. Log in as `demo_admin` → verify login succeeds and student data is intact
