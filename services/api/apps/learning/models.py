from django.conf import settings
from django.db import models


class StudyMode(models.TextChoices):
    STANDARD = 'standard', 'Standard'
    DUE_REVIEW = 'due_review', 'Due review'
    STRUGGLING = 'struggling', 'Struggling'


class CardProgress(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='card_progress')
    flashcard = models.ForeignKey('flashcards.Flashcard', on_delete=models.CASCADE, related_name='progress')
    times_seen = models.PositiveIntegerField(default=0)
    times_correct = models.PositiveIntegerField(default=0)
    times_incorrect = models.PositiveIntegerField(default=0)
    current_streak = models.PositiveIntegerField(default=0)
    avg_confidence = models.FloatField(default=0)
    last_confidence = models.PositiveSmallIntegerField(null=True, blank=True)
    ease_factor = models.FloatField(default=2.5)
    interval_days = models.PositiveIntegerField(default=0)
    next_review_at = models.DateTimeField(null=True, blank=True)
    last_reviewed_at = models.DateTimeField(null=True, blank=True)
    priority_score = models.FloatField(default=0)
    is_mastered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority_score']
        indexes = [
            models.Index(fields=['user', '-priority_score'], name='lrn_cardprog_user_prio_idx'),
            models.Index(fields=['user', 'next_review_at'], name='lrn_cardprog_user_due_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['user', 'flashcard'], name='lrn_cardprog_user_card_uniq'),
        ]


class StudySession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='study_sessions')
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='study_sessions')
    study_kit = models.ForeignKey('study_kits.StudyKit', on_delete=models.SET_NULL, null=True, blank=True, related_name='study_sessions')
    mode = models.CharField(choices=StudyMode.choices, max_length=16, default=StudyMode.STANDARD)
    queue = models.JSONField(default=list, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    ended_at = models.DateTimeField(null=True, blank=True)
    cards_reviewed = models.PositiveIntegerField(default=0)
    cards_correct = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', '-started_at'], name='lrn_session_user_start_idx'),
        ]


class CardReview(models.Model):
    study_session = models.ForeignKey('StudySession', on_delete=models.SET_NULL, null=True, blank=True, related_name='reviews')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='card_reviews')
    flashcard = models.ForeignKey('flashcards.Flashcard', on_delete=models.CASCADE, related_name='reviews')
    confidence = models.PositiveSmallIntegerField()
    is_correct = models.BooleanField()
    response_time_ms = models.PositiveIntegerField(null=True, blank=True)
    reviewed_at = models.DateTimeField(auto_now_add=True, db_index=True)

    class Meta:
        ordering = ['-reviewed_at']
        indexes = [
            models.Index(fields=['user', 'flashcard'], name='lrn_review_user_card_idx'),
            models.Index(fields=['study_session'], name='lrn_review_session_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(confidence__gte=1, confidence__lte=5), name='lrn_review_conf_range'),
        ]
