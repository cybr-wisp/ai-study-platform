from django.db import models


class DocumentFileType(models.TextChoices):
    PDF = 'pdf', 'PDF'
    PPTX = 'pptx', 'PPTX'
    DOCX = 'docx', 'DOCX'
    TXT = 'txt', 'TXT'
    MD = 'md', 'MD'


class DocumentStatus(models.TextChoices):
    UPLOADED = 'uploaded', 'Uploaded'
    QUEUED = 'queued', 'Queued'
    PROCESSING = 'processing', 'Processing'
    PROCESSED = 'processed', 'Processed'
    FAILED = 'failed', 'Failed'


class JobType(models.TextChoices):
    DOCUMENT_INGEST = 'document_ingest', 'Document ingest'
    STUDY_KIT_GENERATION = 'study_kit_generation', 'Study kit generation'
    TEST_GENERATION = 'test_generation', 'Test generation'
    ATTEMPT_GRADING = 'attempt_grading', 'Attempt grading'


class JobStatus(models.TextChoices):
    QUEUED = 'queued', 'Queued'
    RUNNING = 'running', 'Running'
    SUCCEEDED = 'succeeded', 'Succeeded'
    FAILED = 'failed', 'Failed'
    CANCELED = 'canceled', 'Canceled'


class Document(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    original_filename = models.CharField(max_length=255)
    file = models.FileField(upload_to='materials/%Y/%m/', max_length=500)
    file_type = models.CharField(choices=DocumentFileType.choices, max_length=8)
    size_bytes = models.PositiveBigIntegerField()
    sha256 = models.CharField(max_length=64, blank=True, default='')
    page_count = models.PositiveIntegerField(null=True, blank=True)
    status = models.CharField(choices=DocumentStatus.choices, max_length=16, default=DocumentStatus.UPLOADED, db_index=True)
    error_message = models.TextField(blank=True, default='')
    processed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['course', 'status'], name='mat_doc_course_status_idx'),
        ]
        constraints = [
            models.UniqueConstraint(fields=['course', 'sha256'], name='mat_doc_course_sha_uniq', condition=~models.Q(sha256='')),
        ]

    def __str__(self):
        return str(self.title)


class DocumentChunk(models.Model):
    document = models.ForeignKey('Document', on_delete=models.CASCADE, related_name='chunks')
    chunk_index = models.PositiveIntegerField()
    page_number = models.PositiveIntegerField(null=True, blank=True)
    text = models.TextField()
    token_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['document', 'chunk_index']
        constraints = [
            models.UniqueConstraint(fields=['document', 'chunk_index'], name='mat_chunk_doc_index_uniq'),
        ]


class AIJob(models.Model):
    course = models.ForeignKey('courses.Course', on_delete=models.CASCADE, related_name='ai_jobs')
    job_type = models.CharField(choices=JobType.choices, max_length=32)
    status = models.CharField(choices=JobStatus.choices, max_length=16, default=JobStatus.QUEUED)
    progress = models.PositiveSmallIntegerField(default=0)
    document = models.ForeignKey('Document', on_delete=models.CASCADE, null=True, blank=True, related_name='jobs')
    task_id = models.CharField(max_length=255, blank=True, default='')
    model_name = models.CharField(max_length=100, blank=True, default='')
    error_message = models.TextField(blank=True, default='')
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at'], name='mat_job_status_created_idx'),
            models.Index(fields=['course', 'status'], name='mat_job_course_status_idx'),
        ]
        constraints = [
            models.CheckConstraint(condition=models.Q(progress__gte=0, progress__lte=100), name='mat_job_progress_range'),
        ]
