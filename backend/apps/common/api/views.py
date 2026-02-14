from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from apps.common.models import SiteSetting
from apps.common.serializers import SiteSettingSerializer
from apps.common.utils import invalidate_show_prices_cache

class SiteSettingViewSet(viewsets.ModelViewSet):
    """
    Admin ViewSet for managing global site settings.
    
    Only allows updating values. Access restricted to strictly admin/staff users.
    """
    queryset = SiteSetting.objects.all()
    serializer_class = SiteSettingSerializer
    permission_classes = [permissions.IsAdminUser]  # Strict admin check
    lookup_field = "key"

    def update(self, request, *args, **kwargs):
        """
        Update setting value and invalidate cache.
        """
        response = super().update(request, *args, **kwargs)
        
        # Invalidate cache if 'show_prices' was updated
        key = self.kwargs.get("key")
        if key == "show_prices":
            invalidate_show_prices_cache()
            
        return response

    def partial_update(self, request, *args, **kwargs):
        """
        Partial update setting value and invalidate cache.
        """
        response = super().partial_update(request, *args, **kwargs)
        
        # Invalidate cache if 'show_prices' was updated
        key = self.kwargs.get("key")
        if key == "show_prices":
            invalidate_show_prices_cache()
            
        return response
