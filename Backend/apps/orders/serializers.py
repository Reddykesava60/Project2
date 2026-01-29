"""
Serializers for the Orders app.
"""

from decimal import Decimal
from django.utils import timezone
from rest_framework import serializers
from apps.menu.models import MenuItem
from apps.restaurants.models import Restaurant
from .models import Order, OrderItem, DailyOrderSequence, CashAuditLog
from apps.core.utils import generate_order_number


class OrderItemSerializer(serializers.ModelSerializer):
    """Serializer for order items."""
    
    # Aliases for frontend compatibility
    unit_price = serializers.DecimalField(source='price_at_order', max_digits=10, decimal_places=2, read_only=True)
    total_price = serializers.DecimalField(source='subtotal', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = OrderItem
        fields = [
            'id', 'menu_item', 'menu_item_id', 'menu_item_name',
            'price_at_order', 'unit_price', 'quantity', 'subtotal', 'total_price', 'notes', 'attributes',
        ]
        read_only_fields = ['id', 'menu_item_name', 'price_at_order', 'subtotal', 'unit_price', 'total_price', 'menu_item_id']


class CashAuditLogSerializer(serializers.ModelSerializer):
    """Serializer for cash audit log entries."""
    
    staff_name = serializers.CharField(source='staff.get_full_name', read_only=True)
    order_number = serializers.CharField(source='order.order_number', read_only=True)
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    
    class Meta:
        model = CashAuditLog
        fields = [
            'id', 'order', 'order_number', 'restaurant',
            'staff', 'staff_name', 'action', 'action_display',
            'amount', 'notes', 'ip_address', 'created_at',
        ]
        read_only_fields = ['id', 'order', 'restaurant', 'staff', 'ip_address', 'created_at']


class OrderSerializer(serializers.ModelSerializer):
    """
    Full order serializer for owners/staff.
    
    IMPORTANT: This serializer is READ-ONLY for sensitive fields.
    Frontend can NEVER set: payment_status, status (use dedicated endpoints)
    
    Note: Frontend may use 'order_status' or 'status' interchangeably.
    We include both for compatibility.
    Also includes 'daily_order_number' alias for 'order_number' for frontend compatibility.
    """
    
    items = OrderItemSerializer(many=True, read_only=True)
    restaurant_name = serializers.CharField(source='restaurant.name', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    cash_collected_by_name = serializers.CharField(source='cash_collected_by.get_full_name', read_only=True)
    # Aliases for frontend compatibility
    order_status = serializers.SerializerMethodField()
    daily_order_number = serializers.CharField(source='order_number', read_only=True)
    total = serializers.DecimalField(source='total_amount', max_digits=10, decimal_places=2, read_only=True)
    # Override status, payment_method, payment_status to return lowercase for frontend
    status = serializers.SerializerMethodField()
    payment_method = serializers.SerializerMethodField()
    payment_status = serializers.SerializerMethodField()
    
    def get_order_status(self, obj):
        """Return lowercase status for frontend compatibility."""
        return obj.status.lower() if obj.status else None
    
    def get_status(self, obj):
        """Return lowercase status for frontend compatibility."""
        return obj.status.lower() if obj.status else None
    
    def get_payment_method(self, obj):
        """Return lowercase payment_method for frontend compatibility."""
        return obj.payment_method.lower() if obj.payment_method else None
    
    def get_payment_status(self, obj):
        """Return lowercase payment_status for frontend compatibility."""
        return obj.payment_status.lower() if obj.payment_status else None
    
    class Meta:
        model = Order
        fields = [
            'id', 'restaurant', 'restaurant_name',
            'order_number', 'daily_order_number', 'daily_sequence', 'order_type',
            'customer_name', 'table_number',
            'is_parcel', 'spicy_level',  # Order preferences
            'status', 'order_status',  # Both for frontend compat
            'payment_method', 'payment_status',  # READ-ONLY - frontend cannot set these
            'subtotal', 'tax', 'total', 'total_amount',
            'items',
            'created_by', 'created_by_name', 'completed_by',
            'cash_collected_by', 'cash_collected_by_name',
            'cash_collected_at', 'cash_collected_ip',
            'created_at', 'updated_at', 'completed_at',
            'version', 'qr_signature',
        ]
        # ALL fields are read-only - status changes must use dedicated endpoints
        read_only_fields = [
            'id', 'restaurant', 'restaurant_name',
            'order_number', 'daily_order_number', 'daily_sequence', 'order_type',
            'customer_name', 'table_number',
            'is_parcel', 'spicy_level',
            'status', 'order_status',  # CRITICAL: Frontend cannot set status
            'payment_method', 'payment_status',  # CRITICAL: Frontend cannot set payment_status
            'subtotal', 'tax', 'total', 'total_amount',
            'items',
            'created_by', 'created_by_name', 'completed_by',
            'cash_collected_by', 'cash_collected_by_name',
            'cash_collected_at', 'cash_collected_ip',
            'created_at', 'updated_at', 'completed_at',
            'version', 'qr_signature',
        ]


class OrderItemCreateSerializer(serializers.Serializer):
    """Serializer for creating order items."""
    
    menu_item_id = serializers.UUIDField()
    quantity = serializers.IntegerField(min_value=1, max_value=99)
    notes = serializers.CharField(required=False, allow_blank=True, max_length=500)


class OrderCreateSerializer(serializers.Serializer):
    """Serializer for creating orders (public/customer).
    
    IMPORTANT: Customer can select payment_method but NEVER payment_status.
    Orders always start with payment_status='pending'.
    """
    
    customer_name = serializers.CharField(max_length=100)
    table_number = serializers.CharField(max_length=20, required=False, allow_blank=True)
    # PRD: payment_method must be cash or upi (lowercase)
    payment_method = serializers.ChoiceField(choices=['cash', 'upi'])
    items = OrderItemCreateSerializer(many=True, min_length=1)
    privacy_accepted = serializers.BooleanField()
    qr_signature = serializers.CharField(required=False, allow_blank=True)
    # Order preferences
    is_parcel = serializers.BooleanField(required=False, default=False)
    spicy_level = serializers.ChoiceField(
        choices=['normal', 'medium', 'high'],
        required=False,
        default='normal'
    )
    
    def validate_privacy_accepted(self, value):
        if not value:
            raise serializers.ValidationError('You must accept the privacy policy.')
        return value
    
    def validate_items(self, value):
        if not value:
            raise serializers.ValidationError('Order must have at least one item.')
        return value
    
    def create(self, validated_data):
        from django.db import transaction
        
        restaurant = self.context['restaurant']
        items_data = validated_data.pop('items')
        validated_data.pop('privacy_accepted')
        
        with transaction.atomic():
            # Get next sequence number
            daily_sequence = DailyOrderSequence.get_next_sequence(restaurant)
            order_number = generate_order_number(daily_sequence)
            
            # Calculate totals
            subtotal = Decimal('0.00')
            order_items = []
            
            for item_data in items_data:
                try:
                    # LOCK the menu item row to prevent race conditions
                    menu_item = MenuItem.objects.select_for_update().get(
                        id=item_data['menu_item_id'],
                        restaurant=restaurant,
                        is_active=True,
                        is_available=True
                    )
                except MenuItem.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Menu item {item_data['menu_item_id']} not found or unavailable."
                    )
                
                # STOCK CHECK & DECREMENT
                quantity = item_data['quantity']
                if menu_item.stock_quantity is not None:
                    if menu_item.stock_quantity < quantity:
                        # Return structured data (DRF will wrap in list usually, but detailed structure helps)
                        raise serializers.ValidationError(
                            {
                                'code': 'INSUFFICIENT_STOCK',
                                'item_id': str(menu_item.id),
                                'item_name': menu_item.name,
                                'available_quantity': menu_item.stock_quantity,
                                'message': f"Only {menu_item.stock_quantity} units of {menu_item.name} are available."
                            }
                        )
                    menu_item.stock_quantity -= quantity
                    # Optional: Auto-mark unavailable if 0, but backend logic should handle 0 stock visibility
                    # keeping it strictly data-driven
                    menu_item.save(update_fields=['stock_quantity', 'updated_at'])

                item_subtotal = menu_item.price * quantity
                subtotal += item_subtotal
                
                order_items.append({
                    'menu_item': menu_item,
                    'menu_item_name': menu_item.name,
                    'price_at_order': menu_item.price,
                    'quantity': quantity,
                    'subtotal': item_subtotal,
                    'notes': item_data.get('notes', ''),
                })
            
            # Calculate tax
            tax = subtotal * Decimal(str(restaurant.tax_rate))
            total_amount = subtotal + tax
    
            # PRD Rules:
            # - All new orders start with status='pending' and payment_status='pending'
            # - Status transitions: pending -> preparing -> completed
            # - payment_status can only be set by backend (collect_payment or payment webhook)
            
            # Create order with lowercase status values
            order = Order.objects.create(
                restaurant=restaurant,
                order_number=order_number,
                daily_sequence=daily_sequence,
                order_type=Order.OrderType.QR_CUSTOMER,
                customer_name=validated_data['customer_name'],
                table_number=validated_data.get('table_number', ''),
                is_parcel=validated_data.get('is_parcel', False),
                spicy_level=validated_data.get('spicy_level', 'normal'),
                qr_signature=validated_data.get('qr_signature', ''),
                status='pending',  # Always start pending
                payment_method=validated_data['payment_method'],  # Already lowercase from choices
                payment_status='pending',  # Always start pending - NEVER set by frontend
                subtotal=subtotal,
                tax=tax,
                total_amount=total_amount,
            )
            
            # Create order items
            for item in order_items:
                OrderItem.objects.create(order=order, **item)
            
            return order


class StaffOrderCreateSerializer(serializers.Serializer):
    """Serializer for staff-created cash orders."""
    
    customer_name = serializers.CharField(max_length=100, required=False, allow_blank=True)
    items = OrderItemCreateSerializer(many=True, min_length=1)
    
    def create(self, validated_data):
        from django.db import transaction

        restaurant = self.context['restaurant']
        user = self.context['request'].user
        items_data = validated_data.pop('items')
        
        with transaction.atomic():
            # Get next sequence number
            daily_sequence = DailyOrderSequence.get_next_sequence(restaurant)
            order_number = generate_order_number(daily_sequence)
            
            # Calculate totals
            subtotal = Decimal('0.00')
            order_items = []
            
            for item_data in items_data:
                try:
                    # LOCK the menu item row
                    menu_item = MenuItem.objects.select_for_update().get(
                        id=item_data['menu_item_id'],
                        restaurant=restaurant,
                        is_active=True,
                        is_available=True
                    )
                except MenuItem.DoesNotExist:
                    raise serializers.ValidationError(
                        f"Menu item {item_data['menu_item_id']} not found or unavailable."
                    )
                
                # STOCK CHECK & DECREMENT
                quantity = item_data['quantity']
                if menu_item.stock_quantity is not None:
                    if menu_item.stock_quantity < quantity:
                        raise serializers.ValidationError(
                            f"Insufficient stock for {menu_item.name}. Available: {menu_item.stock_quantity}, Requested: {quantity}"
                        )
                    menu_item.stock_quantity -= quantity
                    menu_item.save(update_fields=['stock_quantity', 'updated_at'])
                
                item_subtotal = menu_item.price * quantity
                subtotal += item_subtotal
                
                order_items.append({
                    'menu_item': menu_item,
                    'menu_item_name': menu_item.name,
                    'price_at_order': menu_item.price,
                    'quantity': quantity,
                    'subtotal': item_subtotal,
                    'notes': item_data.get('notes', ''),
                })
            
            # Calculate tax
            tax = subtotal * Decimal(str(restaurant.tax_rate))
            total_amount = subtotal + tax
            
            # Get client IP
            ip_address = self.get_client_ip()
    
            # PRD Rules:
            # - Staff-created cash orders MUST start as pending
            # - Payment is only confirmed when a can_collect_cash staff member collects it
            # - Use lowercase status values
            order = Order.objects.create(
                restaurant=restaurant,
                order_number=order_number,
                daily_sequence=daily_sequence,
                order_type=Order.OrderType.STAFF_CASH,
                customer_name=validated_data.get('customer_name', ''),
                status='pending',  # Lowercase per PRD
                payment_method='cash',  # Lowercase per PRD
                payment_status='pending',  # Lowercase per PRD - NEVER set by frontend
                subtotal=subtotal,
                tax=tax,
                total_amount=total_amount,
                created_by=user,
            )
            
            # Create order items
            for item in order_items:
                OrderItem.objects.create(order=order, **item)
            
            # Create cash audit log for staff-created order
            CashAuditLog.objects.create(
                order=order,
                restaurant=restaurant,
                staff=user,
                action=CashAuditLog.Action.CASH_ORDER_CREATED,
                amount=total_amount,
                ip_address=ip_address,
            )
            
            return order
    
    def get_client_ip(self):
        """Extract client IP from request."""
        request = self.context.get('request')
        if not request:
            return None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')


class OrderStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating order status.
    
    PRD Rules:
    - Only valid statuses: pending, preparing, completed (lowercase)
    - Only valid transitions: pending -> preparing -> completed
    - Completed orders can NEVER be edited
    """
    
    # Only allow valid statuses per PRD (lowercase)
    status = serializers.ChoiceField(choices=['preparing', 'completed'])
    
    def validate(self, attrs):
        order = self.instance
        new_status = attrs['status']
        
        # RULE: Completed orders cannot be modified
        if order and order.status == 'completed':
            raise serializers.ValidationError(
                {'status': 'Completed orders cannot be modified.'}
            )
        
        # Validate transition
        if order and not order.can_transition_to(new_status):
            raise serializers.ValidationError(
                {'status': f'Cannot transition from {order.status} to {new_status}.'}
            )
        
        return attrs
    
    def update(self, order, validated_data):
        new_status = validated_data['status']
        user = self.context['request'].user
        
        if new_status == 'preparing':
            order.mark_as_preparing(user)
        elif new_status == 'completed':
            order.mark_as_completed(user)
        
        return order


class CollectPaymentSerializer(serializers.Serializer):
    """Serializer for collecting cash payment."""
    
    def get_client_ip(self):
        """Extract client IP from request."""
        request = self.context.get('request')
        if not request:
            return None
        
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR')
    
    def update(self, order, validated_data):
        user = self.context['request'].user
        ip_address = self.get_client_ip()
        order.collect_payment(user, ip_address)
        return order
