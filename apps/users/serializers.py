from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'credits', 'is_subscribed', 'subscription_end_date', 'created_at']
        read_only_fields = ['id', 'credits', 'is_subscribed', 'subscription_end_date', 'created_at']


class GoogleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()  # Google ID token from frontend


class AppleAuthSerializer(serializers.Serializer):
    token = serializers.CharField()       # Apple identity token
    first_name = serializers.CharField(required=False, allow_blank=True)
    last_name = serializers.CharField(required=False, allow_blank=True)