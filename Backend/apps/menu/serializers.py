"""
Serializers for the Menu app.
"""

from rest_framework import serializers
from .models import MenuCategory, MenuItem


class MenuItemSerializer(serializers.ModelSerializer):
    """Full menu item serializer for owners."""
    
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'category', 'category_name', 'restaurant',
            'name', 'description', 'price', 'image',
            'display_order', 'is_available', 'is_active',
            'times_ordered', 'version',
            'is_vegetarian', 'is_vegan', 'is_gluten_free',
            'prep_time_minutes',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'times_ordered', 'version', 'created_at', 'updated_at']


class MenuItemPublicSerializer(serializers.ModelSerializer):
    """Public menu item serializer for customers."""
    
    class Meta:
        model = MenuItem
        fields = [
            'id', 'name', 'description', 'price', 'image',
            'is_available',
            'is_vegetarian', 'is_vegan', 'is_gluten_free',
        ]


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
        # Filter to only active and available items
        instance.active_items = instance.items.filter(is_active=True, is_available=True)
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
