from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    credits = models.IntegerField(default=3)
    is_subscribed = models.BooleanField(default=False)
    subscription_end_date = models.DateTimeField(null=True, blank=True)
    google_id = models.CharField(max_length=255, null=True, blank=True)
    apple_id = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def has_credits(self):
        return self.is_subscribed or self.credits > 0

    def deduct_credit(self, count=1):
        if not self.is_subscribed:
            self.credits = max(0, self.credits - count)
            self.save()

    def __str__(self):
        return self.email