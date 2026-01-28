"""
URL patterns for public order endpoints (QR ordering).
"""

from django.urls import path
from .public_views import (
    PublicRestaurantView,
    PublicMenuView,
    PublicOrderCreateView,
    PublicOrderStatusView,
    PublicOrderDetailView,
    CreatePaymentOrderView,
    VerifyPaymentView,
    RazorpayWebhookView,
)

urlpatterns = [
    # Public restaurant info
    path('r/<slug:slug>/', PublicRestaurantView.as_view(), name='public-restaurant'),
    
    # Public menu
    path('r/<slug:slug>/menu/', PublicMenuView.as_view(), name='public-menu'),
    
    # Create order
    path('r/<slug:slug>/order/', PublicOrderCreateView.as_view(), name='public-order-create'),
    
    # Order detail (full info for confirmation page)
    path('r/<slug:slug>/order/<uuid:order_id>/', PublicOrderDetailView.as_view(), name='public-order-detail'),
    
    # Order status (limited info)
    path('r/<slug:slug>/order/<uuid:order_id>/status/', PublicOrderStatusView.as_view(), name='public-order-status'),
    
    # Payment endpoints
    path('r/<slug:slug>/order/<uuid:order_id>/payment/create/', CreatePaymentOrderView.as_view(), name='create-payment-order'),
    path('r/<slug:slug>/order/<uuid:order_id>/payment/verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    
    # Razorpay webhook (global, not per-restaurant)
    path('webhooks/razorpay/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
]
