from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model, authenticate
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import jwt
import requests
import resend
from decouple import config

from .models import PasswordResetOTP, EmailVerificationOTP
from .serializers import (
    GoogleAuthSerializer, AppleAuthSerializer, UserSerializer,
    SignupSerializer, EmailLoginSerializer,
    ForgotPasswordSerializer, VerifyOTPSerializer, ResetPasswordSerializer,
    VerifyEmailSerializer,
)

User = get_user_model()

resend.api_key = config('RESEND_API_KEY')
RESEND_FROM = config('RESEND_FROM_EMAIL', default='no-reply@kalkinso.in')


def get_tokens_for_user(user):
    refresh = RefreshToken.for_user(user)
    return {
        'refresh': str(refresh),
        'access': str(refresh.access_token),
    }


class GoogleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = GoogleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']

        try:
            # verify google token
            google_info = id_token.verify_oauth2_token(
                token,
                google_requests.Request(),
                config('GOOGLE_CLIENT_ID')
            )
        except ValueError:
            return Response({'error': 'Invalid Google token'}, status=status.HTTP_400_BAD_REQUEST)

        email = google_info.get('email')
        google_id = google_info.get('sub')
        first_name = google_info.get('given_name', '')
        last_name = google_info.get('family_name', '')

        if not email:
            return Response({'error': 'Email not found in Google token'}, status=status.HTTP_400_BAD_REQUEST)

        user, created = User.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0],
                'first_name': first_name,
                'last_name': last_name,
                'google_id': google_id,
            }
        )

        if not created and not user.google_id:
            user.google_id = google_id
            user.save()

        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
            'is_new_user': created,
        }, status=status.HTTP_200_OK)


class AppleLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AppleAuthSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        token = serializer.validated_data['token']
        first_name = serializer.validated_data.get('first_name', '')
        last_name = serializer.validated_data.get('last_name', '')

        try:
            # fetch apple public keys
            apple_keys = requests.get('https://appleid.apple.com/auth/keys').json()
            # decode header to get kid
            header = jwt.get_unverified_header(token)
            # find matching key
            key = next((k for k in apple_keys['keys'] if k['kid'] == header['kid']), None)
            if not key:
                raise ValueError('Apple key not found')

            from jwt.algorithms import RSAAlgorithm
            public_key = RSAAlgorithm.from_jwk(key)

            apple_info = jwt.decode(
                token,
                public_key,
                algorithms=['RS256'],
                audience=config('APPLE_CLIENT_ID'),
            )
        except Exception:
            return Response({'error': 'Invalid Apple token'}, status=status.HTTP_400_BAD_REQUEST)

        email = apple_info.get('email')
        apple_id = apple_info.get('sub')

        if not email:
            # apple only sends email on first login
            try:
                user = User.objects.get(apple_id=apple_id)
            except User.DoesNotExist:
                return Response({'error': 'Email not found'}, status=status.HTTP_400_BAD_REQUEST)
        else:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email.split('@')[0],
                    'first_name': first_name,
                    'last_name': last_name,
                    'apple_id': apple_id,
                }
            )
            if not created and not user.apple_id:
                user.apple_id = apple_id
                user.save()

        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        }, status=status.HTTP_200_OK)


class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(UserSerializer(request.user).data)

    def patch(self, request):
        serializer = UserSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)


class SignupView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = SignupSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        otp_code = EmailVerificationOTP.generate_otp()
        EmailVerificationOTP.objects.create(user=user, otp=otp_code)

        resend.Emails.send({
            'from': RESEND_FROM,
            'to': user.email,
            'subject': 'Verify Your Email – Spacia',
            'html': f'''
            <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
              <div style="background:linear-gradient(135deg,#f97316,#a855f7);padding:32px 24px;text-align:center">
                <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;letter-spacing:-0.5px">Spacia</h1>
                <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:13px">AI-Powered Interior Design</p>
              </div>
              <div style="padding:36px 32px">
                <h2 style="margin:0 0 8px;color:#111827;font-size:20px;font-weight:600">Verify Your Email Address</h2>
                <p style="margin:0 0 24px;color:#6b7280;font-size:14px;line-height:1.6">Hi {user.first_name or 'there'},<br/>Thank you for signing up! Use the OTP below to verify your email address and get started.</p>
                <div style="background:#f9fafb;border:1px dashed #d1d5db;border-radius:10px;padding:24px;text-align:center;margin-bottom:24px">
                  <p style="margin:0 0 6px;color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px">Your OTP</p>
                  <p style="margin:0;font-size:40px;font-weight:700;letter-spacing:10px;color:#111827">{otp_code}</p>
                  <p style="margin:10px 0 0;color:#9ca3af;font-size:12px">This OTP expires in <strong>10 minutes</strong></p>
                </div>
                <p style="margin:0;color:#6b7280;font-size:13px;line-height:1.6">If you did not create an account with Spacia, you can safely ignore this email.</p>
              </div>
              <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:20px 32px;text-align:center">
                <p style="margin:0;color:#9ca3af;font-size:12px">Warm regards,<br/><strong style="color:#6b7280">The Spacia Team</strong></p>
                <p style="margin:8px 0 0;color:#d1d5db;font-size:11px">© 2025 Spacia. All rights reserved.</p>
              </div>
            </div>
            ''',
        })
        return Response({'detail': 'OTP sent to your email. Please verify to continue.'}, status=status.HTTP_201_CREATED)


