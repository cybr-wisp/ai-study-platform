from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from . import views

app_name = 'accounts'

urlpatterns = [
    path('accounts/register', views.RegisterView.as_view(), name='register'),
    path('accounts/token', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('accounts/token/refresh', TokenRefreshView.as_view(), name='token_refresh'),
    path('accounts/me', views.MeView.as_view(), name='me'),
]
