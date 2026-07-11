from celery import shared_task
from django.utils import timezone
from .models import UserSubscription


@shared_task
def expire_subscriptions():
    """Expire all subscriptions past their expiry date."""
    expired_subs = UserSubscription.objects.filter(
        status=UserSubscription.STATUS_ACTIVE,
        expires_at__lt=timezone.now()
    ).select_related('user')

    for sub in expired_subs:
        sub.status = UserSubscription.STATUS_EXPIRED
        sub.save()

        user = sub.user
        user.is_subscribed = False
        user.subscription_end_date = None
        if user.credits == -1:
            user.credits = 0
        user.save()
