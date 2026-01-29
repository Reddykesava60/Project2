"""
Public views for customer ordering via QR code.
"""

import json
import logging
import hashlib
import secrets
from decimal import Decimal
from django.conf import settings
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.core.cache import cache

from apps.core.utils import verify_qr_signature, generate_order_number
from apps.core.audit import create_audit_log, AuditLog
from apps.restaurants.models import Restaurant
from apps.menu.models import MenuCategory, MenuItem
from apps.menu.serializers import MenuCategoryPublicSerializer
from .models import Order, OrderItem, DailyOrderSequence
from .serializers import OrderCreateSerializer, OrderSerializer
from .payment_service import razorpay_service, process_order_payment, PaymentServiceError

logger = logging.getLogger(__name__)


class PublicRestaurantView(APIView):
    """Get basic restaurant info for QR landing pages."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        try:
            restaurant = Restaurant.objects.get(slug=slug, status='ACTIVE')
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'id': str(restaurant.id),
            'name': restaurant.name,
            'slug': restaurant.slug,
            'currency': restaurant.currency,
            'timezone': restaurant.timezone,
        })


class PublicMenuView(APIView):
    """Get menu for a restaurant via QR code."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, slug):
        # Get restaurant
        try:
            restaurant = Restaurant.objects.get(slug=slug, status='ACTIVE')
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Optional: Verify QR signature
        qr_version = request.query_params.get('v')
        signature = request.query_params.get('sig')
        
        if qr_version and signature:
            if not verify_qr_signature(str(restaurant.id), int(qr_version), signature, restaurant.qr_secret):
                return Response(
                    {'error': 'Invalid or expired QR code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Get menu categories with items
        categories = MenuCategory.objects.filter(
            restaurant=restaurant,
            is_active=True
        ).prefetch_related('items')
        
        serializer = MenuCategoryPublicSerializer(categories, many=True)
        
        return Response({
            'restaurant': {
                'id': str(restaurant.id),
                'name': restaurant.name,
                'slug': restaurant.slug,
                'currency': restaurant.currency,
            },
            'categories': serializer.data,
        })


class PublicOrderCreateView(generics.CreateAPIView):
    """Create a customer order via QR code.
    
    CRITICAL PAYMENT RULES:
    - CASH orders: Created immediately with status=pending, payment_status=pending
    - UPI orders: NOT created here. Must use /payment/initiate/ and /payment/verify/ flow.
      Order is only created AFTER payment verification succeeds.
    """
    
    serializer_class = OrderCreateSerializer
    permission_classes = [AllowAny]
    
    def create(self, request, slug):
        # Get restaurant
        try:
            restaurant = Restaurant.objects.get(slug=slug, status='ACTIVE')
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify QR signature if provided
        qr_signature = request.data.get('qr_signature', '')
        qr_version = request.data.get('qr_version')
        
        if qr_version and qr_signature:
            if not verify_qr_signature(str(restaurant.id), int(qr_version), qr_signature, restaurant.qr_secret):
                return Response(
                    {'error': 'Invalid or expired QR code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # CRITICAL: Check payment method
        payment_method = request.data.get('payment_method', '').lower()
        
        # For UPI orders, do NOT create order. Return error directing to payment flow.
        # UNLESS SKIP_UPI_PAYMENT_FLOW is enabled for local testing
        skip_upi_flow = getattr(settings, 'SKIP_UPI_PAYMENT_FLOW', False)
        if payment_method == 'upi' and not skip_upi_flow:
            return Response(
                {
                    'error': 'UPI_REQUIRES_PAYMENT_FLOW',
                    'message': 'UPI orders must use /payment/initiate/ endpoint first.',
                    'redirect': f'/api/public/r/{slug}/payment/initiate/'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # CASH orders (or UPI with skip flow): Create immediately
        serializer = self.get_serializer(
            data=request.data,
            context={'restaurant': restaurant, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # If UPI with skip flow enabled, auto-approve the payment
        if payment_method == 'upi' and skip_upi_flow:
            order.status = 'preparing'
            order.payment_status = 'success'
            order.save(update_fields=['status', 'payment_status'])
        
        # Audit log for order creation
        order_type_desc = 'UPI (auto-approved)' if (payment_method == 'upi' and skip_upi_flow) else 'CASH'
        create_audit_log(
            action=AuditLog.Action.ORDER_CREATED,
            restaurant=restaurant,
            entity=order,
            entity_type='Order',
            entity_repr=f'Order {order.order_number}',
            description=f'Customer created {order_type_desc} order via QR: {order.total_amount}',
            metadata={
                'order_type': order.order_type,
                'payment_method': order.payment_method,
                'table_number': order.table_number,
                'item_count': order.items.count(),
            },
            request=request
        )
        
        # Return order confirmation
        return Response({
            'success': True,
            'order': {
                'id': str(order.id),
                'order_number': order.order_number,
                'daily_order_number': order.order_number,  # Alias for frontend
                'status': order.status.lower(),  # Frontend expects lowercase
                'payment_method': order.payment_method.lower(),  # Frontend expects lowercase
                'payment_status': order.payment_status.lower(),  # Frontend expects lowercase
                'total_amount': float(order.total_amount),
                'total': float(order.total_amount),  # Frontend expects 'total'
            },
            'message': 'Order placed successfully!',
        }, status=status.HTTP_201_CREATED)


class PublicOrderStatusView(APIView):
    """Get order status (public - limited info)."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, slug, order_id):
        try:
            order = Order.objects.get(
                id=order_id,
                restaurant__slug=slug,
                restaurant__status='ACTIVE'
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        return Response({
            'id': str(order.id),
            'order_number': order.order_number,
            'daily_order_number': order.order_number,  # Alias for frontend
            'status': order.status.lower(),  # Frontend expects lowercase
            'payment_method': order.payment_method.lower(),
            'payment_status': order.payment_status.lower(),
            'total': float(order.total_amount),
            'total_amount': float(order.total_amount),
            'created_at': order.created_at.isoformat(),
        })


class PublicOrderDetailView(APIView):
    """Get full order details for order confirmation page (public)."""
    
    permission_classes = [AllowAny]
    
    def get(self, request, slug, order_id):
        try:
            order = Order.objects.select_related('restaurant').prefetch_related('items__menu_item').get(
                id=order_id,
                restaurant__slug=slug,
                restaurant__status='ACTIVE'
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Return full order details for confirmation page
        items_data = []
        for item in order.items.all():
            items_data.append({
                'id': str(item.id),
                'menu_item': str(item.menu_item_id),
                'menu_item_id': str(item.menu_item_id),  # Alias
                'menu_item_name': item.menu_item_name,
                'price_at_order': float(item.price_at_order),
                'unit_price': float(item.price_at_order),  # Alias for frontend
                'quantity': item.quantity,
                'subtotal': float(item.subtotal),
                'total_price': float(item.subtotal),  # Alias for frontend
            })
        
        return Response({
            'id': str(order.id),
            'order_number': order.order_number,
            'daily_order_number': order.order_number,  # Alias for frontend compatibility
            'daily_sequence': order.daily_sequence,
            'restaurant_id': str(order.restaurant_id),
            'restaurant': str(order.restaurant_id),  # Alias
            'customer_name': order.customer_name or '',
            'payment_method': order.payment_method.lower(),  # Frontend expects lowercase
            'payment_status': order.payment_status.lower(),  # Frontend expects lowercase
            'status': order.status.lower(),  # Frontend expects lowercase
            'order_type': order.order_type,
            'subtotal': float(order.subtotal),
            'tax': float(order.tax),
            'total': float(order.total_amount),  # Frontend expects 'total'
            'total_amount': float(order.total_amount),
            'items': items_data,
            'created_at': order.created_at.isoformat(),
            'updated_at': order.updated_at.isoformat(),
            'version': order.version,
        })


# Cache key prefix for pending UPI payments
UPI_PENDING_CACHE_PREFIX = 'upi_pending_'
UPI_PENDING_CACHE_TIMEOUT = 15 * 60  # 15 minutes


class InitiateUPIPaymentView(APIView):
    """
    Initiate UPI payment WITHOUT creating an order in DB.
    
    CRITICAL PAYMENT RULE:
    - Validates cart data
    - Stores cart in cache with payment_token
    - Creates Razorpay order
    - Returns Razorpay details for frontend
    - NO ORDER IS CREATED until payment is verified
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, slug):
        """Initiate UPI payment flow."""
        # Get restaurant
        try:
            restaurant = Restaurant.objects.get(slug=slug, status='ACTIVE')
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Verify QR signature if provided
        qr_signature = request.data.get('qr_signature', '')
        qr_version = request.data.get('qr_version')
        
        if qr_version and qr_signature:
            if not verify_qr_signature(str(restaurant.id), int(qr_version), qr_signature, restaurant.qr_secret):
                return Response(
                    {'error': 'Invalid or expired QR code.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Validate required fields
        customer_name = request.data.get('customer_name', '').strip()
        items_data = request.data.get('items', [])
        privacy_accepted = request.data.get('privacy_accepted', False)
        table_number = request.data.get('table_number', '')
        is_parcel = request.data.get('is_parcel', False)
        spicy_level = request.data.get('spicy_level', 'normal')
        
        if not customer_name:
            return Response(
                {'error': 'Customer name is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not items_data:
            return Response(
                {'error': 'Order must have at least one item.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not privacy_accepted:
            return Response(
                {'error': 'You must accept the privacy policy.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate and calculate totals
        subtotal = Decimal('0.00')
        validated_items = []
        
        for item_data in items_data:
            try:
                menu_item = MenuItem.objects.get(
                    id=item_data.get('menu_item_id'),
                    restaurant=restaurant,
                    is_active=True,
                    is_available=True
                )
                
                # Manual stock check for initiation
                quantity = int(item_data.get('quantity', 1))
                if menu_item.stock_quantity is not None and menu_item.stock_quantity < quantity:
                     return Response(
                        {
                            'error': 'INSUFFICIENT_STOCK',
                            'code': 'INSUFFICIENT_STOCK',
                            'item_id': str(menu_item.id),
                            'item_name': menu_item.name,
                            'available_quantity': menu_item.stock_quantity,
                            'requested_quantity': quantity,
                            'message': f"Only {menu_item.stock_quantity} units of {menu_item.name} are available."
                        },
                        status=status.HTTP_400_BAD_REQUEST
                    )

            except MenuItem.DoesNotExist:
                return Response(
                    {
                        'error': 'ITEM_UNAVAILABLE',
                        'code': 'ITEM_UNAVAILABLE',
                        'item_id': item_data.get('menu_item_id'),
                        'message': 'One or more items in your cart are unavailable.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            quantity = int(item_data.get('quantity', 1))
            if quantity < 1:
                return Response(
                    {'error': 'Item quantity must be at least 1.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            item_subtotal = menu_item.price * quantity
            subtotal += item_subtotal
            
            validated_items.append({
                'menu_item_id': str(menu_item.id),
                'menu_item_name': menu_item.name,
                'price': str(menu_item.price),
                'quantity': quantity,
                'subtotal': str(item_subtotal),
                'notes': item_data.get('notes', ''),
            })
        
        # Calculate tax
        tax = subtotal * restaurant.tax_rate
        total_amount = subtotal + tax
        
        # Check if Razorpay is configured
        if not razorpay_service.is_configured:
            return Response(
                {'error': 'Online payment is not available.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        # Generate unique payment token
        payment_token = secrets.token_urlsafe(32)
        
        # Store cart data in cache (NOT in database)
        cart_data = {
            'restaurant_id': str(restaurant.id),
            'restaurant_slug': slug,
            'customer_name': customer_name,
            'table_number': table_number,
            'is_parcel': is_parcel,
            'spicy_level': spicy_level,
            'qr_signature': qr_signature,
            'items': validated_items,
            'subtotal': str(subtotal),
            'tax': str(tax),
            'total_amount': str(total_amount),
            'payment_method': 'upi',
        }
        
        try:
            # Amount in paise (smallest currency unit)
            amount_paise = int(total_amount * 100)
            
            razorpay_order = razorpay_service.create_order(
                amount=amount_paise,
                currency=restaurant.currency,
                receipt=payment_token,  # Use token as receipt, not order_id
                notes={
                    'payment_token': payment_token,
                    'restaurant_id': str(restaurant.id),
                    'restaurant_slug': slug,
                }
            )
            
            # Store razorpay order ID with cart data
            cart_data['razorpay_order_id'] = razorpay_order['id']
            
            # Cache the cart data
            cache_key = f"{UPI_PENDING_CACHE_PREFIX}{payment_token}"
            cache.set(cache_key, cart_data, timeout=UPI_PENDING_CACHE_TIMEOUT)
            
            logger.info(f"Initiated UPI payment for {slug}, token={payment_token[:8]}...")
            
            return Response({
                'success': True,
                'payment_token': payment_token,
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': razorpay_service.key_id,
                'amount': amount_paise,
                'currency': restaurant.currency,
                'total_amount': float(total_amount),
                'message': 'Payment initiated. Complete payment to place order.',
            })
            
        except PaymentServiceError as e:
            logger.error(f"Failed to initiate UPI payment: {e}")
            return Response(
                {'error': 'Failed to initialize payment.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class CreatePaymentOrderView(APIView):
    """
    DEPRECATED: This endpoint should not be used for new UPI orders.
    Use InitiateUPIPaymentView instead.
    
    Kept for backward compatibility but returns error for UPI orders.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, slug, order_id):
        """Create Razorpay order for payment - DEPRECATED."""
        # Return error - UPI orders should use new flow
        return Response(
            {
                'error': 'DEPRECATED_ENDPOINT',
                'message': 'UPI orders must use /payment/initiate/ endpoint. Orders are only created after payment verification.',
                'redirect': f'/api/public/r/{slug}/payment/initiate/'
            },
            status=status.HTTP_400_BAD_REQUEST
        )


class VerifyUPIPaymentView(APIView):
    """
    Verify Razorpay payment and CREATE order only after successful verification.
    
    CRITICAL PAYMENT RULE:
    - This is the ONLY endpoint that creates UPI orders
    - Order is created ONLY if payment verification succeeds
    - If verification fails, NO order is created
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, slug):
        """Verify payment and create order if successful."""
        payment_token = request.data.get('payment_token')
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        if not payment_token:
            return Response(
                {'error': 'Payment token is required.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return Response(
                {'error': 'Missing payment details.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Retrieve cart data from cache
        cache_key = f"{UPI_PENDING_CACHE_PREFIX}{payment_token}"
        cart_data = cache.get(cache_key)
        
        if not cart_data:
            return Response(
                {'error': 'Payment session expired or invalid token.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify the razorpay_order_id matches what we stored
        if cart_data.get('razorpay_order_id') != razorpay_order_id:
            logger.warning(f"Razorpay order ID mismatch for token {payment_token[:8]}")
            return Response(
                {'error': 'Payment order mismatch.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get restaurant
        try:
            restaurant = Restaurant.objects.get(
                id=cart_data['restaurant_id'],
                slug=slug,
                status='ACTIVE'
            )
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # CRITICAL: Verify payment signature with Razorpay SDK
        # This is the ONLY source of truth for payment success.
        # The razorpay_service.verify_payment_signature() method handles:
        # - Real Razorpay SDK verification when RAZORPAY_LIVE_MODE=True
        # - Simulation mode when RAZORPAY_FORCE_SUCCESS=True and RAZORPAY_LIVE_MODE=False
        from django.db import transaction
        
        try:
            # ALWAYS call verify_payment_signature - it handles mode switching internally
            razorpay_service.verify_payment_signature(
                razorpay_order_id,
                razorpay_payment_id,
                razorpay_signature
            )
            
            # Payment verified! Now create the order in database
            with transaction.atomic():
                # Get next sequence number
                daily_sequence = DailyOrderSequence.get_next_sequence(restaurant)
                order_number = generate_order_number(daily_sequence)
                
                # Create order with payment already successful
                order = Order.objects.create(
                    restaurant=restaurant,
                    order_number=order_number,
                    daily_sequence=daily_sequence,
                    order_type=Order.OrderType.QR_CUSTOMER,
                    customer_name=cart_data['customer_name'],
                    table_number=cart_data.get('table_number', ''),
                    is_parcel=cart_data.get('is_parcel', False),
                    spicy_level=cart_data.get('spicy_level', 'normal'),
                    qr_signature=cart_data.get('qr_signature', ''),
                    status='preparing',  # Payment successful = preparing (lowercase per PRD)
                    payment_method='upi',  # Lowercase per PRD
                    payment_status='success',  # Payment verified = success (lowercase per PRD)
                    payment_id=razorpay_payment_id,
                    subtotal=Decimal(cart_data['subtotal']),
                    tax=Decimal(cart_data['tax']),
                    total_amount=Decimal(cart_data['total_amount']),
                )
                
                # Create order items
                for item_data in cart_data['items']:
                    OrderItem.objects.create(
                        order=order,
                        menu_item_id=item_data['menu_item_id'],
                        menu_item_name=item_data['menu_item_name'],
                        price_at_order=Decimal(item_data['price']),
                        quantity=item_data['quantity'],
                        subtotal=Decimal(item_data['subtotal']),
                        notes=item_data.get('notes', ''),
                    )
                
                # Audit log
                create_audit_log(
                    action=AuditLog.Action.ORDER_CREATED,
                    restaurant=restaurant,
                    entity=order,
                    entity_type='Order',
                    entity_repr=f'Order {order.order_number}',
                    description=f'UPI order created after payment verification: {order.total_amount}',
                    metadata={
                        'order_type': order.order_type,
                        'payment_method': order.payment_method,
                        'payment_id': razorpay_payment_id,
                        'table_number': order.table_number,
                        'item_count': order.items.count(),
                    },
                    request=request
                )
            
            # Clear the cache
            cache.delete(cache_key)
            
            logger.info(f"UPI order {order.order_number} created after payment verification")
            
            return Response({
                'success': True,
                'order': {
                    'id': str(order.id),
                    'order_number': order.order_number,
                    'daily_order_number': order.order_number,
                    'status': order.status,
                    'payment_method': order.payment_method,
                    'payment_status': order.payment_status,
                    'total_amount': float(order.total_amount),
                    'total': float(order.total_amount),
                },
                'message': 'Payment verified and order placed successfully!',
            }, status=status.HTTP_201_CREATED)
            
        except PaymentServiceError as e:
            # Payment verification failed - NO ORDER CREATED
            logger.warning(f"UPI payment verification failed for token {payment_token[:8]}: {e}")
            
            # Clear the cache - payment failed
            cache.delete(cache_key)
            
            return Response(
                {
                    'error': 'PAYMENT_VERIFICATION_FAILED',
                    'message': 'Payment verification failed. No order was created.',
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class VerifyPaymentView(APIView):
    """
    DEPRECATED: Legacy endpoint for verifying payment on existing orders.
    
    New UPI flow uses VerifyUPIPaymentView which creates order after verification.
    This is kept for any edge cases but should not be used for new orders.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request, slug, order_id):
        """Verify payment signature - DEPRECATED."""
        # Check if this is an attempt to use the new payment_token flow
        if request.data.get('payment_token'):
            return Response(
                {
                    'error': 'WRONG_ENDPOINT',
                    'message': 'Use /payment/verify/ without order_id for token-based verification.',
                    'redirect': f'/api/public/r/{slug}/payment/verify/'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Legacy flow - try to find existing order
        try:
            order = Order.objects.get(
                id=order_id,
                restaurant__slug=slug,
                payment_method='upi'
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        razorpay_payment_id = request.data.get('razorpay_payment_id')
        razorpay_order_id = request.data.get('razorpay_order_id')
        razorpay_signature = request.data.get('razorpay_signature')
        
        if not all([razorpay_payment_id, razorpay_order_id, razorpay_signature]):
            return Response(
                {'error': 'Missing payment details.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        success, message = process_order_payment(
            order,
            razorpay_payment_id,
            razorpay_order_id,
            razorpay_signature
        )
        
        if success:
            return Response({
                'success': True,
                'order_number': order.order_number,
                'status': order.status,
                'message': 'Payment verified successfully!',
            })
        else:
            return Response(
                {'error': message},
                status=status.HTTP_400_BAD_REQUEST
            )


@method_decorator(csrf_exempt, name='dispatch')
class RazorpayWebhookView(APIView):
    """
    Webhook endpoint for Razorpay events.
    
    This handles asynchronous payment notifications from Razorpay.
    Critical for catching payments that succeed but fail to verify on client.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        """Handle Razorpay webhook events."""
        # Get signature from header
        signature = request.headers.get('X-Razorpay-Signature', '')
        
        if not signature:
            logger.warning("Webhook received without signature")
            return Response(
                {'error': 'Missing signature'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Verify webhook signature
        try:
            if not razorpay_service.verify_webhook_signature(request.body, signature):
                logger.warning("Invalid webhook signature")
                return Response(
                    {'error': 'Invalid signature'},
                    status=status.HTTP_400_BAD_REQUEST
                )
        except PaymentServiceError as e:
            logger.error(f"Webhook verification error: {e}")
            return Response(
                {'error': 'Webhook not configured'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
        
        # Parse event
        try:
            event = json.loads(request.body)
        except json.JSONDecodeError:
            return Response(
                {'error': 'Invalid JSON'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        event_type = event.get('event')
        payload = event.get('payload', {})
        
        logger.info(f"Received webhook event: {event_type}")
        
        # Handle payment captured event
        if event_type == 'payment.captured':
            payment = payload.get('payment', {}).get('entity', {})
            self._handle_payment_captured(payment)
        
        # Handle payment failed event
        elif event_type == 'payment.failed':
            payment = payload.get('payment', {}).get('entity', {})
            self._handle_payment_failed(payment)
        
        return Response({'status': 'ok'})
    
    def _handle_payment_captured(self, payment: dict):
        """Handle successful payment capture."""
        notes = payment.get('notes', {}) or {}
        order_id = notes.get('order_id')
        restaurant_id = notes.get('restaurant_id')

        # Require explicit correlation info to avoid cross-tenant updates
        if not order_id or not restaurant_id:
            logger.warning("Webhook payment.captured missing order_id/restaurant_id notes")
            return

        try:
            order = Order.objects.get(
                id=order_id,
                restaurant_id=restaurant_id,
                payment_method='upi',  # Lowercase per PRD
            )
        except Order.DoesNotExist:
            logger.warning(f"Order not found for webhook (tenant-scoped): {order_id}")
            return

        # Use lowercase values per PRD
        if order.payment_status != 'success':
            order.payment_id = payment.get('id') or ''
            order.payment_status = 'success'  # Lowercase per PRD
            if order.status == 'pending':
                order.status = 'preparing'  # Lowercase per PRD
            order.save(update_fields=['payment_id', 'payment_status', 'status', 'updated_at', 'version'])
            logger.info(f"Order {order_id} marked as paid via webhook")
    
    def _handle_payment_failed(self, payment: dict):
        """Handle failed payment.
        
        Note: Per PRD, payment_status only has 'pending' and 'success'.
        Failed payments stay as 'pending' - the order will be cleaned up by the
        end-of-day cleanup job.
        """
        notes = payment.get('notes', {}) or {}
        order_id = notes.get('order_id')
        restaurant_id = notes.get('restaurant_id')

        if not order_id or not restaurant_id:
            logger.warning("Webhook payment.failed missing order_id/restaurant_id notes")
            return

        try:
            order = Order.objects.get(
                id=order_id,
                restaurant_id=restaurant_id,
                payment_method='upi',  # Lowercase per PRD
            )
        except Order.DoesNotExist:
            logger.warning(f"Order not found for failed payment webhook (tenant-scoped): {order_id}")
            return

        # Log the failure but don't change payment_status (PRD only has pending/success)
        # Order will be cleaned up by end-of-day job if payment is never successful
        logger.warning(f"Payment failed for order {order_id} - will be cleaned up by EOD job")
