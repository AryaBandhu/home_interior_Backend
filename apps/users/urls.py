from django.urls import path
from .views import (
    DevLoginView, GoogleLoginView, AppleLoginView, MeView,
    SignupView, EmailLoginView, ForgotPasswordView, VerifyOTPView, ResetPasswordView,
    VerifyEmailView,
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('auth/google/', GoogleLoginView.as_view(), name='google-login'),
    path('auth/apple/', AppleLoginView.as_view(), name='apple-login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('auth/me/', MeView.as_view(), name='me'),
    path('auth/dev-login/', DevLoginView.as_view(), name='dev-login'),
    path('auth/signup/', SignupView.as_view(), name='signup'),
    path('auth/verify-email/', VerifyEmailView.as_view(), name='verify-email'),
    path('auth/login/', EmailLoginView.as_view(), name='email-login'),
    path('auth/forgot-password/', ForgotPasswordView.as_view(), name='forgot-password'),
    path('auth/verify-otp/', VerifyOTPView.as_view(), name='verify-otp'),
    path('auth/reset-password/', ResetPasswordView.as_view(), name='reset-password'),
]