"""
Custom permissions for multi-tenant access control.
"""

from rest_framework import permissions


class IsOwner(permissions.BasePermission):
    """
    Permission to only allow owners of a restaurant to access it.
    Platform admins also have access for oversight.
    """
    def has_permission(self, request, view):
        # Backwards compatible role values: some older data/tests use 'OWNER'
        # Platform admins have oversight access
        return request.user.is_authenticated and request.user.role in ['restaurant_owner', 'OWNER', 'platform_admin', 'ADMIN']

    def has_object_permission(self, request, view, obj):
        # Platform admins can access any object
        if request.user.role in ['platform_admin', 'ADMIN']:
            return True
        # Check if the object has a restaurant attribute
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.owner == request.user
        # Check if the object is a restaurant
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class IsStaff(permissions.BasePermission):
    """
    Permission for staff members of a restaurant.
    """
    def has_permission(self, request, view):
        # Backwards compatible role values: some older data/tests use 'OWNER'/'STAFF'
        return request.user.is_authenticated and request.user.role in ['restaurant_owner', 'staff', 'OWNER', 'STAFF']

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Owners have full access to their restaurants
        if user.role in ['restaurant_owner', 'OWNER']:
            if hasattr(obj, 'restaurant'):
                return obj.restaurant.owner == user
            if hasattr(obj, 'owner'):
                return obj.owner == user
        
        # Staff have access to their assigned restaurant
        if user.role in ['staff', 'STAFF']:
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile and staff_profile.restaurant:
                if hasattr(obj, 'restaurant'):
                    return obj.restaurant == staff_profile.restaurant
                if hasattr(obj, 'id'):
                    return obj.id == staff_profile.restaurant_id
        
        return False


class IsPlatformAdmin(permissions.BasePermission):
    """
    Permission for platform administrators.
    """
    def has_permission(self, request, view):
        # Backwards compatible role values: some older data/tests use 'ADMIN'
        return request.user.is_authenticated and request.user.role in ['platform_admin', 'ADMIN']


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Allow read access to anyone, write access only to owners.
    """
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user.is_authenticated and request.user.role == 'restaurant_owner'

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        if hasattr(obj, 'restaurant'):
            return obj.restaurant.owner == request.user
        if hasattr(obj, 'owner'):
            return obj.owner == request.user
        return False


class CanCollectCash(permissions.BasePermission):
    """
    Permission for staff who can collect cash payments.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        if user.role in ['restaurant_owner', 'OWNER']:
            return True
        
        if user.role in ['staff', 'STAFF']:
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile:
                return staff_profile.can_collect_cash
        
        return False


class CanOverrideOrders(permissions.BasePermission):
    """
    Permission for staff who can override order prices.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        if user.role in ['restaurant_owner', 'OWNER']:
            return True
        
        if user.role in ['staff', 'STAFF']:
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile:
                return staff_profile.can_override_orders
        
        return False


class CanManageStock(permissions.BasePermission):
    """
    Permission for staff who can manage stock/menu items.
    """
    def has_permission(self, request, view):
        user = request.user
        if not user.is_authenticated:
            return False
        
        if user.role in ['restaurant_owner', 'OWNER', 'platform_admin', 'ADMIN']:
            return True
        
        if user.role in ['staff', 'STAFF']:
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile and staff_profile.is_active:
                return staff_profile.can_manage_stock
        
        return False

    def has_object_permission(self, request, view, obj):
        user = request.user
        
        if user.role in ['platform_admin', 'ADMIN']:
            return True

        # Owners
        if user.role in ['restaurant_owner', 'OWNER']:
            if hasattr(obj, 'restaurant'):
                return obj.restaurant.owner == user
            if hasattr(obj, 'owner'):
                return obj.owner == user

        # Staff
        if user.role in ['staff', 'STAFF']:
            staff_profile = getattr(user, 'staff_profile', None)
            if staff_profile and staff_profile.is_active and staff_profile.can_manage_stock:
                if hasattr(obj, 'restaurant'):
                    return obj.restaurant == staff_profile.restaurant
                if hasattr(obj, 'id'):
                    return obj.id == staff_profile.restaurant_id
        
        return False
