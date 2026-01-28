"""
Views for the Orders app.
"""

from rest_framework import viewsets, generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Sum
from datetime import timedelta

from apps.core.permissions import IsOwner, IsStaff, CanCollectCash
from apps.core.utils import verify_qr_signature
from apps.core.audit import create_audit_log, AuditLog
from apps.restaurants.models import Restaurant
from .models import Order, OrderItem
from .serializers import (
    OrderSerializer,
    OrderCreateSerializer,
    StaffOrderCreateSerializer,
    OrderStatusUpdateSerializer,
    CollectPaymentSerializer,
)


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for order management (owners/staff).
    
    Endpoints:
    - GET /api/orders/ - List orders (tenant-scoped)
    - GET /api/orders/active/ - List active orders
    - GET /api/orders/today/ - List today's orders
    - POST /api/orders/{id}/update_status/ - Update order status
    - POST /api/orders/{id}/collect_payment/ - Collect cash payment
    - POST /api/orders/verify_qr/ - Verify order QR code
    """
    
    serializer_class = OrderSerializer
    permission_classes = [IsAuthenticated, IsStaff]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'status', 'payment_method', 'order_type']
    
    def get_queryset(self):
        """Return tenant-scoped queryset."""
        user = self.request.user
        
        if user.role == 'platform_admin':
            return Order.objects.all()
        
        if user.role == 'restaurant_owner':
            return Order.objects.filter(restaurant__owner=user)
        
        if user.role == 'staff':
            # Staff only sees active/pending orders (not completed/cancelled)
            active_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY']
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile and staff_profile.restaurant:
                return Order.objects.filter(
                    restaurant=staff_profile.restaurant,
                    status__in=active_statuses
                )
        
        return Order.objects.none()
    
    @action(detail=False, methods=['get'], url_path='all')
    def all_orders(self, request):
        """
        Get all orders for owner (with filters).
        Matches frontend expectation: GET /api/orders/all
        """
        queryset = self.get_queryset()
        
        # Apply filters
        status_filter = request.query_params.get('status')
        payment_method = request.query_params.get('payment_method')
        payment_status = request.query_params.get('payment_status')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        if payment_method:
            queryset = queryset.filter(payment_method=payment_method)
        if payment_status:
            queryset = queryset.filter(payment_status=payment_status)
        if start_date:
            queryset = queryset.filter(created_at__date__gte=start_date)
        if end_date:
            queryset = queryset.filter(created_at__date__lte=end_date)
        
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def today(self, request):
        """Get today's orders."""
        today = timezone.now().date()
        queryset = self.get_queryset().filter(created_at__date=today)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active (non-completed) orders."""
        active_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY']
        queryset = self.get_queryset().filter(status__in=active_statuses)
        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['post'], url_path='update_status')
    def update_status(self, request, pk=None):
        """
        Update order status with proper validation.
        Frontend sends: {status: 'COMPLETED'} or other status values.
        """
        order = self.get_object()
        old_status = order.status
        
        # Get status from request
        new_status_str = request.data.get('status')
        if not new_status_str:
            return Response(
                {
                    'error': 'MISSING_STATUS',
                    'message': 'Status is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Convert to uppercase to match model choices
        new_status_str = new_status_str.upper()
        
        # Map frontend status to backend status
        status_mapping = {
            'COMPLETED': Order.Status.COMPLETED,
            'PENDING': Order.Status.PENDING,
            'PREPARING': Order.Status.PREPARING,
            'READY': Order.Status.READY,
            'CANCELLED': Order.Status.CANCELLED,
        }
        
        if new_status_str not in status_mapping:
            return Response(
                {
                    'error': 'INVALID_STATUS',
                    'message': f'Invalid status: {new_status_str}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        new_status = status_mapping[new_status_str]
        
        # Special handling for COMPLETED status - use complete() logic
        if new_status == Order.Status.COMPLETED:
            # Check payment status
            if order.payment_status != Order.PaymentStatus.SUCCESS:
                return Response(
                    {
                        'error': 'PAYMENT_NOT_COMPLETE',
                        'message': 'Order cannot be completed until payment is successful.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Check if already completed
            if order.status == Order.Status.COMPLETED:
                return Response(
                    {
                        'error': 'ORDER_ALREADY_COMPLETED',
                        'message': 'This order has already been completed.'
                    },
                    status=status.HTTP_409_CONFLICT
                )
            
            # Validate status transition
            if not order.can_transition_to(Order.Status.COMPLETED):
                return Response(
                    {
                        'error': 'INVALID_STATUS_TRANSITION',
                        'message': f'Cannot complete order from status {order.status}.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Complete the order
            order.mark_as_completed(user=request.user)
            
            # Audit log
            create_audit_log(
                action=AuditLog.Action.ORDER_COMPLETED,
                user=request.user,
                restaurant=order.restaurant,
                entity=order,
                entity_type='Order',
                entity_repr=f'Order {order.order_number}',
                description=f'Order {order.order_number} completed',
                request=request
            )
        else:
            # For other status changes, use standard validation
            if not order.can_transition_to(new_status):
                return Response(
                    {
                        'error': 'INVALID_STATUS_TRANSITION',
                        'message': f'Cannot transition from {order.status} to {new_status}.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Update status
            order.status = new_status
            order.save(update_fields=['status', 'updated_at', 'version'])
            
            # Audit log
            create_audit_log(
                action=AuditLog.Action.ORDER_STATUS_CHANGE,
                user=request.user,
                restaurant=order.restaurant,
                entity=order,
                entity_type='Order',
                entity_repr=f'Order {order.order_number}',
                old_value={'status': old_status},
                new_value={'status': order.status},
                description=f'Status changed from {old_status} to {order.status}',
                request=request
            )
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'], permission_classes=[IsAuthenticated, CanCollectCash])
    def collect_payment(self, request, pk=None):
        """
        Collect cash payment for an order.
        Only allowed for users with can_collect_cash permission.
        """
        order = self.get_object()
        
        if order.payment_method != 'CASH':
            return Response(
                {
                    'error': 'NOT_CASH_ORDER',
                    'message': 'This is not a cash order.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if order.payment_status == 'SUCCESS':
            return Response(
                {
                    'error': 'ALREADY_COLLECTED',
                    'message': 'Payment has already been collected.'
                },
                status=status.HTTP_409_CONFLICT
            )
        
        serializer = CollectPaymentSerializer(context={'request': request})
        order = serializer.update(order, {})
        
        # Cash collection is already audited in the model's collect_payment method
        # via CashAuditLog. Also add to main AuditLog for consistency.
        create_audit_log(
            action=AuditLog.Action.CASH_COLLECTED,
            user=request.user,
            restaurant=order.restaurant,
            entity=order,
            entity_type='Order',
            entity_repr=f'Order {order.order_number}',
            new_value={'amount': str(order.total_amount)},
            description=f'Cash collected: {order.total_amount}',
            request=request
        )
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'], url_path='complete')
    def complete(self, request, pk=None):
        """
        Complete an order.
        Order must have payment_status = SUCCESS before completion.
        """
        order = self.get_object()
        
        # Check payment status
        if order.payment_status != Order.PaymentStatus.SUCCESS:
            return Response(
                {
                    'error': 'PAYMENT_NOT_COMPLETE',
                    'message': 'Order cannot be completed until payment is successful.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if already completed
        if order.status == Order.Status.COMPLETED:
            return Response(
                {
                    'error': 'ORDER_ALREADY_COMPLETED',
                    'message': 'This order has already been completed.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Validate status transition
        if not order.can_transition_to(Order.Status.COMPLETED):
            return Response(
                {
                    'error': 'INVALID_STATUS_TRANSITION',
                    'message': f'Cannot complete order from status {order.status}.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Complete the order
        order.mark_as_completed(user=request.user)
        
        # Audit log
        create_audit_log(
            action=AuditLog.Action.ORDER_COMPLETED,
            user=request.user,
            restaurant=order.restaurant,
            entity=order,
            entity_type='Order',
            entity_repr=f'Order {order.order_number}',
            description=f'Order {order.order_number} completed',
            request=request
        )
        
        return Response(OrderSerializer(order).data)
    
    @action(detail=True, methods=['post'], url_path='cash', permission_classes=[IsAuthenticated, CanCollectCash])
    def cash(self, request, pk=None):
        """
        Collect cash payment for an order.
        Alias for collect_payment to match frontend API expectations.
        """
        return self.collect_payment(request, pk)
    
    @action(detail=False, methods=['post'], url_path='verify-qr')
    def verify_qr(self, request):
        """
        Verify an order QR code scanned by staff.
        Accessible via both /orders/verify-qr/ and /orders/verify_qr/ for frontend compatibility.
        """
        """
        Verify an order QR code scanned by staff.
        
        Expected request body:
        {
            "token": "qr-token-string"  # QR token from frontend
        }
        
        Returns order details if verification successful.
        """
        from apps.core.utils import parse_qr_token
        
        qr_token = request.data.get('token')
        
        if not qr_token:
            return Response(
                {
                    'error': 'MISSING_TOKEN',
                    'message': 'QR token is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get the staff's restaurant
        user = request.user
        restaurant = None
        
        if user.role == 'restaurant_owner':
            restaurant = user.owned_restaurants.first()
        elif user.role == 'staff':
            # Staff users have restaurant via staff_profile
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile and staff_profile.restaurant:
                restaurant = staff_profile.restaurant
        
        if not restaurant:
            return Response(
                {
                    'error': 'NO_RESTAURANT',
                    'message': 'User is not associated with a restaurant.'
                },
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Parse QR token
        qr_data = parse_qr_token(qr_token)
        
        # If it's just an order_id (backward compatibility)
        if 'order_id' in qr_data:
            try:
                order = Order.objects.get(
                    id=qr_data['order_id'],
                    restaurant=restaurant
                )
            except Order.DoesNotExist:
                create_audit_log(
                    action=AuditLog.Action.QR_VERIFICATION_FAILED,
                    user=request.user,
                    restaurant=restaurant,
                    description=f'QR verification failed for order_id: {qr_data["order_id"]}',
                    metadata={'order_id': qr_data['order_id']},
                    request=request,
                    severity=AuditLog.Severity.WARNING
                )
                return Response(
                    {
                        'error': 'ORDER_NOT_FOUND',
                        'message': 'Order not found or does not belong to this restaurant.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        else:
            # Verify QR signature
            restaurant_id = qr_data.get('restaurant_id')
            qr_version = qr_data.get('qr_version')
            signature = qr_data.get('signature')
            
            if not all([restaurant_id, qr_version, signature]):
                return Response(
                    {
                        'error': 'INVALID_QR_TOKEN',
                        'message': 'QR token is malformed.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify restaurant matches
            if str(restaurant.id) != restaurant_id:
                create_audit_log(
                    action=AuditLog.Action.QR_VERIFICATION_FAILED,
                    user=request.user,
                    restaurant=restaurant,
                    description=f'QR verification failed: restaurant mismatch',
                    metadata={'qr_restaurant_id': restaurant_id},
                    request=request,
                    severity=AuditLog.Severity.WARNING
                )
                return Response(
                    {
                        'error': 'RESTAURANT_MISMATCH',
                        'message': 'QR code does not belong to this restaurant.'
                    },
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Verify signature
            if not verify_qr_signature(restaurant_id, int(qr_version), signature, restaurant.qr_secret):
                create_audit_log(
                    action=AuditLog.Action.QR_VERIFICATION_FAILED,
                    user=request.user,
                    restaurant=restaurant,
                    description=f'QR verification failed: invalid signature',
                    request=request,
                    severity=AuditLog.Severity.WARNING
                )
                return Response(
                    {
                        'error': 'INVALID_QR_SIGNATURE',
                        'message': 'QR code signature is invalid or expired.'
                    },
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Find order by QR signature (if stored) or by restaurant + recent orders
            # For now, we'll need order_id in the token or search by signature
            # This is a simplified version - in production, QR should contain order_id
            order = None
            if 'order_id' in qr_data:
                try:
                    order = Order.objects.get(
                        id=qr_data['order_id'],
                        restaurant=restaurant
                    )
                except Order.DoesNotExist:
                    pass
            
            if not order:
                return Response(
                    {
                        'error': 'ORDER_NOT_FOUND',
                        'message': 'Order not found for this QR code.'
                    },
                    status=status.HTTP_404_NOT_FOUND
                )
        
        # Check if order is already completed (QR is single-use)
        if order.status == Order.Status.COMPLETED:
            return Response(
                {
                    'error': 'ORDER_ALREADY_COMPLETED',
                    'message': 'This order has already been completed.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Log successful verification
        create_audit_log(
            action=AuditLog.Action.QR_VERIFIED,
            user=request.user,
            restaurant=restaurant,
            entity=order,
            entity_type='Order',
            entity_repr=f'Order {order.order_number}',
            description=f'QR verified for order {order.order_number}',
            request=request
        )
        
        # Return order in format expected by frontend
        serializer = OrderSerializer(order)
        return Response(serializer.data)


class StaffCreateOrderView(generics.CreateAPIView):
    """Create a staff cash order."""
    
    serializer_class = StaffOrderCreateSerializer
    permission_classes = [IsAuthenticated, IsStaff, CanCollectCash]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        
        user = self.request.user
        if user.role == 'restaurant_owner':
            restaurant_id = self.request.data.get('restaurant')
            if restaurant_id:
                try:
                    context['restaurant'] = Restaurant.objects.get(
                        id=restaurant_id,
                        owner=user
                    )
                except Restaurant.DoesNotExist:
                    pass
        elif user.role == 'staff':
            # Staff users have restaurant via staff_profile
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile and staff_profile.restaurant:
                context['restaurant'] = staff_profile.restaurant
        
        return context
    
    def create(self, request, *args, **kwargs):
        context = self.get_serializer_context()
        if 'restaurant' not in context:
            return Response(
                {
                    'error': 'RESTAURANT_NOT_FOUND',
                    'message': 'Restaurant not found or you do not have access.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = self.get_serializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        order = serializer.save()
        
        # Audit log
        create_audit_log(
            action=AuditLog.Action.ORDER_CREATED,
            user=request.user,
            restaurant=order.restaurant,
            entity=order,
            entity_type='Order',
            entity_repr=f'Order {order.order_number}',
            description=f'Staff created cash order: {order.total_amount}',
            metadata={
                'order_type': order.order_type,
                'payment_method': order.payment_method,
                'item_count': order.items.count(),
            },
            request=request
        )
        
        return Response(
            OrderSerializer(order).data,
            status=status.HTTP_201_CREATED
        )


class DashboardStatsView(APIView):
    """Get dashboard statistics for owners."""
    
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get(self, request):
        user = request.user
        restaurant_id = request.query_params.get('restaurant')
        
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, owner=user)
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        today = timezone.now().date()
        yesterday = today - timedelta(days=1)
        
        # Active orders (all time - matches staff view)
        active_statuses = ['PENDING', 'AWAITING_PAYMENT', 'PREPARING', 'READY']
        all_active_orders = Order.objects.filter(
            restaurant=restaurant,
            status__in=active_statuses
        )
        
        # Today's stats (for trend analysis)
        today_orders = Order.objects.filter(
            restaurant=restaurant,
            created_at__date=today
        )
        yesterday_orders = Order.objects.filter(
            restaurant=restaurant,
            created_at__date=yesterday
        )
        
        today_completed = today_orders.filter(status='COMPLETED')
        yesterday_completed = yesterday_orders.filter(status='COMPLETED')
        
        today_revenue = sum(o.total_amount for o in today_completed)
        yesterday_revenue = sum(o.total_amount for o in yesterday_completed)
        
        # Calculate trends
        orders_trend = 0
        if yesterday_orders.count() > 0:
            orders_trend = ((today_orders.count() - yesterday_orders.count()) / yesterday_orders.count()) * 100
        
        revenue_trend = 0
        if yesterday_revenue > 0:
            revenue_trend = ((float(today_revenue) - float(yesterday_revenue)) / float(yesterday_revenue)) * 100
        
        # Calculate cash vs online breakdown
        today_cash_revenue = sum(o.total_amount for o in today_completed.filter(payment_method='CASH'))
        today_online_revenue = sum(o.total_amount for o in today_completed.filter(payment_method='ONLINE'))
        
        # Calculate orders by hour for today
        from django.db.models.functions import TruncHour
        hourly_orders = today_orders.annotate(
            hour=TruncHour('created_at')
        ).values('hour').annotate(
            count=Count('id')
        ).order_by('hour')
        
        orders_by_hour = [
            {'hour': int(stat['hour'].strftime('%H')), 'count': stat['count']}
            for stat in hourly_orders
        ]
        
        return Response({
            # Active orders (all time - matches staff active orders count)
            'active_orders': all_active_orders.count(),
            'pending_orders': all_active_orders.count(),  # Alias for frontend compatibility
            
            # Today's stats
            'today_orders': today_orders.count(),
            'completed_orders': today_completed.count(),
            'today_pending': today_orders.filter(status__in=active_statuses).count(),
            
            # Revenue
            'today_revenue': float(today_revenue),
            'cash_revenue': float(today_cash_revenue),
            'online_revenue': float(today_online_revenue),
            
            # Trends
            'orders_trend': round(orders_trend, 1),
            'revenue_trend': round(revenue_trend, 1),
            'orders_by_hour': orders_by_hour,
        })
