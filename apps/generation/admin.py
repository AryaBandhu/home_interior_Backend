from django.contrib import admin
from .models import GenerationJob, GeneratedImage


class GeneratedImageInline(admin.TabularInline):
    model = GeneratedImage
    extra = 0
    readonly_fields = ['image', 'created_at']


@admin.register(GenerationJob)
class GenerationJobAdmin(admin.ModelAdmin):
    list_display = ['user', 'room_type', 'design_style', 'color_theme', 'room_size', 'num_samples', 'status', 'created_at']
    list_filter = ['status', 'room_type', 'design_style', 'color_theme', 'room_size']
    search_fields = ['user__email', 'prompt_used']
    ordering = ['-created_at']
    readonly_fields = ['prompt_used', 'created_at', 'completed_at']
    inlines = [GeneratedImageInline]


@admin.register(GeneratedImage)
class GeneratedImageAdmin(admin.ModelAdmin):
    list_display = ['job', 'image', 'created_at']
    ordering = ['-created_at']