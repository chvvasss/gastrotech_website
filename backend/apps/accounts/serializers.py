"""
Serializers for the accounts app.
"""

from django.contrib.auth import authenticate
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken

from .models import User


class UserMeSerializer(serializers.ModelSerializer):
    """
    Serializer for the current authenticated user.

    Returns basic user information including id, email, role, and is_active.
    """

    class Meta:
        model = User
        fields = ["id", "email", "role", "is_active"]
        read_only_fields = ["id", "email", "role", "is_active"]


class EmailTokenObtainPairSerializer(serializers.Serializer):
    """
    Custom JWT token serializer that accepts email instead of username.
    
    This is necessary because our User model uses email as USERNAME_FIELD,
    but SimpleJWT's default serializer expects a field named 'username'.
    """
    
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, style={"input_type": "password"})
    
    access = serializers.CharField(read_only=True)
    refresh = serializers.CharField(read_only=True)
    
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")
        
        if not email or not password:
            raise serializers.ValidationError({
                "detail": "Both email and password are required."
            })
        
        # Authenticate using email (since USERNAME_FIELD = 'email')
        user = authenticate(
            request=self.context.get("request"),
            username=email,  # Django's authenticate uses 'username' but our backend maps it to email
            password=password,
        )
        
        if not user:
            raise serializers.ValidationError({
                "detail": "Invalid email or password."
            })
        
        if not user.is_active:
            raise serializers.ValidationError({
                "detail": "User account is disabled."
            })
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return {
            "access": str(refresh.access_token),
            "refresh": str(refresh),
        }
