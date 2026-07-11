from django.urls import path
from .views import PlanListView, PublicPlanListView, CreateOrderView, VerifyPaymentView, SubscriptionStatusView, CashfreeWebhookView

urlpatterns = [
    path('plans/',          PlanListView.as_view(),          name='plans'),
    path('plans-public/',   PublicPlanListView.as_view(),    name='plans-public'),
    path('create-order/',   CreateOrderView.as_view(),       name='create-order'),
    path('verify-payment/', VerifyPaymentView.as_view(),     name='verify-payment'),
    path('status/',         SubscriptionStatusView.as_view(),name='subscription-status'),
    path('webhook/',        CashfreeWebhookView.as_view(),   name='cashfree-webhook'),
]
