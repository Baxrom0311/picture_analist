"""
Serializers for Evaluations app.
"""
from rest_framework import serializers
from .models import Evaluation, CategoryScore, EvaluationHistory
from apps.artworks.serializers import CategorySerializer


class CategoryScoreSerializer(serializers.ModelSerializer):
    """Serializer for CategoryScore - shows per-category evaluation details."""
    category = CategorySerializer(read_only=True)

    class Meta:
        model = CategoryScore
        fields = ('id', 'category', 'score', 'feedback', 'strengths', 'improvements')


class EvaluationHistorySerializer(serializers.ModelSerializer):
    """Serializer for evaluation lifecycle history."""
    action_display = serializers.CharField(source='get_action_display', read_only=True)

    class Meta:
        model = EvaluationHistory
        fields = ('id', 'action', 'action_display', 'message', 'metadata', 'created_at')


class EvaluationListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for evaluation list."""
    artwork_title = serializers.CharField(source='artwork.title', read_only=True)
    artwork_id = serializers.IntegerField(source='artwork.id', read_only=True)

    class Meta:
        model = Evaluation
        fields = (
            'id', 'artwork_id', 'artwork_title', 'total_score', 'grade',
            'processing_time', 'created_at'
        )


class EvaluationDetailSerializer(serializers.ModelSerializer):
    """Full serializer for evaluation detail with category scores and history."""
    category_scores = CategoryScoreSerializer(many=True, read_only=True)
    history = EvaluationHistorySerializer(many=True, read_only=True)
    artwork_id = serializers.IntegerField(source='artwork.id', read_only=True)
    artwork_title = serializers.CharField(source='artwork.title', read_only=True)
    artwork_image = serializers.ImageField(source='artwork.image', read_only=True)

    class Meta:
        model = Evaluation
        fields = (
            'id', 'artwork_id', 'artwork_title', 'artwork_image',
            'llm_provider', 'llm_model', 'prompt_version',
            'total_score', 'summary', 'grade', 'raw_response',
            'processing_time', 'api_cost', 'created_at',
            'category_scores', 'history'
        )
