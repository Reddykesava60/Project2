"""
URL patterns for /api/me endpoint.
Returns current authenticated user profile.
"""

from django.urls import path
from .views import ProfileView

# This creates /api/me endpoint
urlpatterns = [
    path('', ProfileView.as_view(), name='me'),
]
