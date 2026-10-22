from rest_framework import serializers

from .models import CardProgress, StudySession, CardReview


class CardProgressSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardProgress
        fields = ['id', 'user', 'flashcard', 'times_seen', 'times_correct', 'times_incorrect', 'current_streak', 'avg_confidence', 'last_confidence', 'ease_factor', 'interval_days', 'next_review_at', 'last_reviewed_at', 'priority_score', 'is_mastered', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'flashcard', 'times_seen', 'times_correct', 'times_incorrect', 'current_streak', 'avg_confidence', 'last_confidence', 'ease_factor', 'interval_days', 'next_review_at', 'last_reviewed_at', 'priority_score', 'is_mastered', 'created_at', 'updated_at']


class StudySessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudySession
        fields = ['id', 'user', 'course', 'study_kit', 'mode', 'queue', 'started_at', 'ended_at', 'cards_reviewed', 'cards_correct']
        read_only_fields = ['id', 'user', 'course', 'study_kit', 'mode', 'queue', 'started_at', 'ended_at', 'cards_reviewed', 'cards_correct']


class CardReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = CardReview
        fields = ['id', 'study_session', 'user', 'flashcard', 'confidence', 'is_correct', 'response_time_ms', 'reviewed_at']
        read_only_fields = ['id', 'study_session', 'user', 'flashcard', 'reviewed_at']
