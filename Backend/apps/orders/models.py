"""
Order models for DineFlow2.
Handles customer QR orders and staff cash orders.
"""

from django.db import models, transaction
from django.conf import settings
from django.utils import timezone
from apps.core.models import VersionedModel
from apps.restaurants.models import Restaurant
from apps.menu.models import MenuItem


class Order(VersionedModel):
    """
    Order model - represents a customer order.
    Supports both QR-based customer orders and staff-created cash orders.
    """
    
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        AWAITING_PAYMENT = 'AWAITING_PAYMENT', 'Awaiting Payment'
        PREPARING = 'PREPARING', 'Preparing'
        READY = 'READY', 'Ready'
        COMPLETED = 'COMPLETED', 'Completed'
        CANCELLED = 'CANCELLED', 'Cancelled'
        FAILED = 'FAILED', 'Failed'
    
    class PaymentMethod(models.TextChoices):
        CASH = 'CASH', 'Cash'
        ONLINE = 'ONLINE', 'Online'
    
    class PaymentStatus(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SUCCESS = 'SUCCESS', 'Success'
        FAILED = 'FAILED', 'Failed'
        REFUNDED = 'REFUNDED', 'Refunded'
    
    class OrderType(models.TextChoices):
        QR_CUSTOMER = 'QR_CUSTOMER', 'QR Customer Order'
        STAFF_CASH = 'STAFF_CASH', 'Staff Cash Order'
    
    # Restaurant
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='orders'
    )
    
    # Order identification
    order_number = models.CharField(max_length=10)  # Human-readable: A1, A2, B1, etc.
    daily_sequence = models.PositiveIntegerField()  # Sequential number for the day
    
    # Order type
    order_type = models.CharField(
        max_length=20,
        choices=OrderType.choices,
        default=OrderType.QR_CUSTOMER
    )
    
    # Customer info (GDPR: minimal data, no PII stored long-term)
    customer_name = models.CharField(max_length=100, blank=True)
    table_number = models.CharField(max_length=20, blank=True)  # Table/location identifier
    
    # QR validation
    qr_signature = models.CharField(max_length=64, blank=True)
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    
    # Payment
    payment_method = models.CharField(
        max_length=10,
        choices=PaymentMethod.choices,
        default=PaymentMethod.CASH
    )
    payment_status = models.CharField(
        max_length=10,
        choices=PaymentStatus.choices,
        default=PaymentStatus.PENDING
    )
    payment_id = models.CharField(max_length=100, blank=True)  # External payment ID
    
    # Amounts (stored as snapshot at order time)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    tax = models.DecimalField(max_digits=10, decimal_places=2)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Staff handling
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_orders'
    )
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='completed_orders'
    )
    
    # Cash collection tracking
    cash_collected_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cash_collected_orders'
    )
    cash_collected_at = models.DateTimeField(null=True, blank=True)
    cash_collected_ip = models.GenericIPAddressField(null=True, blank=True)
    
    # Analytics fields (calculated on creation for efficient aggregation)
    hour_of_day = models.PositiveSmallIntegerField(default=0)  # 0-23
    day_of_week = models.PositiveSmallIntegerField(default=0)  # 0-6 (Monday=0)
    
    # Timestamps
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'Order'
        verbose_name_plural = 'Orders'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'created_at']),
            models.Index(fields=['restaurant', 'status']),
            models.Index(fields=['order_number']),
            models.Index(fields=['restaurant', 'hour_of_day']),
            models.Index(fields=['restaurant', 'day_of_week']),
        ]
    
    def __str__(self):
        return f"Order {self.order_number} - {self.restaurant.name}"
    
    def save(self, *args, **kwargs):
        """Override save to set analytics fields on creation."""
        if not self.pk:  # Only on creation
            now = timezone.now()
            self.hour_of_day = now.hour
            self.day_of_week = now.weekday()  # Monday=0, Sunday=6
        super().save(*args, **kwargs)
    
    # Valid status transitions map
    ALLOWED_TRANSITIONS = {
        Status.PENDING: [Status.AWAITING_PAYMENT, Status.PREPARING, Status.CANCELLED],
        Status.AWAITING_PAYMENT: [Status.PREPARING, Status.CANCELLED, Status.FAILED],
        Status.PREPARING: [Status.READY, Status.COMPLETED, Status.CANCELLED],
        Status.READY: [Status.COMPLETED, Status.CANCELLED],
        Status.COMPLETED: [],  # Terminal state
        Status.CANCELLED: [],  # Terminal state
        Status.FAILED: [Status.PENDING],  # Can retry
    }
    
    def can_transition_to(self, new_status):
        """Check if transition to new_status is allowed."""
        return new_status in self.ALLOWED_TRANSITIONS.get(self.status, [])
    
    def _validate_transition(self, new_status):
        """Validate and raise exception if transition is not allowed."""
        if not self.can_transition_to(new_status):
            raise ValueError(
                f"Cannot transition from {self.status} to {new_status}. "
                f"Allowed: {self.ALLOWED_TRANSITIONS.get(self.status, [])}"
            )
    
    def mark_as_preparing(self, user=None):
        """Mark order as being prepared."""
        self._validate_transition(self.Status.PREPARING)
        self.status = self.Status.PREPARING
        self.save(update_fields=['status', 'updated_at', 'version'])
    
    def mark_as_ready(self, user=None):
        """Mark order as ready for pickup."""
        self._validate_transition(self.Status.READY)
        self.status = self.Status.READY
        self.save(update_fields=['status', 'updated_at', 'version'])
    
    def mark_as_completed(self, user=None):
        """Mark order as completed. Payment must be successful."""
        # Validate payment status before completion
        if self.payment_status != self.PaymentStatus.SUCCESS:
            raise ValueError('Order cannot be completed until payment is successful.')
        
        self._validate_transition(self.Status.COMPLETED)
        self.status = self.Status.COMPLETED
        self.completed_at = timezone.now()
        self.completed_by = user
        self.save(update_fields=['status', 'completed_at', 'completed_by', 'updated_at', 'version'])
    
    def mark_as_cancelled(self, user=None):
        """Cancel the order."""
        self._validate_transition(self.Status.CANCELLED)
        self.status = self.Status.CANCELLED
        self.save(update_fields=['status', 'updated_at', 'version'])
    
    def collect_payment(self, user=None, ip_address=None):
        """Mark cash payment as collected."""
        self.payment_status = self.PaymentStatus.SUCCESS
        self.cash_collected_by = user
        self.cash_collected_at = timezone.now()
        self.cash_collected_ip = ip_address
        if self.status == self.Status.AWAITING_PAYMENT:
            self.status = self.Status.PREPARING
        self.save(update_fields=[
            'payment_status', 'status', 'cash_collected_by', 
            'cash_collected_at', 'cash_collected_ip', 'updated_at', 'version'
        ])
        
        # Create audit log entry
        CashAuditLog.objects.create(
            order=self,
            restaurant=self.restaurant,
            staff=user,
            action=CashAuditLog.Action.CASH_COLLECTED,
            amount=self.total_amount,
            ip_address=ip_address,
        )


