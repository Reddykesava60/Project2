"""
Views for the Menu app.
"""

from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsOwner, CanManageStock
from apps.core.audit import create_audit_log, AuditLog
from apps.restaurants.models import Restaurant, Staff
from .models import MenuCategory, MenuItem
from .serializers import (
    MenuCategorySerializer,
    MenuCategoryPublicSerializer,
    MenuCategoryCreateSerializer,
    MenuItemSerializer,
    MenuItemPublicSerializer,
    MenuItemCreateSerializer,
    MenuItemStockUpdateSerializer,
)


class MenuCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for menu category management."""
    
    permission_classes = [IsAuthenticated, CanManageStock]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'is_active']
    pagination_class = None
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MenuCategoryCreateSerializer
        return MenuCategorySerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['platform_admin', 'ADMIN']:
            return MenuCategory.objects.all()
        
        # Owner
        if user.role in ['restaurant_owner', 'OWNER']:
            return MenuCategory.objects.filter(restaurant__owner=user)
            
        # Staff with permission
        if user.role in ['staff', 'STAFF']:
            try:
                staff = user.staff_profile
                if staff.is_active and staff.can_manage_stock:
                    return MenuCategory.objects.filter(restaurant=staff.restaurant)
            except Staff.DoesNotExist:
                pass
                
        return MenuCategory.objects.none()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            try:
                context['restaurant'] = Restaurant.objects.get(
                    id=restaurant_id,
                    owner=self.request.user
                )
            except Restaurant.DoesNotExist:
                pass
        # Also check for restaurant in POST data
        if self.request.method == 'POST' and not context.get('restaurant'):
            restaurant_id = self.request.data.get('restaurant')
            if restaurant_id:
                try:
                    context['restaurant'] = Restaurant.objects.get(
                        id=restaurant_id,
                        owner=self.request.user
                    )
                except Restaurant.DoesNotExist:
                    pass
            else:
                # Default to first owned restaurant
                restaurant = self.request.user.owned_restaurants.first()
                if restaurant:
                    context['restaurant'] = restaurant
        return context
    
    def perform_create(self, serializer):
        """Create category with audit logging."""
        category = serializer.save()
        
        create_audit_log(
            action=AuditLog.Action.CATEGORY_CREATED,
            user=self.request.user,
            restaurant=category.restaurant,
            entity=category,
            entity_type='MenuCategory',
            entity_repr=category.name,
            description=f'Category created: {category.name}',
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Delete category with audit logging."""
        create_audit_log(
            action=AuditLog.Action.CATEGORY_DELETED,
            user=self.request.user,
            restaurant=instance.restaurant,
            entity=instance,
            entity_type='MenuCategory',
            entity_repr=instance.name,
            description=f'Category deleted: {instance.name}',
            request=self.request
        )
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Update display order of category."""
        category = self.get_object()
        new_order = request.data.get('display_order')
        if new_order is not None:
            category.display_order = int(new_order)
            category.save(update_fields=['display_order', 'updated_at'])
        return Response({'display_order': category.display_order})


class MenuItemViewSet(viewsets.ModelViewSet):
    """ViewSet for menu item management."""
    
from apps.core.permissions import IsOwner, CanManageStock

# ...

class MenuItemViewSet(viewsets.ModelViewSet):
    """ViewSet for menu item management."""
    
    permission_classes = [IsAuthenticated, CanManageStock]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'category', 'is_available', 'is_active']
    pagination_class = None
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MenuItemCreateSerializer
        return MenuItemSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['platform_admin', 'ADMIN']:
            return MenuItem.objects.all()
            
        # Owner: see all items for their restaurant
        if user.role in ['restaurant_owner', 'OWNER']:
            return MenuItem.objects.filter(restaurant__owner=user)
            
        # Staff: see items for their restaurant if they have permission
        if user.role in ['staff', 'STAFF']:
            try:
                staff = user.staff_profile
                if staff.is_active and staff.can_manage_stock:
                    return MenuItem.objects.filter(restaurant=staff.restaurant)
            except Staff.DoesNotExist:
                pass
                
        return MenuItem.objects.none()
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            try:
                context['restaurant'] = Restaurant.objects.get(
                    id=restaurant_id,
                    owner=self.request.user
                )
            except Restaurant.DoesNotExist:
                pass
        # Also check for restaurant from category in POST data
        if self.request.method == 'POST' and not context.get('restaurant'):
            category_id = self.request.data.get('category')
            if category_id:
                try:
                    category = MenuCategory.objects.get(
                        id=category_id,
                        restaurant__owner=self.request.user
                    )
                    context['restaurant'] = category.restaurant
                except MenuCategory.DoesNotExist:
                    pass
        return context
    
    def perform_create(self, serializer):
        """Create menu item with audit logging."""
        item = serializer.save()
        
        create_audit_log(
            action=AuditLog.Action.MENU_ITEM_CREATED,
            user=self.request.user,
            restaurant=item.restaurant,
            entity=item,
            entity_type='MenuItem',
            entity_repr=f'{item.name} - ₹{item.price}',
            description=f'Menu item created: {item.name}',
            metadata={'price': str(item.price), 'category': item.category.name},
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Update menu item with audit logging."""
        old_item = self.get_object()
        old_price = old_item.price
        
        item = serializer.save()
        
        create_audit_log(
            action=AuditLog.Action.MENU_ITEM_UPDATED,
            user=self.request.user,
            restaurant=item.restaurant,
            entity=item,
            entity_type='MenuItem',
            entity_repr=f'{item.name} - ₹{item.price}',
            old_value={'price': str(old_price)} if old_price != item.price else None,
            new_value={'price': str(item.price)} if old_price != item.price else None,
            description=f'Menu item updated: {item.name}',
            request=self.request
        )
    
    def perform_destroy(self, instance):
        """Delete menu item with audit logging."""
        create_audit_log(
            action=AuditLog.Action.MENU_ITEM_DELETED,
            user=self.request.user,
            restaurant=instance.restaurant,
            entity=instance,
            entity_type='MenuItem',
            entity_repr=f'{instance.name} - ₹{instance.price}',
            description=f'Menu item deleted: {instance.name}',
            request=self.request
        )
        instance.delete()
    
    @action(detail=True, methods=['post'])
    def toggle_availability(self, request, pk=None):
        """Toggle item availability (simple toggle for owners)."""
        item = self.get_object()
        item.is_available = not item.is_available
        if not item.is_available:
            item.unavailable_since = timezone.now()
        else:
            item.unavailable_since = None
            item.unavailable_reason = ''
        item.save(update_fields=['is_available', 'unavailable_since', 'unavailable_reason', 'updated_at'])
        return Response({'is_available': item.is_available})
    
    @action(detail=True, methods=['patch'], url_path='availability')
    def update_availability(self, request, pk=None):
        """
        Update item availability and stock.
        Accessible by owners and staff with can_manage_stock permission.
        
        PATCH /api/menu/items/{id}/availability/
        Body: {
            "is_available": true/false,
            "stock_quantity": 10 or null,
            "reason": "Out of stock"
        }
        """
        item = self.get_object()
        serializer = MenuItemStockUpdateSerializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        old_available = item.is_available
        old_stock = item.stock_quantity
        
        # Update fields
        if 'is_available' in serializer.validated_data:
            item.is_available = serializer.validated_data['is_available']
            if not item.is_available and old_available:
                item.unavailable_since = timezone.now()
            elif item.is_available:
                item.unavailable_since = None
        
        if 'stock_quantity' in serializer.validated_data:
            item.stock_quantity = serializer.validated_data['stock_quantity']
            # Auto-mark unavailable if stock is 0
            if item.stock_quantity == 0:
                item.is_available = False
                item.unavailable_since = timezone.now()
                if not item.unavailable_reason:
                    item.unavailable_reason = 'Out of stock'
        
        if 'reason' in serializer.validated_data:
            item.unavailable_reason = serializer.validated_data['reason']
        
        item.save()
        
        # Audit log
        create_audit_log(
            action=AuditLog.Action.MENU_ITEM_UPDATED,
            user=self.request.user,
            restaurant=item.restaurant,
            entity=item,
            entity_type='MenuItem',
            entity_repr=item.name,
            old_value={'is_available': old_available, 'stock_quantity': old_stock},
            new_value={'is_available': item.is_available, 'stock_quantity': item.stock_quantity},
            description=f'Stock/availability updated for {item.name}',
            request=self.request
        )
        
        return Response({
            'id': str(item.id),
            'name': item.name,
            'is_available': item.is_available,
            'stock_quantity': item.stock_quantity,
            'unavailable_reason': item.unavailable_reason,
            'unavailable_since': item.unavailable_since,
        })
    
    @action(detail=True, methods=['post'])
    def reorder(self, request, pk=None):
        """Update display order of item."""
        item = self.get_object()
        new_order = request.data.get('display_order')
        if new_order is not None:
            item.display_order = int(new_order)
            item.save(update_fields=['display_order', 'updated_at'])
        return Response({'display_order': item.display_order})


