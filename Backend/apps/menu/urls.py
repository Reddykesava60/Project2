"""
URL patterns for the Menu app.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MenuCategoryViewSet, MenuItemViewSet

router = DefaultRouter()
router.register('categories', MenuCategoryViewSet, basename='category')
router.register('items', MenuItemViewSet, basename='item')

app_name = 'menu'

urlpatterns = [
    path('', include(router.urls)),
]
