from django.urls import include, path


urlpatterns = [
    path('', include('apps.accounts.urls')),
    path('', include('apps.analytics.urls')),
    path('', include('apps.courses.urls')),
    path('', include('apps.materials.urls')),
    path('', include('apps.study_kits.urls')),
    path('', include('apps.flashcards.urls')),
    path('', include('apps.learning.urls')),
    path('', include('apps.practice_tests.urls')),
]
