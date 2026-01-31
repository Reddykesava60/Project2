"""
Serializers for the Restaurants app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Restaurant, Staff, ApiKey

User = get_user_model()


class RestaurantSerializer(serializers.ModelSerializer):
    """Full restaurant serializer for owners."""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'slug', 'description', 'logo',
            'owner', 'owner_name', 'owner_email',
            'status', 'subscription_tier', 'subscription_active',
            'timezone', 'currency', 'tax_rate', 'qr_version',
            'phone', 'email', 'address',
            'is_active',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'owner', 'qr_version', 'created_at', 'updated_at']
    
    def get_is_active(self, obj):
        """Return True if restaurant is active and subscription is valid."""
        return obj.status == Restaurant.Status.ACTIVE and obj.subscription_active


class RestaurantPublicSerializer(serializers.ModelSerializer):
    """Public restaurant serializer for customers."""
    
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'slug', 'description', 'logo',
            'currency', 'status', 'is_active',
        ]
    
    def get_is_active(self, obj):
        """Return True if restaurant is active and subscription is valid."""
        return obj.status == Restaurant.Status.ACTIVE and obj.subscription_active


class RestaurantCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating a restaurant."""
    
    class Meta:
        model = Restaurant
        fields = [
            'name', 'description', 'logo',
            'timezone', 'currency', 'tax_rate',
            'phone', 'email', 'address',
        ]
    
    def create(self, validated_data):
        validated_data['owner'] = self.context['request'].user
        restaurant = super().create(validated_data)
        
        # Link owner to restaurant (unified context)
        user = self.context['request'].user
        if not user.restaurant:
            user.restaurant = restaurant
            user.save(update_fields=['restaurant'])
            
        return restaurant


class StaffSerializer(serializers.ModelSerializer):
    """Serializer for staff members."""
    
    name = serializers.CharField(source='user.get_full_name', read_only=True)
    user_email = serializers.EmailField(source='user.email', read_only=True)
    two_factor_enabled = serializers.BooleanField(source='user.two_factor_enabled', read_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'id', 'user', 'name', 'user_email',
            'restaurant', 'position',
            'can_collect_cash', 'can_override_orders', 'can_manage_stock',
            'is_active', 'two_factor_enabled',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'restaurant', 'created_at', 'updated_at']


class StaffCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating staff members."""
    
    email = serializers.EmailField(write_only=True)
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True)
    
    class Meta:
        model = Staff
        fields = [
            'email', 'first_name', 'last_name', 'password',
            'position', 'can_collect_cash', 'can_override_orders', 'can_manage_stock',
        ]
    
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError('A user with this email already exists.')
        return value
    
    def create(self, validated_data):
        # Get restaurant from context
        restaurant = self.context['restaurant']
        
        # Create user first with restaurant link
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            role='staff',
            restaurant=restaurant,  # Link user to restaurant for consistent scoping
        )
        
        # Create staff profile
        staff = Staff.objects.create(
            user=user,
            restaurant=restaurant,
            position=validated_data.get('position', ''),
            can_collect_cash=validated_data.get('can_collect_cash', False),
            can_override_orders=validated_data.get('can_override_orders', False),
            can_manage_stock=validated_data.get('can_manage_stock', False),
        )
        
        return staff


class ApiKeySerializer(serializers.ModelSerializer):
    """Serializer for API keys."""
    
    class Meta:
        model = ApiKey
        fields = [
            'id', 'name', 'key', 'is_active', 'last_used',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'key', 'last_used', 'created_at', 'updated_at']
