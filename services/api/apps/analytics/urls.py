from django.urls import path

from . import views

app_name = 'analytics'

urlpatterns = [
    path('analytics/dashboard', views.DashboardView.as_view(), name='dashboard'),
    path('analytics/courses/<int:course_id>/progress', views.CourseProgressView.as_view(), name='course_progress'),
    path('analytics/study-kits/<int:kit_id>/progress', views.StudyKitProgressView.as_view(), name='study_kit_progress'),
]
