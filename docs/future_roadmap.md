# Future Product Roadmap - InterviewForge AI

This document outlines future product phases, architectural extensions, and premium features planned for InterviewForge AI.

---

## Phase 6: Voice & Video Sentiment Analysis (Q1 2027)

### Goal
Provide real-time speech and behavioral diagnostics to score body language, speech pacing, eye contact, and confidence levels.

### Architecture Plan
* **Audio Analysis (Speech-to-Text & Pacing)**:
  * Capture audio streams using browser WebRTC APIs.
  * Transcribe via Groq Whisper API endpoints.
  * Compute words-per-minute (WPM) and detect filler words ("like", "uh", "um") using customized regex analyzers.
* **Video sentiment analysis**:
  * Utilize lightweight models like FaceMesh/MediaPipe in-browser to trace facial expressions and posture.
  * Identify candidate distraction indices (measuring screen-off attention levels during questions).

---

## Phase 7: Recruiter & Portal Management Systems (Q2 2027)

### Goal
Allow recruiters and hiring managers to configure candidate screenings, view scoreboards, and compare applicants.

```text
+-------------------+       +-----------------------+       +-------------------+
|  Recruiter Panel  |------>| Public Mock Job Posts |------>| Candidate invites |
+-------------------+       +-----------------------+       +-------------------+
          |                                                           |
          +-------------------- [ View detailed PDF & Analytics ] <---+
```

### Key Integrations
* **Public Screening Hub**: Recruiters post specific JDs and generate unique screening link invitations.
* **Consolidated Dashboards**: Employers scan aggregated candidate scores, ATS grades, and mock interview transcripts.
* **Auto-Shortlisting**: Rank applicants based on match scores and technical grades.

---

## Phase 8: Mock Coding Sandbox Integration (Q3 2027)

### Goal
Incorporate LeetCode-style code compilers inside mock interviews to create full technical screenings.

### Proposed Architecture
* **Sandboxed Code Execution**:
  * Build a secure Docker container environment (e.g. using Judge0 or custom gRPC runtimes) to compile and test code blocks.
  * Supported languages: Python, JavaScript, Java, Go.
* **Dynamic Code Evaluation**:
  * The AI Interview engine dynamically writes simple test asserts on-the-fly based on selected challenges, validating candidate logic against edge cases in real-time.
* **Split Workspace Interface**:
  * Interactive terminal canvas displayed adjacent to the conversational video box.
