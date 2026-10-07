# 🎓 EduPulse — Production-Grade E-Learning Platform

A modern, production-style E-Learning Platform built with **Python 3.10+ / 3.14**, **FastAPI**, **SQLAlchemy ORM**, **Pydantic v2**, **JWT Authentication with Bcrypt**, **Jinja2 Server-Rendered UI**, and **Chart.js** for student and admin learning analytics.

EduPulse is engineered to deliver a clean SaaS user experience — avoiding clunky academic CRUD patterns in favor of modular architecture, responsive design, verified assessments, and administrative telemetry.

---

## 🌟 Key Features

### 👨‍🎓 Student Experience
- **Hero & Marketplace Discovery**: Browse courses with real-time text search, category filters (Python, Data Structures, Databases, Web Development), difficulty levels (Beginner, Intermediate, Advanced), and sorting (Popular, Top Rated, Newest).
- **Curriculum & Syllabus Inspector**: Structured modules, lesson breakdown with time durations, learning outcomes checklist, and instant enrollment.
- **Interactive Learning Room**:
  - Left navigation drawer with module accordions, completed checkmark status badges, and quick assessment links.
  - Video stream area supporting YouTube and embedded players.
  - Formatted technical lessons with code blocks, downloadable resource links, and key takeaways.
  - Interactive **Mark as Complete** button that updates course completion percentage in real-time and advances to the next lesson.
- **Interactive MCQ Assessments**:
  - Timed quiz interface with styled radio option cards.
  - Automated instant evaluation: Score percentage, count of correct/incorrect answers, and Pass/Fail status.
  - Detailed review highlighting chosen answers vs correct answers with in-depth conceptual explanations.
- **Analytics & Progress Dashboard**:
  - Real-time statistics: Enrolled Courses, Completed Courses, Lessons Completed, Average Quiz Score.
  - Learning streak tracker with consecutive activity tracking.
  - Interactive **Chart.js** performance visualization plotting scores across dates.
- **Account & Security Management**:
  - Edit student profile, bio, and change password with verification.

### 🛡️ Administrator Portal
- **Telemetry & Analytics**:
  - 6 Key Metrics: Total Students, Total Courses, Total Enrollments, Total Lessons, Avg Course Completion Rate, Avg Quiz Score.
  - Dual **Chart.js** charts: Enrollment Growth Trends and Course Popularity Distribution.
  - Recent learner signups and quiz submissions.
- **Course & Curriculum Builder**:
  - Full CRUD operations with instant publish/draft toggles.
  - Module management with custom ordering.
  - Lesson management with rich content, video links, external resources, and durations.
- **Assessment & Question Bank Manager**:
  - Create assessments linked to courses with configurable passing thresholds.
  - Author MCQ questions with 4 selectable options, correct option selector, and explanation feedback.
- **Student Directory**:
  - View registered learners, enrolled counts, completed courses, average exam scores, and activity dates.
  - Detailed student statistics modal for granular inspection.

---

## 🏗️ Technology Stack

| Layer | Technology | Purpose |
| :--- | :--- | :--- |
| **Backend** | Python 3.10+ (tested on Python 3.14) | Core language runtime |
| **Framework** | FastAPI 0.110+ | High-performance asynchronous REST & web application framework |
| **Server** | Uvicorn (ASGI) | Lightning-fast ASGI production server |
| **Database** | SQLite / PostgreSQL via SQLAlchemy 2.0+ | Relational ORM supporting SQLite locally and zero-change migration to PostgreSQL |
| **Data Validation** | Pydantic v2 | Strict schema validation, type safety, and automatic docs |
| **Authentication** | JWT (`pyjwt`) & `bcrypt` | Secure token signing and salted password hashing (RFC compliant) |
| **Templating** | Jinja2 | Clean server-rendered HTML views |
| **Styling** | Modern Responsive CSS | Polished SaaS design system (Inter + Plus Jakarta Sans typography) |
| **Analytics** | Chart.js 4+ | Dynamic canvas charts for student progress and admin telemetry |

---

## 📁 Project Structure

