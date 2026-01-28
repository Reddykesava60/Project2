"""
URL patterns for the Users app.
"""

from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView

from .views import (
    RegisterView,
    ProfileView,
    PasswordChangeView,
    LoginHistoryView,
    LogoutView,
    CustomTokenObtainPairView,
)

app_name = 'users'

urlpatterns = [
    # Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('token/', CustomTokenObtainPairView.as_view(), name='token'),  # Alias for frontend
    path('token/refresh/', TokenRefreshView.as_view(), name='token-refresh'),
    path('logout/', LogoutView.as_view(), name='logout'),
    
    # Profile
    path('me/', ProfileView.as_view(), name='me'),  # Frontend expects /auth/me/
    path('profile/', ProfileView.as_view(), name='profile'),
    path('password/change/', PasswordChangeView.as_view(), name='password-change'),
    
    # Security
    path('login-history/', LoginHistoryView.as_view(), name='login-history'),
]
