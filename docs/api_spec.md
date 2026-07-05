# REST API Specification - InterviewForge AI

This document specifies the REST API endpoints, request payloads, response payloads, status codes, and communication logic for the InterviewForge AI platform.

---

## 1. Authentication Endpoints

### Register User
* **Endpoint**: `POST /api/auth/register/`
* **Request Header**: `Content-Type: application/json`
* **Request Body**:
  ```json
  {
    "email": "candidate@example.com",
    "username": "candidate_dev",
    "password": "StrongPassword123!",
    "role": "candidate"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "id": "e229f345-0d32-4752-b883-7c9b2a7590fe",
    "email": "candidate@example.com",
    "username": "candidate_dev",
    "role": "candidate",
    "message": "Registration successful. Please verify your email address."
  }
  ```
* **Errors**:
  * `400 Bad Request`: Email/Username already exists or password too weak.

### Login (Session Start)
* **Endpoint**: `POST /api/auth/login/`
* **Request Body**:
  ```json
  {
    "username": "candidate_dev",
    "password": "StrongPassword123!"
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "status": "success",
    "username": "candidate_dev",
    "role": "candidate",
    "session_active": true
  }
  ```
* **Headers**: Sets Django session cookies and CSRF token.

---

## 2. Resume & Job Description Endpoints

### Upload Resume
* **Endpoint**: `POST /api/resumes/`
* **Request Header**: `Content-Type: multipart/form-data`
* **Request Body**:
  * `file`: (Binary PDF/DOCX file, max 5MB)
* **Success Response (201 Created)**:
  ```json
  {
    "id": "76fa968e-908d-4f10-ae3d-71b539b6be2d",
    "file_url": "https://res.cloudinary.com/interviewforge/image/upload/v12345/resume_1.pdf",
    "file_name": "resume_1.pdf",
    "version": 1,
    "created_at": "2026-07-05T14:46:00Z",
    "analysis_status": "pending"
  }
  ```

### Retrieve Resume Audit Analysis
* **Endpoint**: `GET /api/resumes/<resume_id>/analysis/`
* **Success Response (200 OK - Processing Complete)**:
  ```json
  {
    "resume_id": "76fa968e-908d-4f10-ae3d-71b539b6be2d",
    "overall_score": 84,
    "scores": {
      "formatting": 19,
      "projects": 15,
      "skills": 18,
      "ats": 17,
      "grammar": 8,
      "achievements": 7,
      "keywords": 0
    },
    "explanations": {
      "formatting": "Excellent use of consistent typography, bullet points, and headers.",
      "keywords": "Lacks specific tool keywords expected for mid-level backend roles like Docker and Redis."
    },
    "improved_bullets": [
      {
        "original": "Worked on the Django app writing databases.",
        "improved": "Refactored PostgreSQL database schemas and optimized queries in Django REST modules, reducing API latency by 34%."
      }
    ]
  }
  ```
* **Success Response (202 Accepted - Still Analyzing)**:
  ```json
  {
    "resume_id": "76fa968e-908d-4f10-ae3d-71b539b6be2d",
    "status": "processing",
    "message": "AI Resume Analyzer task is currently running in the background."
  }
  ```

### Compare Job Description (JD Match)
* **Endpoint**: `POST /api/resumes/<resume_id>/compare-jd/`
* **Request Body**:
  * `title`: "Senior Python Developer"
  * `jd_text`: "We are looking for a Senior Developer with experience in AWS, Docker, CI/CD, and Redis..."
* **Success Response (200 OK)**:
  ```json
  {
    "match_score": 78,
    "missing_skills": ["Docker", "Redis", "AWS", "CI/CD"],
    "suggested_improvements": "Add Docker containers deployments in your portfolio descriptions.",
    "missing_keywords": ["Docker", "AWS", "Kubernetes"],
    "projects_to_build": [
      {
        "title": "Containerized Microservices Cluster",
        "description": "Deploy a multi-container Django/PostgreSQL stack using Docker Compose with Redis caching."
      }
    ],
    "certifications_to_learn": ["AWS Certified Developer - Associate"]
  }
  ```

---

## 3. Mock Interview Engine Endpoints

### Start Mock Session
* **Endpoint**: `POST /api/interviews/start/`
* **Request Body**:
  ```json
  {
    "resume_id": "76fa968e-908d-4f10-ae3d-71b539b6be2d",
    "jd_id": "8bfa2e1a-115f-4a0b-9df0-c8f9ee0b3e5a",
    "interview_type": "Django & Backend",
    "difficulty": "adaptive"
  }
  ```
