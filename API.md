Complete Job Board API Documentation
Base URL
text
http://localhost:8000/api
Authentication
All protected endpoints require a JWT token in the Authorization header:

text
Authorization: Bearer <your_access_token>
Authentication Endpoints
1. Register User
text
POST /api/auth/register/
Request Body:

json
{
  "username": "johndoe",
  "email": "john@example.com",
  "password": "password123",
  "role": "candidate",
  "company": "Tech Corp"  // Required for employer role only
}
Response:

json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "candidate",
    "company": "",
    "avatar": null,
    "phone": "",
    "bio": "",
    "location": "",
    "website": "",
    "created_at": "2024-01-01T00:00:00Z"
  },
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs...",
  "message": "Please verify your email"
}
2. Login
text
POST /api/auth/login/
Request Body:

json
{
  "username": "johndoe",
  "password": "password123"
}
Response:

json
{
  "user": {
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "role": "candidate"
  },
  "access": "eyJhbGciOiJIUzI1NiIs...",
  "refresh": "eyJhbGciOiJIUzI1NiIs..."
}
3. Get Profile
text
GET /api/auth/profile/
Response:

json
{
  "id": 1,
  "username": "johndoe",
  "email": "john@example.com",
  "role": "candidate",
  "company": "",
  "avatar": null,
  "phone": "+1234567890",
  "bio": "Software developer",
  "location": "New York",
  "website": "https://johndoe.com",
  "created_at": "2024-01-01T00:00:00Z"
}
4. Update Profile
text
PUT /api/auth/profile/update/
Request Body (multipart/form-data):

Field	Type	Required
username	string	No
email	string	No
phone	string	No
bio	string	No
location	string	No
website	string	No
avatar	file	No
5. Change Password
text
POST /api/auth/change-password/
Request Body:

json
{
  "old_password": "oldpass123",
  "new_password": "newpass123"
}
6. Forgot Password
text
POST /api/auth/forgot-password/
Request Body:

json
{
  "email": "john@example.com"
}
7. Reset Password
text
POST /api/auth/reset-password/
Request Body:

json
{
  "token": "reset_token_from_email",
  "new_password": "newpass123"
}
8. Verify Email
text
POST /api/auth/verify-email/
Request Body:

json
{
  "email": "john@example.com",
  "token": "verification_token"
}
Job Endpoints
1. List Jobs (Public)
text
GET /api/jobs/
Query Parameters:

Parameter	Type	Description
search	string	Search in title/description
location	string	Filter by location
is_remote	boolean	Filter remote jobs
employment_type	string	full, part, contract, internship, remote
salary_min_gte	number	Minimum salary
salary_max_lte	number	Maximum salary
page	integer	Page number
Response:

json
{
  "count": 25,
  "next": "http://localhost:8000/api/jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": 1,
      "title": "Python Developer",
      "description": "Build amazing applications",
      "requirements": "5+ years Python",
      "location": "Remote",
      "is_remote": true,
      "employment_type": "full",
      "salary_min": 80000,
      "salary_max": 120000,
      "employer_name": "Tech Corp",
      "employer_id": 1,
      "created_at": "2024-01-01T00:00:00Z",
      "is_active": true,
      "views_count": 150,
      "applications_count": 12
    }
  ]
}
2. Get Job Details (Public)
text
GET /api/jobs/{id}/
3. Create Job (Employer Only)
text
POST /api/jobs/
Request Body:

json
{
  "title": "Senior React Developer",
  "description": "Join our team...",
  "requirements": "5+ years React, TypeScript",
  "location": "Remote",
  "is_remote": true,
  "employment_type": "full",
  "salary_min": 90000,
  "salary_max": 140000,
  "expires_at": "2025-12-31T23:59:59Z"
}
4. Update Job (Owner Only)
text
PUT /api/jobs/{id}/
PATCH /api/jobs/{id}/
5. Delete Job (Owner Only)
text
DELETE /api/jobs/{id}/
Application Endpoints
1. Apply to Job (Candidate)
text
POST /api/jobs/{job_id}/apply/
Request Body (multipart/form-data):