```
python1/
├── app/
│   ├── __init__.py
│   ├── config.py              # Environment configuration & Pydantic settings
│   ├── database.py            # SQLAlchemy engine, session maker & Base
│   ├── templating.py          # Universal template renderer helper
│   ├── main.py                # FastAPI app initialization, routes, static mount
│   │
│   ├── models/                # SQLAlchemy database models
│   │   ├── __init__.py
│   │   ├── user.py            # User model (students & admins)
│   │   ├── course.py          # Course model & relationships
│   │   ├── lesson.py          # Module & Lesson models
│   │   ├── progress.py        # Enrollment & LessonProgress models
│   │   └── assessment.py      # Assessment, Question & AssessmentResult models
│   │
│   ├── schemas/               # Pydantic validation schemas
│   │   ├── __init__.py
│   │   ├── user.py            # Auth & User schemas
│   │   ├── course.py          # Course create/update/response schemas
│   │   ├── lesson.py          # Module & Lesson schemas
│   │   ├── progress.py        # Progress & stats schemas
│   │   └── assessment.py      # Assessment submission & result schemas
│   │
│   ├── routers/               # Route handlers & endpoints
│   │   ├── __init__.py
│   │   ├── auth.py            # Login, register, logout (HTML + REST API)
│   │   ├── courses.py         # Marketplace, course details, enrollments
│   │   ├── lessons.py         # Learning room & mark-complete action
│   │   ├── assessments.py     # Quiz taking, auto-grading & review
│   │   ├── progress.py        # Student dashboard, analytics & profile
│   │   └── admin.py           # Admin telemetry, course/lesson/quiz CRUD
│   │
│   ├── services/              # Business logic & domain services
│   │   ├── __init__.py
│   │   ├── auth_service.py    # Password hashing, JWT creation & verification
│   │   ├── course_service.py  # Course queries, filters & mutations
│   │   ├── progress_service.py# Completion math, streaks & dashboard metrics
│   │   └── assessment_service.py # MCQ auto-grader & result compiler
│   │
│   ├── templates/             # Jinja2 server-rendered templates
│   │   ├── base.html          # Global layout, modern navbar & footer
│   │   ├── home.html          # Landing page (Hero, Categories, Testimonials)
│   │   ├── login.html         # Sign in with one-click demo credentials
│   │   ├── register.html      # Student registration
│   │   ├── courses.html       # Marketplace with search & filter pills
│   │   ├── course_detail.html # Syllabus accordion & course objectives
│   │   ├── lesson.html        # Learning interface with module sidebar
│   │   ├── assessment.html    # Interactive MCQ quiz interface
│   │   ├── result.html        # Assessment score & detailed explanations
│   │   ├── dashboard.html     # Student dashboard with Chart.js
│   │   ├── progress.html      # Detailed progress & streak metrics
│   │   ├── profile.html       # Profile settings & password change
│   │   └── admin/
│   │       ├── base_admin.html# Admin sidebar & header layout
│   │       ├── dashboard.html # Admin metrics & dual Chart.js graphs
│   │       ├── courses.html   # Course inventory & status toggle
│   │       ├── course_form.html # Create / Edit course form
│   │       ├── modules_lessons.html # Curriculum visual builder
│   │       ├── assessments.html # Assessment management
│   │       ├── questions.html # Question bank editor & explanation authoring
│   │       └── students.html  # Student directory & profile modal
│   │
│   └── static/
│       ├── css/
│       │   └── style.css      # Custom SaaS design system
│       └── js/
│           ├── main.js        # Modals, toasts, dropdowns
│           ├── learning.js    # Interactive lesson completion AJAX
│           └── charts.js      # Chart.js renderers
│
├── seed_data.py               # Comprehensive realistic database seeder
├── test_platform.py           # 13-suite functional verification test suite
├── requirements.txt           # Python dependencies
├── .env.example               # Environment template
├── .env                       # Local environment configuration
├── README.md                  # Complete documentation
└── run.py                     # Server entrypoint with auto-table generation
```

---

## ⚡ Quick Start Guide

