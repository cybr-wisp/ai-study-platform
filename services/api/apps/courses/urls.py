from rest_framework.routers import SimpleRouter

from . import views

app_name = 'courses'

router = SimpleRouter(trailing_slash=False)
router.register('courses', views.CourseViewSet, basename='course')

urlpatterns = [
    *router.urls,
]
