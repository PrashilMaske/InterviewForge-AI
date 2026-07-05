import json
import logging
from resumes.ai_services import GroqLLMClient

logger = logging.getLogger(__name__)

class QuestionGenerator(GroqLLMClient):
    """Generates the next interview question based on resume, JD, history, and difficulty level."""
    
    SYSTEM_PROMPT = """
    You are an expert interviewer.
    Generate the next question based on:
    1. Candidate Resume
    2. Job Description (if available)
    3. Running Interview History (Questions already asked, Candidate Answers, and Scores)
    4. Target difficulty level (1-10 scale).

    Rules:
    - Do not ask random questions. Build upon the candidate's projects or previous technical responses.
    - Formulate the question in a conversational technical tone.
    - Return JSON containing the question text and a list of key concepts the candidate should address.
    """

    def generate_question(self, resume_text, jd_text, history_list, difficulty_level):
        import random
        # Inject a random topic seed on Round 1 to ensure starting questions are diverse
        topics = [
            "database query optimization and index design",
            "caching strategies, cache invalidation, and Redis key layouts",
            "RESTful API design, HTTP status codes, and middleware routing",
            "concurrency, threads, lock management, and asynchronous workers",
            "API authentication, OAuth, JWT, and header security",
            "unit testing, dependency mocking, and test coverage practices",
            "CI/CD deployment pipelines, Docker containerization, and orchestration",
            "data serialization, validation, and JSON encoding/decoding performance",
            "system bottleneck profiling, horizontal scaling, and load balancers"
        ]
        focus_topic = random.choice(topics) if not history_list else ""

        user_content = {
            "resume_text": resume_text,
            "job_description_text": jd_text,
            "history": history_list,
            "target_difficulty": difficulty_level,
            "starting_topic_focus_seed": focus_topic
        }
        
        result = self.get_structured_completion(self.SYSTEM_PROMPT, json.dumps(user_content), temperature=0.7)
        if result:
            normalized = {}
            normalized["question_text"] = (
                result.get("question_text") or 
                result.get("question") or 
                result.get("text") or 
                "Explain your experience with Python backend development."
            )
            concepts = (
                result.get("expected_key_concepts") or 
                result.get("key_concepts") or 
                result.get("expected_concepts") or 
                result.get("concepts") or 
                ["architecture", "scalability", "testing"]
            )
            if isinstance(concepts, str):
                concepts = [c.strip() for c in concepts.split(',') if c.strip()]
            normalized["expected_key_concepts"] = concepts
            
            try:
                diff_val = result.get("difficulty_level") or result.get("difficulty") or difficulty_level
                normalized["difficulty_level"] = int(float(diff_val))
            except Exception:
                normalized["difficulty_level"] = difficulty_level
                
            return normalized

        # Mock fallback question selection based on target difficulty
        questions = {
            "easy": [
                {
                    "question_text": "What is the difference between a list and a tuple in Python, and when would you use a tuple?",
                    "difficulty_level": 3,
                    "expected_key_concepts": ["Mutability", "Memory footprint", "Hashability"]
                },
                {
                    "question_text": "How do Django views interact with templates to display variables to a browser?",
                    "difficulty_level": 3,
                    "expected_key_concepts": ["Context dictionaries", "HttpResponse", "Render function"]
                }
            ],
            "medium": [
                {
                    "question_text": "How does Django handle database transactions? Explain transaction.atomic decorator usage.",
                    "difficulty_level": 6,
                    "expected_key_concepts": ["Atomicity", "Savepoints", "rollback on exceptions"]
                },
                {
                    "question_text": "Explain how you would write a custom Django Middleware to track API response durations.",
                    "difficulty_level": 6,
                    "expected_key_concepts": ["__call__ handler", "process_request", "middleware stacking order"]
                }
            ],
            "hard": [
                {
                    "question_text": "Explain connection pooling in Django. What are the advantages of CONN_MAX_AGE and how does it compare to using a proxy pooler like PgBouncer?",
                    "difficulty_level": 8,
                    "expected_key_concepts": ["Keepalive connections", "Row locking", "PgBouncer session pooling"]
                },
                {
                    "question_text": "How would you architect a caching strategy using Redis in a Django application that handles high-traffic, real-time read and write peaks?",
                    "difficulty_level": 8,
                    "expected_key_concepts": ["Write-through cache", "Cache stampede prevention", "Key eviction policies"]
                }
            ]
        }
        
        level = "easy"
        if difficulty_level >= 7:
            level = "hard"
        elif difficulty_level >= 4:
            level = "medium"
            
        import random
        return random.choice(questions[level])


