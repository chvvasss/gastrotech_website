"""
Views for the accounts app.

Security Features:
- Login rate limiting: 5 attempts/minute, 20 attempts/hour per IP
- Prevents brute force and credential stuffing attacks
"""

from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from .serializers import EmailTokenObtainPairSerializer, UserMeSerializer


class LoginRateThrottle(AnonRateThrottle):
    """Rate limit for login attempts: 5 per minute per IP."""

    rate = "5/minute"
    scope = "login"


class LoginBurstThrottle(AnonRateThrottle):
    """Burst protection for login attempts: 20 per hour per IP."""

    rate = "20/hour"
    scope = "login_burst"


class UserMeView(APIView):
    """
    API endpoint to retrieve the current authenticated user's information.

    GET /api/v1/auth/me
    Returns: {id, email, role, is_active}
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return the current user's information."""
        serializer = UserMeSerializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class EmailTokenObtainPairView(APIView):
    """
    Custom JWT login view that accepts email instead of username.

    POST /api/v1/auth/login/
    Body: {"email": "...", "password": "..."}
    Returns: {"access": "...", "refresh": "..."}

    Security:
    - Rate limited to 5 attempts/minute and 20 attempts/hour per IP
    - Returns 429 Too Many Requests when limit exceeded
    """

    permission_classes = [AllowAny]
    throttle_classes = [LoginRateThrottle, LoginBurstThrottle]

    def post(self, request):
        """Authenticate user and return JWT tokens."""
        serializer = EmailTokenObtainPairSerializer(
            data=request.data, 
            context={"request": request}
        )
        
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_401_UNAUTHORIZED)
