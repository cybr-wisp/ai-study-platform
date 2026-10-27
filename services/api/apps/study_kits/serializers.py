from rest_framework import serializers

from .models import StudyKit, KeyConcept


class StudyKitSerializer(serializers.ModelSerializer):
    # Annotated by StudyKitViewSet.get_queryset; omitted when the instance isn't annotated.
    flashcard_count = serializers.IntegerField(read_only=True)
    mastery_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = StudyKit
        fields = ['id', 'course', 'title', 'kit_type', 'status', 'summary', 'study_guide', 'documents', 'generation_job', 'generation_options', 'model_name', 'created_at', 'updated_at', 'flashcard_count', 'mastery_percent']
        read_only_fields = ['id', 'course', 'status', 'documents', 'generation_job', 'generation_options', 'model_name', 'created_at', 'updated_at']


class KeyConceptSerializer(serializers.ModelSerializer):
    class Meta:
        model = KeyConcept
        fields = ['id', 'study_kit', 'term', 'definition', 'importance', 'position', 'source_chunk']
        read_only_fields = ['id', 'study_kit', 'source_chunk']
