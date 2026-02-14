from rest_framework.routers import DefaultRouter
from django.urls import path
from apps.common.api.views import SiteSettingViewSet
from apps.common.api.public_views import PublicConfigView

router = DefaultRouter()
router.register(r'site-settings', SiteSettingViewSet, basename='site-settings')

urlpatterns = router.urls + [
    path("config/", PublicConfigView.as_view(), name="public-config"),
]
