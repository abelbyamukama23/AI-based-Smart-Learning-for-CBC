from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.generics import RetrieveUpdateAPIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User
from .serializers import (
    RegisterSerializer,
    UserSerializer,
    CBCTokenObtainPairSerializer,
    LearnerProfileSerializer
)

class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            # Generate tokens for immediate login
            refresh = RefreshToken.for_user(user)
            return Response({
                "message": "Account created successfully.",
                "user": UserSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                }
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CBCTokenObtainPairSerializer

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data["refresh"]
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(status=status.HTTP_205_RESET_CONTENT)
        except Exception:
            return Response(status=status.HTTP_400_BAD_REQUEST)

class ProfileView(RetrieveUpdateAPIView):
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        # We handle partial updates differently if they update Learner data vs User data.
        # For simplicity in MVP, we just expose the full UserSerializer for GET,
        # but for PATCH, we might just update class_level.
        # To keep it standard, we'll use UserSerializer for both, 
        # but custom update logic might be needed if they want to update nested LearnerProfile.
        return UserSerializer
        
    def patch(self, request, *args, **kwargs):
        # Handle updating class_level in the nested Learner model
        user = self.get_object()
        class_level = request.data.get('class_level')
        
        if class_level and hasattr(user, 'learner_profile'):
            user.learner_profile.class_level = class_level
            user.learner_profile.save()
            
        # Continue with normal user update (e.g. username) if provided
        return super().patch(request, *args, **kwargs)