class AnswerEvaluator(GroqLLMClient):
    """Scores responses across technical, communication, confidence, and depth matrices."""
    
    SYSTEM_PROMPT = """
    You are a Senior Engineer grading a candidate's response.
    Provide an honest, objective grading across Technical Accuracy, Communication, Confidence, and Depth.
    If the candidate answers with gibberish, greetings, or off-topic responses, score them accordingly (e.g., 0-2 out of 10).
    
    You must return a JSON object with the following exact keys:
    {
      "overall_score": <float, average of sub-scores out of 10.0>,
      "scores": {
        "technical": <int, 0-10>,
        "communication": <int, 0-10>,
        "confidence": <int, 0-10>,
        "depth": <int, 0-10>
      },
      "strengths": [<string>],
      "weaknesses": [<string>],
      "missing_concepts": [<string>],
      "ideal_answer": <string>,
      "suggestions": [<string>]
    }
    """

    def evaluate_answer(self, question_text, answer_text, expected_concepts):
        user_content = {
            "question": question_text,
            "answer": answer_text,
            "expected_concepts": expected_concepts
        }
        
        result = self.get_structured_completion(self.SYSTEM_PROMPT, json.dumps(user_content))
        if result:
            normalized = {}
            
            # --- Extract score values defensively ---
            scores_dict = result.get("scores") or result.get("grade") or result.get("grades") or {}
            
            def extract_score(key_options, default_val):
                for k in key_options:
                    val = scores_dict.get(k)
                    if val is not None:
                        try:
                            return int(float(val))
                        except Exception:
                            pass
                    val = result.get(k)
                    if val is not None:
                        try:
                            return int(float(val))
                        except Exception:
                            pass
                return default_val

            tech = extract_score(["technical", "technical_score", "Technical Accuracy", "Technical"], 7)
            comm = extract_score(["communication", "communication_score", "Communication", "communication_accuracy"], 8)
            conf = extract_score(["confidence", "confidence_score", "Confidence"], 8)
            depth = extract_score(["depth", "depth_score", "Depth"], 7)
            
            normalized["scores"] = {
                "technical": tech,
                "communication": comm,
                "confidence": conf,
                "depth": depth
            }
            
            # Overall Score: calculate as average of sub-scores if not explicitly provided
            overall = result.get("overall_score") or result.get("score") or result.get("overall")
            if overall is not None:
                try:
                    normalized["overall_score"] = float(overall)
                except Exception:
                    normalized["overall_score"] = round((tech + comm + conf + depth) / 4.0, 2)
            else:
                normalized["overall_score"] = round((tech + comm + conf + depth) / 4.0, 2)

            # Strengths
            strengths = result.get("strengths") or result.get("strength")
            if not strengths:
                strengths = ["Excellent articulation of concepts." if normalized["overall_score"] >= 8.5 else "Good effort."]
            elif isinstance(strengths, str):
                strengths = [s.strip() for s in strengths.split(",") if s.strip()]
            normalized["strengths"] = strengths
            
            # Weaknesses
            weaknesses = result.get("weaknesses") or result.get("weakness")
            if not weaknesses:
                weaknesses = ["Incomplete technical explanation." if normalized["overall_score"] < 7.0 else "Expand your explanation further."]
            elif isinstance(weaknesses, str):
                weaknesses = [w.strip() for w in weaknesses.split(",") if w.strip()]
            normalized["weaknesses"] = weaknesses

            # Missing Concepts
            missing = result.get("missing_concepts") or result.get("missing_key_concepts") or result.get("missing")
            if not missing:
                missing = []
            elif isinstance(missing, str):
                missing = [m.strip() for m in missing.split(",") if m.strip()]
            normalized["missing_concepts"] = missing
            
            # Ideal Answer
            normalized["ideal_answer"] = result.get("ideal_answer") or result.get("ideal") or "No ideal answer generated."
            
            # Suggestions
            suggestions = result.get("suggestions") or result.get("actionable_suggestions") or result.get("actionable")
            if not suggestions:
                suggestions = ["Practice more standard coding drills."]
            elif isinstance(suggestions, str):
                suggestions = [s.strip() for s in suggestions.split(",") if s.strip()]
            normalized["suggestions"] = suggestions

            return normalized

        # Mock fallback evaluation
        return {
            "overall_score": 7.5,
            "scores": {
                "technical": 7,
                "communication": 8,
                "confidence": 8,
                "depth": 7
            },
            "strengths": [
                "Clearly explains mutability differences.",
                "Demonstrates practical coding knowledge."
            ],
            "weaknesses": [
                "Could expand on hashability and dictionary index operations."
            ],
            "missing_concepts": [
                "Tuple hashability",
                "dictionary keys mutability restriction"
            ],
            "ideal_answer": "Lists are mutable, while tuples are immutable. Because of immutability, tuples are hashable and can serve as dictionary keys, and they consume less memory allocations.",
            "suggestions": [
                "Review the official Python dictionary key guidelines."
            ]
        }


