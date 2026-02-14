"""
Serializers for the orders app.

This module provides DRF serializers for cart and cart item operations.
"""

from decimal import Decimal

from rest_framework import serializers

from apps.catalog.models import Product, Variant
from apps.orders.models import Cart, CartItem


class VariantMinimalSerializer(serializers.ModelSerializer):
    """
    Minimal variant serializer for cart item display.
    
    Includes essential variant info needed for cart display.
    """
    
    product_name = serializers.CharField(source="product.title_tr", read_only=True)
    product_slug = serializers.SlugField(source="product.slug", read_only=True)
    price = serializers.SerializerMethodField()
    currency = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = Variant
        fields = [
            "id",
            "model_code",
            "name_tr",
            "name_en",
            "sku",
            "size",
            "color",
            "dimensions",
            "price",
            "currency",
            "stock_qty",
            "is_available",
            "product_name",
            "product_slug",
        ]
        read_only_fields = fields
    
    def get_price(self, obj) -> Decimal:
        """Return display price."""
        return obj.get_display_price()
    
    def get_currency(self, obj) -> str:
        """Return currency (from product or default)."""
        return "TRY"
    
    def get_is_available(self, obj) -> bool:
        """Check if variant is available for purchase."""
        # Check product is active and stock > 0 (or null = unlimited)
        if obj.product.status != Product.Status.ACTIVE:
            return False
        if obj.stock_qty == 0:
            return False
        return True


class CartItemSerializer(serializers.ModelSerializer):
    """
    Serializer for cart items with variant details and snapshots.
    """
    
    variant = VariantMinimalSerializer(read_only=True)
    line_total = serializers.SerializerMethodField()
    
    class Meta:
        model = CartItem
        fields = [
            "id",
            "variant",
            "quantity",
            "unit_price_snapshot",
            "currency_snapshot",
            "product_name_snapshot",
            "variant_label_snapshot",
            "line_total",
            "added_at",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "unit_price_snapshot",
            "currency_snapshot",
            "product_name_snapshot",
            "variant_label_snapshot",
            "line_total",
            "added_at",
            "created_at",
        ]
    
    def get_line_total(self, obj) -> Decimal:
        """Calculate line total."""
        return obj.line_total


class CartWarningSerializer(serializers.Serializer):
    """Serializer for cart warnings."""
    
    variant_id = serializers.UUIDField(help_text="Variant with issue")
    requested = serializers.IntegerField(help_text="Requested quantity")
    available = serializers.IntegerField(help_text="Available stock")
    reason = serializers.CharField(help_text="Warning reason code")


class CartSerializer(serializers.ModelSerializer):
    """
    Serializer for cart with items and computed totals.
    
    Response includes:
    - totals: { item_count, subtotal, currency, has_pricing_gaps }
    - warnings: array of stock/pricing warnings
    """
    
    items = CartItemSerializer(many=True, read_only=True)
    totals = serializers.SerializerMethodField()
    warnings = serializers.SerializerMethodField()
    is_anonymous = serializers.SerializerMethodField()
    
    class Meta:
        model = Cart
        fields = [
            "id",
            "token",
            "status",
            "currency",
            "is_anonymous",
            "items",
            "totals",
            "warnings",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "token",
            "status",
            "items",
            "totals",
            "warnings",
            "created_at",
            "updated_at",
        ]
    
    def get_totals(self, obj) -> dict:
        """Return computed cart totals including has_pricing_gaps."""
        return obj.compute_totals()
    
    def get_warnings(self, obj) -> list:
        """
        Compute warnings for items with stock issues.
        
        Returns list of dicts with:
        - variant_id, requested, available, reason
        """
        warnings = []
        for item in obj.items.select_related("variant"):
            variant = item.variant
            # Check stock availability
            if variant.stock_qty is not None and variant.stock_qty >= 0:
                if item.quantity > variant.stock_qty:
                    warnings.append({
                        "variant_id": str(variant.id),
                        "requested": item.quantity,
                        "available": variant.stock_qty,
                        "reason": "insufficient_stock",
                    })
            # Check pricing gaps
            if item.unit_price_snapshot is None and variant.get_display_price() is None:
                warnings.append({
                    "variant_id": str(variant.id),
                    "requested": item.quantity,
                    "available": variant.stock_qty or 0,
                    "reason": "missing_price",
                })
        return warnings
    
    def get_is_anonymous(self, obj) -> bool:
        """Check if cart is anonymous."""
        return obj.user is None


class CartTokenSerializer(serializers.Serializer):
    """
    Serializer for cart token creation response.
    """
    
    cart_token = serializers.UUIDField(read_only=True)
    cart = CartSerializer(read_only=True)


class AddItemSerializer(serializers.Serializer):
    """
    Serializer for adding items to cart.
    """
    
    variant_id = serializers.UUIDField(
        help_text="UUID of the variant to add",
    )
    quantity = serializers.IntegerField(
        min_value=1,
        default=1,
        help_text="Quantity to add (default 1)",
    )
    
    def validate_variant_id(self, value):
        """Validate variant exists."""
        if not Variant.objects.filter(id=value).exists():
            raise serializers.ValidationError("Variant not found")
        return value


class UpdateItemSerializer(serializers.Serializer):
    """
    Serializer for updating cart item quantity.
    """
    
    quantity = serializers.IntegerField(
        min_value=0,
        help_text="New quantity (0 to remove)",
    )


class MergeCartSerializer(serializers.Serializer):
    """
    Serializer for cart merge request.
    
    Uses X-Cart-Token header for source cart identification.
    """
    
    pass  # No body needed - reads from header


class CartMergeResultSerializer(serializers.Serializer):
    """
    Serializer for cart merge result.
    
    Includes warnings for stock issues encountered during merge.
    """
    
    merged_count = serializers.IntegerField(help_text="Items successfully merged")
    skipped_count = serializers.IntegerField(help_text="Items skipped due to stock/other issues")
    warnings = CartWarningSerializer(many=True, help_text="Stock/pricing warnings")
    dry_run = serializers.BooleanField(
        default=False,
        help_text="True if this was a preview without commit"
    )
    cart = CartSerializer()
    predicted_items = serializers.ListField(
        child=serializers.DictField(),
        required=False,
        help_text="Predicted item list (dry_run only)"
    )
