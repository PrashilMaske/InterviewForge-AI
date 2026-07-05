import uuid
from django.db import models
from django.conf import settings

class ProgressHistory(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='progress_histories')
    date = models.DateField()
    resume_score = models.IntegerField(null=True, blank=True)
    average_interview_score = models.DecimalField(max_digits=4, decimal_places=2, default=0.0)
    skill_strengths = models.JSONField(default=list)
    skill_weaknesses = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'date')
        verbose_name_plural = 'Progress histories'

    def __str__(self):
        return f"{self.user.username} progress on {self.date}"
