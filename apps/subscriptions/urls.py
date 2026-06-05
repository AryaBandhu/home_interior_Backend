from django.urls import path
from .views import PlanListView, CreateOrderView, VerifyPaymentView, SubscriptionStatusView, RazorpayWebhookView

urlpatterns = [
    path('plans/',          PlanListView.as_view(),          name='plans'),
    path('create-order/',   CreateOrderView.as_view(),       name='create-order'),
    path('verify-payment/', VerifyPaymentView.as_view(),     name='verify-payment'),
    path('status/',         SubscriptionStatusView.as_view(),name='subscription-status'),
    path('webhook/',        RazorpayWebhookView.as_view(),   name='razorpay-webhook'),
]