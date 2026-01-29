"""
Views for the Restaurants app.
"""

import secrets
import qrcode
import io
import base64
from django.http import HttpResponse
from django.db import models
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny

from apps.core.permissions import IsOwner, IsStaff, IsPlatformAdmin
from apps.core.utils import generate_qr_signature
from apps.core.audit import create_audit_log, AuditLog
from .models import Restaurant, Staff, ApiKey
from .serializers import (
    RestaurantSerializer,
    RestaurantPublicSerializer,
    RestaurantCreateSerializer,
    StaffSerializer,
    StaffCreateSerializer,
    ApiKeySerializer,
)


class RestaurantViewSet(viewsets.ModelViewSet):
    """ViewSet for restaurant management."""
    
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return RestaurantCreateSerializer
        return RestaurantSerializer
    
    def get_queryset(self):
        # Allow public access for specific actions
        if self.action in ['menu', 'retrieve_public']:
            return Restaurant.objects.filter(status='ACTIVE')
            
        user = self.request.user
        if not user.is_authenticated:
            return Restaurant.objects.none()
            
        if user.role in ['platform_admin', 'ADMIN']:
            return Restaurant.objects.all()
        return Restaurant.objects.filter(owner=user)
    
    @action(detail=True, methods=['post'], url_path='qr/regenerate')
    def regenerate_qr(self, request, pk=None):
        """Regenerate QR code by incrementing version."""
        restaurant = self.get_object()
        old_version = restaurant.qr_version
        restaurant.increment_qr_version()
        from apps.core.utils import generate_qr_signature
        signature = generate_qr_signature(str(restaurant.id), restaurant.qr_version, restaurant.qr_secret)
        
        # Audit log
        create_audit_log(
            action=AuditLog.Action.QR_REGENERATED,
            user=request.user,
            restaurant=restaurant,
            entity=restaurant,
            entity_type='Restaurant',
            entity_repr=restaurant.name,
            old_value={'qr_version': old_version},
            new_value={'qr_version': restaurant.qr_version},
            description=f'QR code regenerated (version {old_version} -> {restaurant.qr_version})',
            request=request
        )
        
        # Generate Base64 QR
        qr_base64 = self._generate_qr_base64(restaurant, signature)
        
        return Response({
            'qr_version': restaurant.qr_version,
            'signature': signature,
            'qr_code_url': qr_base64,
            'menu_url': f"/r/{restaurant.slug}?v={restaurant.qr_version}&sig={signature}",
        })

    def _generate_qr_base64(self, restaurant, signature):
        """Helper to generate Base64 QR code."""
        frontend_url = self.request.META.get('HTTP_ORIGIN', 'http://localhost:3000')
        target_url = f"{frontend_url}/r/{restaurant.slug}?v={restaurant.qr_version}&sig={signature}"
        
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(target_url)
        qr.make(fit=True)

        img = qr.make_image(fill_color="black", back_color="white")
        
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        image_base64 = base64.b64encode(buffer.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{image_base64}"


    
    @action(detail=True, methods=['get'], url_path='qr')
    def qr(self, request, pk=None):
        """Get QR code data for the restaurant (frontend expects /restaurants/{id}/qr/)."""
        return self.qr_data(request, pk)

    
    @action(detail=True, methods=['get'])
    def qr_data(self, request, pk=None):
        """Get QR code data for the restaurant."""
        restaurant = self.get_object()
        from apps.core.utils import generate_qr_signature
        signature = generate_qr_signature(str(restaurant.id), restaurant.qr_version, restaurant.qr_secret)
        # Generate Base64 QR
        qr_base64 = self._generate_qr_base64(restaurant, signature)
        
        return Response({
            'restaurant_id': str(restaurant.id),
            'slug': restaurant.slug,
            'qr_version': restaurant.qr_version,
            'signature': signature,
            'qr_code_url': qr_base64,
            'menu_url': f"/r/{restaurant.slug}?v={restaurant.qr_version}&sig={signature}",
        })
    
    @action(detail=True, methods=['get'], permission_classes=[AllowAny])
    def menu(self, request, pk=None):
        """Get public menu for a restaurant (no auth required)."""
        restaurant = self.get_object()
        
        # Import serializers here to avoid circular imports
        from apps.menu.models import MenuCategory
        from apps.menu.serializers import MenuCategoryPublicSerializer
        
        # Get active categories (serializer filters items)
        categories = MenuCategory.objects.filter(
            restaurant=restaurant,
            is_active=True
        ).prefetch_related('items').order_by('display_order')
        
        serializer = MenuCategoryPublicSerializer(categories, many=True)
        return Response(serializer.data)


class RestaurantPublicView(generics.RetrieveAPIView):
    """Public view for restaurant details (for QR ordering)."""
    
    queryset = Restaurant.objects.filter(status='ACTIVE')
    serializer_class = RestaurantPublicSerializer
    permission_classes = [AllowAny]
    lookup_field = 'slug'

    def get_object(self):
        queryset = self.filter_queryset(self.get_queryset())
        lookup_url_kwarg = self.lookup_field
        slug_param = self.kwargs[lookup_url_kwarg]

        try:
            # Try finding by slug first (standard case)
            obj = queryset.get(slug=slug_param)
        except Restaurant.DoesNotExist:
            # If fail, try finding by ID (workaround for frontend UUID usage)
            import uuid
            try:
                # Validate UUID format
                uuid_obj = uuid.UUID(slug_param)
                obj = queryset.get(id=slug_param)
            except (ValueError, Restaurant.DoesNotExist):
                # Raise original 404 if neither works
                from django.http import Http404
                raise Http404("No Restaurant matches the given query.")

        self.check_object_permissions(self.request, obj)
        return obj


class StaffViewSet(viewsets.ModelViewSet):
    """ViewSet for staff management."""
    
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_serializer_class(self):
        if self.action == 'create':
            return StaffCreateSerializer
        return StaffSerializer
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['platform_admin', 'ADMIN']:
            return Staff.objects.all()
        return Staff.objects.filter(restaurant__owner=user)
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        # Get restaurant from URL parameter or query
        restaurant_id = self.request.query_params.get('restaurant')
        if restaurant_id:
            try:
                context['restaurant'] = Restaurant.objects.get(
                    id=restaurant_id,
                    owner=self.request.user
                )
            except Restaurant.DoesNotExist:
                pass
        return context
    
    def perform_create(self, serializer):
        """Create staff member with audit logging."""
        staff = serializer.save()
        
        create_audit_log(
            action=AuditLog.Action.STAFF_CREATED,
            user=self.request.user,
            restaurant=staff.restaurant,
            entity=staff,
            entity_type='Staff',
            entity_repr=str(staff),
            description=f'Staff member created: {staff.user.email}',
            metadata={
                'can_collect_cash': staff.can_collect_cash,
                'can_override_orders': staff.can_override_orders,
                'position': staff.position,
            },
            request=self.request
        )
    
    def perform_update(self, serializer):
        """Update staff member with audit logging."""
        old_staff = self.get_object()
        old_values = {
            'can_collect_cash': old_staff.can_collect_cash,
            'can_override_orders': old_staff.can_override_orders,
            'is_active': old_staff.is_active,
        }
        
        staff = serializer.save()
        
        new_values = {
            'can_collect_cash': staff.can_collect_cash,
            'can_override_orders': staff.can_override_orders,
            'is_active': staff.is_active,
        }
        
        # Check if permissions changed
        if old_values != new_values:
            create_audit_log(
                action=AuditLog.Action.STAFF_PERMISSION_CHANGE,
                user=self.request.user,
                restaurant=staff.restaurant,
                entity=staff,
                entity_type='Staff',
                entity_repr=str(staff),
                old_value=old_values,
                new_value=new_values,
                description=f'Staff permissions updated: {staff.user.email}',
                request=self.request
            )
        else:
            create_audit_log(
                action=AuditLog.Action.STAFF_UPDATED,
                user=self.request.user,
                restaurant=staff.restaurant,
                entity=staff,
                entity_type='Staff',
                entity_repr=str(staff),
                description=f'Staff member updated: {staff.user.email}',
                request=self.request
            )
    
    @action(detail=True, methods=['post'])
    def toggle_active(self, request, pk=None):
        """Toggle staff active status."""
        staff = self.get_object()
        old_status = staff.is_active
        staff.is_active = not staff.is_active
        staff.save(update_fields=['is_active', 'updated_at'])
        
        action = AuditLog.Action.STAFF_DEACTIVATED if not staff.is_active else AuditLog.Action.STAFF_UPDATED
        create_audit_log(
            action=action,
            user=request.user,
            restaurant=staff.restaurant,
            entity=staff,
            entity_type='Staff',
            entity_repr=str(staff),
            old_value={'is_active': old_status},
            new_value={'is_active': staff.is_active},
            description=f'Staff active status changed: {old_status} -> {staff.is_active}',
            request=request
        )
        
        return Response({'is_active': staff.is_active})
    
    @action(detail=True, methods=['post'])
    def reset_password(self, request, pk=None):
        """Reset staff password to a temporary one."""
        import secrets
        staff = self.get_object()
        
        # Generate temporary password
        temp_password = secrets.token_urlsafe(8)
        staff.user.set_password(temp_password)
        staff.user.save(update_fields=['password'])
        
        create_audit_log(
            action=AuditLog.Action.PASSWORD_CHANGE,
            user=request.user,
            restaurant=staff.restaurant,
            entity=staff,
            entity_type='Staff',
            entity_repr=str(staff),
            description=f'Password reset for staff: {staff.user.email}',
            request=request
        )
        
        return Response({
            'message': 'Password reset successfully.',
            'temporary_password': temp_password,
            'email': staff.user.email,
        })


class ApiKeyViewSet(viewsets.ModelViewSet):
    """ViewSet for API key management."""
    
    serializer_class = ApiKeySerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        user = self.request.user
        if user.role in ['platform_admin', 'ADMIN']:
            return ApiKey.objects.all()
        return ApiKey.objects.filter(restaurant__owner=user)
    
    def perform_create(self, serializer):
        # Generate a secure API key
        key = secrets.token_urlsafe(32)
        serializer.save(key=key)
