"""
Audit logging system for DineFlow2.
Provides append-only audit trail for all critical actions.
"""

import logging
from functools import wraps
from django.db import models
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)


class AuditLog(models.Model):
    """
    Append-only audit log for tracking all critical system actions.
    
    This model is intentionally designed to be immutable after creation.
    No update or delete operations should be performed on audit logs.
    """
    
    class Action(models.TextChoices):
        # Authentication
        LOGIN_SUCCESS = 'LOGIN_SUCCESS', 'Login Success'
        LOGIN_FAILED = 'LOGIN_FAILED', 'Login Failed'
        LOGOUT = 'LOGOUT', 'Logout'
        PASSWORD_CHANGE = 'PASSWORD_CHANGE', 'Password Changed'
        
        # Orders
        ORDER_CREATED = 'ORDER_CREATED', 'Order Created'
        ORDER_STATUS_CHANGE = 'ORDER_STATUS_CHANGE', 'Order Status Changed'
        ORDER_COMPLETED = 'ORDER_COMPLETED', 'Order Completed'
        ORDER_CANCELLED = 'ORDER_CANCELLED', 'Order Cancelled'
        
        # Payments
        PAYMENT_INITIATED = 'PAYMENT_INITIATED', 'Payment Initiated'
        PAYMENT_SUCCESS = 'PAYMENT_SUCCESS', 'Payment Successful'
        PAYMENT_FAILED = 'PAYMENT_FAILED', 'Payment Failed'
        CASH_COLLECTED = 'CASH_COLLECTED', 'Cash Collected'
        REFUND_ISSUED = 'REFUND_ISSUED', 'Refund Issued'
        
        # Staff management
        STAFF_CREATED = 'STAFF_CREATED', 'Staff Created'
        STAFF_UPDATED = 'STAFF_UPDATED', 'Staff Updated'
        STAFF_PERMISSION_CHANGE = 'STAFF_PERMISSION_CHANGE', 'Staff Permission Changed'
        STAFF_DEACTIVATED = 'STAFF_DEACTIVATED', 'Staff Deactivated'
        
        # Restaurant
        RESTAURANT_CREATED = 'RESTAURANT_CREATED', 'Restaurant Created'
        RESTAURANT_UPDATED = 'RESTAURANT_UPDATED', 'Restaurant Updated'
        RESTAURANT_STATUS_CHANGE = 'RESTAURANT_STATUS_CHANGE', 'Restaurant Status Changed'
        
        # Subscriptions
        SUBSCRIPTION_CANCELLED = 'SUBSCRIPTION_CANCELLED', 'Subscription Cancelled'
        SUBSCRIPTION_REACTIVATED = 'SUBSCRIPTION_REACTIVATED', 'Subscription Reactivated'
        
        # QR
        QR_REGENERATED = 'QR_REGENERATED', 'QR Code Regenerated'
        QR_SCANNED = 'QR_SCANNED', 'QR Code Scanned'
        QR_VERIFIED = 'QR_VERIFIED', 'QR Verification Successful'
        QR_VERIFICATION_FAILED = 'QR_VERIFICATION_FAILED', 'QR Verification Failed'
        
        # Menu
        MENU_ITEM_CREATED = 'MENU_ITEM_CREATED', 'Menu Item Created'
        MENU_ITEM_UPDATED = 'MENU_ITEM_UPDATED', 'Menu Item Updated'
        MENU_ITEM_DELETED = 'MENU_ITEM_DELETED', 'Menu Item Deleted'
        CATEGORY_CREATED = 'CATEGORY_CREATED', 'Category Created'
        CATEGORY_DELETED = 'CATEGORY_DELETED', 'Category Deleted'
    
    class Severity(models.TextChoices):
        INFO = 'INFO', 'Info'
        WARNING = 'WARNING', 'Warning'
        ERROR = 'ERROR', 'Error'
        CRITICAL = 'CRITICAL', 'Critical'
    
    # Timestamp - immutable
    timestamp = models.DateTimeField(default=timezone.now, db_index=True)
    
    # Actor information
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    user_email = models.EmailField(blank=True)  # Preserved even if user is deleted
    
    # Tenant isolation
    restaurant = models.ForeignKey(
        'restaurants.Restaurant',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs'
    )
    restaurant_name = models.CharField(max_length=200, blank=True)  # Preserved
    
    # Action details
    action = models.CharField(max_length=50, choices=Action.choices, db_index=True)
    severity = models.CharField(max_length=10, choices=Severity.choices, default=Severity.INFO)
    
    # Target entity (what was affected)
    entity_type = models.CharField(max_length=50, blank=True)  # Order, Staff, MenuItem, etc.
    entity_id = models.CharField(max_length=50, blank=True)  # UUID of the entity
    entity_repr = models.CharField(max_length=200, blank=True)  # Human-readable representation
    
    # Change details
    old_value = models.JSONField(null=True, blank=True)
    new_value = models.JSONField(null=True, blank=True)
    
    # Additional context
    description = models.TextField(blank=True)
    metadata = models.JSONField(default=dict)  # Extra structured data
    
    # Request context (security tracking)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    request_id = models.CharField(max_length=50, blank=True)  # For tracing
    
    class Meta:
        verbose_name = 'Audit Log'
        verbose_name_plural = 'Audit Logs'
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['restaurant', 'timestamp']),
            models.Index(fields=['user', 'timestamp']),
            models.Index(fields=['action', 'timestamp']),
            models.Index(fields=['entity_type', 'entity_id']),
        ]
        # Prevent modification - Django doesn't have read-only table constraints,
        # but we enforce this in code
    
    def __str__(self):
        return f"[{self.timestamp}] {self.action} by {self.user_email or 'System'}"
    
    def save(self, *args, **kwargs):
        """Override save to enforce append-only behavior."""
        if self.pk:
            # Prevent updates to existing records
            raise ValueError("AuditLog entries are immutable and cannot be modified.")
        
        # Capture user email and restaurant name for historical reference
        if self.user and not self.user_email:
            self.user_email = self.user.email
        if self.restaurant and not self.restaurant_name:
            self.restaurant_name = self.restaurant.name
            
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        """Prevent deletion of audit logs."""
        raise ValueError("AuditLog entries cannot be deleted.")


