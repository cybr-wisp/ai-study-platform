from rest_framework.routers import SimpleRouter

from . import views

app_name = 'practice_tests'

router = SimpleRouter(trailing_slash=False)
router.register('practice-tests/attempts', views.TestAttemptViewSet, basename='test_attempt')
router.register('practice-tests', views.PracticeTestViewSet, basename='practice_test')

urlpatterns = [
    *router.urls,
]