class PublicMenuView(generics.ListAPIView):
    """Public menu view for customers (QR ordering)."""
    
    serializer_class = MenuCategoryPublicSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        slug = self.kwargs.get('slug')
        return MenuCategory.objects.filter(
            restaurant__slug=slug,
            restaurant__status='ACTIVE',
            is_active=True
        ).prefetch_related('items')
    
    def list(self, request, *args, **kwargs):
        slug = self.kwargs.get('slug')
        
        # Verify restaurant exists and is active
        try:
            restaurant = Restaurant.objects.get(slug=slug, status='ACTIVE')
        except Restaurant.DoesNotExist:
            return Response(
                {'error': 'Restaurant not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        queryset = self.get_queryset()
        serializer = self.get_serializer(queryset, many=True)
        
        return Response({
            'restaurant': {
                'id': str(restaurant.id),
                'name': restaurant.name,
                'slug': restaurant.slug,
                'currency': restaurant.currency,
            },
            'categories': serializer.data,
        })


class StaffMenuItemListView(generics.ListAPIView):
    """
    List menu items for staff with stock information.
    Staff must have can_manage_stock permission or be restaurant owner.
    """
    
    from .serializers import MenuItemStaffSerializer
    serializer_class = MenuItemStaffSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None
    
    def get_queryset(self):
        user = self.request.user
        
        # Check if staff
        try:
            staff = user.staff_profile
            if not staff.is_active or not staff.can_manage_stock:
                return MenuItem.objects.none()
            return MenuItem.objects.filter(
                restaurant=staff.restaurant,
                is_active=True
            ).select_related('category')
        except Staff.DoesNotExist:
            pass
        
        # Check if owner
        if user.role == 'restaurant_owner':
            restaurant_id = self.request.query_params.get('restaurant')
            if restaurant_id:
                return MenuItem.objects.filter(
                    restaurant_id=restaurant_id,
                    restaurant__owner=user,
                ).select_related('category')
            return MenuItem.objects.filter(
                restaurant__owner=user,
                is_active=True
            ).select_related('category')
        
        return MenuItem.objects.none()


class StaffUpdateAvailabilityView(generics.UpdateAPIView):
    """
    Update item availability - accessible by staff with can_manage_stock.
    
    PATCH /api/menu/staff/items/{id}/availability/
    """
    
    from .serializers import MenuItemStockUpdateSerializer
    serializer_class = MenuItemStockUpdateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Staff with can_manage_stock permission
        try:
            staff = user.staff_profile
            if staff.is_active and staff.can_manage_stock:
                return MenuItem.objects.filter(
                    restaurant=staff.restaurant,
                    
                )
        except Staff.DoesNotExist:
            pass
        
        # Owner always has access
        if user.role == 'restaurant_owner':
            return MenuItem.objects.filter(
                restaurant__owner=user,
                is_active=True
            )
        
        return MenuItem.objects.none()
    
    def get_object(self):
        queryset = self.get_queryset()
        pk = self.kwargs.get('pk')
        try:
            return queryset.get(pk=pk)
        except MenuItem.DoesNotExist:
            from rest_framework.exceptions import NotFound, PermissionDenied
            # Check if item exists at all
            if MenuItem.objects.filter(pk=pk).exists():
                raise PermissionDenied('You do not have permission to manage stock for this item.')
            raise NotFound('Menu item not found.')
    
    def update(self, request, *args, **kwargs):
        item = self.get_object()
        serializer = self.get_serializer(data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        old_available = item.is_available
        old_stock = item.stock_quantity
        
        # Update fields
        if 'is_available' in serializer.validated_data:
            item.is_available = serializer.validated_data['is_available']
            if not item.is_available and old_available:
                item.unavailable_since = timezone.now()
            elif item.is_available:
                item.unavailable_since = None
                item.unavailable_reason = ''
        
        if 'stock_quantity' in serializer.validated_data:
            item.stock_quantity = serializer.validated_data['stock_quantity']
            # Auto-mark unavailable if stock is 0
            if item.stock_quantity == 0:
                item.is_available = False
                item.unavailable_since = timezone.now()
                if not item.unavailable_reason:
                    item.unavailable_reason = 'Out of stock'
        
        if 'reason' in serializer.validated_data:
            item.unavailable_reason = serializer.validated_data['reason']
        
        item.save()
        
        # Audit log
        create_audit_log(
            action=AuditLog.Action.MENU_ITEM_UPDATED,
            user=request.user,
            restaurant=item.restaurant,
            entity=item,
            entity_type='MenuItem',
            entity_repr=item.name,
            old_value={'is_available': old_available, 'stock_quantity': old_stock},
            new_value={'is_available': item.is_available, 'stock_quantity': item.stock_quantity},
            description=f'Staff stock update for {item.name}',
            request=request
        )
        
        return Response({
            'id': str(item.id),
            'name': item.name,
            'is_available': item.is_available,
            'stock_quantity': item.stock_quantity,
            'unavailable_reason': item.unavailable_reason,
            'unavailable_since': item.unavailable_since,
            'is_in_stock': item.is_in_stock,
        })
