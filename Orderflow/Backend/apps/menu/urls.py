"""
URL patterns for the Menu app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    MenuCategoryViewSet, 
    MenuItemViewSet,
    StaffMenuItemListView,
    StaffUpdateAvailabilityView,
)

router = DefaultRouter()
router.register('categories', MenuCategoryViewSet, basename='category')
router.register('items', MenuItemViewSet, basename='item')

app_name = 'menu'

urlpatterns = [
    path('', include(router.urls)),
    # Staff stock management endpoints
    path('staff/items/', StaffMenuItemListView.as_view(), name='staff-items'),
    path('staff/items/<uuid:pk>/availability/', StaffUpdateAvailabilityView.as_view(), name='staff-update-availability'),
]
