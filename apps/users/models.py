from django.contrib.auth.models import AbstractUser
from django.db import models
import random
import string
from django.utils import timezone
from datetime import timedelta


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    credits = models.IntegerField(default=3)
    is_subscribed = models.BooleanField(default=False)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    google_id = models.CharField(max_length=255, null=True, blank=True)
    apple_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)
    is_verified = models.BooleanField(default=False)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def has_credits(self):
        return self.credits == -1 or self.credits > 0

    def deduct_credit(self, count=1):
        if self.credits == -1:
            return  # unlimited
        self.credits = max(0, self.credits - count)
        self.save()

    def __str__(self):
        return self.email


class PasswordResetOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otp_requests')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=10)

    @classmethod
    def generate_otp(cls):
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"{self.user.email} - {self.otp}"


class EmailVerificationOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='email_otps')
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used = models.BooleanField(default=False)

    def is_valid(self):
        return not self.is_used and timezone.now() < self.created_at + timedelta(minutes=10)

    @classmethod
    def generate_otp(cls):
        return ''.join(random.choices(string.digits, k=6))

    def __str__(self):
        return f"{self.user.email} - {self.otp}"