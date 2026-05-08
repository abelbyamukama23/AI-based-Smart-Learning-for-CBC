from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.tokens import RefreshToken
from .models import User, Learner, School, Role, ClassLevel

class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = ['id', 'school_name', 'region', 'district']

class LearnerProfileSerializer(serializers.ModelSerializer):
    school = SchoolSerializer(read_only=True)
    class Meta:
        model = Learner
        fields = ['class_level', 'enrolled_at', 'school']

class UserSerializer(serializers.ModelSerializer):
    learner_profile = LearnerProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'role', 'is_active', 'date_joined', 'learner_profile']

class RegisterSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)
    first_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    last_name = serializers.CharField(max_length=150, required=False, allow_blank=True)
    username = serializers.CharField(max_length=150, required=False, allow_blank=True)
    role = serializers.ChoiceField(choices=Role.choices, default=Role.LEARNER)
    
    class_level = serializers.ChoiceField(choices=ClassLevel.choices, required=False)
    school_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    region = serializers.CharField(max_length=100, required=False, allow_blank=True)
    district = serializers.CharField(max_length=100, required=False, allow_blank=True)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value
        
    def validate(self, data):
        role = data.get('role', Role.LEARNER)
        if role == Role.LEARNER:
            required_learner_fields = ['class_level', 'school_name', 'region', 'district']
            for field in required_learner_fields:
                if not data.get(field):
                    raise serializers.ValidationError({field: "This field is required for learners."})
        return data

    def create(self, validated_data):
        role = validated_data.get('role', Role.LEARNER)
        username = validated_data.get('username') or validated_data['email'].split('@')[0]
        
        # 1. Create User
        user = User.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            role=role
        )

        # 2. Create Learner Profile if applicable
        if role == Role.LEARNER:
            school, _ = School.objects.get_or_create(
                school_name=validated_data.get('school_name'),
                defaults={
                    'region': validated_data.get('region'),
                    'district': validated_data.get('district')
                }
            )

            Learner.objects.create(
                user=user,
                school=school,
                class_level=validated_data.get('class_level')
            )
        return user

class CBCTokenObtainPairSerializer(TokenObtainPairSerializer):
    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims
        token['role'] = user.role
        token['email'] = user.email
        if user.role == Role.LEARNER and hasattr(user, 'learner_profile'):
            token['class_level'] = user.learner_profile.class_level
            
        return token
