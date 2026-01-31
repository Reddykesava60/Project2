"""
URL patterns for Platform Admin endpoints.
These endpoints are for managing all restaurants in the platform.
Frontend expects: /api/admin/restaurants/... and /api/admin/audit-logs/...
"""

from django.urls import path, include
from .admin_views import (
    AdminRestaurantListView,
    AdminRestaurantStatusView,
    SubscriptionListView,
    SubscriptionActionView,
)

urlpatterns = [
    # Restaurant management
    path('restaurants/', AdminRestaurantListView.as_view(), name='admin-restaurant-list'),
    path('restaurants/<uuid:pk>/', AdminRestaurantStatusView.as_view(), name='admin-restaurant-detail'),
    
    # Subscription management
    path('subscriptions/', SubscriptionListView.as_view(), name='admin-subscription-list'),
    path('subscriptions/<uuid:pk>/cancel/', SubscriptionActionView.as_view(), {'action': 'cancel'}, name='admin-subscription-cancel'),
    path('subscriptions/<uuid:pk>/reactivate/', SubscriptionActionView.as_view(), {'action': 'reactivate'}, name='admin-subscription-reactivate'),
    
    # Audit logs (alias to main audit-logs endpoint)
    path('audit-logs/', include('apps.core.audit_urls')),
]
