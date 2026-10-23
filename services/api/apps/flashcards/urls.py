from django.urls import path
from .views import FlashcardListView, FlashcardDetailView

urlpatterns = [
    path('', FlashcardListView.as_view(), name='flashcard-list'),
    path('<int:pk>/', FlashcardDetailView.as_view(), name='flashcard-detail'),
]