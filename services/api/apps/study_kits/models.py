from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models


class StudyKitStatus(models.TextChoices):
    PENDING = 'pending', 'Pending'
    GENERATING = 'generating', 'Generating'
    READY = 'ready', 'Ready'
    FAILED = 'failed', 'Failed'


class StudyKit(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='study_kits')
    title = models.CharField(max_length=200)
    status = models.CharField(choices=StudyKitStatus.choices, max_length=16, default=StudyKitStatus.PENDING, db_index=True)
    summary = models.TextField(blank=True, default='')
    study_guide = models.TextField(blank=True, default='')
    documents = models.ManyToManyField('materials.Document', related_name='study_kits', blank=True)
    generation_job = models.ForeignKey('materials.AIJob', on_delete=models.SET_NULL, null=True, blank=True, related_name='study_kits')
    generation_options = models.JSONField(default=dict, blank=True)
    model_name = models.CharField(max_length=100, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'status'], name='kit_course_status_idx'),
        ]

    def __str__(self):
        return str(self.title)


class KeyConcept(models.Model):
    study_kit = models.ForeignKey('StudyKit', on_delete=models.CASCADE, related_name='key_concepts')
    term = models.CharField(max_length=255)
    definition = models.TextField()
    importance = models.PositiveSmallIntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])
    position = models.PositiveIntegerField(default=0)
    source_chunk = models.ForeignKey('materials.DocumentChunk', on_delete=models.SET_NULL, null=True, blank=True, related_name='key_concepts')

    class Meta:
        ordering = ['study_kit', 'position']

    def __str__(self):
        return str(self.term)
