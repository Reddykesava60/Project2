"""
Public views for customer ordering via QR code.
"""

import json
import logging
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from apps.core.utils import verify_qr_signature
from apps.core.audit import create_audit_log, AuditLog
from apps.restaurants.models import Restaurant
from apps.menu.models import MenuCategory
from apps.menu.serializers import MenuCategoryPublicSerializer
from .models import Order
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
    """Create a customer order via QR code."""
    
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
        
        # Create order
        serializer = self.get_serializer(
            data=request.data,
            context={'restaurant': restaurant, 'request': request}
        )
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Audit log for order creation
        create_audit_log(
            action=AuditLog.Action.ORDER_CREATED,
            restaurant=restaurant,
            entity=order,
            entity_type='Order',
            entity_repr=f'Order {order.order_number}',
            description=f'Customer created order via QR: {order.total_amount}',
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


class CreatePaymentOrderView(APIView):
    """Create a Razorpay order for online payment."""
    
    permission_classes = [AllowAny]
    
    def post(self, request, slug, order_id):
        """Create Razorpay order for payment."""
        try:
            order = Order.objects.get(
                id=order_id,
                restaurant__slug=slug,
                payment_method='ONLINE',
                payment_status='PENDING'
            )
        except Order.DoesNotExist:
            return Response(
                {'error': 'Order not found or already paid.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if not razorpay_service.is_configured:
            return Response(
                {'error': 'Online payment is not available.'},
                status=status.HTTP_503_SERVICE_UNAVAILABLE
            )
        
        try:
            # Amount in paise (smallest currency unit)
            amount_paise = int(order.total_amount * 100)
            
            razorpay_order = razorpay_service.create_order(
                amount=amount_paise,
                currency=order.restaurant.currency,
                receipt=str(order.id),
                notes={
                    'order_number': order.order_number,
                    'restaurant_id': str(order.restaurant.id),
                }
            )
            
            return Response({
                'razorpay_order_id': razorpay_order['id'],
                'razorpay_key_id': razorpay_service.key_id,
                'amount': amount_paise,
                'currency': order.restaurant.currency,
                'order_id': str(order.id),
                'order_number': order.order_number,
            })
            
        except PaymentServiceError as e:
            logger.error(f"Failed to create payment order: {e}")
            return Response(
                {'error': 'Failed to initialize payment.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class VerifyPaymentView(APIView):
    """Verify Razorpay payment after completion."""
    
    permission_classes = [AllowAny]
    
    def post(self, request, slug, order_id):
        """Verify payment signature and update order."""
        try:
            order = Order.objects.get(
                id=order_id,
                restaurant__slug=slug,
                payment_method='ONLINE'
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
        order_id = payment.get('notes', {}).get('order_id')
        if not order_id:
            # Try to get from receipt
            order_id = payment.get('order_id')
        
        if order_id:
            try:
                # Find order by razorpay order_id in notes or by our order ID
                order = Order.objects.get(id=order_id)
                if order.payment_status != 'SUCCESS':
                    order.payment_id = payment.get('id')
                    order.payment_status = 'SUCCESS'
                    if order.status == 'AWAITING_PAYMENT':
                        order.status = 'PREPARING'
                    order.save()
                    logger.info(f"Order {order_id} marked as paid via webhook")
            except Order.DoesNotExist:
                logger.warning(f"Order not found for webhook: {order_id}")
    
    def _handle_payment_failed(self, payment: dict):
        """Handle failed payment."""
        notes = payment.get('notes', {})
        order_id = notes.get('order_id')
        
        if order_id:
            try:
                order = Order.objects.get(id=order_id)
                if order.payment_status == 'PENDING':
                    order.payment_status = 'FAILED'
                    order.save(update_fields=['payment_status', 'updated_at'])
                    logger.info(f"Order {order_id} marked as failed via webhook")
            except Order.DoesNotExist:
                logger.warning(f"Order not found for failed payment webhook: {order_id}")
