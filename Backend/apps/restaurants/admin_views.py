"""
Admin views for Platform Admin functionality.
Allows management of all restaurants in the platform.
"""

from rest_framework import generics, serializers, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from apps.core.permissions import IsPlatformAdmin
from apps.core.audit import create_audit_log, AuditLog
from .models import Restaurant
from .serializers import RestaurantSerializer


class AdminRestaurantSerializer(serializers.ModelSerializer):
    """Serializer for admin restaurant management."""
    
    owner_name = serializers.CharField(source='owner.get_full_name', read_only=True)
    owner_email = serializers.EmailField(source='owner.email', read_only=True)
    order_count = serializers.SerializerMethodField()
    staff_count = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = Restaurant
        fields = [
            'id', 'name', 'slug', 'description', 'logo',
            'owner', 'owner_name', 'owner_email',
            'status', 'subscription_tier', 'subscription_active',
            'is_active',
            'timezone', 'currency', 'tax_rate', 'qr_version',
            'phone', 'email', 'address',
            'order_count', 'staff_count',
            'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'slug', 'owner', 'qr_version', 'created_at', 'updated_at']
    
    def get_order_count(self, obj):
        return obj.orders.count()
    
    def get_staff_count(self, obj):
        return obj.staff_members.count()
    
    def get_is_active(self, obj):
        """Return True if restaurant is active and subscription is valid."""
        return obj.status == Restaurant.Status.ACTIVE and obj.subscription_active


class AdminRestaurantListView(generics.ListAPIView):
    """
    List all restaurants (Platform Admin only).
    
    Supports filtering by:
    - status: ACTIVE, INACTIVE, SUSPENDED
    - subscription_tier: FREE, BASIC, PREMIUM, ENTERPRISE
    """
    
    serializer_class = AdminRestaurantSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    
    def get_queryset(self):
        queryset = Restaurant.objects.select_related('owner').all()
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by subscription tier
        tier_filter = self.request.query_params.get('subscription_tier')
        if tier_filter:
            queryset = queryset.filter(subscription_tier=tier_filter)
        
        return queryset


class AdminRestaurantStatusView(APIView):
    """
    Update restaurant status (Platform Admin only).
    
    Supports:
    - ACTIVE: Restaurant is operational
    - INACTIVE: Restaurant is disabled by owner
    - SUSPENDED: Restaurant is suspended by platform admin
    """
    
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    
    def patch(self, request, pk):
        try:
            restaurant = Restaurant.objects.get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response(
                {
                    'error': 'RESTAURANT_NOT_FOUND',
                    'message': 'Restaurant not found.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        new_status = request.data.get('status')
        
        if new_status not in ['ACTIVE', 'INACTIVE', 'SUSPENDED']:
            return Response(
                {
                    'error': 'INVALID_STATUS',
                    'message': 'Status must be ACTIVE, INACTIVE, or SUSPENDED.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = restaurant.status
        restaurant.status = new_status
        restaurant.save(update_fields=['status', 'updated_at'])
        
        # Audit log
        create_audit_log(
            action=AuditLog.Action.RESTAURANT_STATUS_CHANGE,
            user=request.user,
            restaurant=restaurant,
            entity=restaurant,
            entity_type='Restaurant',
            entity_repr=restaurant.name,
            old_value={'status': old_status},
            new_value={'status': new_status},
            description=f'Restaurant status changed from {old_status} to {new_status}',
            request=request
        )
        
        return Response({
            'success': True,
            'id': str(restaurant.id),
            'name': restaurant.name,
            'status': restaurant.status,
            'message': f'Restaurant status updated to {new_status}.'
        })


class SubscriptionListView(generics.ListAPIView):
    """List all restaurant subscriptions (Platform Admin only)."""
    
    serializer_class = AdminRestaurantSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    
    def get_queryset(self):
        return Restaurant.objects.select_related('owner').all()
    
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        subscriptions = []
        for restaurant in queryset:
            subscriptions.append({
                'id': str(restaurant.id),
                'restaurant_id': str(restaurant.id),
                'restaurant_name': restaurant.name,
                'owner_email': restaurant.owner.email,
                'tier': restaurant.subscription_tier,
                'status': 'active' if restaurant.subscription_active else 'cancelled',
                'is_active': restaurant.subscription_active,
                'created_at': restaurant.created_at.isoformat(),
            })
        return Response(subscriptions)


class SubscriptionActionView(APIView):
    """Cancel or reactivate a restaurant subscription (Platform Admin only)."""
    
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    
    def post(self, request, pk, action):
        try:
            restaurant = Restaurant.objects.get(pk=pk)
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'RESTAURANT_NOT_FOUND', 'message': 'Restaurant not found.'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        if action == 'cancel':
            old_value = restaurant.subscription_active
            restaurant.subscription_active = False
            restaurant.save(update_fields=['subscription_active', 'updated_at'])
            
            create_audit_log(
                action=AuditLog.Action.SUBSCRIPTION_CANCELLED,
                user=request.user,
                restaurant=restaurant,
                entity=restaurant,
                entity_type='Restaurant',
                entity_repr=restaurant.name,
                old_value={'subscription_active': old_value},
                new_value={'subscription_active': False},
                description=f'Subscription cancelled for {restaurant.name}',
                request=request
            )
            
            return Response({
                'success': True,
                'id': str(restaurant.id),
                'status': 'cancelled',
                'message': 'Subscription cancelled.'
            })
        
        elif action == 'reactivate':
            old_value = restaurant.subscription_active
            restaurant.subscription_active = True
            restaurant.save(update_fields=['subscription_active', 'updated_at'])
            
            create_audit_log(
                action=AuditLog.Action.SUBSCRIPTION_REACTIVATED,
                user=request.user,
                restaurant=restaurant,
                entity=restaurant,
                entity_type='Restaurant',
                entity_repr=restaurant.name,
                old_value={'subscription_active': old_value},
                new_value={'subscription_active': True},
                description=f'Subscription reactivated for {restaurant.name}',
                request=request
            )
            
            return Response({
                'success': True,
                'id': str(restaurant.id),
                'status': 'active',
                'message': 'Subscription reactivated.'
            })
        
        return Response(
            {'error': 'INVALID_ACTION', 'message': 'Action must be cancel or reactivate.'},
            status=status.HTTP_400_BAD_REQUEST
        )