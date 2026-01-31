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
    InitiateUPIPaymentView,
    VerifyUPIPaymentView,
    PublicReservationView,
    RazorpayWebhookView,
)

urlpatterns = [
    # Public restaurant info
    path('r/<slug:slug>/', PublicRestaurantView.as_view(), name='public-restaurant'),
    
    # Public menu
    path('r/<slug:slug>/menu/', PublicMenuView.as_view(), name='public-menu'),
    
    # NEW: Stock Reservation (Step 1)
    path('r/<slug:slug>/reserve/', PublicReservationView.as_view(), name='public-reserve'),
    
    # Create order (CASH only - UPI must use payment/initiate flow)
    path('r/<slug:slug>/order/', PublicOrderCreateView.as_view(), name='public-order-create'),
    
    # Order detail (full info for confirmation page)
    path('r/<slug:slug>/order/<uuid:order_id>/', PublicOrderDetailView.as_view(), name='public-order-detail'),
    
    # Order status (limited info)
    path('r/<slug:slug>/order/<uuid:order_id>/status/', PublicOrderStatusView.as_view(), name='public-order-status'),
    
    # NEW UPI Payment flow (no order created until payment verified)
    # Step 1: Initiate payment - validates cart, creates Razorpay order, returns payment_token
    path('r/<slug:slug>/payment/initiate/', InitiateUPIPaymentView.as_view(), name='initiate-upi-payment'),
    # Step 2: Verify payment - verifies signature, creates order ONLY if successful
    path('r/<slug:slug>/payment/verify/', VerifyUPIPaymentView.as_view(), name='verify-upi-payment'),
    
    # DEPRECATED: Legacy payment endpoints (for backward compatibility)
    path('r/<slug:slug>/order/<uuid:order_id>/payment/create/', CreatePaymentOrderView.as_view(), name='create-payment-order'),
    path('r/<slug:slug>/order/<uuid:order_id>/payment/verify/', VerifyPaymentView.as_view(), name='verify-payment'),
    
    # Razorpay webhook (global, not per-restaurant)
    path('webhooks/razorpay/', RazorpayWebhookView.as_view(), name='razorpay-webhook'),
]
