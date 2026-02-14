"""
Admin serializers for inquiries.
"""

from rest_framework import serializers

from .models import Inquiry, InquiryItem


class InquiryItemSerializer(serializers.ModelSerializer):
    """Serializer for inquiry items in admin views."""
    
    class Meta:
        model = InquiryItem
        fields = [
            "id",
            "model_code_snapshot",
            "model_name_tr_snapshot",
            "product_title_tr_snapshot",
            "product_slug_snapshot",
            "series_slug_snapshot",
            "qty",
        ]


class InquiryListSerializer(serializers.ModelSerializer):
    """Serializer for inquiry list in admin views."""
    
    items_count = serializers.SerializerMethodField()
    items_summary = serializers.CharField(read_only=True)
    
    class Meta:
        model = Inquiry
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "company",
            "status",
            "items_count",
            "items_summary",
            "product_slug_snapshot",
            "model_code_snapshot",
            "created_at",
            "updated_at",
        ]
    
    def get_items_count(self, obj):
        # Use annotated count if available, otherwise use property
        if hasattr(obj, "items_count_annotated"):
            return obj.items_count_annotated
        return obj.items_count


class InquiryDetailSerializer(serializers.ModelSerializer):
    """Serializer for inquiry detail in admin views."""
    
    items = InquiryItemSerializer(many=True, read_only=True)
    items_count = serializers.SerializerMethodField()
    items_summary = serializers.CharField(read_only=True)
    
    class Meta:
        model = Inquiry
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "company",
            "message",
            "status",
            "internal_note",
            "source_url",
            "utm_source",
            "utm_medium",
            "utm_campaign",
            "product_slug_snapshot",
            "model_code_snapshot",
            "items_count",
            "items_summary",
            "items",
            "created_at",
            "updated_at",
        ]
    
    def get_items_count(self, obj):
        return obj.items.count()


class InquiryUpdateSerializer(serializers.Serializer):
    """Serializer for updating inquiry."""
    
    status = serializers.ChoiceField(
        choices=Inquiry.Status.choices,
        required=False,
    )
    internal_note = serializers.CharField(
        required=False,
        allow_blank=True,
    )