Field	Type	Required
cover_letter	string	Yes
resume	file	Yes (PDF, DOC, DOCX, TXT, max 5MB)
Response:

json
{
  "success": true,
  "application_id": 42,
  "job_title": "Python Developer"
}
2. Get My Applications (Candidate)
text
GET /api/jobs/applications/my/
Response:

json
{
  "count": 5,
  "results": [
    {
      "id": 42,
      "job_title": "Python Developer",
      "status": "pending",
      "cover_letter": "I am interested...",
      "applied_at": "2024-01-01T00:00:00Z",
      "resume_url": "http://localhost:8000/media/resumes/resume.pdf"
    }
  ]
}
3. Get Single Application Details (Candidate or Employer)
text
GET /api/jobs/applications/{id}/
Response:

json
{
  "id": 42,
  "job_title": "Python Developer",
  "job_id": 1,
  "candidate_name": "John Doe",
  "candidate_email": "john@example.com",
  "status": "reviewed",
  "cover_letter": "I am very interested...",
  "employer_notes": "Strong portfolio",
  "applied_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-05T00:00:00Z",
  "resume_url": "http://localhost:8000/media/resumes/resume.pdf"
}
4. Get Applications for My Jobs (Employer)
text
GET /api/jobs/applications/employer/
5. Update Application Status (Employer)
text
PATCH /api/jobs/applications/{id}/status/
Request Body:

json
{
  "status": "reviewed"
}
Status Options: pending, reviewed, interview, rejected, hired

6. Withdraw Application (Candidate)
text
DELETE /api/jobs/applications/{id}/withdraw/
Saved Jobs Endpoints
1. Save a Job (Candidate)
text
POST /api/jobs/saved/
Request Body:

json
{
  "job_id": 1
}
2. List Saved Jobs (Candidate)
text
GET /api/jobs/saved/
3. Remove Saved Job (Candidate)
text
DELETE /api/jobs/saved/{id}/
Job Alert Endpoints
1. Create Job Alert (Candidate)
text
POST /api/jobs/alerts/
Request Body:

json
{
  "search_keyword": "Python",
  "location": "Remote",
  "is_remote": true,
  "employment_type": "full",
  "salary_min": 80000,
  "frequency": "daily"
}
2. List Job Alerts (Candidate)
text
GET /api/jobs/alerts/
3. Delete Job Alert (Candidate)
text
DELETE /api/jobs/alerts/{id}/
Company Reviews Endpoints
1. Get Company Reviews (Public)
text
GET /api/companies/{company_id}/reviews/
2. Get Rating Summary (Public)
text
GET /api/companies/{company_id}/reviews/summary/
Response:

json
{
  "average_rating": 4.5,
  "total_reviews": 12,
  "rating_distribution": {
    "1": 1,
    "2": 0,
    "3": 2,
    "4": 4,
    "5": 5
  }
}
3. Post a Review (Candidate)
text
POST /api/companies/{company_id}/reviews/
Request Body:

json
{
  "rating": 5,
  "comment": "Great company to work with!"
}
Additional Endpoints
1. Update Resume (Candidate)
text
PUT /api/jobs/update-resume/
Request Body (multipart/form-data):

Field	Type	Required
resume	file	Yes
2. Email Preferences (Authenticated)
text
GET /api/jobs/email-preferences/
Response:

json
{
  "receive_email_notifications": true
}
text
POST /api/jobs/email-preferences/
Request Body:

json
{
  "receive_email_notifications": false
}
3. Company Jobs (Public)
text
GET /api/jobs/company/{employer_id}/jobs/
4. Job Share Links (Public)
text
GET /api/jobs/{job_id}/share/
Response:

