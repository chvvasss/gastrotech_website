"""
Django Admin configuration for inquiries.
"""

from django.contrib import admin
from django.db.models import Count

from .models import Inquiry, InquiryItem


class InquiryItemInline(admin.TabularInline):
    """Inline for viewing/editing inquiry items."""
    
    model = InquiryItem
    extra = 0
    fields = [
        "model_code_snapshot",
        "model_name_tr_snapshot",
        "product_title_tr_snapshot",
        "qty",
        "variant",
    ]
    readonly_fields = [
        "model_code_snapshot",
        "model_name_tr_snapshot",
        "product_title_tr_snapshot",
    ]
    autocomplete_fields = ["variant"]


@admin.register(Inquiry)
class InquiryAdmin(admin.ModelAdmin):
    """Admin for Inquiry model."""
    
    list_display = [
        "created_at",
        "full_name",
        "email",
        "phone",
        "company",
        "status",
        "items_count_display",
        "items_summary_display",
        "product_slug_snapshot",
        "model_code_snapshot",
    ]
    list_filter = ["status", "created_at"]
    search_fields = [
        "full_name",
        "email",
        "company",
        "model_code_snapshot",
        "product_slug_snapshot",
        "items__model_code_snapshot",
    ]
    ordering = ["-created_at"]
    date_hierarchy = "created_at"
    readonly_fields = [
        "created_at",
        "updated_at",
        "product_slug_snapshot",
        "model_code_snapshot",
    ]
    
    fieldsets = (
        ("Contact Information", {
            "fields": ("full_name", "email", "phone", "company"),
        }),
        ("Message", {
            "fields": ("message",),
        }),
        ("Product Interest (Legacy Single-Item)", {
            "fields": (
                "product",
                "variant",
                "product_slug_snapshot",
                "model_code_snapshot",
            ),
            "classes": ("collapse",),
            "description": "For single-item inquiries. Multi-item inquiries use Items below.",
        }),
        ("Tracking", {
            "fields": ("source_url", "utm_source", "utm_medium", "utm_campaign"),
            "classes": ("collapse",),
        }),
        ("Status & Notes", {
            "fields": ("status", "internal_note"),
        }),
        ("Timestamps", {
            "fields": ("created_at", "updated_at"),
            "classes": ("collapse",),
        }),
    )
    
    inlines = [InquiryItemInline]
    autocomplete_fields = ["product", "variant"]
    
    def items_count_display(self, obj):
        """Display count of inquiry items."""
        count = getattr(obj, "_items_count", None)
        if count is None:
            count = obj.items.count()
        return count if count else "—"
    items_count_display.short_description = "Items"
    items_count_display.admin_order_field = "_items_count"
    
    def items_summary_display(self, obj):
        """Display summary of first 3 model codes."""
        return obj.items_summary or "—"
    items_summary_display.short_description = "Item Codes"
    
    def get_queryset(self, request):
        return (
            super().get_queryset(request)
            .select_related("product", "variant")
            .prefetch_related("items")
            .annotate(_items_count=Count("items"))
        )
