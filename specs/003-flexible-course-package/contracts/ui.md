# UI Contracts: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Feature**: 003-flexible-course-package
**Date**: 2026-04-27
**Spec**: [spec.md](./spec.md) | **Plan**: [plan.md](./plan.md)

---

## 1. Classes Tab (NEW)

**Location**: Main navigation, between "Schedule" and "Attendance" tabs.
**Route**: `/classes`
**Component**: `frontend/src/features/classes/ClassesPage.jsx`
**Access**: Admin + Staff (admin sees fee column; staff does not)

### Navigation

- New nav item: icon `AppstoreOutlined` (or similar), label "Classes" / "Lớp học" (vi)
- Position: after Schedule, before Attendance

### Table Columns

| Column | Field | Sortable | Filterable | Admin Only | Notes |
|--------|-------|----------|------------|------------|-------|
| Display ID | `display_id` | No | No | No | Computed, format `Jane-Mon-1730[-N]` |
| Teacher | `teacher_name` | Yes | Yes (dropdown) | No | |
| Weekday | `day_of_week` | Yes | Yes (dropdown) | No | Display as "Mon"–"Sun" |
| Time | `start_time` | Yes | No | No | HH:MM format |
| Duration | `duration_minutes` | No | No | No | Display as "60 min" |
| Enrolled | `enrolled_count` | Yes | No | No | Integer count |
| Fee/Lesson | `tuition_fee_per_lesson` | Yes | No | **Yes** | VND formatted with thousand separators |

### Actions

| Action | Trigger | Auth | Description |
|--------|---------|------|-------------|
| View detail | Click row | Any | Navigate to `/classes/{id}` |
| Create class | "Create Class" button (top-right) | Admin | Navigate to `/classes/new` (reuse existing `ClassForm` with fee field) |

### Empty State

"No classes found. Create a class to get started."

---

## 2. Class Create/Edit Form (MODIFIED)

**Component**: `frontend/src/features/schedule/ClassForm.jsx` (existing, modified)
**Access**: Admin only

### New Field

| Field | Component | Props | Validation | Notes |
|-------|-----------|-------|------------|-------|
| Fee per Lesson | `InputNumber` (Ant Design) | `min={1}`, `max={100000000}`, `formatter={vndFormatter}`, `parser={vndParser}`, `addonAfter="VND"` | Required, positive integer | Admin-only. Placeholder: "200,000" |

### Field Order (updated)

1. Teacher (existing select)
2. Class Name (existing text input)
3. Day of Week (existing select)
4. Start Time (existing time picker)
5. Duration (existing number input)
6. **Fee per Lesson** (NEW — InputNumber with VND formatting)
7. Students (existing multi-select)

### ID Attributes

| Element | ID |
|---------|-----|
| Fee input | `class-form-tuition-fee-per-lesson` |

---

## 3. Class Detail (MODIFIED)

**Component**: `frontend/src/features/schedule/ClassDetail.jsx` (existing, modified)
**Access**: Any authenticated; fee visible to admin only

### New Display Fields

| Field | Visibility | Format |
|-------|-----------|--------|
| Display ID | All | Bold header, e.g. "Jane-Mon-1730" |
| Fee per Lesson | Admin only | "200,000 VND" with thousand separators |

---

## 4. Package Creation Form (RESTRUCTURED)

**Component**: `frontend/src/features/tuition/TuitionPage.jsx` → new `PackageForm` sub-component
**Access**: Admin only
**Trigger**: "Assign Package" button on Tuition page

### Form Layout

Five inputs in a modal or drawer:

| # | Field | Component | Props / Behavior | Validation |
|---|-------|-----------|-----------------|------------|
| 1 | Student | `Select` (Ant Design) | Search by name, shows student name + status | Required |
| 2 | Class | `AutoComplete` (Ant Design) | Typeahead by display ID; each option shows display ID + teacher + schedule. Filters from `/classes` endpoint. | Required. Must exist. |
| 3 | Number of Lessons | `InputNumber` | `min={1}`, `max={500}`, `precision={0}` | Required, positive integer |
| 4 | Lesson Kind | `AutoComplete` (Ant Design) | Typeahead from `/lesson-kinds?search=`. If no match, admin can submit the typed name to create inline. Shows "Create new: {typed}" option when no exact match. | Required, 1–100 chars |
| 5 | Tuition Fee | `InputNumber` | VND formatting, `min={1}`, `max={1000000000}`, `addonAfter="VND"` | Required, positive integer |

### Auto-fill Behavior

```
When class AND number_of_lessons are both set:
  IF isManualFeeEdit == false:
    tuitionFee = class.tuition_fee_per_lesson × numberOfLessons
  ELSE:
    keep current manual value

When admin types in tuition fee field:
  Set isManualFeeEdit = true

"Reset to auto-fill" button (optional):
  Set isManualFeeEdit = false → triggers recompute
```

### Enrollment Validation (client-side pre-check)

Before submitting:
- Check if `student_id` is in `class.enrolled_students`.
- If not, show inline warning: "**{student_name}** is not enrolled in **{class_display_id}**. [Enroll student →]" with a link to the class enrollment flow.
- The server also validates this on save (422 error).

### Error States

| Condition | Message |
|-----------|---------|
| Student not enrolled in class | "Alice is not enrolled in Jane-Mon-1730. Enroll the student first." + link to class |
| Number of lessons = 0 or negative | "Number of lessons must be a positive integer." |
| Tuition fee = 0 or negative | "Tuition fee must be a positive amount." |
| No class selected | "Please select a class." |
| No lesson kind entered | "Please enter or select a lesson kind." |

