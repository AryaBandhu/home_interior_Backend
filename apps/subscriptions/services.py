import requests
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
from .models import SubscriptionPlan, UserSubscription


def get_cashfree_headers():
    return {
        'x-client-id': settings.CASHFREE_APP_ID,
        'x-client-secret': settings.CASHFREE_SECRET_KEY,
        'x-api-version': '2023-08-01',
        'Content-Type': 'application/json',
    }


def get_cashfree_base_url():
    if settings.CASHFREE_ENV == 'PRODUCTION':
        return 'https://api.cashfree.com/pg'
    return 'https://sandbox.cashfree.com/pg'


def create_order(user, plan):
    """
    Create a Cashfree order server-side.
    Returns order_id and payment_session_id for frontend checkout.
    """
    import uuid
    order_id = f"order_{user.id}_{plan.id}_{uuid.uuid4().hex[:8]}"
    amount = float(plan.price)

    payload = {
        'order_id': order_id,
        'order_amount': amount,
        'order_currency': 'INR',
        'customer_details': {
            'customer_id': str(user.id),
            'customer_email': user.email,
            'customer_phone': '9999999999',  # fallback, Cashfree requires phone
            'customer_name': user.get_full_name() or user.username or 'Customer',
        },
        'order_meta': {
            'return_url': f"{settings.FRONTEND_URL.split(',')[0].strip()}/pricing?order_id={{order_id}}",
        },
        'order_note': f'user_{user.id}_plan_{plan.id}',
        'order_tags': {
            'user_id': str(user.id),
            'plan_id': str(plan.id),
        },
    }

    try:
        response = requests.post(
            f"{get_cashfree_base_url()}/orders",
            headers=get_cashfree_headers(),
            json=payload,
            timeout=15,
        )
        response.raise_for_status()
        data = response.json()

        return {
            'success': True,
            'order_id': data['order_id'],
            'payment_session_id': data['payment_session_id'],
            'order_amount': amount,
            'order_currency': 'INR',
            'env': settings.CASHFREE_ENV,
        }
    except requests.exceptions.HTTPError as e:
        error_msg = e.response.json().get('message', str(e)) if e.response else str(e)
        return {'success': False, 'error': error_msg}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def verify_payment(order_id):
    """
    Verify payment status with Cashfree API.
    Returns True if payment is successful.
    """
    try:
        response = requests.get(
            f"{get_cashfree_base_url()}/orders/{order_id}/payments",
            headers=get_cashfree_headers(),
            timeout=15,
        )
        response.raise_for_status()
        payments = response.json()

        for payment in payments:
            if payment.get('payment_status') == 'SUCCESS':
                return {
                    'success': True,
                    'payment_id': payment.get('cf_payment_id'),
                }

        return {'success': False, 'error': 'Payment not successful'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def get_order_details(order_id):
    """Fetch order details from Cashfree."""
    try:
        response = requests.get(
            f"{get_cashfree_base_url()}/orders/{order_id}",
            headers=get_cashfree_headers(),
            timeout=15,
        )
        response.raise_for_status()
        return {'success': True, 'data': response.json()}
    except Exception as e:
        return {'success': False, 'error': str(e)}


def verify_and_activate(user, plan, order_id):
    """
    Verify Cashfree payment and activate subscription.
    """
    result = verify_payment(order_id)
    if not result['success']:
        return result

    payment_id = result.get('payment_id', order_id)

    # Check if already activated (idempotency)
    already_active = UserSubscription.objects.filter(
        user=user,
        status=UserSubscription.STATUS_ACTIVE,
        payment_reference=str(payment_id),
    ).exists()

    if already_active:
        return {'success': True, 'message': 'Already activated'}

    subscription = activate_subscription(user, plan, payment_reference=str(payment_id))
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
