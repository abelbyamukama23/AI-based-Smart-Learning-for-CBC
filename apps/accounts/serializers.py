"""
apps/accounts/serializers.py
─────────────────────────────
Serializers are pure I/O adapters — they validate and shape data only.
All business logic has been moved to apps/accounts/services.py.

Design Principle (SRP): Serializers no longer orchestrate DB writes.
Design Principle (DIP): RegisterSerializer delegates to UserRegistrationService.
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from .models import Learner, Role, School, User


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ["id", "school_name", "region", "district"]


class LearnerProfileSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)

    class Meta:
        model = Learner
        fields = ["class_level", "enrolled_at", "school", "preferred_methodology", "preferred_language", "familiar_region", "preferred_subjects", "theme"]


class UserSerializer(serializers.ModelSerializer):
    learner_profile = LearnerProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ["id", "email", "username", "first_name", "last_name", "role", "is_active", "date_joined", "learner_profile"]


class RegisterSerializer(serializers.Serializer):
    """Input validator for POST /api/v1/auth/register/."""

    email      = serializers.EmailField()
    password   = serializers.CharField(write_only=True, min_length=8)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name  = serializers.CharField(max_length=150, required=False, allow_blank=True)
    username   = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role       = serializers.ChoiceField(choices=Role.choices, default=Role.LEARNER)

    # Learner-specific fields (required when role=LEARNER)
    class_level  = serializers.ChoiceField(choices=[("S1","S1"),("S2","S2"),("S3","S3"),("S4","S4"),("S5","S5"),("S6","S6")], required=False)
    school_name  = serializers.CharField(max_length=200, required=False, allow_blank=True)
    region       = serializers.CharField(max_length=100, required=False, allow_blank=True)
    district     = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate(self, data):
        """Cross-field validation only — uniqueness checked in the service."""
        role = data.get("role", Role.LEARNER)
        if role == Role.LEARNER:
            for field in ["class_level", "school_name", "region", "district"]:
                if not data.get(field):
                    raise serializers.ValidationError(
                        {field: "This field is required for learners."}
                    )
        return data

    def create(self, validated_data):
        """
        Delegates to UserRegistrationService.
        The serializer never touches the ORM directly.
        """
        from .services import UserRegistrationService
        from .exceptions import DuplicateEmailError, InvalidRoleDataError
        try:
            return UserRegistrationService.register(validated_data)
        except DuplicateEmailError as e:
            raise serializers.ValidationError({"email": str(e)})
        except InvalidRoleDataError as e:
            raise serializers.ValidationError({"non_field_errors": str(e)})


class CBCTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT token with minimal custom claims.

    Design Principle — Claims Minimization:
      Only embed STABLE, IMMUTABLE identity facts.
      Dynamic attributes (class_level) are fetched from the DB per-request,
      not embedded in a 60-minute-lived token that would go stale on promotion.
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)
        # Stable identity claims only
        token["role"] = user.role
        # Removed: email, class_level — these are now served from /api/v1/auth/profile/
        return token
