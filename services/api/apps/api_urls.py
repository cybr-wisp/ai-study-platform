from django.urls import include, path


urlpatterns = [
    path('', include('accounts.urls')),
    path('', include('analytics.urls')),
    path('', include('courses.urls')),
    path('', include('materials.urls')),
    path('', include('study_kits.urls')),
    path('', include('flashcards.urls')),
    path('', include('learning.urls')),
    path('', include('practice_tests.urls')),
]
