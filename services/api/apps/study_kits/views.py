from django.db.models import Case, Count, F, FloatField, Q, Value, When
from django.db.models.functions import Cast

from .views_base import StudyKitViewSetBase


class StudyKitViewSet(StudyKitViewSetBase):
    def get_queryset(self):
        user = self.request.user
        active = Q(flashcards__is_archived=False)
        mastered = active & Q(flashcards__progress__user=user, flashcards__progress__is_mastered=True)
        # The aggregates add a GROUP BY, which makes Django ignore Meta.ordering.
        return super().get_queryset().order_by('-created_at', '-id').annotate(
            flashcard_count=Count('flashcards', filter=active, distinct=True),
            mastered_count=Count('flashcards', filter=mastered, distinct=True),
        ).annotate(
            mastery_percent=Case(
                When(flashcard_count=0, then=Value(0.0)),
                default=Cast(F('mastered_count'), FloatField()) * 100.0 / Cast(F('flashcard_count'), FloatField()),
                output_field=FloatField(),
            ),
        )
