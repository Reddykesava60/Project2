"""
Serializers for the Users app.
"""

from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """
    Serializer for user details.
    
    Frontend expects:
    {
        "id": 12,
        "role": "staff",  # lowercase
        "restaurant_id": 7,
        "can_collect_cash": false
    }
    """
    
    name = serializers.CharField(source='get_full_name', read_only=True)
    role = serializers.SerializerMethodField()  # Return lowercase role
    restaurant_id = serializers.SerializerMethodField()
    restaurant_name = serializers.SerializerMethodField()
    restaurant_slug = serializers.SerializerMethodField()
    can_collect_cash = serializers.SerializerMethodField()
    can_override_orders = serializers.SerializerMethodField()
    can_manage_stock = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = [
            'id', 'email', 'first_name', 'last_name', 'name',
            'role', 'phone', 'is_verified', 'two_factor_enabled',
            'date_joined', 'last_login',
            # Restaurant & Staff fields
            'restaurant_id', 'restaurant_name', 'restaurant_slug',
            'can_collect_cash', 'can_override_orders', 'can_manage_stock',
        ]
        read_only_fields = ['id', 'email', 'role', 'date_joined', 'last_login', 'is_verified']
    
    def get_role(self, obj):
        """Return role as string (frontend expects 'staff', 'restaurant_owner', 'platform_admin')."""
        return obj.role  # Already in correct format
    
    def get_restaurant_id(self, obj):
        """Get the restaurant ID for staff or owner."""
        if obj.role == 'staff':
            staff_profile = getattr(obj, 'staff_profile', None)
            if staff_profile and staff_profile.restaurant:
                return str(staff_profile.restaurant_id)
        elif obj.role == 'restaurant_owner':
            # Get the first owned restaurant
            restaurant = obj.owned_restaurants.first()
            if restaurant:
                return str(restaurant.id)
        elif obj.restaurant:
            return str(obj.restaurant.id)
        return None
    
    def get_restaurant_name(self, obj):
        """Get the restaurant name for staff or owner."""
        if obj.role == 'staff':
            staff_profile = getattr(obj, 'staff_profile', None)
            if staff_profile and staff_profile.restaurant:
                return staff_profile.restaurant.name
        elif obj.role == 'restaurant_owner':
            restaurant = obj.owned_restaurants.first()
            if restaurant:
                return restaurant.name
        elif obj.restaurant:
            return obj.restaurant.name
        return None
    
    def get_restaurant_slug(self, obj):
        """Get the restaurant slug for staff or owner."""
        if obj.role == 'staff':
            staff_profile = getattr(obj, 'staff_profile', None)
            if staff_profile and staff_profile.restaurant:
                return staff_profile.restaurant.slug
        elif obj.role == 'restaurant_owner':
            restaurant = obj.owned_restaurants.first()
            if restaurant:
                return restaurant.slug
        elif obj.restaurant:
            return obj.restaurant.slug
        return None
    
    def get_can_collect_cash(self, obj):
        """Get cash collection permission (staff only)."""
        if obj.role == 'staff':
            staff_profile = getattr(obj, 'staff_profile', None)
            if staff_profile:
                return staff_profile.can_collect_cash
        elif obj.role == 'restaurant_owner':
            # Owners always have all permissions
            return True
        elif obj.can_collect_cash:
            return obj.can_collect_cash
        return False
    
    def get_can_override_orders(self, obj):
        """Get order override permission (staff only)."""
        if obj.role == 'staff':
            staff_profile = getattr(obj, 'staff_profile', None)
            if staff_profile:
                return staff_profile.can_override_orders
        elif obj.role == 'restaurant_owner':
            # Owners always have all permissions
            return True
        return False

    def get_can_manage_stock(self, obj):
        """Get stock management permission (staff only)."""
        if obj.role == 'staff':
            staff_profile = getattr(obj, 'staff_profile', None)
            if staff_profile:
                return staff_profile.can_manage_stock
        elif obj.role == 'restaurant_owner':
            # Owners always have all permissions
            return True
        return False


class UserCreateSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""
    
    password = serializers.CharField(write_only=True, validators=[validate_password])
    password_confirm = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = [
            'email', 'password', 'password_confirm',
            'first_name', 'last_name', 'phone',
        ]
    
    def validate(self, attrs):
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError({'password_confirm': 'Passwords do not match.'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            phone=validated_data.get('phone', ''),
            role=User.Role.RESTAURANT_OWNER,  # New registrations are restaurant owners
        )
        return user


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""
    
    old_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    new_password_confirm = serializers.CharField(write_only=True)
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password_confirm']:
            raise serializers.ValidationError({'new_password_confirm': 'Passwords do not match.'})
        return attrs
    
    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user


class LoginHistorySerializer(serializers.ModelSerializer):
    """Serializer for login history."""
    
    class Meta:
        from .models import LoginHistory
        model = LoginHistory
        fields = ['id', 'ip_address', 'user_agent', 'timestamp', 'success']
        read_only_fields = fields
