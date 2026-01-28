"""
Views for audit log access (Platform Admin only).
"""

from rest_framework import generics, serializers
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.filters import SearchFilter, OrderingFilter

from apps.core.permissions import IsPlatformAdmin
from .audit import AuditLog


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log entries."""
    
    action_display = serializers.CharField(source='get_action_display', read_only=True)
    severity_display = serializers.CharField(source='get_severity_display', read_only=True)
    
    class Meta:
        model = AuditLog
        fields = [
            'id', 'timestamp',
            'user', 'user_email',
            'restaurant', 'restaurant_name',
            'action', 'action_display',
            'severity', 'severity_display',
            'entity_type', 'entity_id', 'entity_repr',
            'old_value', 'new_value',
            'description', 'metadata',
            'ip_address', 'user_agent',
        ]
        read_only_fields = fields  # All fields are read-only


class AuditLogListView(generics.ListAPIView):
    """
    List audit logs (Platform Admin only).
    
    Supports filtering by:
    - action: Filter by action type
    - user: Filter by user ID
    - restaurant: Filter by restaurant ID
    - severity: Filter by severity level
    - entity_type: Filter by entity type (Order, Staff, etc.)
    - timestamp__gte: Filter by start date
    - timestamp__lte: Filter by end date
    
    Supports search in:
    - user_email
    - restaurant_name
    - entity_repr
    - description
    """
    
    serializer_class = AuditLogSerializer
    permission_classes = [IsAuthenticated, IsPlatformAdmin]
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]
    filterset_fields = {
        'action': ['exact'],
        'user': ['exact'],
        'restaurant': ['exact'],
        'severity': ['exact'],
        'entity_type': ['exact'],
        'timestamp': ['gte', 'lte', 'date'],
    }
    search_fields = ['user_email', 'restaurant_name', 'entity_repr', 'description']
    ordering_fields = ['timestamp', 'action', 'severity']
    ordering = ['-timestamp']
    
    def get_queryset(self):
        return AuditLog.objects.select_related('user', 'restaurant').all()
