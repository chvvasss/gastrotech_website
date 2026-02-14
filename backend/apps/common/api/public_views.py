from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAdminUser
from apps.common.models import SiteSetting
from apps.common.utils import (
    get_show_prices,
    invalidate_show_prices_cache,
    get_catalog_mode,
    invalidate_catalog_mode_cache,
)


class PublicConfigView(APIView):
    """
    Public API to retrieve and update global site configuration.
    
    GET: Public - Returns current config values
    PATCH/POST: Admin only - Updates config values
    """
    
    def get_permissions(self):
        if self.request.method == "GET":
            return [AllowAny()]
        return [IsAdminUser()]
    
    def get(self, request):
        return Response({
            "show_prices": get_show_prices(),
            "catalog_mode": get_catalog_mode(),
        })

    def patch(self, request):
        show_prices = request.data.get("show_prices")
        if show_prices is not None:
            setting, created = SiteSetting.objects.get_or_create(
                key="show_prices",
                defaults={"value": {"value": True}, "description": "Show prices on public site"}
            )
            setting.value = {"value": bool(show_prices)}
            setting.save()
            invalidate_show_prices_cache()

        catalog_mode = request.data.get("catalog_mode")
        if catalog_mode is not None:
            setting, created = SiteSetting.objects.get_or_create(
                key="catalog_mode",
                defaults={"value": {"value": False}, "description": "Catalog mode - show PDFs instead of products"}
            )
            setting.value = {"value": bool(catalog_mode)}
            setting.save()
            invalidate_catalog_mode_cache()

        return Response({
            "show_prices": get_show_prices(),
            "catalog_mode": get_catalog_mode(),
        })
    
    def post(self, request):
        # Allow POST as alias for PATCH for convenience
        return self.patch(request)

