import stripe
from django.conf import settings
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework import status

from .models import SubscriptionPlan, UserSubscription
from .serializers import SubscriptionPlanSerializer, UserSubscriptionSerializer
from .services import create_checkout_session, activate_subscription, check_and_expire_subscriptions
from django.contrib.auth import get_user_model

User = get_user_model()
stripe.api_key = settings.STRIPE_SECRET_KEY


class PlanListView(APIView):
    """Get all active subscription plans"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        plans = SubscriptionPlan.objects.filter(is_active=True).order_by('price')
        return Response(SubscriptionPlanSerializer(plans, many=True).data)


class CreateCheckoutView(APIView):
    """Create Stripe checkout session for a plan"""
    permission_classes = [IsAuthenticated]

    def post(self, request):
        plan_id = request.data.get('plan_id')
        if not plan_id:
            return Response({'error': 'plan_id is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            plan = SubscriptionPlan.objects.get(id=plan_id, is_active=True)
        except SubscriptionPlan.DoesNotExist:
            return Response({'error': 'Plan not found'}, status=status.HTTP_404_NOT_FOUND)

        result = create_checkout_session(request.user, plan)

        if not result['success']:
            return Response({'error': result['error']}, status=status.HTTP_400_BAD_REQUEST)

        return Response({
            'checkout_url': result['checkout_url'],
            'session_id': result['session_id'],
        })


class SubscriptionStatusView(APIView):
    """Get current user subscription status"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user

        # check and expire if needed
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
class StripeWebhookView(APIView):
    """
    Stripe webhook — called by Stripe after payment.
    This is how we know payment succeeded.
    Add this URL in Stripe dashboard → Webhooks.
    """
    permission_classes = [AllowAny]

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
            )
        except ValueError:
            return Response({'error': 'Invalid payload'}, status=status.HTTP_400_BAD_REQUEST)
        except stripe.error.SignatureVerificationError:
            return Response({'error': 'Invalid signature'}, status=status.HTTP_400_BAD_REQUEST)

        # handle successful payment
        if event['type'] == 'checkout.session.completed':
            session = event['data']['object']

            user_id = session['metadata'].get('user_id')
            plan_id = session['metadata'].get('plan_id')

            try:
                user = User.objects.get(id=user_id)
                plan = SubscriptionPlan.objects.get(id=plan_id)
                activate_subscription(user, plan)
            except (User.DoesNotExist, SubscriptionPlan.DoesNotExist):
                return Response({'error': 'User or plan not found'}, status=status.HTTP_404_NOT_FOUND)

        return Response({'status': 'ok'})