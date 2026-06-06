from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status
from django.utils import timezone
from django.core.files.base import ContentFile
import requests
import uuid

from .models import GenerationJob, GeneratedImage
from .serializers import GenerationJobCreateSerializer, GenerationJobSerializer
from .services import generate_images   
from apps.prompts.models import RoomType, DesignStyle, ColorTheme, RoomSize, PromptTemplate


class OptionsView(APIView):
    """Returns all active options for frontend dropdowns"""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({
            'room_types': [{'id': r.id, 'name': r.name, 'slug': r.slug} for r in RoomType.objects.filter(is_active=True)],
            'design_styles': [{'id': d.id, 'name': d.name, 'slug': d.slug} for d in DesignStyle.objects.filter(is_active=True)],
            'color_themes': [{'id': c.id, 'name': c.name, 'slug': c.slug} for c in ColorTheme.objects.filter(is_active=True)],
            'room_sizes': [{'id': s.id, 'name': s.name, 'slug': s.slug} for s in RoomSize.objects.filter(is_active=True)],
        })


class GenerationView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # check credits
        if not user.has_credits():
            return Response(
                {'error': 'No credits remaining. Please subscribe to continue.'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        serializer = GenerationJobCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        # fetch selected options
        room_type = RoomType.objects.get(id=data['room_type_id'])
        design_style = DesignStyle.objects.get(id=data['design_style_id'])
        color_theme = ColorTheme.objects.get(id=data['color_theme_id'])
        room_size = RoomSize.objects.get(id=data['room_size_id'])
        num_samples = data['num_samples']

        # find matching prompt template
        try:
            prompt_template = PromptTemplate.objects.get(
                room_type=room_type,
                design_style=design_style,
                color_theme=color_theme,
                room_size=room_size,
                is_active=True,
            )
            prompt_text = prompt_template.prompt_text
        except PromptTemplate.DoesNotExist:
            # fallback prompt if no template found
            prompt_text = (
                f"Redesign this {room_size.name.lower()} {room_type.name.lower()} "
                f"in {design_style.name.lower()} style with {color_theme.name.lower()} color theme. "
                f"Photorealistic, high quality interior design."
            )

        # create job
        job = GenerationJob.objects.create(
            user=user,
            input_image=data['input_image'],
            room_type=room_type,
            design_style=design_style,
            color_theme=color_theme,
            room_size=room_size,
            num_samples=num_samples,
            prompt_used=prompt_text,
            status=GenerationJob.STATUS_PROCESSING,
        )

        # call AI API
        result = generate_images(job.input_image.path, prompt_text, num_samples)

        if not result['success']:
            job.status = GenerationJob.STATUS_FAILED
            job.error_message = result.get('error', 'Unknown error')
            job.save()
            return Response(
                {'error': job.error_message},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

        # save generated images from base64
        import base64
        for img_b64 in result.get('image_b64_list', []):
            filename = f"{uuid.uuid4()}.jpg"
            generated = GeneratedImage(job=job)
            generated.image.save(filename, ContentFile(base64.b64decode(img_b64)), save=True)

        # save generated images from URLs
        for img_url in result.get('image_urls', []):
            try:
                img_response = requests.get(img_url, timeout=10)
                img_response.raise_for_status()
                filename = f"{uuid.uuid4()}.jpg"
                generated = GeneratedImage(job=job)
                generated.image.save(filename, ContentFile(img_response.content), save=True)
            except Exception:
                pass

        # update job status
        job.status = GenerationJob.STATUS_COMPLETED
        job.completed_at = timezone.now()
        job.save()

        # deduct credit
        user.deduct_credit(count=1)

        return Response(GenerationJobSerializer(job, context={'request': request}).data, status=status.HTTP_201_CREATED)


class HistoryView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        jobs = GenerationJob.objects.filter(
            user=request.user
        ).prefetch_related('images').order_by('-created_at')
        return Response(GenerationJobSerializer(jobs, many=True, context={'request': request}).data)


class GenerationDetailView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        try:
            job = GenerationJob.objects.prefetch_related('images').get(pk=pk, user=request.user)
        except GenerationJob.DoesNotExist:
            return Response({'error': 'Not found'}, status=status.HTTP_404_NOT_FOUND)
        return Response(GenerationJobSerializer(job, context={'request': request}).data)