### 1. Requirements
- **Python Version**: Python 3.10, 3.11, 3.12, 3.13, or **3.14**
- **Operating System**: Windows, macOS, or Linux

### 2. Install Dependencies
Open your terminal in the project directory:

```bash
pip install -r requirements.txt
```

### 3. Initialize & Seed Database
Seed the database with pre-configured courses, modules, lessons, assessments, questions, and demo student/admin accounts:

```bash
python seed_data.py
```

### 4. Start the Application
Run the FastAPI development server:

```bash
python run.py
```

The server will initialize on:
👉 **http://127.0.0.1:8000**

Interactive API Docs (Swagger):
👉 **http://127.0.0.1:8000/docs**

---

## 🔑 Demo Credentials

| Role | Email | Password | Access Rights |
| :--- | :--- | :--- | :--- |
| **Administrator** | `admin@elearning.com` | `admin123` | Full Admin Console (`/admin`), Course CRUD, Lesson & Assessment Builders, Student Directory |
| **Student** | `student@elearning.com` | `student123` | Enrolled Courses, Learning Room, Quiz Submissions, Progress Analytics |

> 💡 **Tip:** On the `/login` page, you can click the **"Demo Student"** or **"Demo Admin"** quick-fill button to populate credentials in one click.

---

## 🧪 Running the Automated Verification Suite

Run the comprehensive test suite verifying landing page rendering, course search, JWT authentication, protected dashboard routes, lesson completion, and quiz grading:

```bash
python test_platform.py
```

---

## 🔌 REST API Endpoints Overview

### Authentication
- `POST /api/auth/register` — Register a new student account
- `POST /api/auth/login` — Authenticate and receive JWT Bearer token + set cookie
- `GET /api/auth/me` — Retrieve authenticated user profile
- `POST /api/auth/logout` — Revoke access token

### Courses & Enrollment
- `GET /api/courses` — List courses (supports `search`, `category`, `difficulty`, `sort_by`)
- `GET /api/courses/{course_id}` — Get course details with modules, lessons, and assessments
- `POST /api/courses` — Create course *(Admin only)*
- `PUT /api/courses/{course_id}` — Update course *(Admin only)*
- `DELETE /api/courses/{course_id}` — Delete course *(Admin only)*
- `POST /api/courses/{course_id}/enroll` — Enroll user in course
- `GET /api/my-courses` — List user's enrolled courses with progress

### Lessons & Progress
- `GET /api/lessons/{lesson_id}` — Get lesson details and completion state
- `POST /api/lessons/{lesson_id}/complete` — Mark lesson as completed and recalculate course progress
- `GET /api/progress` — Get aggregated progress metrics, active courses, and chart data
- `GET /api/courses/{course_id}/progress` — Get specific course progress percentage

### Assessments
- `GET /api/assessments/{assessment_id}` — Retrieve assessment questions
- `POST /api/assessments/{assessment_id}/submit` — Submit answers, calculate score, evaluate pass/fail, and generate explanations

---

## 🗄️ Database Schema & Production Readiness

The database is built using SQLAlchemy Declarative Base. To switch from SQLite to PostgreSQL in production:
1. Update `DATABASE_URL` in `.env`:
   ```env
   DATABASE_URL=postgresql://user:password@localhost:5432/elearning
   ```
2. Install `psycopg2-binary` or `asyncpg`.
3. SQLAlchemy handles schema migrations and type mapping without rewriting application queries.

---

## 🛡️ Security Best Practices
- **Password Protection**: Passwords are encrypted with salted `bcrypt` hashes. Plain-text passwords are never stored or logged.
- **Stateless Tokens**: JWTs signed with `HS256` carrying expiration timestamps (`exp`).
- **Dual Session Authentication**: Endpoints verify tokens from both `Authorization: Bearer <token>` headers and `HttpOnly` cookies, ensuring both SPA client requests and browser page navigations work seamlessly.
- **RBAC**: Administrative routes verify `current_user.role == 'admin'`, redirecting or rejecting unauthorized users.
- **Zero Dummy Links**: All navigation tabs, forms, buttons, and progress counters are connected to working database records and services.
