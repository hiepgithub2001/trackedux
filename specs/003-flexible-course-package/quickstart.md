# Quickstart: Flexible Course Package with Class Catalog & Lesson Kind Vocabulary

**Feature**: 003-flexible-course-package
**Date**: 2026-04-27

---

## Prerequisites

- PostgreSQL 16+ running locally
- Node 20+ installed
- Python 3.11+ with pip

## Setup

### 1. Start the Backend

```bash
cd backend
pip install -e ".[dev]"
uvicorn app.main:app --reload --port 8000
```

### 2. Run Database Migrations

```bash
cd backend
alembic upgrade head
```

This runs migration `012_flexible_course_package.py` which:
- Creates the `lesson_kinds` table and seeds initial kinds (Beginner, Elementary, Intermediate, Advanced)
- Adds `tuition_fee_per_lesson` to `class_sessions`
- Drops `skill_level` from `students`
- Rebuilds `packages`, `payment_records`, and `renewal_reminders` tables with the new schema

### 3. Seed Data (optional)

```bash
cd backend
python -m app.scripts.seed
```

### 4. Start the Frontend

```bash
cd frontend
npm install
npm run dev
```

### 5. Open the App

Navigate to `http://localhost:5173` in your browser.

---

## Smoke Test Flow

### Step 1: Log In as Admin

- URL: `http://localhost:5173/login`
- Credentials: `admin@piano.vn` / `admin123`
- Expected: Redirect to dashboard

### Step 2: Verify Classes Tab

- Click **"Classes"** in the sidebar navigation
- Expected: A table listing all classes with columns:
  - Display ID (e.g., "Jane-Mon-1730")
  - Teacher name
  - Weekday (Mon–Sun)
  - Time (HH:MM)
  - Duration (minutes)
  - Enrolled count
  - Fee/Lesson (VND, admin-only column)

### Step 3: Set Fee on a Class

- Click any class row that has no fee set (fee shows "—")
- In the detail/edit view, enter `tuition_fee_per_lesson` = **200,000** VND
- Save
- Expected: Fee appears in the Classes list as "200,000"

### Step 4: Create a New Class with Fee

- Click **"Create Class"** button
- Fill in:
  - Teacher: (pick any teacher)
  - Name: "Test Package Class"
  - Day: Monday
  - Time: 14:00
  - Duration: 45 min
  - Fee/Lesson: **150,000** VND
  - Students: (pick at least one student)
- Save
- Expected: New class appears in list with display ID and fee

### Step 5: Navigate to Tuition and Assign a Package

- Click **"Tuition"** in the sidebar
- Click **"Assign Package"** button
- Fill in the package form:
  - **Student**: Pick a student who is enrolled in the class from Step 4
  - **Class**: Type the display ID and select from typeahead
  - **Number of Lessons**: **10**
  - Expected: Fee auto-fills to **1,500,000** VND (150,000 × 10)
  - **Lesson Kind**: Type "Beginner" and select from suggestions
  - Leave fee as auto-filled
- Click **Save**
- Expected: Package appears in the tuition list with:
  - Class display ID
  - Lesson Kind = "Beginner"
  - 10 lessons / 10 remaining
  - Fee = 1,500,000 VND

### Step 6: Test Auto-fill Override

- Click **"Assign Package"** again
- Select a different student enrolled in the same class
- Enter Lessons = **20**
- Expected: Auto-fill = **3,000,000** VND
- Manually change fee to **2,800,000** VND (discount)
- Change Lessons to **25**
- Expected: Fee stays at **2,800,000** (manual edit preserved)
- Save
- Expected: Package saved with fee = 2,800,000

### Step 7: Test Inline Lesson Kind Create

- Click **"Assign Package"** again
- Fill Student + Class + Lessons
- In Lesson Kind, type **"Jazz Foundations"**
- Expected: Typeahead shows "Create new: Jazz Foundations"
- Select the create option
- Save
- Expected: Package saved. "Jazz Foundations" now appears in lesson kind suggestions for future packages.

### Step 8: Test Enrollment Validation

- Open **"Assign Package"**
- Select a student who is NOT enrolled in the chosen class
- Fill remaining fields and click Save
- Expected: Error message: "{Student} is not enrolled in {Class}. Enroll the student first." with a link to class enrollment

### Step 9: Verify Attendance Still Works

- Navigate to **Attendance**
- Select the class from Step 4
- Mark the student from Step 5 as "Present"
- Save
- Navigate back to **Tuition**
- Expected: The student's package now shows **9 remaining** sessions (was 10)

---

## Verification Checklist

| # | Check | Pass? |
|---|-------|-------|
| 1 | Classes tab visible in navigation | ☐ |
| 2 | Display IDs compute correctly (teacher-day-time format) | ☐ |
| 3 | Fee/Lesson column visible to admin, hidden from staff | ☐ |
| 4 | Package form has 5 inputs (no 12/24/36 presets) | ☐ |
| 5 | Auto-fill fee works when class + lessons both set | ☐ |
| 6 | Manual fee edit preserved across class/lesson changes | ☐ |
| 7 | Inline lesson kind creation works | ☐ |
| 8 | Enrollment validation rejects non-enrolled student | ☐ |
| 9 | Attendance decrements remaining sessions | ☐ |
| 10 | `skill_level` field removed from student forms | ☐ |
| 11 | Class deletion blocked when packages reference it | ☐ |
| 12 | Bilingual translations present (no untranslated keys) | ☐ |
