from django.urls import path
from .views import OptionsView, GenerationView, HistoryView, GenerationDetailView

urlpatterns = [
    path('options/', OptionsView.as_view(), name='options'),
    path('generate/', GenerationView.as_view(), name='generate'),
    path('history/', HistoryView.as_view(), name='history'),
    path('history/<int:pk>/', GenerationDetailView.as_view(), name='generation-detail'),
]