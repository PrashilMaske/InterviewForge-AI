import uuid
from django.db import models
from django.conf import settings

class Resume(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='resumes')
    file_url = models.URLField(max_length=500)
    file_name = models.CharField(max_length=255)
    version = models.IntegerField(default=1)
    created_at = models.DateTimeField(auto_now_add=True)

    def save(self, *args, **kwargs):
        if not self.pk:
            # Auto-calculate incremental version
            last_resume = Resume.objects.filter(user=self.user).order_by('-version').first()
            if last_resume:
                self.version = last_resume.version + 1
            else:
                self.version = 1
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.user.username} - Resume v{self.version}"

class ResumeAnalysis(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    resume = models.OneToOneField(Resume, on_delete=models.CASCADE, related_name='analysis')
    overall_score = models.IntegerField()
    formatting_score = models.IntegerField()
    projects_score = models.IntegerField()
    skills_score = models.IntegerField()
    ats_score = models.IntegerField()
    grammar_score = models.IntegerField()
    achievements_score = models.IntegerField()
    keywords_score = models.IntegerField()
    
    # Store complex JSON payload evaluations
    section_explanations = models.JSONField(default=dict)
    improved_bullets = models.JSONField(default=list)
    parsed_entities = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Analysis for {self.resume} (Score: {self.overall_score})"

class JobDescription(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='job_descriptions')
    title = models.CharField(max_length=255)
    raw_text = models.TextField()
    file_url = models.URLField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"JD: {self.title}"
