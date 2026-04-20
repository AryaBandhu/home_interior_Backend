from django.db import models


class RoomType(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class RoomSize(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class DesignStyle(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class ColorTheme(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return self.name


class PromptTemplate(models.Model):
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='prompts')
    design_style = models.ForeignKey(DesignStyle, on_delete=models.CASCADE, related_name='prompts')
    color_theme = models.ForeignKey(ColorTheme, on_delete=models.CASCADE, related_name='prompts')
    room_size = models.ForeignKey(RoomSize, on_delete=models.CASCADE, related_name='prompts')
    prompt_text = models.TextField()
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ['room_type', 'design_style', 'color_theme', 'room_size']

    def __str__(self):
        return f"{self.room_type} | {self.design_style} | {self.color_theme} | {self.room_size}"