
# Job Board Backend API

![Coverage](https://img.shields.io/badge/coverage-89%25-brightgreen)
![Tests](https://img.shields.io/badge/tests-passing-brightgreen)
![Python](https://img.shields.io/badge/python-3.12-blue)
![Django](https://img.shields.io/badge/django-5.2-blue)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue)
![Redis](https://img.shields.io/badge/Redis-7-blue)
![Celery](https://img.shields.io/badge/Celery-enabled-blue)
![Docker](https://img.shields.io/badge/Docker-enabled-blue)
![WebSockets](https://img.shields.io/badge/WebSockets-enabled-blue)
![License](https://img.shields.io/badge/license-MIT-blue)
[![CI](https://github.com/andugetachew/job-board-backend/actions/workflows/ci.yml/badge.svg)](https://github.com/andugetachew/job-board-backend/actions)
## 🌐 Live Demo

| | URL |
|--|--|
| **API Base** | https://job-board-backend-1xpd.onrender.com |
| **Swagger Docs** | https://job-board-backend-1xpd.onrender.com/api/docs/ |
| **ReDoc** | https://job-board-backend-1xpd.onrender.com/api/redoc/ |
| **Health Check** | https://job-board-backend-1xpd.onrender.com/health/ |

### Local Development

- API: http://localhost:8001
- Swagger Docs: http://localhost:8001/api/docs/
- ReDoc: http://localhost:8001/api/redoc/
- Health: http://localhost:8001/health/


## 📊 Quality Metrics

- 87% code coverage
- 0 failed tests
- Unit + integration + permission + analytics test layers
- WebSocket consumer tests included
- Redis cache decorator tests included
- Role-based permission tests included

## 📸 API Documentation Preview

> Full interactive documentation available at `/api/docs/`

### Overview & Authentication
![Swagger Overview](docs/swagger1.png)

### Jobs & Applications
![Jobs and Applications](docs/swagger2.png)

### Analytics & Saved Jobs
![Analytics and Saved Jobs](docs/swagger3.png)

### Reviews & Admin
![Reviews and Admin](docs/swagger4.png)

> A production-ready job board REST API — employers post and manage job listings, candidates apply and track application status in real time, admins oversee the platform. Built with Django REST Framework, PostgreSQL, Redis, Celery, Django Channels (WebSockets), and Docker.

## ⚡ Why This Project?
| Challenge | Solution |
|------------|----------|
| Duplicate job applications | unique_together(job, candidate) |
| Slow job listings | Redis caching with automatic invalidation |
| Resume processing | Celery background parsing |
| Real-time updates | Django Channels WebSockets |
| Data recovery | Soft delete |
| Employer analytics | Optimized aggregate queries |

### 🚀 Features

- JWT authentication with email verification
- Candidate, employer and admin roles
- Job posting and application workflow
- Resume upload and background parsing
- Employer and candidate analytics
- Redis caching and rate limiting
- Celery background processing
- Real-time notifications via WebSockets
- Dockerized deployment
- 89% code coverage with automated tests

---
## 🛠 Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Django 5.2, Django REST Framework 3.15 |
| Database | PostgreSQL 16 |
| Cache & Broker | Redis 7 |
| Authentication | JWT (djangorestframework-simplejwt) |
| Background Tasks | Celery + Redis |
| Real-Time | Django Channels + WebSockets |
| API Docs | drf-spectacular (Swagger + ReDoc) |
| Testing | pytest, pytest-django, pytest-cov |
| Containerization | Docker, Docker Compose |

---

## 🏗 System Architecture

```text
Client (Web / Mobile)
        │
        ▼
Django REST API (Daphne)
        │
        ├── PostgreSQL
        ├── Redis
        │     ├── Cache
        │     └── Celery Broker
        ▼
Celery Workers
```


---

## 📁 Project Structure

job-board-backend/
├── accounts/            # Auth, registration, email verification, password reset
├── jobs/                # Job listings, applications, saved jobs, alerts
│   ├── models.py        # Job, Application, SavedJob, JobAlert, StatusHistory
│   ├── views.py         # All job and application endpoints
│   ├── decorators.py    # cache_for_jobs, invalidate_job_cache
│   ├── analytics.py     # Employer and candidate analytics views
│   ├── tasks.py         # Resume parsing, email notifications
│   └── consumers.py     # WebSocket notification consumers
├── reviews/             # Company reviews
├── backup/              # Database backup views
├── config/              # Settings, URLs, cache, permissions, throttling
└── tests/               # Full test suite


---
## 📡 API Endpoints
/api/v1/

auth/
users/
companies/
jobs/
applications/
resumes/
saved-jobs/
alerts/
notifications/
analytics/
reviews/

---

## 💡 Example API Usage

**Register as a candidate:**
```bash
curl -X POST http://localhost:8001/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "candidate@example.com",
    "username": "andualem",
    "password": "SecurePass123",
    "password2": "SecurePass123",
    "role": "candidate"
  }'
```

**Post a job (employer):**
```bash
curl -X POST http://localhost:8001/api/jobs/ \
  -H "Authorization: Bearer <access_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Senior Django Developer",
    "description": "We need an experienced Django developer...",
    "location": "Addis Ababa",
    "employment_type": "full",
    "expires_at": "2026-12-31T00:00:00Z"
  }'
```

**Apply to a job:**
```bash
curl -X POST http://localhost:8001/api/jobs/1/apply/ \
  -H "Authorization: Bearer <access_token>" \
  -F "resume=@/path/to/resume.pdf" \
  -F "cover_letter=I am excited to apply..."
```

**Get employer analytics:**
```bash
curl http://localhost:8001/api/analytics/employer/ \
  -H "Authorization: Bearer <access_token>"
```

---

## ⚡ Performance Strategy

### Redis Caching
- Job listings cached per URL path with 15-minute TTL
- `cache_for_jobs` decorator forces JSON rendering before pickling
- `invalidate_job_cache` uses `delete_pattern("job_list_*")` on any write

### Database Optimization
- Indexes on `employer`, `is_active`, `location`, `salary_min/max`, `is_deleted`
- `select_related()` for ForeignKey traversals
- Soft delete with `is_deleted` flag — no data loss on job removal
- `unique_together` on `(job, candidate)` prevents duplicate applications

---

## ⚙️ Background Tasks (Celery)

| Task | Trigger |
|------|---------|
| Send verification email | On registration |
| Send password reset email | On forgot password |
| Parse resume | On application submitted |
| Send application notification | On status change |
| Send job alert emails | Periodic — matching new jobs |

---

## 🔐 Security

- JWT with blacklisting on logout
- Rate limiting on auth and application endpoints
- CORS protection
- Role-based permissions: `IsCandidate`, `IsEmployer`, `IsAdminUser`
- Soft delete on jobs and accounts — no hard deletes
- Input validation via DRF serializers

---

## 🧪 Testing

```bash
# Run full test suite inside Docker
docker-compose exec backend pytest --tb=short -q

# With coverage report
docker-compose exec backend pytest --cov=. --cov-report=term-missing

# Specific module
docker-compose exec backend pytest tests/test_analytics.py -v
```

### ✅ Test Results: 89% coverage


## 🎯 Design Decisions

**`cache_for_jobs` decorator** — caches job list responses in Redis. DRF `Response` objects are lazy and must be rendered before pickling. The decorator forces `response.render()` with a JSON renderer before calling `cache.set()`, preventing `ContentNotRenderedError`.

**Soft delete on jobs** — employers can restore deleted jobs. `is_deleted=True` hides from public listings but preserves all application history and audit trails.

**Employer/candidate analytics** — dedicated `EmployerAnalyticsView` and `CandidateAnalyticsView` aggregate data per user without expensive joins — scoped entirely to the authenticated user's data.

**Role-based access** — `User.role` is a `CharField` with choices `candidate/employer/admin`. `is_employer` and `is_candidate` are `@property` methods — not DB columns — keeping the model lean.

**Resume parsing via Celery** — parsing happens asynchronously after application submission so the HTTP response returns immediately. Extracted fields (`parsed_email`, `parsed_phone`, `extracted_skills`) are stored on the `Application` model.

---

## 📦 Quick Start

```bash
git clone https://github.com/andugetachew/job-board-backend.git
cd job-board-backend
cp .env.example .env
docker-compose up --build
```

- API: `http://localhost:8001/`
- Swagger Docs: `http://localhost:8001/api/docs/`
- Admin Panel: `http://localhost:8001/admin/`

---

## 🔑 Environment Variables

```env
SECRET_KEY=your-secret-key
DEBUG=False
ALLOWED_HOSTS=localhost,127.0.0.1

DB_NAME=jobboard_db
DB_USER=postgres
DB_PASSWORD=yourpassword
DB_HOST=db
DB_PORT=5432

REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@email.com
EMAIL_HOST_PASSWORD=your-app-password
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL=noreply@jobboard.com

FRONTEND_URL=http://localhost:3000
```

---

## 🐳 Docker Services

```bash
docker-compose up --build
```

| Service | Description | Port |
|---------|-------------|------|
| backend | Django + Daphne (ASGI) | 8001 |
| db | PostgreSQL 16 | 5432 |
| redis | Cache + Message broker | 6380 |
| celery | Background task worker | — |

---

## 📄 License

MIT License

---

## 👨‍💻 Author

**Andualem Getachew**

[![GitHub](https://img.shields.io/badge/GitHub-andugetachew-black?logo=github)](https://github.com/andugetachew)
[![Email](https://img.shields.io/badge/Email-andugeta41%40gmail.com-red?logo=gmail)](mailto:andugeta41@gmail.com)