from rest_framework import serializers
from .models import Flashcard, StudyAttempt

class FlashcardSerializer(serializers.ModelSerializer):
    class Meta:
        model = Flashcard
        fields = ['id', 'question', 'answer', 'created_at']
        read_only_fields = ['id', 'created_at']

class StudyAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyAttempt
        fields = ['id', 'flashcard', 'is_correct', 'confidence', 'created_at']
        read_only_fields = ['id', 'created_at']