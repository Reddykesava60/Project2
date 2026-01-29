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


class MenuItemAttribute(models.Model):
    """
    Configurable attributes for menu items.
    Examples: egg count options, spice levels, toppings, portion sizes.
    
    Each attribute defines what customizations are available for a menu item.
    The actual selected values are stored in OrderItem.attributes as JSON.
    """
    
    class AttributeType(models.TextChoices):
        NUMBER = 'number', 'Number'  # e.g., egg count (0, 1, 2)
        SELECT = 'select', 'Select'  # e.g., spice level (normal, medium, high)
        MULTISELECT = 'multiselect', 'Multi-Select'  # e.g., toppings
        BOOLEAN = 'boolean', 'Boolean'  # e.g., extra cheese (yes/no)
    
    # Tenant isolation - every row has restaurant_id
    restaurant = models.ForeignKey(
        Restaurant,
        on_delete=models.CASCADE,
        related_name='menu_item_attributes'
    )
    menu_item = models.ForeignKey(
        MenuItem,
        on_delete=models.CASCADE,
        related_name='attributes'
    )
    
    # Attribute definition
    name = models.CharField(max_length=100, help_text='Internal name (e.g., egg_count)')
    display_name = models.CharField(max_length=100, help_text='Display name (e.g., Number of Eggs)')
    attribute_type = models.CharField(
        max_length=20,
        choices=AttributeType.choices,
        default=AttributeType.SELECT
    )
    
    # Options for select/multiselect types (JSON array)
    # e.g., ["normal", "medium", "high"] or [0, 1, 2, 3]
    options = models.JSONField(
        default=list,
        blank=True,
        help_text='Available options for select/multiselect types'
    )
    
    # Default value
    default_value = models.JSONField(
        null=True,
        blank=True,
        help_text='Default value for this attribute'
    )
    
    # Constraints for number type
    min_value = models.IntegerField(null=True, blank=True)
    max_value = models.IntegerField(null=True, blank=True)
    
    # Price modifiers (optional)
    price_modifier = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Additional price per unit/selection'
    )
    
    # Display
    display_order = models.PositiveIntegerField(default=0)
    is_required = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Menu Item Attribute'
        verbose_name_plural = 'Menu Item Attributes'
        ordering = ['menu_item', 'display_order', 'name']
        unique_together = ['menu_item', 'name']
        indexes = [
            models.Index(fields=['restaurant', 'menu_item']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.menu_item.name})"
