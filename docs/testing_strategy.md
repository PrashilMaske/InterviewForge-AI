# Testing Strategy - InterviewForge AI

This document establishes the testing framework, methodologies, unit assertions, API mock patterns, and LLM verification protocols for InterviewForge AI.

---

## 1. Automated Testing Framework

We utilize `pytest` alongside `pytest-django` as our core test runner.

### Test Directory Layout
```text
tests/
├── __init__.py
├── conftest.py              # Pytest fixtures (DB user setups, file mocks)
├── test_auth.py             # User register, login, session validation tests
├── test_resumes.py          # Upload tests, text extraction verification
├── test_interviews.py       # Adaptive difficulty logic, submission grading
└── test_ai_mocks.py         # Mocked Groq client tests
```

---

## 2. Unit & Integration Testing Strategy

### A. Mocking Groq LLM Calls
To ensure tests run fast and don't consume API credits, we mock the Groq API handler:
```python
# tests/test_ai_mocks.py
import pytest
from unittest.mock import patch
from resumes.ai_services import ResumeAnalyzer

@pytest.mark.django_db
@patch("resumes.ai_services.Groq")
def test_resume_analysis_service(mock_groq_class):
    # Setup mock client behavior
    mock_client = mock_groq_class.return_value
    mock_client.chat.completions.create.return_value.choices[0].message.content = """
    {
      "overall_score": 85,
      "scores": {"formatting": 20, "projects": 15, "skills": 15, "ats": 15, "grammar": 10, "achievements": 5, "keywords": 5},
      "score_explanations": {"formatting": "Good layout."},
      "improved_bullet_points": [],
      "extracted_entities": {"name": "Test Candidate", "email": "test@example.com", "skills": ["Python"], "experience_years": 2.0}
    }
    """
    
    analyzer = ResumeAnalyzer()
    result = analyzer.analyze("Sample raw resume content")
    
    assert result["overall_score"] == 85
    assert "Test Candidate" in result["extracted_entities"]["name"]
```

### B. Adaptive Difficulty Calculation Test
Verifies that difficulty escalates or diminishes based on user grading scores:
```python
# tests/test_interviews.py
from interviews.utils import calculate_adaptive_difficulty

def test_adaptive_difficulty_escalation():
    # If the user scores average 8.5/10, increase difficulty
    current_difficulty = 5
    recent_scores = [8.0, 9.0]
    next_diff = calculate_adaptive_difficulty(current_difficulty, recent_scores)
    assert next_diff > current_difficulty

def test_adaptive_difficulty_deescalation():
    # If the user scores average 4.0/10, decrease difficulty
    current_difficulty = 5
    recent_scores = [3.0, 5.0]
    next_diff = calculate_adaptive_difficulty(current_difficulty, recent_scores)
    assert next_diff < current_difficulty
```

---

## 3. UI/UX and Asynchronous Integration Verification

We verify the client-side templates and asynchronous JavaScript flow using manual tests:
1. **Interactive File Loading**: Check that clicking the drag-and-drop area updates the loading indicators and starts background polling immediately.
2. **Chart.js Canvas Render**: Verify that historical dashboard values read from `/api/analytics/dashboard/` are successfully mapped to lines and bar graphs on index dashboards.
3. **Session Interactivity**: Simulate an interview mock session from start to finish:
   * Select a resume.
   * Start mock session.
   * Verify dynamic textarea focus and response submit handlers.
   * Verify feedback pops up in real-time.

---

## 4. LLM JSON Output Schema Validation

To prevent LLM format drifts or syntax errors from breaking backend parsers, we run schema validations on LLM outputs before storing them in PostgreSQL database tables:
```python
import json
from jsonschema import validate, ValidationError

RESUME_SCHEMA = {
    "type": "object",
    "properties": {
        "overall_score": {"type": "integer", "minimum": 0, "maximum": 100},
        "scores": {"type": "object"},
        "score_explanations": {"type": "object"},
        "improved_bullet_points": {"type": "array"}
    },
    "required": ["overall_score", "scores", "score_explanations", "improved_bullet_points"]
}

def validate_llm_json(response_content):
    try:
        data = json.loads(response_content)
        validate(instance=data, schema=RESUME_SCHEMA)
        return True, data
    except (json.JSONDecodeError, ValidationError) as e:
        return False, str(e)
```
If schema validation fails, the service retries the query once with an added instructions modifier: *"Ensure output fits the requested JSON schema structure exactly: [Schema Detail]"*.