* **Success Response (201 Created)**:
  ```json
  {
    "session_id": "a9a8341b-4f4d-44aa-9c12-32a2f8b5490a",
    "status": "active",
    "current_difficulty": 5,
    "total_questions_asked": 0
  }
  ```

### Get Next Question
* **Endpoint**: `GET /api/interviews/<session_id>/next-question/`
* **Success Response (200 OK)**:
  ```json
  {
    "question_id": "df2b3a98-16e0-40e1-bb17-8e6d87e07a3c",
    "question_text": "In your resume, you mention building dynamic models. How do you handle database connection pools and caching with Redis in Django for high traffic sites?",
    "difficulty_level": 6,
    "elapsed_seconds": 0
  }
  ```
* **Success Response (200 OK - Max questions reached)**:
  ```json
  {
    "session_id": "a9a8341b-4f4d-44aa-9c12-32a2f8b5490a",
    "status": "completed",
    "message": "All interview rounds completed. Generating PDF reports."
  }
  ```

### Submit Answer and Get Instant Grading
* **Endpoint**: `POST /api/interviews/<session_id>/submit-answer/`
* **Request Body**:
  ```json
  {
    "question_id": "df2b3a98-16e0-40e1-bb17-8e6d87e07a3c",
    "answer_text": "I set up connection pools by using django-redis backend config. We configure django caches backend, and then save models using keys. For connection pooling, we adjust CONN_MAX_AGE.",
    "response_time_seconds": 85
  }
  ```
* **Success Response (200 OK)**:
  ```json
  {
    "answer_id": "40fb3a88-29cb-4c54-bbf5-5e648be389ef",
    "scores": {
      "overall": 8.0,
      "technical": 8,
      "communication": 9,
      "confidence": 8,
      "depth": 7
    },
    "strengths": ["Clear understanding of Django settings and CONN_MAX_AGE caching configuration."],
    "weaknesses": ["Missed detailing transactional isolation when using pools."],
    "missing_concepts": ["JWT Refresh Tokens", "Redis Cache eviction policies"],
    "ideal_answer": "To implement Redis caching, configure the django-redis backend in settings.py...",
    "next_difficulty_level": 7
  }
  ```

---

## 4. Report & Analytics Endpoints

### Get Final Report Status & Data
* **Endpoint**: `GET /api/interviews/<session_id>/report/`
* **Success Response (200 OK)**:
  ```json
  {
    "session_id": "a9a8341b-4f4d-44aa-9c12-32a2f8b5490a",
    "pdf_url": "https://res.cloudinary.com/interviewforge/raw/upload/v123/report.pdf",
    "readiness_score": 82,
    "strengths": ["Object-Oriented Programming", "REST APIs"],
    "weaknesses": ["System design scale", "Redis caching patterns"],
    "timeline": [
      {"round": 1, "score": 6.5},
      {"round": 2, "score": 8.0},
      {"round": 3, "score": 9.2}
    ],
    "learning_plan_weeks": [
      {
        "week": 1,
        "topic": "Advanced Redis Caching & Connection Pools",
        "lessons": ["Django Cache framework configurations", "CONN_MAX_AGE deep-dive"],
        "estimated_hours": 6
      }
    ]
  }
  ```

### Dashboard Analytics Metrics
* **Endpoint**: `GET /api/analytics/dashboard/`
* **Success Response (200 OK)**:
  ```json
  {
    "resume_score": 84,
    "interview_score": 7.8,
    "average_performance": 81.5,
    "interview_streak": 5,
    "skill_progress": {
      "Django": 85,
      "Python": 90,
      "Redis": 40,
      "System Design": 55
    },
    "weak_skills": ["Redis", "System Design"],
    "strong_skills": ["Python", "Django"],
    "upcoming_recommendations": [
      "Review Redis caching structures",
      "Upload improved version of resume 1"
    ],
    "chart_datasets": {
      "resume_growth": [
        {"version": 1, "date": "2026-06-01", "score": 68},
        {"version": 2, "date": "2026-07-05", "score": 84}
      ],
      "interview_accuracy": [
        {"date": "2026-06-15", "score": 6.8},
        {"date": "2026-07-01", "score": 7.8}
      ]
    }
  }
  ```
