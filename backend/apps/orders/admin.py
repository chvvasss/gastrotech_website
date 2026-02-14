"""
Admin configuration for the orders app.

Provides Django Admin interfaces for Cart and CartItem models.
"""

from django.contrib import admin
from django.utils.html import format_html

from apps.orders.models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    """Inline for cart items in Cart admin."""
    
    model = CartItem
    extra = 0
    readonly_fields = [
        "id",
        "variant",
        "quantity",
        "unit_price_snapshot",
        "currency_snapshot",
        "line_total_display",
        "added_at",
    ]
    fields = [
        "variant",
        "quantity",
        "unit_price_snapshot",
        "currency_snapshot",
        "line_total_display",
        "added_at",
    ]
    
    def line_total_display(self, obj):
        """Display line total."""
        return f"{obj.line_total} {obj.currency_snapshot}"
    line_total_display.short_description = "Line Total"
    
    def has_add_permission(self, request, obj=None):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return True


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    """Admin for Cart model."""
    
    list_display = [
        "token_short",
        "user_display",
        "status",
        "item_count_display",
        "subtotal_display",
        "currency",
        "created_at",
        "updated_at",
    ]
    list_filter = [
        "status",
        "currency",
        "created_at",
    ]
    search_fields = [
        "token",
        "user__email",
        "ip_address",
    ]
    readonly_fields = [
        "id",
        "token",
        "created_at",
        "updated_at",
        "subtotal_display",
        "item_count_display",
    ]
    fieldsets = [
        ("Cart Info", {
            "fields": ["id", "token", "user", "status", "currency"],
        }),
        ("Totals", {
            "fields": ["subtotal_display", "item_count_display"],
        }),
        ("Metadata", {
            "fields": ["ip_address", "user_agent", "expires_at"],
            "classes": ["collapse"],
        }),
        ("Timestamps", {
            "fields": ["created_at", "updated_at"],
        }),
    ]
    inlines = [CartItemInline]
    date_hierarchy = "created_at"
    ordering = ["-created_at"]
    
    def token_short(self, obj):
        """Display short token."""
        return obj.token.hex[:8]
    token_short.short_description = "Token"
    
    def user_display(self, obj):
        """Display user or anonymous."""
        if obj.user:
            return obj.user.email
        return format_html('<span style="color: #999;">Anonymous</span>')
    user_display.short_description = "User"
    
    def item_count_display(self, obj):
        """Display item count."""
        return obj.item_count
    item_count_display.short_description = "Items"
    
    def subtotal_display(self, obj):
        """Display subtotal with currency."""
        return f"{obj.subtotal} {obj.currency}"
    subtotal_display.short_description = "Subtotal"
    
    def get_queryset(self, request):
        """Optimize queryset with prefetch."""
        qs = super().get_queryset(request)
        return qs.prefetch_related("items__variant")


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    """Admin for CartItem model."""
    
    list_display = [
        "id_short",
        "cart_token",
        "variant_display",
        "quantity",
        "unit_price_snapshot",
        "line_total_display",
        "added_at",
    ]
    list_filter = [
        "cart__status",
        "added_at",
    ]
    search_fields = [
        "cart__token",
        "variant__model_code",
        "variant__name_tr",
    ]
    readonly_fields = [
        "id",
        "cart",
        "variant",
        "quantity",
        "unit_price_snapshot",
        "currency_snapshot",
        "line_total_display",
        "added_at",
        "created_at",
    ]
    date_hierarchy = "added_at"
    ordering = ["-added_at"]
    
    def id_short(self, obj):
        """Display short ID."""
        return str(obj.id)[:8]
    id_short.short_description = "ID"
    
    def cart_token(self, obj):
        """Display cart token."""
        return obj.cart.token.hex[:8]
    cart_token.short_description = "Cart"
    
    def variant_display(self, obj):
        """Display variant info."""
        return f"{obj.variant.model_code} - {obj.variant.name_tr}"
    variant_display.short_description = "Variant"
    
    def line_total_display(self, obj):
        """Display line total."""
        return f"{obj.line_total} {obj.currency_snapshot}"
    line_total_display.short_description = "Line Total"
    
    def get_queryset(self, request):
        """Optimize queryset with select_related."""
        qs = super().get_queryset(request)
        return qs.select_related("cart", "variant", "variant__product")
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
