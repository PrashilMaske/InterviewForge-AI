import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.utils import timezone
from .models import InterviewSession, Question, Answer, Evaluation, LearningPlan
from .ai_services import QuestionGenerator, AnswerEvaluator, LearningCoach
from .utils import calculate_adaptive_difficulty, generate_interview_report_pdf
from resumes.models import Resume, JobDescription
from resumes.parser import extract_text

@login_required
def start_interview_view(request):
    if request.method == 'POST':
        resume_id = request.POST.get('resume_id')
        jd_id = request.POST.get('jd_id')
        interview_type = request.POST.get('interview_type', 'Python & Backend')
        difficulty = request.POST.get('difficulty', 'medium')
        
        resume = get_object_or_404(Resume, id=resume_id, user=request.user) if resume_id else None
        jd = get_object_or_404(JobDescription, id=jd_id, user=request.user) if jd_id else None
        
        # Default starting difficulty level
        starting_level = 5
        if difficulty == 'easy':
            starting_level = 3
        elif difficulty == 'hard':
            starting_level = 8

        session = InterviewSession.objects.create(
            user=request.user,
            resume=resume,
            jd=jd,
            interview_type=interview_type,
            difficulty=difficulty,
            current_difficulty_level=starting_level,
            status='active'
        )
        return redirect('interview_arena', session_id=session.id)

    # Load resumes and job descriptions for the templates selectors
    resumes = request.user.resumes.all()
    jds = request.user.job_descriptions.all()
    context = {
        'resumes': resumes,
        'jds': jds,
    }
    return render(request, 'start_interview.html', context)

