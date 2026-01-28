"""
URL patterns for staff management endpoints.
Matches frontend expectations: /api/staff
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StaffViewSet

router = DefaultRouter()
router.register('', StaffViewSet, basename='staff')

app_name = 'staff'

urlpatterns = [
    path('', include(router.urls)),
]
