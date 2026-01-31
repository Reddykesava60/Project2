"""
Views for the Users app.
"""

from rest_framework import generics, status, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model

from apps.core.audit import create_audit_log, AuditLog, get_client_ip
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    PasswordChangeSerializer,
    LoginHistorySerializer,
)
from .models import LoginHistory

User = get_user_model()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom token serializer that records login history."""
    
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user info to response
        user = self.user
        data['user'] = UserSerializer(user).data
        
        return data


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom login view that records login history and audit logs.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    def post(self, request, *args, **kwargs):
        ip_address = get_client_ip(request)
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
        
        # Attempt login
        serializer = self.get_serializer(data=request.data)
        
        try:
            serializer.is_valid(raise_exception=True)
            user = serializer.user
            
            # Record successful login
            LoginHistory.objects.create(
                user=user,
                ip_address=ip_address,
                user_agent=user_agent,
                success=True
            )
            
            # Update user's last login IP
            user.last_login_ip = ip_address
            user.save(update_fields=['last_login_ip'])
            
            # Get restaurant for audit log
            restaurant = None
            if user.role in ['staff', 'STAFF']:
                staff_profile = getattr(user, 'staff_profile', None)
                if staff_profile and staff_profile.restaurant:
                    restaurant = staff_profile.restaurant
            elif user.role in ['restaurant_owner', 'OWNER']:
                restaurant = user.owned_restaurants.first()
            elif user.restaurant:
                restaurant = user.restaurant
            
            # Audit log
            create_audit_log(
                action=AuditLog.Action.LOGIN_SUCCESS,
                user=user,
                restaurant=restaurant,
                description=f'User logged in successfully',
                ip_address=ip_address,
                user_agent=user_agent
            )
            
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
            
        except Exception as e:
            # Record failed login attempt
            email = request.data.get('email') or request.data.get('username')
            if email:
                try:
                    user = User.objects.get(email=email)
                    LoginHistory.objects.create(
                        user=user,
                        ip_address=ip_address,
                        user_agent=user_agent,
                        success=False
                    )
                    
                    # Audit log for failed attempt
                    create_audit_log(
                        action=AuditLog.Action.LOGIN_FAILED,
                        user=user,
                        description=f'Failed login attempt',
                        ip_address=ip_address,
                        user_agent=user_agent,
                        severity=AuditLog.Severity.WARNING
                    )
                except User.DoesNotExist:
                    # User doesn't exist - still log for security
                    create_audit_log(
                        action=AuditLog.Action.LOGIN_FAILED,
                        description=f'Failed login attempt for unknown email: {email}',
                        ip_address=ip_address,
                        user_agent=user_agent,
                        severity=AuditLog.Severity.WARNING
                    )
            
            raise


class RegisterView(generics.CreateAPIView):
    """Register a new user (restaurant owner)."""
    
    queryset = User.objects.all()
    serializer_class = UserCreateSerializer
    permission_classes = [permissions.AllowAny]
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'user': UserSerializer(user).data,
            'tokens': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            }
        }, status=status.HTTP_201_CREATED)


class ProfileView(generics.RetrieveUpdateAPIView):
    """
    Get or update current user profile.
    
    This is the /api/me endpoint that frontend uses.
    Returns user info including role, restaurant_id, permissions.
    """
    
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_object(self):
        return self.request.user


class PasswordChangeView(APIView):
    """Change user password."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        serializer = PasswordChangeSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        # Audit log
        create_audit_log(
            action=AuditLog.Action.PASSWORD_CHANGE,
            user=request.user,
            description='User changed their password',
            request=request
        )
        
        return Response({'message': 'Password changed successfully.'})


class LoginHistoryView(generics.ListAPIView):
    """List login history for current user."""
    
    serializer_class = LoginHistorySerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return LoginHistory.objects.filter(user=self.request.user)[:50]


class LogoutView(APIView):
    """Logout user by blacklisting refresh token."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            
            # Audit log
            create_audit_log(
                action=AuditLog.Action.LOGOUT,
                user=request.user,
                description='User logged out',
                request=request
            )
            
            return Response({'message': 'Logged out successfully.'})
        except Exception:
            return Response(
                {
                    'error': 'INVALID_TOKEN',
                    'message': 'Invalid token.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
