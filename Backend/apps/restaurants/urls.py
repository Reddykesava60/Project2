"""
URL patterns for the Restaurants app.
Includes restaurant management, staff management, and menu management.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import RestaurantViewSet, StaffViewSet, ApiKeyViewSet, RestaurantPublicView
from apps.menu.views import MenuCategoryViewSet, MenuItemViewSet

router = DefaultRouter()
router.register('', RestaurantViewSet, basename='restaurant')

# Separate routers for staff, categories, products (flat URLs as frontend expects)
staff_router = DefaultRouter()
staff_router.register('', StaffViewSet, basename='staff')

category_router = DefaultRouter()
category_router.register('', MenuCategoryViewSet, basename='category')

product_router = DefaultRouter()
product_router.register('', MenuItemViewSet, basename='product')

app_name = 'restaurants'

urlpatterns = [
    # Public restaurant view for QR ordering
    path('public/<slug:slug>/', RestaurantPublicView.as_view(), name='public-restaurant'),
    
    # Alias for frontend compatibility (frontend expects /restaurants/slug/{slug}/)
    path('slug/<slug:slug>/', RestaurantPublicView.as_view(), name='restaurant-by-slug'),
    
    # Staff management (/api/restaurant/staff/)
    path('staff/', include(staff_router.urls)),
    
    # Category management (/api/restaurant/categories/)
    path('categories/', include(category_router.urls)),
    
    # Product/MenuItem management (/api/restaurant/products/)
    path('products/', include(product_router.urls)),
    
    # API keys (/api/restaurant/api-keys/)
    path('api-keys/', ApiKeyViewSet.as_view({'get': 'list', 'post': 'create'}), name='api-key-list'),
    path('api-keys/<uuid:pk>/', ApiKeyViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'}), name='api-key-detail'),
    
    # Restaurant management endpoints (main router)
    path('', include(router.urls)),
]
