from rest_framework import serializers

from .models import Flashcard


class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['id', 'study_kit', 'front', 'back', 'hint', 'difficulty', 'position', 'is_ai_generated', 'is_archived', 'source_chunk', 'created_at', 'updated_at']
        read_only_fields = ['id', 'study_kit', 'is_ai_generated', 'source_chunk', 'created_at', 'updated_at']
