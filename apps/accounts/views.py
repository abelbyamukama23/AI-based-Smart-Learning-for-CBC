"""
apps/accounts/views.py
───────────────────────
HTTP adapters only — all business logic lives in services.py.

Design Patterns:
  • Service Layer — views delegate to services, never touch ORM directly.
  • Explicit Exception Handling — no bare except; each exception type gets
    a specific, informative response (Circuit Breaker at the HTTP boundary).
"""

import logging

from rest_framework import status
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from .models import User
from .serializers import (
    CBCTokenObtainPairSerializer,
    RegisterSerializer,
    UserSerializer,
)
from .services import LearnerProfileService

logger = logging.getLogger(__name__)


class RegisterView(APIView):
    """POST /api/v1/auth/register/"""
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        user = serializer.save()
        refresh = RefreshToken.for_user(user)
        return Response(
            {
                "message": "Account created successfully.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class CustomTokenObtainPairView(TokenObtainPairView):
    """POST /api/v1/auth/login/ — JWT login."""
    serializer_class = CBCTokenObtainPairSerializer


class LogoutView(APIView):
    """
    POST /api/v1/auth/logout/

    Blacklists the provided refresh token.
    Explicit exception handling: KeyError and TokenError return different,
    descriptive error messages (no bare `except Exception`).
    """
    permission_classes = [IsAuthenticated]

    def post(self, request):
        refresh_token = request.data.get("refresh")
        if not refresh_token:
            return Response(
                {"detail": "A 'refresh' token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            RefreshToken(refresh_token).blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except TokenError as e:
            return Response(
                {"detail": f"Invalid or expired token: {e}"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Exception:
            logger.exception("Unexpected error during logout")
            return Response(
                {"detail": "An unexpected error occurred during logout."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class ProfileView(RetrieveUpdateAPIView):
    """
    GET  /api/v1/auth/profile/ — Retrieve authenticated user profile.
    PATCH /api/v1/auth/profile/ — Update username or learner class_level.
    """
    permission_classes = [IsAuthenticated]
    serializer_class = UserSerializer

    def get_object(self):
        return self.request.user

    def patch(self, request, *args, **kwargs):
        user = self.get_object()
        class_level = request.data.get("class_level")
        if class_level:
            LearnerProfileService.update_class_level(user, class_level)
            
        # Handle nested learner profile settings
        preferences = request.data.get("learner_profile", {})
        if preferences and hasattr(user, "learner_profile"):
            profile = user.learner_profile
            if "preferred_methodology" in preferences:
                profile.preferred_methodology = preferences["preferred_methodology"]
            if "preferred_language" in preferences:
                profile.preferred_language = preferences["preferred_language"]
            if "familiar_region" in preferences:
                profile.familiar_region = preferences["familiar_region"]
            if "preferred_subjects" in preferences:
                profile.preferred_subjects = preferences["preferred_subjects"]
            if "theme" in preferences:
                profile.theme = preferences["theme"]
            profile.save()

        return super().patch(request, *args, **kwargs)
