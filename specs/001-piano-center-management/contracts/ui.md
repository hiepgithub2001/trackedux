# UI Contracts: Piano Center Management System

**Phase**: 1 — Design & Contracts  
**Date**: 2026-04-27

---

## Pages & Routes

| Route | Page | Role | Description |
|-------|------|------|-------------|
| `/login` | Login | Public | Auth form (admin/staff/parent) |
| `/` | Dashboard | Admin, Staff | Operational overview |
| `/students` | Student List | Admin, Staff | Filterable student table |
| `/students/new` | Add Student | Admin, Staff | Student creation form |
| `/students/:id` | Student Detail | Admin, Staff | Full student profile with tabs |
| `/schedule` | Weekly Calendar | Admin, Staff | Weekly calendar view |
| `/classes/new` | Create Class | Admin | Class creation form |
| `/classes/:id` | Class Detail | Admin, Staff | Class info + enrolled students |
| `/attendance` | Attendance | Admin, Staff | Session attendance marking |
| `/attendance/:classId/:date` | Mark Attendance | Admin, Staff | Batch attendance form |
| `/teachers` | Teacher List | Admin | Teacher management |
| `/teachers/new` | Add Teacher | Admin | Teacher creation form |
| `/teachers/:id` | Teacher Detail | Admin | Teacher profile + availability |
| `/tuition` | Tuition Management | Admin | Package & payment overview |
| `/tuition/:studentId` | Student Tuition | Admin | Package detail + payment history |
| `/portal` | Parent Portal Home | Parent | Child list |
| `/portal/child/:id` | Child Detail | Parent | Schedule, attendance, notes |
| `/reports` | Monthly Reports | Admin | Charts and metrics (Phase 2) |

---

## Layout Structure

### Admin/Staff Layout
```
┌─────────────────────────────────────────────┐
│  Header: Logo | Navigation | Lang | User    │
├──────┬──────────────────────────────────────┤
│ Side │                                      │
│ Nav  │         Main Content Area            │
│      │                                      │
│  📊  │                                      │
│  👨‍🎓  │                                      │
│  📅  │                                      │
│  ✅  │                                      │
│  👨‍🏫  │                                      │
│  💰  │                                      │
├──────┴──────────────────────────────────────┤
│  Footer (mobile: bottom nav)                │
└─────────────────────────────────────────────┘
```

### Parent Portal Layout
```
┌─────────────────────────────────────────────┐
│  Header: Logo | Lang | User                 │
├─────────────────────────────────────────────┤
│                                             │
│          Main Content (no sidebar)          │
│                                             │
└─────────────────────────────────────────────┘
```

### Mobile Layout (< 768px)
- Sidebar collapses to hamburger menu
- Calendar switches to day view
- Tables switch to card layout
- Forms become full-width single-column

---

## Key Component Contracts

### StudentTable
- **Props**: `filters`, `sortBy`, `onStudentClick`
- **Columns**: Name, Nickname, Skill Level, Status (badge), Remaining Sessions, Enrolled Date
- **Features**: Search (unaccented), sort by columns, filter by status/skill level
- **Pagination**: Server-side, 20 per page

### WeeklyCalendar
- **Props**: `weekStart`, `teacherFilter`, `onSessionClick`
- **Display**: 7-day grid, time slots from 07:00-21:00
- **Session Cards**: Single base color for regular sessions; cards render the class `name`, teacher name, and student count
- **Makeup marker** (clarification 2026-04-27): when `is_makeup === true`, render an Ant Design `<Tag color="orange">Makeup</Tag>` (i18n key: `schedule.makeupBadge`) above the time range so makeup sessions are visually distinct from regular recurring sessions
- **Info shown**: Time range (`start_time` → `start_time + duration_minutes`), teacher name, student names, makeup badge when applicable
- **Interactions**: Click to view/edit, drag to reschedule (stretch goal)

### ClassForm (create / edit)
- **Props**: `mode` (`'create' | 'edit'`), `initialValues`, `onSubmit`
- **Fields**:
  - `name` — text input, required (replaces the previous "Class type" dropdown per clarification 2026-04-27)
  - `teacher_id` — searchable select
  - `day_of_week` — select (Mon–Sun)
  - `start_time` — time picker (15-min step)
  - `duration_minutes` — number input, default 60, minimum 1 (replaces the previous "End time" picker)
  - `student_ids` — multi-select with no upper bound (no "max capacity" enforcement)
  - `is_recurring` — toggle, default on
- **Submit**: Calls `POST /api/v1/classes` (or `PATCH` for edit). On `409` conflict, surfaces a toast listing the conflicting sessions.

### AttendanceBatchForm
- **Props**: `classSessionId`, `sessionDate`, `students`
- **Display**: Student list with radio buttons (Present/Absent/Absent with Notice)
- **Shows**: Current package remaining for each student
- **Submit**: Batch POST, shows remaining sessions after save

### PackageCard
- **Props**: `package`
- **Display**: Total/Remaining sessions, progress bar, payment status badge
- **Warning**: Red highlight when remaining ≤ 2, "Owing" badge when negative

### LanguageSwitcher
- **Props**: none (reads from context)
- **Display**: Toggle button "VI | EN"
- **Behavior**: Switches entire UI language, persists to localStorage + user profile

---

## i18n Key Namespaces

```
src/i18n/
├── en.json       # English translations
└── vi.json       # Vietnamese translations
```

**Top-level namespaces**:
- `common` — Shared labels (Save, Cancel, Delete, Search, etc.)
- `auth` — Login, logout, password
- `students` — Student management labels
- `teachers` — Teacher management labels
- `schedule` — Calendar and class labels
- `attendance` — Attendance labels and status
- `tuition` — Package and payment labels
- `dashboard` — Dashboard metric labels
- `portal` — Parent portal labels
- `notifications` — Notification messages
- `validation` — Error messages
