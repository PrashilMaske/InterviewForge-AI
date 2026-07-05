# UI/UX Specifications & Wireframes - InterviewForge AI

This document defines the user interface design standards, premium dark mode glassmorphism styles, color palettes, typography, and wireframe structures for the InterviewForge AI platform.

---

## 1. Design Token System

To create a premium SaaS aesthetic, we define a unified style sheet framework using vanilla CSS variables.

### Color Palette (Premium Dark/Glow Theme)
```css
:root {
  --bg-main: #0b0f19;         /* Very dark navy */
  --bg-glass: rgba(17, 24, 39, 0.65); /* Translucent dark slate */
  --border-glass: rgba(255, 255, 255, 0.08);
  --accent-primary: #6366f1;   /* Indigo */
  --accent-secondary: #a855f7; /* Purple */
  --accent-glow: rgba(99, 102, 241, 0.15);
  
  --text-main: #f3f4f6;       /* Near white */
  --text-muted: #9ca3af;      /* Cool gray */
  --text-green: #34d399;      /* Mint success */
  --text-red: #f87171;        /* Soft error */
}
```

### Aesthetic Properties
* **Glassmorphism Base**:
  `backdrop-filter: blur(16px); background: var(--bg-glass); border: 1px solid var(--border-glass);`
* **Radial Background Glows**:
  Vibrant background layout achieved using custom circular gradients placed behind screens.
* **Typography**:
  Use `Inter` or `Outfit` from Google Fonts to convey state-of-the-art engineering.
* **Skeletal Animation**:
  Custom CSS keyframe sweeps (`shimmer`) to represent AI background tasks loading.

---

## 2. Page Layouts & Wireframes

### A. Landing Page (`templates/index.html`)
A high-converting product showcase page.
* **Header**: Logo, navigation links (Dashboard, Docs), "Get Started" call-to-action (CTA).
* **Hero Section**:
  * Title: "Forge Your Interview Readiness with AI" (gradient typography text).
  * Sub-headline: "Parse resumes, analyze ATS gaps, and conduct adaptive technical drills styled after top firms."
  * Action Cards: Upload Resume CTA button, Start Mock Interview CTA button.
* **Interactive Feature Showcase**:
  * Hovering over feature cards triggers a smooth scale translation and a subtle glow border transition.

### B. Dashboard Page (`templates/dashboard.html`)
The candidate core portal containing progress charts and resume version list.
* **Layout Grid**:
  ```text
  +---------------------------------------------------------+
  |                   Global Glass Header                   |
  +--------------------+------------------------------------+
  |  Metrics Row       | Resume Score [84%] | Streak [5 days]|
  +--------------------+------------------------------------+
  |                    |                                    |
  |  Left: Analytics   |  Right: Quick Tools & Actions      |
  |  [Chart.js Graph]  |  [Upload New Resume File]          |
  |  (Performance Growth)|  [Compare Job Description (JD)]   |
  |                    |                                    |
  +--------------------+------------------------------------+
  |  Bottom Row: Resume Version History & Interview Records |
  +---------------------------------------------------------+
  ```
* **Interactive Elements**:
  * Hovering on a resume version displays an "Analyze ATS" and "Compare JD" options popup.

### C. Resume & JD Upload Page (`templates/upload.html`)
* **Layout**:
  * Two glassmorphic split cards. Left: "Resume Versioning Upload" (PDF/DOCX dropzone). Right: "Job Description Matcher" (Input text area or PDF/DOCX file uploader).
* **States**:
  * Drag & Drop visual state transition (border color turns to `--accent-primary` on hover).
  * Uploading state replaces container content with a looping skeleton spinner.

### D. Interview Arena (`templates/arena.html`)
The main mock-interview workspace resembling an editor or diagnostic workspace.
* **Layout Split-Pane Grid**:
  * **Left Panel (Mock Interview Workspace)**:
    * Displays active question text (e.g., "Question 3 of 5").
    * Textarea for typing candidate responses.
    * Control buttons: "Submit Answer" (with countdown response-time clock) and "Quit Session".
  * **Right Panel (Live AI Evaluation Feed)**:
    * When no question is submitted, displays a subtle glassmorphic layout: *"Awaiting candidate answer..."*.
    * Once submitted, shows score gauges, list of Strengths & Weaknesses, Missing Key Concepts, and expandable Ideal Answer card.

### E. Learning Roadmap Page (`templates/roadmap.html`)
* **Layout**:
  * A central vertical timeline thread.
  * Every roadmap week is rendered inside a glassmorphic block:
    * Week Header: e.g. "Week 1: Advanced Caching" (Status: In Progress / Complete).
    * Week Details: Sub-lessons lists, exercises to code, and target resources links.
  * Progress updates instantly when candidate marks a week complete.
