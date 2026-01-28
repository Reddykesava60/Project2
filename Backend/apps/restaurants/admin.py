"""
Admin configuration for the Restaurants app.
"""

from django.contrib import admin
from .models import Restaurant, Staff, ApiKey


@admin.register(Restaurant)
class RestaurantAdmin(admin.ModelAdmin):
    """Admin for Restaurant model."""
    
    list_display = ['name', 'owner', 'status', 'subscription_tier', 'subscription_active', 'created_at']
    list_filter = ['status', 'subscription_tier', 'subscription_active', 'created_at']
    search_fields = ['name', 'slug', 'owner__email', 'owner__first_name', 'owner__last_name']
    prepopulated_fields = {'slug': ('name',)}
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('name', 'slug', 'description', 'logo')}),
        ('Owner', {'fields': ('owner',)}),
        ('Status', {'fields': ('status', 'subscription_tier', 'subscription_active')}),
        ('Settings', {'fields': ('timezone', 'currency', 'tax_rate', 'qr_version')}),
        ('Contact', {'fields': ('phone', 'email', 'address')}),
    )


@admin.register(Staff)
class StaffAdmin(admin.ModelAdmin):
    """Admin for Staff model."""
    
    list_display = ['user', 'restaurant', 'position', 'can_collect_cash', 'can_override_orders', 'is_active']
    list_filter = ['is_active', 'can_collect_cash', 'can_override_orders', 'restaurant']
    search_fields = ['user__email', 'user__first_name', 'user__last_name', 'restaurant__name']
    ordering = ['restaurant', 'user__first_name']


@admin.register(ApiKey)
class ApiKeyAdmin(admin.ModelAdmin):
    """Admin for ApiKey model."""
    
    list_display = ['name', 'restaurant', 'is_active', 'last_used', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'restaurant__name']
    readonly_fields = ['key', 'last_used']
    ordering = ['-created_at']
