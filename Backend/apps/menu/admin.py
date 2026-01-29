"""
Admin configuration for the Menu app.
"""

from django.contrib import admin
from .models import MenuCategory, MenuItem


@admin.register(MenuCategory)
class MenuCategoryAdmin(admin.ModelAdmin):
    """Admin for MenuCategory model."""
    
    list_display = ['name', 'restaurant', 'display_order', 'is_active', 'created_at']
    list_filter = ['is_active', 'restaurant', 'created_at']
    search_fields = ['name', 'restaurant__name']
    ordering = ['restaurant', 'display_order', 'name']


@admin.register(MenuItem)
class MenuItemAdmin(admin.ModelAdmin):
    """Admin for MenuItem model."""
    
    list_display = ['name', 'category', 'restaurant', 'price', 'is_vegetarian', 'is_vegan', 'is_available', 'is_active', 'times_ordered']
    list_filter = ['is_available', 'is_active', 'is_vegetarian', 'is_vegan', 'restaurant', 'category']
    search_fields = ['name', 'description', 'restaurant__name']
    ordering = ['restaurant', 'category', 'display_order', 'name']
    list_editable = ['is_vegetarian', 'is_vegan', 'is_available', 'is_active']
    
    fieldsets = (
        (None, {'fields': ('name', 'description', 'category', 'restaurant')}),
        ('Pricing', {'fields': ('price', 'version')}),
        ('Display', {'fields': ('image', 'display_order')}),
        ('Status', {'fields': ('is_available', 'is_active')}),
        ('Dietary', {'fields': ('is_vegetarian', 'is_vegan', 'is_gluten_free')}),
        ('Preparation', {'fields': ('prep_time_minutes',)}),
        ('Analytics', {'fields': ('times_ordered',)}),
    )
    readonly_fields = ['version', 'times_ordered']
