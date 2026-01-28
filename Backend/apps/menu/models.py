"""
Menu models for DineFlow2.
Categories and MenuItems with versioning for price tracking.
"""

from django.db import models
from apps.core.models import VersionedModel
from apps.restaurants.models import Restaurant


class MenuCategory(VersionedModel):
    """
    Category for organizing menu items.
    """
    
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_categories'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    display_order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'Menu Category'
        verbose_name_plural = 'Menu Categories'
        ordering = ['display_order', 'name']
        unique_together = ['restaurant', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.restaurant.name}"


class MenuItem(VersionedModel):
    """
    Individual menu item with price versioning.
    Price changes are tracked via version field.
    """
    
    category = models.ForeignKey(
        MenuCategory,
        on_delete=models.CASCADE,
        related_name='items'
    )
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_items'
    )
    
    # Basic info
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Display
    image = models.ImageField(upload_to='menu/items/', blank=True, null=True)
    display_order = models.PositiveIntegerField(default=0)
    
    # Status
    is_available = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Analytics
    times_ordered = models.PositiveIntegerField(default=0)
    
    # Dietary info
    is_vegetarian = models.BooleanField(default=False)
    is_vegan = models.BooleanField(default=False)
    is_gluten_free = models.BooleanField(default=False)
    
    # Preparation
    prep_time_minutes = models.PositiveIntegerField(default=15)
    
    class Meta:
        verbose_name = 'Menu Item'
        verbose_name_plural = 'Menu Items'
        ordering = ['display_order', 'name']
    
    def __str__(self):
        return f"{self.name} - ₹{self.price}"
    
    def increment_times_ordered(self, count: int = 1):
        """Increment the times_ordered counter."""
        self.times_ordered += count
        self.save(update_fields=['times_ordered', 'updated_at'])
