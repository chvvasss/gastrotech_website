"""
Serializers for inquiries API.
"""

from rest_framework import serializers

from apps.catalog.models import Product, Variant
from .models import Inquiry, InquiryItem


class InquiryItemInputSerializer(serializers.Serializer):
    """Serializer for individual items in a multi-item quote request."""
    
    model_code = serializers.CharField(max_length=32)
    qty = serializers.IntegerField(min_value=1, default=1)


class InquiryCreateSerializer(serializers.Serializer):
    """
    Serializer for creating inquiries.
    
    Supports two modes:
    a) Single item: product_slug + model_code (backwards compatible)
    b) Multi-item: items: [{model_code, qty}]
    
    Includes honeypot field "website" that must be empty.
    """
    
    # Contact fields
    full_name = serializers.CharField(max_length=200)
    email = serializers.EmailField()
    phone = serializers.CharField(max_length=30, required=False, allow_blank=True)
    company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    message = serializers.CharField(required=False, allow_blank=True)
    
    # Single-item mode (backwards compatible)
    product_slug = serializers.CharField(required=False, allow_blank=True)
    model_code = serializers.CharField(required=False, allow_blank=True)
    
    # Multi-item mode
    items = InquiryItemInputSerializer(many=True, required=False)
    
    # Tracking
    source_url = serializers.URLField(required=False, allow_blank=True)
    utm_source = serializers.CharField(max_length=100, required=False, allow_blank=True)
    utm_medium = serializers.CharField(max_length=100, required=False, allow_blank=True)
    utm_campaign = serializers.CharField(max_length=100, required=False, allow_blank=True)
    
    # Honeypot field (must be empty)
    website = serializers.CharField(required=False, allow_blank=True)
    
    def validate_website(self, value):
        """Honeypot validation - must be empty."""
        if value:
            raise serializers.ValidationError("Invalid submission.")
        return value
    
    def create(self, validated_data):
        """Create inquiry with product/variant resolution."""
        product_slug = validated_data.pop("product_slug", "")
        model_code = validated_data.pop("model_code", "")
        items_data = validated_data.pop("items", [])
        validated_data.pop("website", None)  # Remove honeypot
        
        product = None
        variant = None
        
        # Single-item mode (backwards compatible)
        if model_code or product_slug:
            # Try to resolve product
            if product_slug:
                try:
                    product = Product.objects.get(slug=product_slug)
                except Product.DoesNotExist:
                    pass
            
            # Try to resolve variant
            if model_code:
                try:
                    variant = Variant.objects.select_related("product").get(
                        model_code=model_code
                    )
                    if not product and variant.product:
                        product = variant.product
                except Variant.DoesNotExist:
                    pass
        
        # Store snapshot values for single-item mode
        product_slug_snapshot = ""
        if product:
            product_slug_snapshot = product.slug
        elif product_slug:
            product_slug_snapshot = product_slug
        
        model_code_snapshot = ""
        if variant:
            model_code_snapshot = variant.model_code
        elif model_code:
            model_code_snapshot = model_code
        
        # Create inquiry
        inquiry = Inquiry.objects.create(
            full_name=validated_data.get("full_name", ""),
            email=validated_data.get("email", ""),
            phone=validated_data.get("phone", ""),
            company=validated_data.get("company", ""),
            message=validated_data.get("message", ""),
            product=product,
            variant=variant,
            product_slug_snapshot=product_slug_snapshot,
            model_code_snapshot=model_code_snapshot,
            source_url=validated_data.get("source_url", ""),
            utm_source=validated_data.get("utm_source", ""),
            utm_medium=validated_data.get("utm_medium", ""),
            utm_campaign=validated_data.get("utm_campaign", ""),
        )
        
        # Create inquiry items (multi-item mode)
        if items_data:
            for item_data in items_data:
                item_model_code = item_data.get("model_code", "")
                item_qty = item_data.get("qty", 1)
                
                item_variant = None
                if item_model_code:
                    try:
                        item_variant = Variant.objects.select_related(
                            "product", "product__series"
                        ).get(model_code=item_model_code)
                    except Variant.DoesNotExist:
                        pass
                
                # Create InquiryItem with snapshots
                inquiry_item = InquiryItem(
                    inquiry=inquiry,
                    variant=item_variant,
                    qty=item_qty,
                    model_code_snapshot=item_model_code,
                )
                
                # Populate additional snapshots if variant found
                if item_variant:
                    inquiry_item.model_name_tr_snapshot = item_variant.name_tr
                    if item_variant.product:
                        inquiry_item.product_slug_snapshot = item_variant.product.slug
                        inquiry_item.product_title_tr_snapshot = item_variant.product.title_tr
                        if item_variant.product.series:
                            inquiry_item.series_slug_snapshot = item_variant.product.series.slug
                
                inquiry_item.save()
        
        return inquiry


class InquiryResponseSerializer(serializers.Serializer):
    """Response serializer for inquiry creation."""
    
    id = serializers.UUIDField()
    status = serializers.CharField()
    items_count = serializers.IntegerField()


class QuoteItemInputSerializer(serializers.Serializer):
    """Serializer for validating quote items."""
    
    model_code = serializers.CharField(max_length=32)
    qty = serializers.IntegerField(min_value=1, default=1)


class QuoteItemOutputSerializer(serializers.Serializer):
    """Serializer for validated quote item output."""
    
    model_code = serializers.CharField()
    qty = serializers.IntegerField()
    valid = serializers.BooleanField()
    model_name_tr = serializers.CharField(allow_null=True)
    product_title_tr = serializers.CharField(allow_null=True)
    series_slug = serializers.CharField(allow_null=True)
    error = serializers.CharField(allow_null=True)


class QuoteComposeInputSerializer(serializers.Serializer):
    """Input serializer for quote compose endpoint."""
    
    full_name = serializers.CharField(max_length=200, required=False, allow_blank=True)
    company = serializers.CharField(max_length=200, required=False, allow_blank=True)
    note = serializers.CharField(required=False, allow_blank=True)
    items = QuoteItemInputSerializer(many=True)
    website = serializers.CharField(required=False, allow_blank=True)  # Honeypot
    
    def validate_website(self, value):
        """Honeypot validation - must be empty."""
        if value:
            raise serializers.ValidationError("Invalid submission.")
        return value
    
    def validate_items(self, value):
        """Ensure at least one item."""
        if not value:
            raise serializers.ValidationError("At least one item is required.")
        return value


class QuoteComposeItemOutputSerializer(serializers.Serializer):
    """Output serializer for individual item in quote compose response."""
    
    model_code = serializers.CharField()
    qty = serializers.IntegerField()
    name_tr = serializers.CharField(allow_null=True)
    product_slug = serializers.CharField(allow_null=True)
    product_title_tr = serializers.CharField(allow_null=True)
    series_slug = serializers.CharField(allow_null=True)
    category_slug = serializers.CharField(allow_null=True)
    dimensions = serializers.CharField(allow_null=True)
    weight_kg = serializers.DecimalField(max_digits=10, decimal_places=2, allow_null=True)
    list_price = serializers.DecimalField(max_digits=12, decimal_places=2, allow_null=True)
    spec_row = serializers.ListField(child=serializers.DictField(), allow_null=True)
    error = serializers.CharField(allow_null=True)


class QuoteComposeOutputSerializer(serializers.Serializer):
    """Output serializer for quote compose endpoint."""
    
    items_resolved = QuoteComposeItemOutputSerializer(many=True)
    message_tr = serializers.CharField()
    message_en = serializers.CharField(allow_null=True)