class LearningCoach(GroqLLMClient):
    """Constructs a customized week-by-week learning roadmap addressing key weaknesses."""
    
    SYSTEM_PROMPT = """
    You are an expert Technical Coach. Based on the candidate's performance across the mock interview sessions, construct a weekly learning timeline (roadmaps).
    Provide structured milestones, learning goals, resources, and custom exercises.
    Return JSON only.
    """

    def generate_roadmap(self, performance_summary):
        result = self.get_structured_completion(self.SYSTEM_PROMPT, json.dumps(performance_summary))
        if result:
            normalized = {}
            try:
                normalized["total_weeks"] = int(result.get("total_weeks") or 4)
            except Exception:
                normalized["total_weeks"] = 4
            normalized["weeks"] = result.get("weeks") or []
            return normalized

        # Mock fallback roadmap
        return {
            "total_weeks": 4,
            "weeks": [
                {
                    "week": 1,
                    "topic": "Python Core Mutability & Data Structures",
                    "lessons": [
                        "Deep copy vs. shallow copy structures",
                        "Tuple memory storage and hash lookup pools"
                    ],
                    "suggested_exercises": [
                        "Create a dictionary using tuples as complex indexing elements."
                    ],
                    "estimated_hours": 4
                },
                {
                    "week": 2,
                    "topic": "Advanced Django Database Transactions",
                    "lessons": [
                        "Atomic blocks and database exception propagation",
                        "Dealing with race conditions in Django ORM"
                    ],
                    "suggested_exercises": [
                        "Write a mock transaction api that rolls back bank funds transfer on failure."
                    ],
                    "estimated_hours": 6
                },
                {
                    "week": 3,
                    "topic": "Caching Configurations with Redis",
                    "lessons": [
                        "Django caches configs and Redis storage drivers",
                        "Key evictions and cache invalidation policies"
                    ],
                    "suggested_exercises": [
                        "Deploy a Docker redis service and hook it to a Django cache manager."
                    ],
                    "estimated_hours": 6
                },
                {
                    "week": 4,
                    "topic": "System Scale & Connection Pooling",
                    "lessons": [
                        "CONN_MAX_AGE settings and PgBouncer deployment",
                        "Rate-limiting architectures and token-buckets"
                    ],
                    "suggested_exercises": [
                        "Configure a PgBouncer local container connecting to PostgreSQL."
                    ],
                    "estimated_hours": 8
                }
            ]
        }
