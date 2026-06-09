
---

# 📡 CLEAN `API.md`

```markdown id="jobboard_api"
# Job Board API Documentation

## Base URL
http://localhost:8000/api

---

## 🔐 Authentication

### Register
POST /auth/register/

```json
{
  "username": "john",
  "email": "john@email.com",
  "password": "password123"
}

Login

POST /auth/login/

{
  "username": "john",
  "password": "password123"
}

Response:

{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
💼 Jobs
List Jobs

GET /jobs/

Supports:

search
filters
pagination
Create Job (Employer)

POST /jobs/

{
  "title": "Python Developer",
  "description": "Build APIs",
  "location": "Remote",
  "employment_type": "full_time",
  "salary_min": 80000,
  "salary_max": 120000
}
Update Job

PUT /jobs/{id}/

Delete Job (Soft Delete)

DELETE /jobs/{id}/

📄 Applications
Apply to Job

POST /jobs/{id}/apply/

Rules:

Requires authentication
One application per job
Rate limited
{
  "cover_letter": "I am interested in this role"
}
My Applications

GET /jobs/applications/my/

Employer Applications

GET /jobs/applications/employer/

Update Status

PATCH /jobs/applications/{id}/status/

{
  "status": "interview"
}
Withdraw Application

DELETE /jobs/applications/{id}/withdraw/

💾 Saved Jobs

POST /jobs/saved/
GET /jobs/saved/
DELETE /jobs/saved/{id}/

⭐ Reviews

POST /companies/{id}/reviews/

{
  "rating": 5,
  "comment": "Great company"
}

GET /companies/{id}/reviews/

🔔 Notifications

GET /notifications/

⚡ Rate Limits
Endpoint	Limit
Apply	5/hour
Login	10/15 min
API	1000/day
🔄 WebSocket

ws://localhost:8000/ws/notifications/{user_id}/

{
  "type": "application_update",
  "job_id": 1,
  "status": "interview"
}
❌ Error Format
{
  "detail": "Error message"
}
📌 Status Codes
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
429 Rate Limited
500 Server Error
