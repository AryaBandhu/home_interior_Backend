import razorpay
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, UserSubscription

client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


def create_order(user, plan):
    """
    Create a Razorpay Order server-side.
    The frontend uses this order_id to open the Razorpay checkout popup.
    """
    try:
        order = client.order.create({
            'amount': int(plan.price * 100),   # paise (INR) or smallest currency unit
            'currency': 'INR',                  # change to your currency if needed
            'receipt': f'user_{user.id}_plan_{plan.id}',
            'notes': {
                'user_id': str(user.id),
                'plan_id': str(plan.id),
            }
        })
        return {
            'success': True,
            'order_id': order['id'],
            'amount': order['amount'],
            'currency': order['currency'],
            'key_id': settings.RAZORPAY_KEY_ID,   # frontend needs this to open checkout
        }
    except razorpay.errors.BadRequestError as e:
        return {'success': False, 'error': str(e)}


def verify_and_activate(user, plan, payment_data):
    """
    Verify Razorpay payment signature, then activate subscription.
    Call this after frontend completes payment and sends back payment details.

    payment_data must contain:
        razorpay_order_id
        razorpay_payment_id
        razorpay_signature
    """
    try:
        client.utility.verify_payment_signature({
            'razorpay_order_id':   payment_data['razorpay_order_id'],
            'razorpay_payment_id': payment_data['razorpay_payment_id'],
            'razorpay_signature':  payment_data['razorpay_signature'],
        })
    except razorpay.errors.SignatureVerificationError:
        return {'success': False, 'error': 'Invalid payment signature'}

    subscription = activate_subscription(
        user, plan, payment_reference=payment_data['razorpay_payment_id']
    )
    return {'success': True, 'subscription': subscription}


def activate_subscription(user, plan, payment_reference=''):
    """Activate subscription after verified payment."""
    expires_at = timezone.now() + timedelta(days=plan.duration_days)

    # Deactivate any existing active subscription
    UserSubscription.objects.filter(
        user=user,
        status=UserSubscription.STATUS_ACTIVE
    ).update(status=UserSubscription.STATUS_EXPIRED)

    # Create new subscription
    subscription = UserSubscription.objects.create(
        user=user,
        plan=plan,
        status=UserSubscription.STATUS_ACTIVE,
        expires_at=expires_at,
        payment_reference=payment_reference,
    )

    # Update user flags
    user.is_subscribed = True
    user.subscription_end_date = expires_at

    # Grant credits based on plan
    if plan.unlimited:
        user.credits = -1  # -1 signals unlimited
    else:
        user.credits += plan.credits_granted

    user.save()

    return subscription


def check_and_expire_subscriptions(user):
    """Check if subscription has expired and update accordingly."""
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
        # Reset unlimited credits to 0 on expiry
        if user.credits == -1:
            user.credits = 0
        user.save()