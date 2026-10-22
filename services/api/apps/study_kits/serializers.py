from rest_framework import serializers

from .models import StudyKit, KeyConcept


class StudyKitSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyKit
        fields = ['id', 'course', 'title', 'status', 'summary', 'study_guide', 'documents', 'generation_job', 'generation_options', 'model_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'course', 'status', 'documents', 'generation_job', 'generation_options', 'model_name', 'created_at', 'updated_at']


class KeyConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyConcept
        fields = ['id', 'study_kit', 'term', 'definition', 'importance', 'position', 'source_chunk']
        read_only_fields = ['id', 'study_kit', 'source_chunk']
