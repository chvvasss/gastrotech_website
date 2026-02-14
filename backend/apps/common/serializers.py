from rest_framework import serializers
from apps.common.models import SiteSetting

class SiteSettingSerializer(serializers.ModelSerializer):
    """Serializer for SiteSetting model."""
    
    class Meta:
        model = SiteSetting
        fields = [
            "id",
            "key",
            "value",
            "description",
            "updated_at",
        ]
        read_only_fields = ["updated_at"]
        # key should be read-only after creation typically, or we prevent creation via API mostly.
        # But for admin, maybe we allow updating value only.
