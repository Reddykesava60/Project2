"""
Serializers for the Menu app.
"""

from rest_framework import serializers
from .models import MenuCategory, MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    """Full menu item serializer for owners."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    effective_availability = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name', 'restaurant',
            'name', 'description', 'price', 'image',
            'display_order', 'is_available', 'is_active',
            'stock_quantity', 'reserved_stock', 'available_stock',
            'unavailable_reason', 'unavailable_since',
            'is_in_stock', 'effective_availability',
            'times_ordered', 'version',
            'is_vegetarian', 'is_vegan', 'is_gluten_free',
            'prep_time_minutes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'times_ordered', 'version', 'created_at', 'updated_at']


class MenuItemPublicSerializer(serializers.ModelSerializer):
    """Public menu item serializer for customers."""
    
    stock_quantity = serializers.SerializerMethodField()

    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'image',
            'is_available', 'stock_quantity',
            'is_vegetarian', 'is_vegan', 'is_gluten_free',
        ]

    def get_stock_quantity(self, obj):
        """Return available stock. Returns None for unlimited stock."""
        if obj.stock_quantity is None:
            return None
        return obj.available_stock


class MenuCategorySerializer(serializers.ModelSerializer):
    """Full category serializer for owners."""
    
    items = MenuItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = MenuCategory
        fields = [
            'id', 'restaurant', 'name', 'description',
            'display_order', 'is_active', 'version',
            'items', 'item_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'version', 'created_at', 'updated_at']
    
    def get_item_count(self, obj):
        return obj.items.filter(is_active=True).count()


class MenuCategoryPublicSerializer(serializers.ModelSerializer):
    """Public category serializer for customers."""
    
    items = MenuItemPublicSerializer(many=True, source='active_items')
    
    class Meta:
        model = MenuCategory
        fields = ['id', 'name', 'description', 'items']
    
    def to_representation(self, instance):
        # Filter to only active, available, AND in-stock items
        from django.db.models import Q
        
        # 1. DB Level Filter: Active and marked available
        db_items = instance.items.filter(
            Q(is_active=True) & 
            Q(is_available=True)
        )
        
        # 2. Application Level Filter: Check dynamic available_stock (handles reservations)
        instance.active_items = [
            item for item in db_items 
            if item.is_in_stock
        ]
        
        return super().to_representation(instance)


class MenuCategoryCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating categories."""
    
    class Meta:
        model = MenuCategory
        fields = ['name', 'description', 'display_order', 'is_active']
    
    def create(self, validated_data):
        validated_data['restaurant'] = self.context['restaurant']
        return super().create(validated_data)


class MenuItemCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating menu items."""
    
    class Meta:
        model = MenuItem
        fields = [
            'category', 'name', 'description', 'price', 'image',
            'display_order', 'is_available', 'is_active',
            'is_vegetarian', 'is_vegan', 'is_gluten_free',
            'prep_time_minutes',
        ]
    
    def validate_category(self, value):
        restaurant = self.context['restaurant']
        if value.restaurant != restaurant:
            raise serializers.ValidationError('Category does not belong to this restaurant.')
        return value
    
    def create(self, validated_data):
        validated_data['restaurant'] = self.context['restaurant']
        return super().create(validated_data)


class MenuItemStockUpdateSerializer(serializers.Serializer):
    """Serializer for updating item availability and stock."""
    
    is_available = serializers.BooleanField(required=False)
    stock_quantity = serializers.IntegerField(required=False, allow_null=True, min_value=0)
    reason = serializers.CharField(required=False, allow_blank=True, max_length=255)


class MenuItemStaffSerializer(serializers.ModelSerializer):
    """Menu item serializer for staff - includes stock info but not all editing fields."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    is_in_stock = serializers.BooleanField(read_only=True)
    effective_availability = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name',
            'name', 'description', 'price', 'image',
            'is_available', 'is_active',
            'stock_quantity', 'unavailable_reason', 'unavailable_since',
            'is_in_stock', 'effective_availability',
            'is_vegetarian', 'is_vegan', 'is_gluten_free',
        ]
        read_only_fields = fields  # Staff can only view, stock updates via dedicated endpoint
