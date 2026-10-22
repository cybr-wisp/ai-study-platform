from rest_framework import serializers

from .models import Document, DocumentChunk, AIJob


class DocumentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Document
        fields = ['id', 'course', 'title', 'original_filename', 'file', 'file_type', 'size_bytes', 'sha256', 'page_count', 'status', 'error_message', 'processed_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'course', 'original_filename', 'file', 'file_type', 'size_bytes', 'sha256', 'page_count', 'status', 'error_message', 'processed_at', 'created_at', 'updated_at']


class DocumentChunkSerializer(serializers.ModelSerializer):
    class Meta:
        model = DocumentChunk
        fields = ['id', 'document', 'chunk_index', 'page_number', 'text', 'token_count']
        read_only_fields = ['id', 'document']


class AIJobSerializer(serializers.ModelSerializer):
    class Meta:
        model = AIJob
        fields = ['id', 'course', 'job_type', 'status', 'progress', 'document', 'task_id', 'model_name', 'error_message', 'started_at', 'finished_at', 'created_at', 'updated_at']
        read_only_fields = ['id', 'course', 'job_type', 'status', 'progress', 'document', 'task_id', 'model_name', 'error_message', 'started_at', 'finished_at', 'created_at', 'updated_at']
