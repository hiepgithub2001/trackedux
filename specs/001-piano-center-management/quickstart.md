# TrackedUX — Piano Center Management System

A bilingual (Vietnamese/English) piano learning center management system. Built with FastAPI (Python) and React (Vite). Installable as a Progressive Web App (PWA).

## Prerequisites (Linux)

- **Python**: 3.11+
- **Node.js**: 20 LTS
- **PostgreSQL**: 16+

---

## Local Environment Setup Guide (Linux)

### 1. Database Setup (PostgreSQL)

You need to create a PostgreSQL database and configure the connection credentials. You must also enable specific extensions for Vietnamese unaccented search.

Install PostgreSQL (if you haven't already on Ubuntu/Debian):
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
```

Create a new database and user. Here is how to set the password, create the database `trackedux`, and enable the required extensions:

```bash
# Create a new user called 'trackedux_user' with password 'admin'
sudo -u postgres psql -c "CREATE USER trackedux_user WITH PASSWORD 'admin';"

# Create the database and assign ownership to the new user
sudo -u postgres createdb -O trackedux_user trackedux

# Connect to the database as superuser to create extensions
sudo -u postgres psql -d trackedux -c "CREATE EXTENSION IF NOT EXISTS \"uuid-ossp\";"
sudo -u postgres psql -d trackedux -c "CREATE EXTENSION IF NOT EXISTS unaccent;"
sudo -u postgres psql -d trackedux -c "CREATE EXTENSION IF NOT EXISTS pg_trgm;"
```

### 2. Backend Setup

The backend is built with FastAPI and uses SQLAlchemy with asyncpg.

```bash
# Navigate to the backend directory
cd backend

# Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -e ".[dev]"

# Configure environment variables
cp .env.example .env
```

**Configure `.env`:**
Edit the `.env` file you just created and update the `DATABASE_URL` with the password you set in step 1. Also, set a secure random string for `JWT_SECRET`.

```env
DATABASE_URL=postgresql+asyncpg://trackedux_user:admin@localhost:5432/trackedux
JWT_SECRET=your_random_secret_key
JWT_ALGORITHM=HS256
ACCESS_TOKEN_TTL_MINUTES=15
REFRESH_TOKEN_TTL_DAYS=7
DEFAULT_LANGUAGE=vi
```

**How to generate secure keys:**
- For `JWT_SECRET`, run:
  ```bash
  openssl rand -hex 32
  ```

**Run Database Migrations and Seed Data:**
Initialize your database schema and seed the initial admin user:
```bash
alembic upgrade head
python -m app.scripts.seed
```

**Start the Backend Server:**
```bash
uvicorn app.main:app --reload --port 8000
```
The API will be available at `http://localhost:8000`, and the interactive API documentation at `http://localhost:8000/docs`.

### 3. Frontend Setup

The frontend is a React application powered by Vite.

Open a new terminal window:
```bash
# Navigate to the frontend directory
cd backend/../frontend  # or just cd ../frontend from the backend dir

# Configure environment variables
cp .env.example .env

# Install dependencies
npm install

# Start the development server
npm run dev
```
The frontend will be available at `http://localhost:5173`.

---

## Key Workflows

### Register a Student
1. Open http://localhost:5173. Toggle language with "VI | EN" in the header.
2. Log in using the default seeded admin credentials:
   - **Username**: `admin`
   - **Password**: `admin123`
3. Click **Thêm học sinh** / **Add Student**.
4. Fill in the student's name, parent info, skill level, and notes.
5. Click **Lưu** / **Save**. The student appears in the student list.

### Create a Class Schedule
1. Navigate to **Lịch học** / **Schedule**.
2. Click **Tạo lớp** / **Create Class**.
3. Select class type (1:1, Pair, Group), assign a teacher and students, pick a time slot.
4. Click **Lưu** / **Save**. The class appears on the weekly calendar.
5. If a scheduling conflict exists, the system will display a warning and prevent the booking.

### Mark Attendance
1. Navigate to **Điểm danh** / **Attendance**.
2. Select today's class session.
3. Mark each student as: Present / Absent / Absent with Notice.
4. Click **Lưu** / **Save**. Remaining sessions update automatically.
5. For absent students, optionally schedule a makeup session.

### Manage Tuition Packages
1. Navigate to **Học phí** / **Tuition**.
2. Select a student and click **Tạo gói** / **Create Package**.
3. Choose 12, 24, 36, or custom number of sessions. Enter price (VND).
4. Record payment when received.
5. The system auto-reminds when a student has ≤2 sessions remaining.

---

## Testing

To run the test suites for both backend and frontend:

**Backend:**
```bash
cd backend
source venv/bin/activate
pytest                 # runs unit + integration (testcontainers spins up Postgres)
pytest tests/contract  # OpenAPI contract drift check
```

**Frontend:**
```bash
cd frontend
npm test               # vitest + Testing Library
npm run test:e2e       # Playwright smoke (login → schedule → attendance)
```

---

## PWA Mobile Support

TrackedUX is installable as a Progressive Web App (PWA) on Android and iOS devices.

### Install on Mobile

**Android (Chrome 100+):**
1. Open `https://your-domain/` in Chrome.
2. An install banner will appear: "Cài đặt ứng dụng" / "Install App".
3. Tap to add the app to your home screen.

**iOS (Safari 16.4+):**
1. Open the app in Safari.
2. Tap **Share → Thêm vào Màn hình chính** / **Add to Home Screen**.

### Connection Handling

- **Offline Banner**: A yellow "Mất kết nối" / "No Connection" banner appears when the device loses connectivity.
- **Online-Only**: The app does not cache API data offline. All operations require an active connection.

---

## Project Structure

```
trackedux/
├── backend/
│   ├── alembic/              # Database migrations
│   │   └── versions/         # Sequential: 001_, 002_, 003_, ...
│   ├── app/
│   │   ├── api/              # FastAPI route handlers
│   │   │   ├── auth.py
│   │   │   ├── students.py
│   │   │   ├── teachers.py
│   │   │   ├── classes.py
│   │   │   ├── attendance.py
│   │   │   ├── packages.py
│   │   │   ├── dashboard.py
│   │   │   └── portal.py     # Parent portal (Phase 2)
│   │   ├── core/             # Config, security, dependencies
│   │   │   ├── config.py
│   │   │   ├── security.py
│   │   │   └── deps.py
│   │   ├── crud/             # Database CRUD operations
│   │   ├── db/               # Database session & engine
│   │   ├── models/           # SQLAlchemy ORM models
│   │   ├── schemas/          # Pydantic request/response schemas
│   │   ├── services/         # Business logic layer
│   │   ├── scripts/          # Seed data, utilities
│   │   └── main.py           # FastAPI app entry point
│   ├── tests/
│   │   ├── unit/
│   │   ├── integration/
│   │   └── contract/
│   ├── alembic.ini
│   ├── pyproject.toml
│   └── .env.example
├── frontend/
│   ├── public/               # PWA icons, static assets
│   ├── src/
│   │   ├── api/              # API client (axios)
│   │   ├── auth/             # Auth context, login page
│   │   ├── components/       # Shared UI components
│   │   ├── features/         # Feature modules
│   │   │   ├── students/
│   │   │   ├── teachers/
│   │   │   ├── schedule/
│   │   │   ├── attendance/
│   │   │   ├── tuition/
│   │   │   ├── dashboard/
│   │   │   └── portal/       # Parent portal (Phase 2)
│   │   ├── i18n/             # Translations (en.json, vi.json)
│   │   ├── lib/              # Utilities, helpers
│   │   ├── pwa/              # PWA components
│   │   ├── routes/           # Route definitions
│   │   ├── styles/           # Global CSS
│   │   ├── App.jsx
│   │   └── main.jsx
│   ├── e2e/                  # Playwright tests
│   ├── package.json
│   ├── vite.config.js
│   └── .env.example
├── specs/                    # Feature specifications
├── README.md
└── .gitignore
```
