from django.urls import path
from .views import DevLoginView, GoogleLoginView, AppleLoginView, MeView
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/google/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/apple/', AppleLoginView.as_view(), name='apple-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/dev-login/', DevLoginView.as_view(), name='dev-login'),
]