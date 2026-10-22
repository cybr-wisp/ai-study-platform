from django.urls import path
from rest_framework.routers import SimpleRouter

from . import views

app_name = 'learning'

router = SimpleRouter(trailing_slash=False)
router.register('learning/card-progress', views.CardProgressViewSet, basename='card_progress')
router.register('learning/sessions', views.StudySessionViewSet, basename='study_session')

urlpatterns = [
    path('learning/struggling-cards', views.StrugglingCardsView.as_view(), name='struggling_cards'),
    *router.urls,
]