### ID Attributes

| Element | ID |
|---------|-----|
| Student select | `package-form-student` |
| Class autocomplete | `package-form-class` |
| Number of lessons | `package-form-lesson-count` |
| Lesson kind autocomplete | `package-form-lesson-kind` |
| Tuition fee input | `package-form-tuition-fee` |
| Reset auto-fill button | `package-form-reset-fee` |
| Submit button | `package-form-submit` |

---

## 5. Tuition List (MODIFIED)

**Component**: `frontend/src/features/tuition/TuitionPage.jsx` (existing, modified)
**Access**: Any authenticated; fee/price columns admin-only

### Updated Table Columns

| Column | Field | Admin Only | Notes |
|--------|-------|------------|-------|
| Student | `student_name` | No | |
| Class | `class_display_id` | No | **NEW** — shows human-readable class ID |
| Lesson Kind | `lesson_kind_name` | No | **NEW** — shows lesson kind label |
| Lessons | `number_of_lessons` | No | **RENAMED** from "Package Type" |
| Remaining | `remaining_sessions` | No | |
| Tuition Fee | `price` | **Yes** | VND formatted |
| Payment Status | `payment_status` | No | Badge with color coding |
| Status | `is_active` | No | Active/Inactive tag |

### Dropped Columns

| Column | Reason |
|--------|--------|
| Package Type | Replaced by free-form "Lessons" count |

---

## 6. Student Forms & Detail (MODIFIED)

### StudentForm (create/edit)

**Drop**: `skill_level` field (Select input).

**Update**: `personality_notes` textarea placeholder:
- EN: `"e.g., currently at intermediate level, struggles with sight-reading"`
- VI: `"VD: hiện ở trình độ trung cấp, gặp khó khăn với đọc bản nhạc"`

### StudentDetail

**Drop**: `skill_level` display row.

### StudentList

**Drop**: `skill_level` table column.

---

## 7. Student Profile — Active Package Section (MODIFIED)

When a student has an active package, the student detail page shows:

| Field | Value | Notes |
|-------|-------|-------|
| Class | `class_display_id` (with teacher/schedule tooltip) | **NEW** |
| Lesson Kind | `lesson_kind_name` | **NEW** |
| Lessons | `number_of_lessons` total, `remaining_sessions` remaining | RENAMED |
| Tuition Fee | VND formatted | Admin only |
| Payment | Status badge | |

---

## 8. i18n Keys (NEW)

### English (`en.json`) additions

```json
{
  "nav.classes": "Classes",
  "classes.title": "Classes",
  "classes.displayId": "Class ID",
  "classes.teacher": "Teacher",
  "classes.weekday": "Weekday",
  "classes.time": "Time",
  "classes.duration": "Duration",
  "classes.enrolled": "Enrolled",
  "classes.feePerLesson": "Fee/Lesson",
  "classes.createClass": "Create Class",
  "classes.noClasses": "No classes found. Create a class to get started.",
  "package.class": "Class",
  "package.lessonKind": "Lesson Kind",
  "package.numberOfLessons": "Number of Lessons",
  "package.tuitionFee": "Tuition Fee",
  "package.assignPackage": "Assign Package",
  "package.resetAutoFill": "Reset to auto-fill",
  "package.notEnrolled": "{{student}} is not enrolled in {{class}}. Enroll the student first.",
  "package.createKindOption": "Create new: \"{{name}}\"",
  "lessonKind.title": "Lesson Kind",
  "student.notesPlaceholder": "e.g., currently at intermediate level, struggles with sight-reading"
}
```

### Vietnamese (`vi.json`) additions

```json
{
  "nav.classes": "Lớp học",
  "classes.title": "Danh sách lớp học",
  "classes.displayId": "Mã lớp",
  "classes.teacher": "Giáo viên",
  "classes.weekday": "Thứ",
  "classes.time": "Giờ",
  "classes.duration": "Thời lượng",
  "classes.enrolled": "Học viên",
  "classes.feePerLesson": "Học phí/buổi",
  "classes.createClass": "Tạo lớp mới",
  "classes.noClasses": "Chưa có lớp học nào. Tạo lớp để bắt đầu.",
  "package.class": "Lớp học",
  "package.lessonKind": "Loại bài",
  "package.numberOfLessons": "Số buổi học",
  "package.tuitionFee": "Học phí",
  "package.assignPackage": "Tạo gói học",
  "package.resetAutoFill": "Đặt lại tự động",
  "package.notEnrolled": "{{student}} chưa đăng ký lớp {{class}}. Vui lòng đăng ký học viên trước.",
  "package.createKindOption": "Tạo mới: \"{{name}}\"",
  "lessonKind.title": "Loại bài",
  "student.notesPlaceholder": "VD: hiện ở trình độ trung cấp, gặp khó khăn với đọc bản nhạc"
}
```

---

## Design Notes

### VND Formatter (shared utility)

```javascript
// Used across fee inputs
const vndFormatter = (value) =>
  value ? `${value}`.replace(/\B(?=(\d{3})+(?!\d))/g, ',') : '';

const vndParser = (value) =>
  value ? value.replace(/,/g, '') : '';
```

### Weekday Display Mapping

```javascript
const WEEKDAY_LABELS = {
  en: ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
  vi: ['T2', 'T3', 'T4', 'T5', 'T6', 'T7', 'CN'],
};
```
