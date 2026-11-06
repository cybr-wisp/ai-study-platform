from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from django.db import models

class Flashcard(models.Model):
    question = models.TextField()
    answer = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.question[:50]
    
class StudyAttempt(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_attempts'
    )
    flashcard = models.ForeignKey(
        Flashcard, on_delete=models.CASCADE, related_name='attempts'
    )
    is_correct = models.BooleanField()
    confidence = models.PositiveSmallIntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [models.Index(fields=['user', 'flashcard'])]

    def __str__(self):
        return f'{self.user} - card {self.flashcard_id} - {"correct" if self.is_correct else "wrong"}'