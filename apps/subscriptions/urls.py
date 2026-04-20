from django.urls import path
from .views import PlanListView, CreateCheckoutView, SubscriptionStatusView, StripeWebhookView

urlpatterns = [
    path('plans/', PlanListView.as_view(), name='plans'),
    path('checkout/', CreateCheckoutView.as_view(), name='checkout'),
    path('status/', SubscriptionStatusView.as_view(), name='subscription-status'),
    path('webhook/', StripeWebhookView.as_view(), name='stripe-webhook'),
]