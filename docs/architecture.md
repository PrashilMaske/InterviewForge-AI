# Software Architecture - InterviewForge AI

This document details the software architecture, data flows, components, and design decisions of the InterviewForge AI platform.

---

## 1. High-Level Architecture Overview

InterviewForge AI follows a service-oriented Monolith architecture, where Django serves as both the MVC web controller (routing page requests to server-side templates) and the API provider (handling async queries from Javascript).

```mermaid
graph TB
    subgraph Clients
        Browser[HTML5 / CSS / Vanilla JS App]
    end

    subgraph Backend [Django Web Application]
        Views[Django Template Controller]
        DRF[Django REST APIs]
        Middleware[Auth, Rate Limiters, Sanitizers]
        
        subgraph Services
            ResumeService[Resume Parser & Analyzer]
            MatchService[JD Match Engine]
            InterviewEngine[Adaptive Interview Manager]
            RoadmapService[Learning Coach]
            ReportService[ReportLab PDF Engine]
        end
    end

    subgraph Data & Storage
        DB[(PostgreSQL Database)]
        CloudStore[(Cloudinary CDN)]
    end

    subgraph External
        Groq[Groq API - Llama 3.3 70B]
    end

    Browser -->|GET html pages| Views
    Browser -->|AJAX JSON APIs| DRF
    DRF --> Middleware
    Views --> DB
    DRF --> Services
    
    ResumeService -->|Extract Text| PyMuPDF[PyMuPDF / Docx]
    ResumeService -->|NLP| Spacy[spaCy Engine]
    
    Services -->|Asynchronous tasks| Q2[Django Q2 Task Worker]
    Q2 --> DB
    
    Services -->|Prompt Pipeline| Groq
    ReportService -->|Store PDF| CloudStore
    ResumeService -->|Upload Resumes| CloudStore
    DB --- Services
```

---

## 2. Component Design & Responsibilities

### Frontend Layer (Web UI)
* **HTML5 Templates**: Renders clean semantic templates utilizing server-side variables (Django context).
* **Vanilla CSS (style.css)**: Centralizes style tokens, premium glassmorphism layouts, custom dark theme, hover glows, cards, timelines, and fluid animations.
* **Vanilla JavaScript (main.js & charts.js)**: 
  * Controls page transitions, form submissions, and loading skeletons.
  * Handles audio/text interactive state in the **Interview Arena** via fetch API calls.
  * Draws user progress charts dynamically using **Chart.js**.

### Backend Core & API Gateway (Django)
* **Security & Auth**: Custom middleware manages CSRF verification, rate-limits endpoints (django-ratelimit), and filters input for prompt injections.
* **App-Specific Modules**:
  * `users`: Registers and logs in candidates and recruiters; computes streaks.
  * `resumes`: Parses docs and maintains version tracking and matching scores.
  * `interviews`: Directs mock sessions, maintains state, adjusts difficulty, and stores question logs.
  * `analytics`: Aggregates performance matrices and history maps.

### Background Task Runner (Django Q2)
* Handles heavy operations asynchronously to avoid blocking user threads:
  * Running Groq API analysis on freshly uploaded resumes.
  * Comparing resumes with large JDs.
  * Building detailed PDF reports via ReportLab and syncing with Cloudinary.

### AI Engine (Groq & Llama 3.3 70B)
* Structured prompts execute queries against `Llama-3.3-70b-versatile` using JSON schema modes. Output formatting is strictly controlled on the backend, converting LLM text outputs to validated Python dictionaries.

---

## 3. Core System Data Flows

### A. Resume Analysis & Score Processing Flow
```mermaid
sequenceDiagram
    autonumber
    Candidate->>Browser: Uploads PDF/DOCX Resume
    Browser->>Django: POST /api/resumes/
    Django->>Cloudinary: Store file
    Cloudinary-->>Django: Return URL
    Django->>DB: Save Resume metadata (Version, File URL)
    Django->>Django Q2: Queue Asynchronous Analysis Task
    Django-->>Browser: HTTP 202 Accepted (Task Queued)
    
    rect rgb(20, 20, 35)
        Note over Django Q2, Groq: Asynchronous Execution
        Django Q2->>PyMuPDF: Read and extract text from PDF/DOCX
        PyMuPDF-->>Django Q2: Return raw text
        Django Q2->>spaCy: Extract basic entities (Names, Skills, Companies)
        Django Q2->>Groq: Query ResumeAnalyzer Service (Prompt + Text)
        Groq-->>Django Q2: Return JSON Score & Rewritten Bullets
        Django Q2->>DB: Write ResumeAnalysis record
    end

    Browser->>Django: GET /api/resumes/<id>/status/ (Polling)
    Django-->>Browser: Return Status (Completed / Analyzing)
```

### B. Adaptive Interview Loop
```mermaid
sequenceDiagram
    autonumber
    Candidate->>Browser: Start Interview (Select Type/Difficulty)
    Browser->>Django: POST /api/interviews/start/
    Django->>DB: Initialize InterviewSession (Difficulty 1-10)
    Django-->>Browser: Session ID created
    
    loop Dynamic Q&A Session (e.g., 5 rounds)
        Browser->>Django: GET /api/interviews/<session_id>/next-question/
        Django->>Groq: Generate adaptive question (Resume + JD + History)
        Groq-->>Django: Return Question Text + Expected Key Concepts
        Django->>DB: Create Question record
        Django-->>Browser: Return question to User
        
        Candidate->>Browser: Types or Speaks Answer
        Browser->>Django: POST /api/interviews/<session_id>/submit-answer/
        Django->>Groq: Evaluate Answer (Accuracy, Communication, Confidence, Depth)
        Groq-->>Django: Return Scores, Strengths, Weaknesses, Ideal Answer
        Django->>DB: Save Answer & Evaluation records
        Django->>Django: Update Session current_difficulty_level (Scale 1-10)
        Django-->>Browser: Return instant evaluation feedback
    end

    Browser->>Django: POST /api/interviews/<session_id>/terminate/
    Django->>Django Q2: Queue ReportLab PDF & Roadmap Tasks
```

---

## 4. Architectural Patterns

1. **MVC Pattern (Server-Side Rendering)**: Ensures speedy initial loads and search-engine visibility for candidate landing and public resources.
2. **AJAX API Bridge**: Uses asynchronous JavaScript client requests to keep mock interviews and matching states responsive without full page refreshes.
3. **Service Layer Isolation**: AI API code is isolated from models and views. The `ai_services.py` modules act as standalone utility classes that can be tested independently of the database.
4. **Idempotent Analysis**: Resume and JD analyses are saved in DB records linked by foreign key relationships. If the user requests a rematch, the DB checks for cached matching tables before calling external APIs.
5. **Stateful Session Store**: Mock interview histories, question logs, and candidate records are persisted cleanly, letting candidates pause and resume mock runs.
