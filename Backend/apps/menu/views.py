"""
Views for the Menu app.
"""

from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.decorators import action
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.permissions import IsOwner
from apps.core.audit import create_audit_log, AuditLog
from apps.restaurants.models import Restaurant
from .models import MenuCategory, MenuItem
from .serializers import (
    MenuCategorySerializer,
    MenuCategoryPublicSerializer,
    MenuCategoryCreateSerializer,
    MenuItemSerializer,
    MenuItemPublicSerializer,
    MenuItemCreateSerializer,
)


class MenuCategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for menu category management."""
    
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'is_active']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MenuCategoryCreateSerializer
        return MenuCategorySerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'platform_admin':
            return MenuCategory.objects.all()
        return MenuCategory.objects.filter(restaurant__owner=user)
    
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
    
    permission_classes = [IsAuthenticated, IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['restaurant', 'category', 'is_available', 'is_active']
    
    def get_serializer_class(self):
        if self.action == 'create':
            return MenuItemCreateSerializer
        return MenuItemSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role == 'platform_admin':
            return MenuItem.objects.all()
        return MenuItem.objects.filter(restaurant__owner=user)
    
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
        """Toggle item availability."""
        item = self.get_object()
        item.is_available = not item.is_available
        item.save(update_fields=['is_available', 'updated_at'])
        return Response({'is_available': item.is_available})
    
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
