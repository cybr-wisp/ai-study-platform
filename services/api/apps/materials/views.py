import hashlib
import os

from rest_framework import status
from rest_framework.exceptions import NotFound, ValidationError
from rest_framework.response import Response

from apps.courses.models import Course
from .models import AIJob, Document, DocumentFileType, DocumentStatus, JobType
from .serializers import DocumentSerializer
from .views_base import DocumentViewSetBase, DocumentChunkViewSetBase, AIJobViewSetBase

MAX_UPLOAD_BYTES = 50 * 1024 * 1024
ALLOWED_FILE_TYPES = {choice.value for choice in DocumentFileType}


class DocumentViewSet(DocumentViewSetBase):
    def handle_create(self, request, *args, **kwargs):
        upload = request.FILES.get('file')
        if upload is None:
            raise ValidationError({'file': ['This field is required.']})
        try:
            course_id = int(request.data.get('course_id'))
        except (TypeError, ValueError):
            raise ValidationError({'course_id': ['A valid integer is required.']}) from None

        course = Course.objects.filter(pk=course_id, owner=request.user).first()
        if course is None:
            raise NotFound('Course not found.')

        stem, ext = os.path.splitext(upload.name)
        file_type = ext.lstrip('.').lower()
        if file_type not in ALLOWED_FILE_TYPES:
            return Response(
                {'detail': f"Unsupported file type. Allowed: {', '.join(sorted(ALLOWED_FILE_TYPES))}."},
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )
        if upload.size > MAX_UPLOAD_BYTES:
            return Response({'detail': 'File exceeds the 50 MB limit.'}, status=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE)

        digest = hashlib.sha256()
        for chunk in upload.chunks():
            digest.update(chunk)
        upload.seek(0)
        sha256 = digest.hexdigest()
        if Document.objects.filter(course=course, sha256=sha256).exists():
            return Response({'detail': 'This file was already uploaded to the course.'}, status=status.HTTP_409_CONFLICT)

        auto_process = str(request.data.get('auto_process', 'true')).lower() not in ('false', '0')
        document = Document.objects.create(
            course=course,
            title=(request.data.get('title') or stem)[:255],
            original_filename=upload.name[:255],
            file=upload,
            file_type=file_type,
            size_bytes=upload.size,
            sha256=sha256,
            status=DocumentStatus.QUEUED if auto_process else DocumentStatus.UPLOADED,
        )
        if auto_process:
            # Nothing consumes this queue yet; the ingest worker is not built.
            AIJob.objects.create(course=course, job_type=JobType.DOCUMENT_INGEST, document=document)

        serializer = DocumentSerializer(document, context=self.get_serializer_context())
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class DocumentChunkViewSet(DocumentChunkViewSetBase):
    pass


class AIJobViewSet(AIJobViewSetBase):
    pass
