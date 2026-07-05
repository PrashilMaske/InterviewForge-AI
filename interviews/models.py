import uuid
from django.db import models
from django.conf import settings
from resumes.models import Resume, JobDescription

class InterviewSession(models.Model):
    DIFFICULTY_CHOICES = (
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
        ('adaptive', 'Adaptive'),
    )
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('active', 'Active'),
        ('completed', 'Completed'),
    )

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='interview_sessions')
    resume = models.ForeignKey(Resume, on_delete=models.SET_NULL, null=True, blank=True, related_name='interview_sessions')
    jd = models.ForeignKey(JobDescription, on_delete=models.SET_NULL, null=True, blank=True, related_name='interview_sessions')
    interview_type = models.CharField(max_length=50) # e.g. Python, Django, System Design, Behavioral
    difficulty = models.CharField(max_length=20, choices=DIFFICULTY_CHOICES, default='medium')
    current_difficulty_level = models.IntegerField(default=5) # Scale 1 to 10
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.interview_type} ({self.status})"

class Question(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField()
    expected_concepts = models.JSONField(default=list)
    difficulty_level = models.IntegerField(default=5)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Q for Session {self.session.id[:8]}... (Diff: {self.difficulty_level})"

class Answer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    question = models.OneToOneField(Question, on_delete=models.CASCADE, related_name='answer')
    answer_text = models.TextField()
    response_time_seconds = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Answer to {self.question.id[:8]}..."

class Evaluation(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    answer = models.OneToOneField(Answer, on_delete=models.CASCADE, related_name='evaluation')
    overall_score = models.DecimalField(max_digits=4, decimal_places=2) # 0-10 scale
    technical_score = models.IntegerField()
    communication_score = models.IntegerField()
    confidence_score = models.IntegerField()
    depth_score = models.IntegerField()
    
    strengths = models.JSONField(default=list)
    weaknesses = models.JSONField(default=list)
    missing_concepts = models.JSONField(default=list)
    ideal_answer = models.TextField()
    suggestions = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Eval for {self.answer.id[:8]}... (Score: {self.overall_score})"

class Report(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    session = models.OneToOneField(InterviewSession, on_delete=models.CASCADE, related_name='report')
    pdf_url = models.URLField(max_length=500, null=True, blank=True)
    readiness_score = models.IntegerField(default=50) # 0-100 scale
    timeline = models.JSONField(default=list)
    projects_recommended = models.JSONField(default=list)
    courses_recommended = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report for Session {self.session.id[:8]}..."

class LearningPlan(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='learning_plans')
    session = models.ForeignKey(InterviewSession, on_delete=models.CASCADE, related_name='learning_plans')
    roadmap_data = models.JSONField(default=dict)
    current_week = models.IntegerField(default=1)
    total_weeks = models.IntegerField(default=4)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Roadmap for {self.user.username} ({self.total_weeks} weeks)"
