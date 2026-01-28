"""
Admin configuration for the Orders app.
"""

from django.contrib import admin
from .models import Order, OrderItem, DailyOrderSequence


class OrderItemInline(admin.TabularInline):
    """Inline for order items."""
    model = OrderItem
    extra = 0
    readonly_fields = ['menu_item', 'menu_item_name', 'price_at_order', 'quantity', 'subtotal']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    """Admin for Order model."""
    
    list_display = [
        'order_number', 'restaurant', 'status', 'payment_method',
        'payment_status', 'total_amount', 'created_at'
    ]
    list_filter = ['status', 'payment_method', 'payment_status', 'order_type', 'restaurant', 'created_at']
    search_fields = ['order_number', 'customer_name', 'restaurant__name']
    ordering = ['-created_at']
    inlines = [OrderItemInline]
    
    fieldsets = (
        (None, {'fields': ('restaurant', 'order_number', 'daily_sequence', 'order_type')}),
        ('Customer', {'fields': ('customer_name',)}),
        ('Status', {'fields': ('status', 'payment_method', 'payment_status')}),
        ('Amounts', {'fields': ('subtotal', 'tax', 'total_amount')}),
        ('Staff', {'fields': ('created_by', 'completed_by')}),
        ('Timestamps', {'fields': ('created_at', 'updated_at', 'completed_at')}),
        ('Versioning', {'fields': ('version',)}),
    )
    readonly_fields = [
        'order_number', 'daily_sequence', 'subtotal', 'tax', 'total_amount',
        'created_at', 'updated_at', 'version'
    ]


@admin.register(DailyOrderSequence)
class DailyOrderSequenceAdmin(admin.ModelAdmin):
    """Admin for DailyOrderSequence model."""
    
    list_display = ['restaurant', 'date', 'last_sequence']
    list_filter = ['restaurant', 'date']
    ordering = ['-date']
