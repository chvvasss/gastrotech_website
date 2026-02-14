"""
URL configuration for API v1.

All API v1 endpoints are defined here.

Security:
- API docs (Swagger/OpenAPI) are only available in DEBUG mode
- In production, docs endpoints return 404
"""

from django.conf import settings
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from rest_framework_simplejwt.views import TokenRefreshView

from apps.accounts.views import EmailTokenObtainPairView, UserMeView

from .views import HealthCheckView

app_name = "api_v1"

urlpatterns = [
    # Authentication (trailing slashes for consistency)
    # Custom view that accepts 'email' instead of 'username'
    path("auth/login/", EmailTokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("auth/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("auth/me/", UserMeView.as_view(), name="user_me"),
    
    # Health Check
    path("health/", HealthCheckView.as_view(), name="health_check"),
    
    # Cart API (supports both anonymous and authenticated users)
    path("cart/", include("apps.orders.urls")),
    
    # Catalog Public APIs (no trailing slash, endpoints include paths)
    path("", include("apps.catalog.urls")),
    
    # Blog Public APIs
    path("", include("apps.blog.urls")),
    
    # Admin APIs (requires admin/editor role)
    path("admin/", include("apps.catalog.admin_urls")),
    path("admin/", include("apps.inquiries.admin_urls")),
    path("admin/", include("apps.ops.urls")),
    path("admin/", include("apps.blog.admin_urls")),
    
    # Inquiries (public endpoint)
    path("", include("apps.inquiries.urls")),
]

# OpenAPI Schema and Documentation - Only in DEBUG mode
# In production, these endpoints are not available for security
if settings.DEBUG:
    urlpatterns += [
        path("schema/", SpectacularAPIView.as_view(), name="schema"),
        path(
            "docs/",
            SpectacularSwaggerView.as_view(url_name="api_v1:schema"),
            name="swagger_ui",
        ),
    ]
