from rest_framework.routers import SimpleRouter

from . import views

app_name = 'study_kits'

router = SimpleRouter(trailing_slash=False)
router.register('study-kits', views.StudyKitViewSet, basename='study_kit')

urlpatterns = [
    *router.urls,
]
