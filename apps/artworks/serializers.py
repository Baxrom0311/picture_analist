"""
Serializers for Artworks app.
"""
from rest_framework import serializers
from .models import Category, Artwork
from .services.image_service import ImageService
from core.language import SUPPORTED_LANGUAGES, DEFAULT_LANGUAGE


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for Category model."""

    class Meta:
        model = Category
        fields = (
            'id', 
            'name', 'name_uz', 'name_ru', 'name_en',
            'description', 'description_uz', 'description_ru', 'description_en',
            'weight', 'criteria', 'is_active'
        )
        read_only_fields = ('id',)


class ArtworkListSerializer(serializers.ModelSerializer):
    """Serializer for Artwork list view (lightweight)."""
    user = serializers.StringRelatedField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    evaluation_score = serializers.SerializerMethodField()

    class Meta:
        model = Artwork
        fields = (
            'id', 'title', 'user', 'image', 'evaluation_scheme', 'status', 'status_display',
            'format', 'created_at', 'evaluation_score'
        )

    def get_evaluation_score(self, obj) -> float | None:
        if hasattr(obj, 'evaluation'):
            try:
                return float(obj.evaluation.total_score)
            except Exception:
                pass
        return None


class ArtworkDetailSerializer(serializers.ModelSerializer):
    """Serializer for Artwork detail view (full info)."""
    user = serializers.StringRelatedField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = Artwork
        fields = (
            'id', 'user', 'title', 'description', 'image', 'image_url',
            'file_size', 'width', 'height', 'format', 'evaluation_scheme', 'status',
            'status_display', 'created_at', 'updated_at'
        )
        read_only_fields = (
            'id', 'user', 'image_url', 'file_size', 'width', 'height',
            'format', 'status', 'created_at', 'updated_at'
        )


class ArtworkCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a new Artwork (upload)."""
    title = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True, default='')
    evaluation_scheme = serializers.ChoiceField(
        choices=Artwork.EVALUATION_SCHEME_CHOICES,
        required=False,
        default='painting',
    )
    language = serializers.ChoiceField(
        choices=tuple((code, code.upper()) for code in SUPPORTED_LANGUAGES),
        required=False,
        default=DEFAULT_LANGUAGE,
        write_only=True,
    )

    class Meta:
        model = Artwork
        fields = ('title', 'description', 'image', 'evaluation_scheme', 'language')

    def validate_title(self, value):
        from core.sanitizers import sanitize_text
        return sanitize_text(value)

    def validate_description(self, value):
        from core.sanitizers import sanitize_text
        return sanitize_text(value) if value else value

    def validate_image(self, value):
        ImageService().validate_image(value)
        return value

    def create(self, validated_data):
        validated_data.pop('language', None)
        validated_data.setdefault('user', self.context['request'].user)
        return super().create(validated_data)
