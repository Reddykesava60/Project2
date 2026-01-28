"""
URL patterns for QR management endpoints.
Matches frontend expectations: /api/qr/regenerate
"""

from django.urls import path
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from apps.core.permissions import IsOwner
from apps.restaurants.models import Restaurant
from apps.core.utils import generate_qr_signature
from apps.core.audit import create_audit_log, AuditLog


class RegenerateQRView(APIView):
    """Regenerate QR code for a restaurant."""
    
    permission_classes = [IsAuthenticated, IsOwner]
    
    def post(self, request):
        """Regenerate QR code by incrementing version."""
        restaurant_id = request.data.get('restaurant_id') or request.query_params.get('restaurant_id')
        
        if not restaurant_id:
            return Response(
                {
                    'error': 'MISSING_RESTAURANT_ID',
                    'message': 'Restaurant ID is required.'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            restaurant = Restaurant.objects.get(id=restaurant_id, owner=request.user)
        except Restaurant.DoesNotExist:
            return Response(
                {
                    'error': 'RESTAURANT_NOT_FOUND',
                    'message': 'Restaurant not found or you do not have permission.'
                },
                status=status.HTTP_404_NOT_FOUND
            )
        
        old_version = restaurant.qr_version
        restaurant.increment_qr_version()
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
        
        return Response({
            'qr_code_url': f"/r/{restaurant.slug}?v={restaurant.qr_version}&sig={signature}",
            'qr_version': restaurant.qr_version,
        })


app_name = 'qr'

urlpatterns = [
    path('regenerate/', RegenerateQRView.as_view(), name='regenerate-qr'),
]
