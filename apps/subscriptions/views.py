import razorpay
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from .services import create_order, verify_and_activate, check_and_expire_subscriptions
from django.contrib.auth import get_user_model

User = get_user_model()
client = razorpay.Client(auth=(settings.RAZORPAY_KEY_ID, settings.RAZORPAY_KEY_SECRET))


class PlanListView(APIView):
    """Get all active subscription plans."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        return Response(SubscriptionPlanSerializer(plans, many=True).data)


class CreateOrderView(APIView):
    """
    Create a Razorpay Order for a plan.

    Replaces Stripe's CreateCheckoutView.
    Returns order details that the frontend uses to open Razorpay checkout popup.
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
            'order_id':  result['order_id'],
            'amount':    result['amount'],
            'currency':  result['currency'],
            'key_id':    result['key_id'],   # frontend Razorpay.js needs this
        })


class VerifyPaymentView(APIView):
    """
    Verify Razorpay payment after the frontend completes checkout.

    Razorpay does NOT redirect like Stripe — instead the frontend receives
    payment details in a callback and must POST them here for server-side
    signature verification before we activate the subscription.

    Expected body:
        plan_id
        razorpay_order_id
        razorpay_payment_id
        razorpay_signature
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        razorpay_order_id   = request.data.get('razorpay_order_id')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_signature  = request.data.get('razorpay_signature')

        if not all([plan_id, razorpay_order_id, razorpay_payment_id, razorpay_signature]):
            return Response(
                {'error': 'plan_id, razorpay_order_id, razorpay_payment_id and razorpay_signature are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        result = verify_and_activate(
            user=request.user,
            plan=plan,
            payment_data={
                'razorpay_order_id':   razorpay_order_id,
                'razorpay_payment_id': razorpay_payment_id,
                'razorpay_signature':  razorpay_signature,
            }
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
            'credits':       user.credits,
            'subscription':  UserSubscriptionSerializer(active_sub).data if active_sub else None,
        })


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """
    Razorpay webhook — optional but recommended for reliability.
    Handles cases where the user closes the browser before VerifyPaymentView is called.

    Enable in Razorpay Dashboard → Webhooks → payment.captured

    Add RAZORPAY_WEBHOOK_SECRET to settings.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        webhook_secret = getattr(settings, 'RAZORPAY_WEBHOOK_SECRET', None)
        webhook_signature = request.META.get('HTTP_X_RAZORPAY_SIGNATURE')

        # Verify webhook signature if secret is configured
        if webhook_secret:
            try:
                client.utility.verify_webhook_signature(
                    request.body.decode('utf-8'),
                    webhook_signature,
                    webhook_secret
                )
            except razorpay.errors.SignatureVerificationError:
                return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        import json
        try:
            payload = json.loads(request.body)
        except json.JSONDecodeError:
            return Response({'error': 'Invalid JSON'}, status=status.HTTP_400_BAD_REQUEST)

        event = payload.get('event')

        if event == 'payment.captured':
            payment = payload['payload']['payment']['entity']
            notes = payment.get('notes', {})

            user_id = notes.get('user_id')
            plan_id = notes.get('plan_id')

            try:
                user = User.objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
            except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
                return Response({'error': 'User or plan not found'}, status=status.HTTP_404_NOT_FOUND)

            # Only activate if not already active (VerifyPaymentView may have done it already)
            already_active = UserSubscription.objects.filter(
                user=user,
                status=UserSubscription.STATUS_ACTIVE,
                payment_reference=payment['id']
            ).exists()

            if not already_active:
                from .services import activate_subscription
                activate_subscription(user, plan, payment_reference=payment['id'])

        return Response({'status': 'ok'})