def create_audit_log(
    action: str,
    user=None,
    restaurant=None,
    entity=None,
    entity_type: str = '',
    entity_repr: str = '',
    old_value=None,
    new_value=None,
    description: str = '',
    metadata: dict = None,
    ip_address: str = None,
    user_agent: str = '',
    request=None,
    severity: str = AuditLog.Severity.INFO
) -> AuditLog:
    """
    Helper function to create audit log entries.
    
    Usage:
        create_audit_log(
            action=AuditLog.Action.ORDER_CREATED,
            user=request.user,
            restaurant=order.restaurant,
            entity=order,
            entity_type='Order',
            entity_repr=f'Order {order.order_number}',
            description='Customer created new order via QR',
            request=request
        )
    """
    # Extract request info if provided
    if request and not ip_address:
        ip_address = get_client_ip(request)
    if request and not user_agent:
        user_agent = request.META.get('HTTP_USER_AGENT', '')[:500]
    if request and not user and hasattr(request, 'user') and request.user.is_authenticated:
        user = request.user
    
    # Get entity info
    entity_id = ''
    if entity:
        entity_id = str(getattr(entity, 'id', '') or getattr(entity, 'pk', ''))
        if not entity_type:
            entity_type = entity.__class__.__name__
        if not entity_repr:
            entity_repr = str(entity)[:200]
    
    log = AuditLog.objects.create(
        user=user,
        restaurant=restaurant,
        action=action,
        severity=severity,
        entity_type=entity_type,
        entity_id=entity_id,
        entity_repr=entity_repr,
        old_value=old_value,
        new_value=new_value,
        description=description,
        metadata=metadata or {},
        ip_address=ip_address,
        user_agent=user_agent,
    )
    
    logger.info(f"AuditLog: {action} - {entity_type}:{entity_id} by {user}")
    return log


def get_client_ip(request) -> str:
    """Extract client IP from request, handling proxies."""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR')


def audit_action(action: str, entity_type: str = '', get_entity=None, severity: str = AuditLog.Severity.INFO):
    """
    Decorator to automatically audit view actions.
    
    Usage:
        @audit_action(AuditLog.Action.ORDER_COMPLETED, entity_type='Order')
        def complete_order(self, request, pk=None):
            ...
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            result = func(self, request, *args, **kwargs)
            
            # Get entity from result or using getter
            entity = None
            if get_entity and hasattr(self, 'get_object'):
                try:
                    entity = self.get_object()
                except Exception:
                    pass
            
            # Get restaurant from entity or user
            restaurant = None
            if entity and hasattr(entity, 'restaurant'):
                restaurant = entity.restaurant
            elif hasattr(request.user, 'staff_profile') and request.user.staff_profile and request.user.staff_profile.restaurant:
                restaurant = request.user.staff_profile.restaurant
            elif hasattr(request.user, 'owned_restaurants'):
                restaurant = request.user.owned_restaurants.first()
            
            create_audit_log(
                action=action,
                user=request.user if request.user.is_authenticated else None,
                restaurant=restaurant,
                entity=entity,
                entity_type=entity_type,
                request=request,
                severity=severity
            )
            
            return result
        return wrapper
    return decorator
