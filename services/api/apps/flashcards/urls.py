from rest_framework.routers import SimpleRouter

from . import views

app_name = 'flashcards'

router = SimpleRouter(trailing_slash=False)
router.register('flashcards', views.FlashcardViewSet, basename='flashcard')

urlpatterns = [
    *router.urls,
]