class VerifyEmailView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyEmailSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email)
            otp_obj = EmailVerificationOTP.objects.filter(user=user, otp=otp_code, is_used=False).latest('created_at')
        except (User.DoesNotExist, EmailVerificationOTP.DoesNotExist):
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp_obj.is_valid():
            return Response({'error': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        user.is_verified = True
        user.save()
        otp_obj.is_used = True
        otp_obj.save()
        tokens = get_tokens_for_user(user)
        return Response({'user': UserSerializer(user).data, 'tokens': tokens}, status=status.HTTP_200_OK)


class EmailLoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = EmailLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(request, username=serializer.validated_data['email'], password=serializer.validated_data['password'])
        if not user:
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)
        tokens = get_tokens_for_user(user)
        return Response({'user': UserSerializer(user).data, 'tokens': tokens})


class ForgotPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ForgotPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'detail': 'If this email exists, an OTP has been sent.'}, status=status.HTTP_200_OK)

        otp_code = PasswordResetOTP.generate_otp()
        PasswordResetOTP.objects.create(user=user, otp=otp_code)

        resend.Emails.send({
            'from': RESEND_FROM,
            'to': email,
            'subject': 'Reset Your Password – Spacia',
            'html': f'''
            <div style="font-family:Arial,sans-serif;max-width:520px;margin:0 auto;background:#ffffff;border:1px solid #e5e7eb;border-radius:12px;overflow:hidden">
              <div style="background:linear-gradient(135deg,#f97316,#a855f7);padding:32px 24px;text-align:center">
                <h1 style="margin:0;color:#ffffff;font-size:26px;font-weight:700;letter-spacing:-0.5px">Spacia</h1>
                <p style="margin:6px 0 0;color:rgba(255,255,255,0.85);font-size:13px">AI-Powered Interior Design</p>
              </div>
              <div style="padding:36px 32px">
                <h2 style="margin:0 0 8px;color:#111827;font-size:20px;font-weight:600">Password Reset Request</h2>
                <p style="margin:0 0 24px;color:#6b7280;font-size:14px;line-height:1.6">Hi {user.first_name or 'there'},<br/>We received a request to reset your Spacia account password. Use the OTP below to proceed.</p>
                <div style="background:#f9fafb;border:1px dashed #d1d5db;border-radius:10px;padding:24px;text-align:center;margin-bottom:24px">
                  <p style="margin:0 0 6px;color:#6b7280;font-size:12px;text-transform:uppercase;letter-spacing:1px">Your OTP</p>
                  <p style="margin:0;font-size:40px;font-weight:700;letter-spacing:10px;color:#111827">{otp_code}</p>
                  <p style="margin:10px 0 0;color:#9ca3af;font-size:12px">This OTP expires in <strong>10 minutes</strong></p>
                </div>
                <p style="margin:0;color:#6b7280;font-size:13px;line-height:1.6">If you did not request a password reset, please ignore this email. Your account remains secure.</p>
              </div>
              <div style="background:#f9fafb;border-top:1px solid #e5e7eb;padding:20px 32px;text-align:center">
                <p style="margin:0;color:#9ca3af;font-size:12px">Warm regards,<br/><strong style="color:#6b7280">The Spacia Team</strong></p>
                <p style="margin:8px 0 0;color:#d1d5db;font-size:11px">© 2025 Spacia. All rights reserved.</p>
              </div>
            </div>
            ''',
        })
        return Response({'detail': 'If this email exists, an OTP has been sent.'}, status=status.HTTP_200_OK)


class VerifyOTPView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = VerifyOTPSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp_code, is_used=False).latest('created_at')
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp_obj.is_valid():
            return Response({'error': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        return Response({'detail': 'OTP verified.'}, status=status.HTTP_200_OK)


class ResetPasswordView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        email = serializer.validated_data['email']
        otp_code = serializer.validated_data['otp']
        try:
            user = User.objects.get(email=email)
            otp_obj = PasswordResetOTP.objects.filter(user=user, otp=otp_code, is_used=False).latest('created_at')
        except (User.DoesNotExist, PasswordResetOTP.DoesNotExist):
            return Response({'error': 'Invalid OTP.'}, status=status.HTTP_400_BAD_REQUEST)
        if not otp_obj.is_valid():
            return Response({'error': 'OTP has expired.'}, status=status.HTTP_400_BAD_REQUEST)
        user.set_password(serializer.validated_data['password'])
        user.save()
        otp_obj.is_used = True
        otp_obj.save()
        return Response({'detail': 'Password reset successful.'}, status=status.HTTP_200_OK)


from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

class DevLoginView(APIView):
    """ONLY FOR DEVELOPMENT TESTING — remove in production"""
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get('email')
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({'error': 'User not found'}, status=404)
        tokens = get_tokens_for_user(user)
        return Response({
            'user': UserSerializer(user).data,
            'tokens': tokens,
        })