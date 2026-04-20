from django.db import models
from django.conf import settings
from apps.prompts.models import RoomType, DesignStyle, ColorTheme, RoomSize


class GenerationJob(models.Model):
    STATUS_PENDING = 'pending'
    STATUS_PROCESSING = 'processing'
    STATUS_COMPLETED = 'completed'
    STATUS_FAILED = 'failed'

    STATUS_CHOICES = [
        (STATUS_PENDING, 'Pending'),
        (STATUS_PROCESSING, 'Processing'),
        (STATUS_COMPLETED, 'Completed'),
        (STATUS_FAILED, 'Failed'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='generations'
    )
    input_image = models.ImageField(upload_to='uploads/rooms/')
    room_type = models.ForeignKey(RoomType, on_delete=models.SET_NULL, null=True)
    design_style = models.ForeignKey(DesignStyle, on_delete=models.SET_NULL, null=True)
    color_theme = models.ForeignKey(ColorTheme, on_delete=models.SET_NULL, null=True)
    room_size = models.ForeignKey(RoomSize, on_delete=models.SET_NULL, null=True)
    num_samples = models.IntegerField(default=1)
    prompt_used = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default=STATUS_PENDING)
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.email} - {self.room_type} - {self.status}"


class GeneratedImage(models.Model):
    job = models.ForeignKey(GenerationJob, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='generated/')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Image for job {self.job.id}"