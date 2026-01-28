"""
URL configuration for DineFlow2 project.

URL Structure:
- /api/auth/* - Authentication endpoints
- /api/orders/* - Order management
- /api/restaurant/* - Restaurant management and menu
- /api/me - Current user profile
- /api/analytics/* - Analytics endpoints (owner)
- /api/audit-logs - Audit log access (admin)
"""

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # API routes - matching frontend expectations
    path('api/', include([
        # Authentication
        path('auth/', include('apps.users.urls')),
        
        # Current user profile (/api/me)
        path('me/', include('apps.users.me_urls')),
        
        # Orders (authenticated staff/owner)
        path('orders/', include('apps.orders.urls')),
        
        # Restaurant management (owner) - includes categories & products
        path('restaurants/', include('apps.restaurants.urls')),
        
        # Menu endpoints (matching frontend expectations)
        path('menu/', include('apps.menu.urls')),
        
        # Staff endpoints (matching frontend expectations)
        path('staff/', include('apps.restaurants.staff_urls')),
        
        # QR management
        path('qr/', include('apps.restaurants.qr_urls')),
        
        # Analytics (owner)
        path('analytics/', include('apps.orders.analytics_urls')),
        
        # Audit logs (admin) - at /api/audit-logs/
        path('audit-logs/', include('apps.core.audit_urls')),
        
        # Platform admin endpoints - at /api/admin/
        path('admin/', include('apps.restaurants.admin_urls')),
        
        # Also keep admin routes at /api/restaurants/ for backwards compatibility
        path('restaurants/', include('apps.restaurants.admin_urls')),
    ])),
    
    # Public endpoints (for QR ordering) - no auth required
    path('api/public/', include('apps.orders.public_urls')),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
]

# Media files (served in both DEBUG and production)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Debug toolbar URLs
if settings.DEBUG:
    urlpatterns += [
        path('__debug__/', include('debug_toolbar.urls')),
    ]
