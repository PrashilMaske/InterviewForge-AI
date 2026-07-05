from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.utils import timezone
from resumes.models import Resume
from interviews.models import InterviewSession, Evaluation

@login_required
def dashboard_analytics_api(request):
    user = request.user
    
    # Latest Resume score
    latest_resume = user.resumes.all().order_by('-version').first()
    resume_score = 0
    if latest_resume and hasattr(latest_resume, 'analysis'):
        resume_score = latest_resume.analysis.overall_score
        
    # Get all interview sessions
    sessions = user.interview_sessions.filter(status='completed').order_by('created_at')
    
    # Calculate average interview score
    all_scores = []
    interview_growth = []
    
    for s in sessions:
        evals = [q.answer.evaluation.overall_score for q in s.questions.all() if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')]
        if evals:
            session_avg = float(sum(evals) / len(evals))
            all_scores.append(session_avg)
            interview_growth.append({
                "date": s.created_at.strftime('%Y-%m-%d'),
                "score": round(session_avg, 2),
                "type": s.interview_type
            })

    avg_interview = round(sum(all_scores) / len(all_scores), 2) if all_scores else 0.0
    overall_performance = round((resume_score + (avg_interview * 10)) / 2, 1) if all_scores and resume_score else (resume_score or round(avg_interview * 10, 1))

    # Parse strong and weak skills from evaluations
    strong_skills = set()
    weak_skills = set()
    
    # Load from latest evaluations
    for s in sessions:
        for q in s.questions.all():
            if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation'):
                eval_obj = q.answer.evaluation
                # Simple heuristic: if score >= 8, they are strengths, else weaknesses
                is_strong = float(eval_obj.overall_score) >= 8.0
                for concept in eval_obj.missing_concepts:
                    weak_skills.add(concept)
                for strength in eval_obj.strengths:
                    # Clean/guess keywords from strength sentences
                    if "Django" in strength: strong_skills.add("Django")
                    if "Python" in strength: strong_skills.add("Python")
                    if "SQL" in strength: strong_skills.add("SQL")

    # Add defaults if empty
    if not strong_skills:
        strong_skills = ["Python", "Django", "SQL"]
    if not weak_skills:
        weak_skills = ["Redis caching", "AWS deployments", "System Design scale"]

    # Resume growth dataset
    resume_growth = []
    for r in user.resumes.all().order_by('version'):
        if hasattr(r, 'analysis'):
            resume_growth.append({
                "version": f"v{r.version}",
                "date": r.created_at.strftime('%Y-%m-%d'),
                "score": r.analysis.overall_score
            })

    data = {
        "resume_score": resume_score,
        "interview_score": round(avg_interview, 1),
        "average_performance": overall_performance,
        "interview_streak": user.streak,
        "skill_progress": {
            "Python": 90 if "Python" in strong_skills else 65,
            "Django": 85 if "Django" in strong_skills else 60,
            "SQL": 80 if "SQL" in strong_skills else 50,
            "Redis": 35 if "Redis caching" in weak_skills or "Redis" in weak_skills else 70,
            "System Design": 40 if "System Design scale" in weak_skills else 75
        },
        "weak_skills": list(weak_skills)[:3],
        "strong_skills": list(strong_skills)[:3],
        "upcoming_recommendations": [
            "Review Redis caches keys invalidations exercises.",
            "Improve bullet points details under Resume version logs."
        ],
        "chart_datasets": {
            "resume_growth": resume_growth,
            "interview_accuracy": interview_growth
        }
    }
    return JsonResponse(data)