json
{
  "title": "Python Developer",
  "company": "Tech Corp",
  "url": "http://localhost:3000/jobs/1",
  "twitter_url": "https://twitter.com/intent/tweet?text=...",
  "linkedin_url": "https://www.linkedin.com/sharing/share-offsite/?url=..."
}
5. Applicant Profile (Employer Only)
text
GET /api/jobs/applicant/{user_id}/
Admin Endpoints
1. Dashboard Stats (Admin)
text
GET /api/admin/stats/
Response:

json
{
  "totalUsers": 1250,
  "totalJobs": 342,
  "totalApplications": 2147,
  "pendingApplications": 89
}
2. Recent Jobs (Admin)
text
GET /api/admin/recent-jobs/
3. Recent Users (Admin)
text
GET /api/admin/recent-users/
4. Flag Job (Admin)
text
POST /api/admin/jobs/{job_id}/flag/
Response:

json
{
  "message": "Job flagged successfully"
}
Error Responses
400 Bad Request
json
{
  "error": "Validation error message"
}
401 Unauthorized
json
{
  "detail": "Authentication credentials were not provided."
}
403 Forbidden
json
{
  "detail": "You do not have permission to perform this action."
}
404 Not Found
json
{
  "error": "Resource not found"
}
Rate Limits
Endpoint	Limit
Apply to job	5 per hour
Unauthenticated requests	100 per day
Authenticated requests	1000 per day

---
---

## 🚀 cURL Commands for Windows CMD

### Setup: Store Token
```cmd
set TOKEN=your_jwt_token_here
Authentication
Register Candidate

cmd
curl -X POST http://localhost:8000/api/auth/register/ -H "Content-Type: application/json" -d "{\"username\":\"johncandidate\",\"email\":\"john@example.com\",\"password\":\"testpass123\",\"role\":\"candidate\"}"
Register Employer

cmd
curl -X POST http://localhost:8000/api/auth/register/ -H "Content-Type: application/json" -d "{\"username\":\"techcorp\",\"email\":\"hr@techcorp.com\",\"password\":\"testpass123\",\"role\":\"employer\",\"company\":\"Tech Corp\"}"
Login

cmd
curl -X POST http://localhost:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"username\":\"johncandidate\",\"password\":\"testpass123\"}"
Get Profile

cmd
curl -X GET http://localhost:8000/api/auth/profile/ -H "Authorization: Bearer %TOKEN%"
Jobs
List Jobs

cmd
curl -X GET http://localhost:8000/api/jobs/
Create Job (Employer)

cmd
curl -X POST http://localhost:8000/api/jobs/ -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "{\"title\":\"Python Developer\",\"description\":\"Build APIs\",\"requirements\":\"5+ years Python\",\"location\":\"Remote\",\"employment_type\":\"full\",\"expires_at\":\"2025-12-31T23:59:59Z\"}"
Applications
Apply to Job

cmd
curl -X POST http://localhost:8000/api/jobs/1/apply/ -H "Authorization: Bearer %TOKEN%" -F "cover_letter=I am interested" -F "resume=@C:\Users\YourName\Documents\resume.pdf"
Update Application Status (Employer)

cmd
curl -X PATCH http://localhost:8000/api/jobs/applications/1/status/ -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "{\"status\":\"interview\"}"
Complete Workflow Example
cmd
:: 1. Login as employer
curl -X POST http://localhost:8000/api/auth/login/ -H "Content-Type: application/json" -d "{\"username\":\"techcorp\",\"password\":\"testpass123\"}"
:: Copy access token

:: 2. Set token
set TOKEN=eyJhbGciOiJIUzI1NiIs...

:: 3. Create job
curl -X POST http://localhost:8000/api/jobs/ -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "{\"title\":\"Developer\",\"description\":\"Job description\",\"requirements\":\"Skills required\",\"location\":\"Remote\",\"employment_type\":\"full\",\"expires_at\":\"2025-12-31T23:59:59Z\"}"


