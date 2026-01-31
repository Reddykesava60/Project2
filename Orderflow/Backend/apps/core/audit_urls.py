"""
URL patterns for audit log endpoints (Platform Admin only).
"""

from django.urls import path
from .audit_views import AuditLogListView

urlpatterns = [
    path('', AuditLogListView.as_view(), name='audit-log-list'),
]
