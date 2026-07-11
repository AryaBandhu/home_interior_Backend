import hashlib
import hmac
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from .services import create_order, verify_and_activate, check_and_expire_subscriptions, activate_subscription
from django.contrib.auth import get_user_model

User = get_user_model()


class PlanListView(APIView):
    """Get all active subscription plans."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        return Response(SubscriptionPlanSerializer(plans, many=True).data)


class PublicPlanListView(APIView):
    """Get all active subscription plans (public, no auth required)."""
    permission_classes = [AllowAny]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        return Response(SubscriptionPlanSerializer(plans, many=True).data)


class CreateOrderView(APIView):
    """
    Create a Cashfree Order for a plan.
    Returns order_id and payment_session_id for frontend checkout.
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({'error': 'plan_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        result = create_order(request.user, plan)

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'order_id': result['order_id'],
            'payment_session_id': result['payment_session_id'],
            'order_amount': result['order_amount'],
            'order_currency': result['order_currency'],
            'env': result['env'],
        })


class VerifyPaymentView(APIView):
    """
    Verify Cashfree payment after frontend checkout completes.

    Expected body:
        plan_id
        order_id
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        order_id = request.data.get('order_id')

        if not all([plan_id, order_id]):
            return Response(
                {'error': 'plan_id and order_id are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        result = verify_and_activate(
            user=request.user,
            plan=plan,
            order_id=order_id,
        )

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        return Response({'status': 'subscription activated'}, status=status.HTTP_200_OK)


class SubscriptionStatusView(APIView):
    """Get current user subscription status."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        check_and_expire_subscriptions(user)

        active_sub = UserSubscription.objects.filter(
            user=user,
            status=UserSubscription.STATUS_ACTIVE
        ).select_related('plan').first()

        return Response({
            'is_subscribed': user.is_subscribed,
            'credits': user.credits,
            'subscription': UserSubscriptionSerializer(active_sub).data if active_sub else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class CashfreeWebhookView(APIView):
    """
    Cashfree webhook for payment events.
    Handles cases where user closes browser before VerifyPaymentView is called.

    Enable in Cashfree Dashboard → Webhooks → PAYMENT_SUCCESS
    """
    permission_classes = [AllowAny]

    def post(self, request):
        # Verify webhook signature
        timestamp = request.headers.get('x-webhook-timestamp', '')
        signature = request.headers.get('x-webhook-signature', '')

        if settings.CASHFREE_SECRET_KEY and signature:
            raw_body = request.body.decode('utf-8')
            payload_to_sign = timestamp + raw_body
            expected_signature = hmac.new(
                settings.CASHFREE_SECRET_KEY.encode('utf-8'),
                payload_to_sign.encode('utf-8'),
                hashlib.sha256
            ).hexdigest()

            if not hmac.compare_digest(signature, expected_signature):
                return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        import json
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        event_type = payload.get('type')
        data = payload.get('data', {})

        if event_type == 'PAYMENT_SUCCESS_WEBHOOK':
            order = data.get('order', {})
            payment = data.get('payment', {})
            order_id = order.get('order_id', '')
            order_tags = order.get('order_tags', {})

            user_id = order_tags.get('user_id')
            plan_id = order_tags.get('plan_id')

            if not user_id or not plan_id:
                # Try parsing from order_note
                order_note = order.get('order_note', '')
                if 'user_' in order_note and '_plan_' in order_note:
                    parts = order_note.split('_')
                    try:
                        user_id = parts[1]
                        plan_id = parts[3]
                    except (IndexError, ValueError):
                        pass

            if not user_id or not plan_id:
                return Response({'error': 'Missing user/plan info'}, status=status.HTTP_400_BAD_REQUEST)

            try:
                user = User.objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
                return Response({'error': 'User or plan not found'}, status=status.HTTP_404_NOT_FOUND)

            # Only activate if not already done
            payment_id = str(payment.get('cf_payment_id', order_id))
            already_active = UserSubscription.objects.filter(
                user=user,
                status=UserSubscription.STATUS_ACTIVE,
                payment_reference=payment_id,
            ).exists()

            if not already_active:
                activate_subscription(user, plan, payment_reference=payment_id)

        return Response({'status': 'ok'})
