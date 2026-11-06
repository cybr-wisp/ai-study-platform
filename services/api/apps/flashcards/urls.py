from django.urls import path
from .views import (
    FlashcardListView, FlashcardDetailView,
    SubmitAttemptView, NextCardsView, StudyStatsView,
)

urlpatterns = [
    path('', FlashcardListView.as_view(), name='flashcard-list'),
    path('<int:pk>/', FlashcardDetailView.as_view(), name='flashcard-detail'),
    path('study/attempts/', SubmitAttemptView.as_view(), name='study-attempt'),
    path('study/next/', NextCardsView.as_view(), name='study-next'),
    path('study/stats/', StudyStatsView.as_view(), name='study-stats'),
]