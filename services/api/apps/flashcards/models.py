from django.db import models


class FlashcardDifficulty(models.TextChoices):
    EASY = 'easy', 'Easy'
    MEDIUM = 'medium', 'Medium'
    HARD = 'hard', 'Hard'


class Flashcard(models.Model):
    study_kit = models.ForeignKey('study_kits.StudyKit', on_delete=models.CASCADE, related_name='flashcards')
    front = models.TextField()
    back = models.TextField()
    hint = models.TextField(blank=True, default='')
    difficulty = models.CharField(choices=FlashcardDifficulty.choices, max_length=8, default=FlashcardDifficulty.MEDIUM)
    position = models.PositiveIntegerField(default=0)
    is_ai_generated = models.BooleanField(default=False)
    is_archived = models.BooleanField(default=False)
    source_chunk = models.ForeignKey('materials.DocumentChunk', on_delete=models.SET_NULL, null=True, blank=True, related_name='flashcards')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['study_kit', 'position']
        indexes = [
            models.Index(fields=['study_kit', 'is_archived'], name='fc_kit_arch_idx'),
        ]
