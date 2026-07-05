import os
import json
import requests
import logging

logger = logging.getLogger(__name__)

class GroqLLMClient:
    """Helper client to call Groq Chat API."""
    def __init__(self):
        self.api_key = os.getenv('GROQ_API_KEY')
        self.api_url = "https://api.groq.com/openai/v1/chat/completions"
        self.model = "llama-3.3-70b-versatile"

    def get_structured_completion(self, system_prompt, user_content, temperature=0.2):
        if not self.api_key or self.api_key == "your_groq_api_key":
            logger.warning("Groq API key not set. Using fallback mock mode.")
            return None

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ],
            "response_format": {"type": "json_object"},
            "temperature": temperature
        }

        try:
            response = requests.post(self.api_url, headers=headers, json=payload, timeout=30)
            if response.status_code == 200:
                response_data = response.json()
                content = response_data['choices'][0]['message']['content']
                return json.loads(content)
            else:
                logger.error(f"Groq API error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            logger.error(f"Exception during Groq API call: {e}")
            return None


class ResumeAnalyzer(GroqLLMClient):
    """Analyzes a resume against ATS, formatting, grammar, key sections, and gives suggestions."""
    
    SYSTEM_PROMPT = """
    You are an expert ATS (Applicant Tracking System) optimizer and professional resume writer.
    Analyze the candidate's resume and generate a detailed report.
    
    You must return a JSON object with the following exact keys and scoring ranges:
    {
      "overall_score": <int, 0-100 overall score>,
      "scores": {
        "formatting": <int, 0-20 score>,
        "projects": <int, 0-20 score>,
        "skills": <int, 0-20 score>,
        "ats": <int, 0-20 score>,
        "grammar": <int, 0-10 score>,
        "achievements": <int, 0-10 score>,
        "keywords": <int, 0-10 score>
      },
      "score_explanations": {
        "formatting": "<string, detailed formatting review>",
        "projects": "<string, detailed projects review>",
        "skills": "<string, detailed skills review>",
        "ats": "<string, detailed ATS compatibility review>",
        "grammar": "<string, detailed grammar review>",
        "achievements": "<string, detailed achievements review>",
        "keywords": "<string, detailed keywords review>"
      },
      "improved_bullet_points": [
        {
          "original": "<string, original weak bullet from resume>",
          "improved": "<string, rewritten action-oriented STAR bullet>",
          "reason": "<string, why this is stronger and how it optimizes keywords>"
        }
      ],
      "extracted_entities": {
        "name": "<string, candidate name>",
        "email": "<string, email>",
        "skills": [<string, list of detected skills>],
        "experience_years": <float, estimated years of experience>
      }
    }
    """

    def analyze(self, resume_text):
        user_content = f"Resume Text:\n\"\"\"\n{resume_text}\n\"\"\""
        
        result = self.get_structured_completion(self.SYSTEM_PROMPT, user_content)
        if result:
            normalized = {}
            
            # 1. overall_score (scale 0-100)
            overall = result.get("overall_score") or result.get("score") or 70
            try:
                val = float(overall)
                if val <= 10.0:
                    val = val * 10
                normalized["overall_score"] = int(val)
            except Exception:
                normalized["overall_score"] = 70
                
            # 2. scores dict (formatting/projects/skills/ats scale 0-20, grammar/achievements/keywords scale 0-10)
            scores = result.get("scores") or {}
            if not isinstance(scores, dict):
                scores = {}
                
            def get_cat_score(key_options, default_val, max_scale):
                for k in key_options:
                    # check in scores dict
                    val = scores.get(k)
                    if val is not None:
                        try:
                            v = float(val)
                            if max_scale == 20 and v <= 10.0:
                                v = v * 2
                            return int(v)
                        except Exception:
                            pass
                    # check in top level
                    val = result.get(k)
                    if val is not None:
                        try:
                            v = float(val)
                            if max_scale == 20 and v <= 10.0:
                                v = v * 2
                            return int(v)
                        except Exception:
                            pass
                return default_val

            normalized["scores"] = {
                "formatting": get_cat_score(["formatting", "formatting_score"], 15, 20),
                "projects": get_cat_score(["projects", "projects_score"], 14, 20),
                "skills": get_cat_score(["skills", "skills_score"], 15, 20),
                "ats": get_cat_score(["ats", "ats_score", "ats_compatibility", "ats_compatibility_score"], 14, 20),
                "grammar": get_cat_score(["grammar", "grammar_score"], 8, 10),
                "achievements": get_cat_score(["achievements", "achievements_score"], 6, 10),
                "keywords": get_cat_score(["keywords", "keywords_score"], 6, 10)
            }
            
            # 3. score_explanations (must be a dict)
            exp = result.get("score_explanations") or result.get("explanations") or result.get("explanation") or {}
            if isinstance(exp, dict) and exp:
                normalized["score_explanations"] = {
                    "formatting": exp.get("formatting") or result.get("formatting_advice") or "Good layout.",
                    "projects": exp.get("projects") or result.get("projects_advice") or "Detail outcomes.",
                    "skills": exp.get("skills") or result.get("skills_advice") or "Highlight modern libraries.",
                    "ats": exp.get("ats") or result.get("ats_compatibility_advice") or "Optimize keyword densities.",
                    "grammar": exp.get("grammar") or result.get("grammar_advice") or "Clear structure.",
                    "achievements": exp.get("achievements") or result.get("achievements_advice") or "Quantify your achievements.",
                    "keywords": exp.get("keywords") or result.get("keywords_advice") or "Use exact tech stack keywords."
                }
            else:
                normalized["score_explanations"] = {
                    "formatting": result.get("formatting_advice") or "Inconsistent layout, consider a standard clean single column format.",
                    "projects": result.get("projects_advice") or "Focus on quantifiable project milestones and backend scale architecture.",
                    "skills": result.get("skills_advice") or "Add primary infrastructure keys like Redis, Docker, or Postgres.",
                    "ats": result.get("ats_compatibility_advice") or "Format parsing is clean but keyword coverage is low.",
                    "grammar": result.get("grammar_advice") or "Excellent syntax, active voice dominates bullet points.",
                    "achievements": result.get("achievements_advice") or "Use STAR impact verbs: Spearheaded, Optimized, Scaled.",
                    "keywords": result.get("keywords_advice") or "Add precise domain keywords matching your target backend profiles."
                }
            
            # 4. improved_bullet_points (list of dicts)
            bullets = result.get("improved_bullet_points") or result.get("improved_bullets") or result.get("bullets") or []
            if not isinstance(bullets, list):
                bullets = []
            
            # If model returned rewritten_bullet_points as flat strings
            rewritten = result.get("rewritten_bullet_points") or result.get("rewritten_bullets") or []
            if rewritten and isinstance(rewritten, list) and not bullets:
                bullets = []
                for b in rewritten:
                    if isinstance(b, str):
                        bullets.append({
                            "original": "Standard experience bullet point from resume.",
                            "improved": b,
                            "reason": "Re-written with high-impact action verbs and STAR metrics focus."
                        })
                    elif isinstance(b, dict):
                        bullets.append({
                            "original": b.get("original") or "Original bullet point.",
                            "improved": b.get("improved") or b.get("rewritten") or "Optimized bullet.",
                            "reason": b.get("reason") or b.get("advice") or "Optimized formatting and keywords."
                        })
            
            if not bullets:
                bullets = [
                    {
                        "original": "Worked on backend bugs in Django app.",
                        "improved": "Resolved 45+ critical bottleneck bugs in Django modules, improving server stability and user response rates by 22%.",
                        "reason": "Uses action verb, targets key framework, and includes quantifiable improvement metrics."
                    }
                ]
            normalized["improved_bullet_points"] = bullets
            
            # 5. extracted_entities
            entities = result.get("extracted_entities") or result.get("entities") or result.get("profile") or {}
            if not isinstance(entities, dict):
                entities = {}
            normalized["extracted_entities"] = {
                "name": entities.get("name") or result.get("name") or "Candidate Name",
                "email": entities.get("email") or result.get("email") or "email@example.com",
                "skills": entities.get("skills") or result.get("skills") or ["Python", "Django", "JavaScript", "SQL"],
                "experience_years": entities.get("experience_years") or result.get("experience_years") or 2.0
            }
            
            return normalized

        # Mock fallback response for offline testing or when keys are missing
        return {
            "overall_score": 75,
            "scores": {
                "formatting": 15,
                "projects": 14,
                "skills": 16,
                "ats": 14,
                "grammar": 8,
                "achievements": 5,
                "keywords": 3
            },
            "score_explanations": {
                "formatting": "Decent layout but margins are inconsistent.",
                "projects": "Descriptions list duties instead of metrics achieved.",
                "skills": "Good programming list, but misses modern container tools.",
                "ats": "Tables and graphs might confuse standard parsers.",
                "grammar": "Strong overall, but minor voice changes identified.",
                "achievements": "No quantifiable revenue or developer velocity scores.",
                "keywords": "Lacking cloud words like AWS, Docker, and Redis."
            },
            "improved_bullet_points": [
                {
                    "original": "Worked on backend bugs in Django app.",
                    "improved": "Resolved 45+ critical bottleneck bugs in Django modules, improving server stability and user response rates by 22%.",
                    "reason": "Uses action verb, targets key framework, and includes quantifiable improvement metrics."
                }
            ],
            "extracted_entities": {
                "name": "Alex Candidate",
                "email": "alex.dev@example.com",
                "skills": ["Python", "Django", "JavaScript", "SQL"],
                "experience_years": 2.5
            }
        }


class JDMatcher(GroqLLMClient):
    """Matches a parsed resume against a job description to output scores and gap analyses."""
    
    SYSTEM_PROMPT = """
    You are a Senior Technical Recruiter. You will receive a candidate's parsed resume and a Job Description.
    Compute a Match Score out of 100. Identify missing skills, missing keywords, suggest structural modifications, recommend certifications, and propose 2 custom hands-on projects the user should build to patch key technology gaps.
    Return JSON only.
    """

    def match(self, resume_text, jd_text):
        user_content = f"Resume Text:\n\"\"\"\n{resume_text}\n\"\"\"\n\nJob Description:\n\"\"\"\n{jd_text}\n\"\"\""
        
        result = self.get_structured_completion(self.SYSTEM_PROMPT, user_content)
        if result:
            return result

        # Mock fallback response
        return {
            "match_score": 68,
            "missing_skills": ["Docker", "Redis", "AWS", "CI/CD"],
            "missing_keywords": ["Containerization", "Redis Cache", "GitHub Actions"],
            "suggested_improvements": "Add Docker container setups to your portfolio and specify Redis backend inside Django settings.",
            "projects_to_build": [
                {
                    "title": "Django Cache Layer with Redis & Docker",
                    "description": "Construct a REST API with connection pools, Docker Compose configurations, and cache eviction patterns."
                },
                {
                    "title": "Automated Testing & CI/CD Pipeline",
                    "description": "Establish a GitHub Actions flow running pytest modules and deploy code directly to Render hostings."
                }
            ],
            "certifications_to_learn": [
                "AWS Certified Developer - Associate"
            ]
        }
