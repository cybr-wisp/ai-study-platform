from rest_framework.routers import SimpleRouter

from . import views

app_name = 'materials'

router = SimpleRouter(trailing_slash=False)
router.register('materials/jobs', views.AIJobViewSet, basename='a_i_job')
router.register('materials/chunks', views.DocumentChunkViewSet, basename='document_chunk')
router.register('materials/documents', views.DocumentViewSet, basename='document')

urlpatterns = [
    *router.urls,
]
