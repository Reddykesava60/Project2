"""
URL patterns for the Orders app (authenticated).
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import OrderViewSet, StaffCreateOrderView, DashboardStatsView

router = DefaultRouter()
router.register('', OrderViewSet, basename='order')

app_name = 'orders'

urlpatterns = [
    path('staff/create/', StaffCreateOrderView.as_view(), name='staff-create'),
    path('dashboard/stats/', DashboardStatsView.as_view(), name='dashboard-stats'),
    # Alias for QR verification with underscore (frontend compatibility)
    # Frontend expects /orders/verify_qr/ but DRF creates /orders/verify-qr/
    # Add explicit route for underscore version
    path('verify_qr/', OrderViewSet.as_view({'post': 'verify_qr'}), name='verify-qr-underscore'),
    path('', include(router.urls)),
]
