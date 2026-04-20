from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    model = CustomUser
    list_display = ['email', 'username', 'credits', 'is_subscribed', 'is_staff', 'created_at']
    list_filter = ['is_subscribed', 'is_staff', 'is_active']
    search_fields = ['email', 'username']
    ordering = ['-created_at']
    fieldsets = UserAdmin.fieldsets + (
        ('App Info', {
            'fields': ('credits', 'is_subscribed', 'subscription_end_date', 'google_id', 'apple_id')
        }),
    )