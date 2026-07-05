# InterviewForge AI

InterviewForge AI is an AI-powered interview preparation platform. It parses and analyzes candidate resumes, compares them dynamically with job descriptions, conducts interactive adaptive mock interviews, grades technical/soft skill responses, generates automated improvement plans (learning roadmaps), and builds downloadable PDF performance reports.

---

## Key Features

1. **AI Resume Auditor & ATS Optimizer**: Evaluates resumes on ATS compatibility, formatting, grammar, key sections (skills, projects, experience, accomplishments), scores them out of 100, and rewrites bullets to use action verbs.
2. **Dynamic Job Description Matcher**: Compares a resume against a JD to output a match percentage, identifies missing skills/keywords, and recommends certifications or projects.
3. **Adaptive Mock Interview Arena**: Runs interactive interviews that scale in difficulty based on response quality. Uses candidate background and target JD to formulate contextual follow-up questions.
4. **Comprehensive Response Grading**: Grades answers across Technical Accuracy, Communication, Confidence, Depth, and Completeness, providing strengths, weaknesses, and a structured "ideal answer".
5. **Personalized Roadmaps & Progress Analytics**: Custom weekly learning plans addressing skill gaps, tracked via a glassmorphic analytics dashboard with interactive Chart.js growth visuals.
6. **PDF Report Exports**: Downloadable PDF sheets compiling interview logs, grading breakdown, and target exercises.

---

## Technology Stack

* **Backend Framework**: Django 5.x & Django REST Framework (DRF)
* **Database**: PostgreSQL (with proper indexing on user and session foreign keys)
* **AI Model Service**: Groq API + Llama 3.3 70B (`llama-3.3-70b-versatile`)
* **Background Processing**: Django Q2 (using the Django database ORM as a broker for easy deployment)
* **Resume/Doc Extraction**: PyMuPDF (`fitz`), `python-docx`, and `spaCy`
* **PDF Report Generation**: ReportLab
* **File Storage**: Cloudinary (for resumes and PDF reports)
* **Frontend**: HTML5, Vanilla CSS3 (Custom Dark Mode & Glassmorphism design system), Vanilla ES6 JavaScript, and Chart.js

---

## Directory Structure

```text
interview_forge/
├── core/                   # Project configurations and settings
├── users/                  # Custom User model, Session auth, Registration views
├── resumes/                # Uploads, versions, parsing, spaCy tools, and JD comparison
├── interviews/             # Mock interview flows, adaptive grading, PDF reports, AI clients
├── analytics/              # Dashboard metrics, streak calculators, Chart.js views
├── templates/              # High-level HTML templates (Landing, Dashboard, Interview, Roadmap)
│   ├── base.html           # Main base layout with glassmorphic shell
│   ├── index.html          # Landing page
│   ├── dashboard.html      # Main dashboard with charts
│   ├── upload.html         # Resume & JD upload forms
│   ├── arena.html          # Active mock interview arena (asynchronous JS)
│   ├── roadmap.html        # Personalized learning roadmap timeline
│   └── report_detail.html  # Interview feedback and report download page
├── static/                 # Static assets
│   ├── css/
│   │   └── style.css       # Custom high-level glassmorphism, fonts, and dark mode UI
│   └── js/
│       ├── main.js         # API handlers, interview loops, UI transitions
│       └── charts.js       # Chart.js graphs mapping progress
└── docs/                   # Detailed architectural & specification documents
    ├── architecture.md     # Software Architecture Design
    ├── database_schema.md  # Database Schema & PostgreSQL Specs
    ├── api_spec.md         # API Endpoint Specifications
    ├── prompt_architecture.md # AI Prompt Architectures & JSON structures
    ├── ui_wireframes.md    # UI/UX wireframes & design templates
    ├── deployment_guide.md # Deployment manual for Render
    ├── testing_strategy.md # Automated and manual test guides
    └── future_roadmap.md   # Long-term feature expansions
```

---

## Local Setup & Installation

### Prerequisites
* Python 3.10 or higher
* PostgreSQL installed and running
* A Groq API Key
* A Cloudinary account (optional for local mock files, required for production)

### Setup Steps
1. **Clone and navigate to the directory**:
   ```bash
   cd "AI Interview Bot"
   ```

2. **Set up Virtual Environment**:
   ```bash
   python -m venv venv
   .\venv\Scripts\activate
   ```

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   python -m spacy download en_core_web_sm
   ```

4. **Environment Variables**:
   Create a `.env` file in the root folder with the following variables:
   ```env
   SECRET_KEY=your_django_secret_key
   DEBUG=True
   DATABASE_URL=postgres://username:password@localhost:5432/interview_forge
   GROQ_API_KEY=your_groq_api_key
   CLOUDINARY_URL=cloudinary://api_key:api_secret@cloud_name
   ```

5. **Migrations & Database Setup**:
   Ensure PostgreSQL is running and database `interview_forge` is created.
   ```bash
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Run Development Server**:
   ```bash
   python manage.py runserver
   ```
   Open your browser to `http://127.0.0.1:8000/`.

---

## Design and Development Standards

* **Aesthetics**: Every page implements a custom glassmorphism design (`backdrop-filter: blur()`), vibrant radial gradient backgrounds, professional slate/indigo/violet accents, and clear skeletal state loading animations.
* **Modularity**: Separation of concerns is enforced between views (rendering templates), REST viewsets (providing serialized JSON endpoints), and AI services (isolated prompt clients).
* **Robustness**: Validation on all uploads (size limit 5MB, format restriction to `.pdf`, `.docx`, `.txt`) and automated input cleaning.
