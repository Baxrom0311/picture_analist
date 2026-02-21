"""
Serializers for Users app.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    password = serializers.CharField(
        write_only=True,
        required=True,
        validators=[validate_password],
        style={'input_type': 'password'}
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={'input_type': 'password'}
    )

    class Meta:
        model = User
        fields = (
            'username', 'email', 'password', 'password_confirm',
            'first_name', 'last_name'
        )

    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError(
                {'password_confirm': 'Parollar mos kelmadi.'}
            )
        return attrs

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        # Public registration must never allow privileged role assignment.
        validated_data['role'] = 'artist'
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile view/update."""
    artworks_count = serializers.SerializerMethodField()
    evaluations_count = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'email', 'first_name', 'last_name',
            'role', 'phone', 'avatar', 'bio', 'credits',
            'date_joined', 'artworks_count', 'evaluations_count'
        )
        read_only_fields = ('id', 'username', 'role', 'credits', 'date_joined')

    def get_artworks_count(self, obj) -> int:
        return obj.artworks.count()

    def get_evaluations_count(self, obj) -> int:
        return obj.artworks.filter(status='completed').count()


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics."""
    total_artworks = serializers.IntegerField()
    evaluated_artworks = serializers.IntegerField()
    pending_artworks = serializers.IntegerField()
    average_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    highest_score = serializers.DecimalField(max_digits=5, decimal_places=2, allow_null=True)
    credits_remaining = serializers.IntegerField()
    total_api_cost = serializers.DecimalField(max_digits=10, decimal_places=4, allow_null=True)


class ChangePasswordSerializer(serializers.Serializer):
    """Serializer for password change."""
    old_password = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, validators=[validate_password])

    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Joriy parol noto\'g\'ri.')
        return value
