from rest_framework import serializers

from .models import PracticeTest, TestQuestion, TestAttempt, TestAnswer


class PracticeTestSerializer(serializers.ModelSerializer):
    class Meta:
        model = PracticeTest
        fields = ['id', 'course', 'study_kit', 'title', 'status', 'difficulty', 'time_limit_minutes', 'documents', 'generation_job', 'generation_options', 'model_name', 'created_at', 'updated_at']
        read_only_fields = ['id', 'course', 'study_kit', 'status', 'difficulty', 'documents', 'generation_job', 'generation_options', 'model_name', 'created_at', 'updated_at']


class TestQuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['id', 'practice_test', 'question_type', 'prompt', 'choices', 'correct_choice_id', 'reference_answer', 'grading_rubric', 'explanation', 'points', 'position', 'source_chunk']
        read_only_fields = ['id', 'practice_test']


class TestQuestionPublicSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestQuestion
        fields = ['id', 'question_type', 'prompt', 'choices', 'points', 'position']
        read_only_fields = ['id', 'question_type', 'prompt', 'choices', 'points', 'position']


class TestAttemptSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAttempt
        fields = ['id', 'practice_test', 'user', 'status', 'started_at', 'submitted_at', 'graded_at', 'score_points', 'max_points', 'score_percent', 'grading_job']
        read_only_fields = ['id', 'practice_test', 'user', 'status', 'started_at', 'submitted_at', 'graded_at', 'score_points', 'max_points', 'score_percent', 'grading_job']


class TestAnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = TestAnswer
        fields = ['id', 'attempt', 'question', 'selected_choice_id', 'answer_text', 'is_correct', 'points_awarded', 'feedback', 'graded_by', 'answered_at']
        read_only_fields = ['id', 'attempt', 'question', 'is_correct', 'points_awarded', 'feedback', 'graded_by', 'answered_at']
