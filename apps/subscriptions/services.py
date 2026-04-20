import stripe
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, UserSubscription

stripe.api_key = settings.STRIPE_SECRET_KEY


def create_checkout_session(user, plan):
    """Create Stripe checkout session — supports Card, Google Pay, Apple Pay"""
    try:
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],  # google pay + apple pay auto added by stripe
            line_items=[{
                'price_data': {
                    'currency': 'usd',
                    'product_data': {
                        'name': plan.name,
                        'description': plan.description or f'{plan.duration_days} days subscription',
                    },
                    'unit_amount': int(plan.price * 100),  # stripe uses cents
                },
                'quantity': 1,
            }],
            mode='payment',
            success_url=f"{settings.FRONTEND_URL}/payment/success?session_id={{CHECKOUT_SESSION_ID}}",
            cancel_url=f"{settings.FRONTEND_URL}/payment/cancel",
            metadata={
                'user_id': str(user.id),
                'plan_id': str(plan.id),
            }
        )
        return {'success': True, 'checkout_url': session.url, 'session_id': session.id}
    except stripe.error.StripeError as e:
        return {'success': False, 'error': str(e)}


def activate_subscription(user, plan):
    """Activate subscription after successful payment"""
    expires_at = timezone.now() + timedelta(days=plan.duration_days)

    # deactivate any existing active subscription
    UserSubscription.objects.filter(
        user=user,
        status=UserSubscription.STATUS_ACTIVE
    ).update(status=UserSubscription.STATUS_EXPIRED)

    # create new subscription
    subscription = UserSubscription.objects.create(
        user=user,
        plan=plan,
        status=UserSubscription.STATUS_ACTIVE,
        expires_at=expires_at,
    )

    # update user flags
    user.is_subscribed = True
    user.subscription_end_date = expires_at
    user.save()

    return subscription


def check_and_expire_subscriptions(user):
    """Check if subscription has expired and update accordingly"""
    if not user.is_subscribed:
        return

    active_sub = UserSubscription.objects.filter(
        user=user,
        status=UserSubscription.STATUS_ACTIVE
    ).first()

    if active_sub and active_sub.expires_at < timezone.now():
        active_sub.status = UserSubscription.STATUS_EXPIRED
        active_sub.save()
        user.is_subscribed = False
        user.subscription_end_date = None
        user.save()