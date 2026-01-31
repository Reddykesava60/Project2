"""
URL patterns for analytics endpoints (Owner only).
"""

from django.urls import path
from .views import DashboardStatsView
from .analytics_views import DailyAnalyticsView

urlpatterns = [
    path('daily/', DailyAnalyticsView.as_view(), name='analytics-daily'),
    path('dashboard/', DashboardStatsView.as_view(), name='analytics-dashboard'),
]