@login_required
def interview_arena_view(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    if session.status == 'completed':
        return redirect('interview_report', session_id=session.id)
    return render(request, 'arena.html', {'session': session})


# --- ASYNCHRONOUS AJAX INTERACTIVE ENDPOINTS ---

@login_required
def get_next_question_api(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    
    # Restrict session to max 5 questions for a mock interview round
    current_q_count = session.questions.count()
    if current_q_count >= 5:
        session.status = 'completed'
        session.ended_at = timezone.now()
        session.save()
        
        # Compile Report PDF
        generate_interview_report_pdf(session)
        
        # Generate Learning Roadmap Roadmap using Coach
        compile_learning_roadmap(session)
        
        return JsonResponse({
            'status': 'completed',
            'redirect_url': f"/interviews/{session.id}/report/"
        })

    # Prepare inputs for AI Generator
    resume_text = ""
    if session.resume:
        # Load resume content
        try:
            # Fallback pathing extraction
            import os
            from django.conf import settings
            file_name = session.resume.file_url.split('/media/')[-1]
            local_path = os.path.join(settings.MEDIA_ROOT, file_name) if hasattr(settings, 'MEDIA_ROOT') else session.resume.file_url
            resume_text = extract_text(local_path)
        except Exception:
            resume_text = "Experienced developer with Python and Django backgrounds."

    jd_text = session.jd.raw_text if session.jd else "Backend Engineer post requiring system scale expertise."
    
    # Gather question/answer history
    history = []
    for q in session.questions.all():
        ans_text = q.answer.answer_text if hasattr(q, 'answer') else "No response"
        score = float(q.answer.evaluation.overall_score) if (hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')) else 0.0
        history.append({
            "question": q.question_text,
            "answer": ans_text,
            "score": score
        })

    generator = QuestionGenerator()
    q_data = generator.generate_question(resume_text, jd_text, history, session.current_difficulty_level)

    # Save generated question to DB
    new_q = Question.objects.create(
        session=session,
        question_text=q_data["question_text"],
        expected_concepts=q_data["expected_key_concepts"],
        difficulty_level=q_data["difficulty_level"]
    )

    return JsonResponse({
        'status': 'active',
        'question_id': new_q.id,
        'question_text': new_q.question_text,
        'difficulty_level': new_q.difficulty_level,
        'round': current_q_count + 1
    })

@login_required
def submit_answer_api(request, session_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)

    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    
    try:
        data = json.loads(request.body)
        question_id = data.get('question_id')
        answer_text = data.get('answer_text')
        response_time = int(data.get('response_time_seconds', 0))
    except Exception:
        return JsonResponse({'error': 'Invalid JSON body'}, status=400)

    question = get_object_or_404(Question, id=question_id, session=session)
    
    # Create Answer record
    answer = Answer.objects.create(
        question=question,
        answer_text=answer_text,
        response_time_seconds=response_time
    )

    # Check for empty/skipped response to prevent false positive grading fallbacks
    is_skipped = not answer_text.strip() or "No response" in answer_text or "No voice input" in answer_text or "skipped" in answer_text.lower()
    
    if is_skipped:
        eval_data = {
            "overall_score": 0.0,
            "scores": {
                "technical": 0,
                "communication": 0,
                "confidence": 0,
                "depth": 0
            },
            "strengths": ["None (No response provided)"],
            "weaknesses": ["Candidate remained silent or skipped the question."],
            "missing_concepts": question.expected_concepts,
            "ideal_answer": "Candidate did not speak or type a response.",
            "suggestions": ["Ensure you allow microphone access and answer within the time limits."]
        }
    else:
        # Run AI Evaluator on candidate's reply
        evaluator = AnswerEvaluator()
        eval_data = evaluator.evaluate_answer(question.question_text, answer_text, question.expected_concepts)


    # Save Evaluation records
    evaluation = Evaluation.objects.create(
        answer=answer,
        overall_score=eval_data["overall_score"],
        technical_score=eval_data["scores"]["technical"],
        communication_score=eval_data["scores"]["communication"],
        confidence_score=eval_data["scores"]["confidence"],
        depth_score=eval_data["scores"]["depth"],
        strengths=eval_data["strengths"],
        weaknesses=eval_data["weaknesses"],
        missing_concepts=eval_data["missing_concepts"],
        ideal_answer=eval_data["ideal_answer"],
        suggestions=eval_data["suggestions"]
    )

    # Adjust current session difficulty level adaptively
    if session.difficulty == 'adaptive':
        recent_evals = [q.answer.evaluation.overall_score for q in session.questions.all() if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation')]
        # Map values to float score list for formula processing
        float_scores = [float(v) for v in recent_evals[-2:]] # last 2 rounds
        new_diff = calculate_adaptive_difficulty(session.current_difficulty_level, float_scores)
        session.current_difficulty_level = new_diff
        session.save()

    return JsonResponse({
        'scores': {
            'overall': float(evaluation.overall_score),
            'technical': evaluation.technical_score,
            'communication': evaluation.communication_score,
            'confidence': evaluation.confidence_score,
            'depth': evaluation.depth_score
        },
        'strengths': evaluation.strengths,
        'weaknesses': evaluation.weaknesses,
        'missing_concepts': evaluation.missing_concepts,
        'ideal_answer': evaluation.ideal_answer,
        'suggestions': evaluation.suggestions
    })


def compile_learning_roadmap(session):
    """Summarizes weakness fields across session questions and triggers LearningCoach."""
    evals = []
    for q in session.questions.all():
        if hasattr(q, 'answer') and hasattr(q.answer, 'evaluation'):
            evals.append({
                "score": float(q.answer.evaluation.overall_score),
                "weaknesses": q.answer.evaluation.weaknesses,
                "missing_concepts": q.answer.evaluation.missing_concepts
            })
            
    summary = {
        "interview_type": session.interview_type,
        "evaluations": evals
    }
    
    coach = LearningCoach()
    roadmap_data = coach.generate_roadmap(summary)
    
    LearningPlan.objects.create(
        user=session.user,
        session=session,
        roadmap_data=roadmap_data,
        total_weeks=roadmap_data.get("total_weeks", 4)
    )

@login_required
def report_detail_view(request, session_id):
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    report = getattr(session, 'report', None)
    learning_plan = session.learning_plans.first()
    
    context = {
        'session': session,
        'report': report,
        'learning_plan': learning_plan
    }
    return render(request, 'report_detail.html', context)

from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
@login_required
def transcribe_audio_api(request, session_id):
    import os
    import requests
    import tempfile
    
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
        
    session = get_object_or_404(InterviewSession, id=session_id, user=request.user)
    
    if 'audio' not in request.FILES:
        return JsonResponse({'error': 'No audio file provided'}, status=400)
        
    audio_file = request.FILES['audio']
    api_key = os.getenv('GROQ_API_KEY')
    
    if not api_key or api_key == "your_groq_api_key":
        return JsonResponse({
            'error': 'GROQ_API_KEY is not configured in .env.',
            'transcript': 'Please configure GROQ_API_KEY in .env for server-side audio transcription.'
        })
        
    url = "https://api.groq.com/openai/v1/audio/transcriptions"
    headers = {
        "Authorization": f"Bearer {api_key}"
    }
    
    ext = os.path.splitext(audio_file.name)[1] or '.wav'
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as temp_audio:
        for chunk in audio_file.chunks():
            temp_audio.write(chunk)
        temp_audio_path = temp_audio.name
        
    try:
        with open(temp_audio_path, 'rb') as f:
            files = {
                'file': (audio_file.name, f, audio_file.content_type or 'audio/wav')
            }
            data = {
                'model': 'whisper-large-v3',
                'language': 'en'
            }
            response = requests.post(url, headers=headers, files=files, data=data, timeout=30)


            
        if response.status_code == 200:
            transcript_text = response.json().get('text', '')
            return JsonResponse({'status': 'success', 'transcript': transcript_text})
        else:
            return JsonResponse({'error': f"Transcription failed: {response.text}"}, status=response.status_code)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
    finally:
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)

