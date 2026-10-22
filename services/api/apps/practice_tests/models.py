from django.conf import settings
from django.db import models


class PracticeTestStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    GENERATING = 'generating', 'Generating'
    READY = 'ready', 'Ready'
    FAILED = 'failed', 'Failed'


class TestDifficulty(models.TextChoices):
    EASY = 'easy', 'Easy'
    MEDIUM = 'medium', 'Medium'
    HARD = 'hard', 'Hard'


class QuestionType(models.TextChoices):
    MULTIPLE_CHOICE = 'multiple_choice', 'Multiple choice'
    SHORT_ANSWER = 'short_answer', 'Short answer'


class AttemptStatus(models.TextChoices):
    IN_PROGRESS = 'in_progress', 'In progress'
    SUBMITTED = 'submitted', 'Submitted'
    GRADING = 'grading', 'Grading'
    GRADED = 'graded', 'Graded'


class GradedBy(models.TextChoices):
    AUTO = 'auto', 'Auto'
    AI = 'ai', 'AI'


class PracticeTest(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='practice_tests')
    study_kit = models.ForeignKey('study_kits.StudyKit', on_delete=models.SET_NULL, null=True, blank=True, related_name='practice_tests')
    title = models.CharField(max_length=200)
    status = models.CharField(choices=PracticeTestStatus.choices, max_length=16, default=PracticeTestStatus.PENDING, db_index=True)
    difficulty = models.CharField(choices=TestDifficulty.choices, max_length=8, default=TestDifficulty.MEDIUM)
    time_limit_minutes = models.PositiveSmallIntegerField(null=True, blank=True)
    documents = models.ManyToManyField('materials.Document', related_name='practice_tests', blank=True)
    generation_job = models.ForeignKey('materials.AIJob', on_delete=models.SET_NULL, null=True, blank=True, related_name='practice_tests')
    generation_options = models.JSONField(default=dict, blank=True)
    model_name = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'status'], name='pt_test_course_status_idx'),
        ]

    def __str__(self):
        return str(self.title)


class TestQuestion(models.Model):
    practice_test = models.ForeignKey('PracticeTest', on_delete=models.CASCADE, related_name='questions')
    question_type = models.CharField(choices=QuestionType.choices, max_length=16)
    prompt = models.TextField()
    choices = models.JSONField(default=list, blank=True)
    correct_choice_id = models.CharField(max_length=16, blank=True, default='')
    reference_answer = models.TextField(blank=True, default='')
    grading_rubric = models.TextField(blank=True, default='')
    explanation = models.TextField(blank=True, default='')
    points = models.PositiveSmallIntegerField(default=1)
    position = models.PositiveIntegerField(default=0)
    source_chunk = models.ForeignKey('materials.DocumentChunk', on_delete=models.SET_NULL, null=True, blank=True, related_name='test_questions')

    class Meta:
        ordering = ['practice_test', 'position']
        indexes = [
            models.Index(fields=['practice_test', 'position'], name='pt_question_test_pos_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=~models.Q(question_type='multiple_choice') | ~models.Q(correct_choice_id=''), name='pt_question_mc_has_answer'),
        ]


class TestAttempt(models.Model):
    practice_test = models.ForeignKey('PracticeTest', on_delete=models.CASCADE, related_name='attempts')
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='test_attempts')
    status = models.CharField(choices=AttemptStatus.choices, max_length=16, default=AttemptStatus.IN_PROGRESS, db_index=True)
    started_at = models.DateTimeField(auto_now_add=True)
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    score_points = models.FloatField(null=True, blank=True)
    max_points = models.PositiveIntegerField(default=0)
    score_percent = models.FloatField(null=True, blank=True)
    grading_job = models.ForeignKey('materials.AIJob', on_delete=models.SET_NULL, null=True, blank=True, related_name='attempts')

    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['user', 'practice_test'], name='pt_attempt_user_test_idx'),
        ]


class TestAnswer(models.Model):
    attempt = models.ForeignKey('TestAttempt', on_delete=models.CASCADE, related_name='answers')
    question = models.ForeignKey('TestQuestion', on_delete=models.CASCADE, related_name='answers')
    selected_choice_id = models.CharField(max_length=16, blank=True, default='')
    answer_text = models.TextField(blank=True, default='')
    is_correct = models.BooleanField(null=True, blank=True)
    points_awarded = models.FloatField(null=True, blank=True)
    feedback = models.TextField(blank=True, default='')
    graded_by = models.CharField(choices=GradedBy.choices, max_length=8, blank=True, default='')
    answered_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['attempt', 'question']
        constraints = [
            models.UniqueConstraint(fields=['attempt', 'question'], name='pt_answer_attempt_q_uniq'),
        ]
