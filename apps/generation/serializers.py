from rest_framework import serializers
from .models import GenerationJob, GeneratedImage
from apps.prompts.models import RoomType, DesignStyle, ColorTheme, RoomSize


class RoomTypeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomType
        fields = ['id', 'name', 'slug']


class DesignStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = DesignStyle
        fields = ['id', 'name', 'slug']


class ColorThemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ColorTheme
        fields = ['id', 'name', 'slug']


class RoomSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = RoomSize
        fields = ['id', 'name', 'slug']


class GeneratedImageSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedImage
        fields = ['id', 'image', 'created_at']

    def get_image(self, obj):
        request = self.context.get('request')
        if request and obj.image:
            return request.build_absolute_uri(obj.image.url)
        return obj.image.url if obj.image else None


class GenerationJobSerializer(serializers.ModelSerializer):
    images = GeneratedImageSerializer(many=True, read_only=True)
    room_type = RoomTypeSerializer(read_only=True)
    design_style = DesignStyleSerializer(read_only=True)
    color_theme = ColorThemeSerializer(read_only=True)
    room_size = RoomSizeSerializer(read_only=True)
    input_image = serializers.SerializerMethodField()

    class Meta:
        model = GenerationJob
        fields = [
            'id', 'input_image', 'room_type', 'design_style',
            'color_theme', 'room_size', 'num_samples', 'prompt_used',
            'status', 'error_message', 'created_at', 'completed_at', 'images'
        ]
        read_only_fields = ['prompt_used', 'status', 'error_message', 'created_at', 'completed_at']

    def get_input_image(self, obj):
        request = self.context.get('request')
        if request and obj.input_image:
            return request.build_absolute_uri(obj.input_image.url)
        return obj.input_image.url if obj.input_image else None


class GenerationJobCreateSerializer(serializers.Serializer):
    input_image = serializers.ImageField()
    room_type_id = serializers.IntegerField()
    design_style_id = serializers.IntegerField()
    color_theme_id = serializers.IntegerField()
    room_size_id = serializers.IntegerField()
    num_samples = serializers.IntegerField(min_value=1, max_value=4, default=1)

    def validate_room_type_id(self, value):
        if not RoomType.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Invalid room type')
        return value

    def validate_design_style_id(self, value):
        if not DesignStyle.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Invalid design style')
        return value

    def validate_color_theme_id(self, value):
        if not ColorTheme.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Invalid color theme')
        return value

    def validate_room_size_id(self, value):
        if not RoomSize.objects.filter(id=value, is_active=True).exists():
            raise serializers.ValidationError('Invalid room size')
        return value