class OrderItem(models.Model):
    """
    Individual item in an order.
    Stores price at order time for historical accuracy.
    """
    
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='items'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.SET_NULL,
        null=True,
        related_name='order_items'
    )
    
    # Snapshot of item at order time
    menu_item_name = models.CharField(max_length=200)
    price_at_order = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField(default=1)
    
    # Calculated field
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Special instructions
    notes = models.TextField(blank=True)
    
    class Meta:
        verbose_name = 'Order Item'
        verbose_name_plural = 'Order Items'
    
    def __str__(self):
        return f"{self.quantity}x {self.menu_item_name}"
    
    def save(self, *args, **kwargs):
        # Auto-calculate subtotal
        self.subtotal = self.price_at_order * self.quantity
        super().save(*args, **kwargs)


class DailyOrderSequence(models.Model):
    """
    Track daily order sequence numbers per restaurant.
    Ensures unique order numbers per day.
    """
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='daily_sequences'
    )
    date = models.DateField()
    last_sequence = models.PositiveIntegerField(default=0)
    
    class Meta:
        unique_together = ['restaurant', 'date']
    
    @classmethod
    def get_next_sequence(cls, restaurant):
        """Get the next order sequence number for today with atomic locking."""
        today = timezone.now().date()
        with transaction.atomic():
            # Use select_for_update to prevent race conditions
            seq, created = cls.objects.select_for_update().get_or_create(
                restaurant=restaurant,
                date=today,
                defaults={'last_sequence': 0}
            )
            seq.last_sequence += 1
            seq.save(update_fields=['last_sequence'])
            return seq.last_sequence


class CashAuditLog(models.Model):
    """
    Audit trail for all cash-related actions.
    Tracks cash collection, staff orders, and refunds for accountability.
    """
    
    class Action(models.TextChoices):
        CASH_COLLECTED = 'CASH_COLLECTED', 'Cash Collected'
        CASH_ORDER_CREATED = 'CASH_ORDER_CREATED', 'Cash Order Created'
        CASH_REFUND = 'CASH_REFUND', 'Cash Refund'
        PAYMENT_OVERRIDE = 'PAYMENT_OVERRIDE', 'Payment Override'
    
    # Related entities
    order = models.ForeignKey(
        Order,
        on_delete=models.CASCADE,
        related_name='cash_audit_logs'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='cash_audit_logs'
    )
    staff = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='cash_audit_logs'
    )
    
    # Action details
    action = models.CharField(
        max_length=30,
        choices=Action.choices
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    notes = models.TextField(blank=True)
    
    # Security tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    
    # Timestamp
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        verbose_name = 'Cash Audit Log'
        verbose_name_plural = 'Cash Audit Logs'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['restaurant', 'created_at']),
            models.Index(fields=['staff', 'created_at']),
            models.Index(fields=['order']),
        ]
    
    def __str__(self):
        staff_name = self.staff.get_full_name() if self.staff else 'Unknown'
        return f"{self.get_action_display()} - {self.amount} by {staff_name}"
