"""
Views for inquiries API.
"""

from drf_spectacular.utils import extend_schema, OpenApiExample
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from apps.catalog.models import SpecKey, Variant
from .serializers import (
    InquiryCreateSerializer,
    InquiryResponseSerializer,
    QuoteComposeInputSerializer,
    QuoteComposeOutputSerializer,
    QuoteItemInputSerializer,
    QuoteItemOutputSerializer,
)


class InquiryThrottle(AnonRateThrottle):
    """Throttle for inquiry submissions - 20 per hour per IP."""
    
    rate = "20/hour"


@extend_schema(
    summary="Submit inquiry",
    description=(
        "Submit a product inquiry (Teklif İste). "
        "Supports single-item (product_slug + model_code) or multi-item (items array). "
        "Includes honeypot protection and rate limiting."
    ),
    request=InquiryCreateSerializer,
    responses={
        201: InquiryResponseSerializer,
        400: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    },
    examples=[
        OpenApiExample(
            "Single item (legacy)",
            value={
                "full_name": "Ahmet Yılmaz",
                "email": "ahmet@example.com",
                "product_slug": "600-serisi-gazli-ocaklar",
                "model_code": "GKO6010",
            },
        ),
        OpenApiExample(
            "Multi-item quote",
            value={
                "full_name": "Mehmet Kaya",
                "email": "mehmet@hotel.com",
                "company": "Grand Hotel",
                "message": "Need quote for new kitchen",
                "items": [
                    {"model_code": "GKO6010", "qty": 2},
                    {"model_code": "GKO6020", "qty": 1},
                    {"model_code": "EFR6010", "qty": 3},
                ],
            },
        ),
    ],
    tags=["Inquiries"],
    auth=[],  # Public endpoint - no authentication required
)
class InquiryCreateView(APIView):
    """
    POST /api/v1/inquiries
    
    Create a new inquiry (lead).
    Public endpoint with rate limiting.
    
    Modes:
    - Single item: product_slug + model_code (backwards compatible)
    - Multi-item: items: [{model_code, qty}]
    """
    
    permission_classes = [AllowAny]
    throttle_classes = [InquiryThrottle]
    
    def post(self, request):
        serializer = InquiryCreateSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        inquiry = serializer.save()
        
        # TODO: Send email notification here
        # send_inquiry_notification(inquiry)
        
        response_data = {
            "id": inquiry.id,
            "status": "received",
            "items_count": inquiry.items.count(),
        }
        
        return Response(response_data, status=status.HTTP_201_CREATED)


@extend_schema(
    summary="Validate quote items",
    description=(
        "Validate a list of items before submitting a quote request. "
        "Returns normalized data with resolved names for valid items, "
        "and error messages for invalid codes."
    ),
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "items": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "model_code": {"type": "string"},
                            "qty": {"type": "integer", "minimum": 1},
                        },
                        "required": ["model_code"],
                    },
                },
            },
            "required": ["items"],
        }
    },
    responses={
        200: QuoteItemOutputSerializer(many=True),
        400: {"description": "Validation error"},
    },
    examples=[
        OpenApiExample(
            "Validate items",
            value={
                "items": [
                    {"model_code": "GKO6010", "qty": 2},
                    {"model_code": "INVALID123", "qty": 1},
                ],
            },
        ),
    ],
    tags=["Inquiries"],
    auth=[],  # Public endpoint - no authentication required
)
class QuoteValidateView(APIView):
    """
    POST /api/v1/quote/validate
    
    Validate quote items before submission.
    Returns normalized data with resolved names.
    """
    
    permission_classes = [AllowAny]
    
    def post(self, request):
        items_data = request.data.get("items", [])
        
        if not items_data:
            return Response(
                {"error": "items array is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validate input
        input_serializer = QuoteItemInputSerializer(data=items_data, many=True)
        if not input_serializer.is_valid():
            return Response(input_serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Resolve variants
        model_codes = [item["model_code"] for item in input_serializer.validated_data]
        variants = Variant.objects.filter(model_code__in=model_codes).select_related(
            "product", "product__series"
        )
        variant_map = {v.model_code: v for v in variants}
        
        # Build output
        result = []
        for item in input_serializer.validated_data:
            model_code = item["model_code"]
            qty = item.get("qty", 1)
            variant = variant_map.get(model_code)
            
            if variant:
                result.append({
                    "model_code": model_code,
                    "qty": qty,
                    "valid": True,
                    "model_name_tr": variant.name_tr,
                    "product_title_tr": variant.product.title_tr if variant.product else None,
                    "series_slug": variant.product.series.slug if variant.product and variant.product.series else None,
                    "error": None,
                })
            else:
                result.append({
                    "model_code": model_code,
                    "qty": qty,
                    "valid": False,
                    "model_name_tr": None,
                    "product_title_tr": None,
                    "series_slug": None,
                    "error": f"Model code '{model_code}' not found",
                })
        
        return Response(result, status=status.HTTP_200_OK)


@extend_schema(
    summary="Compose quote message",
    description=(
        "Compose a WhatsApp/email-ready quote message from selected items. "
        "Returns resolved item details and a formatted message in Turkish. "
        "Includes honeypot protection and rate limiting."
    ),
    request=QuoteComposeInputSerializer,
    responses={
        200: QuoteComposeOutputSerializer,
        400: {"description": "Validation error"},
        429: {"description": "Rate limit exceeded"},
    },
    examples=[
        OpenApiExample(
            "Compose quote",
            value={
                "full_name": "Mehmet Kaya",
                "company": "Grand Hotel",
                "note": "Kurulum dahil mi?",
                "items": [
                    {"model_code": "GKO6010", "qty": 2},
                    {"model_code": "GKO6030", "qty": 1},
                ],
            },
        ),
    ],
    tags=["Inquiries"],
    auth=[],  # Public endpoint - no authentication required
)
class QuoteComposeView(APIView):
    """
    POST /api/v1/quote/compose
    
    Compose a WhatsApp/email-ready quote message.
    Returns resolved items and formatted message.
    """
    
    permission_classes = [AllowAny]
    throttle_classes = [InquiryThrottle]
    
    def post(self, request):
        serializer = QuoteComposeInputSerializer(data=request.data)
        
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        validated_data = serializer.validated_data
        full_name = validated_data.get("full_name", "")
        company = validated_data.get("company", "")
        note = validated_data.get("note", "")
        items_data = validated_data.get("items", [])
        
        # Resolve variants with optimized query
        model_codes = [item["model_code"] for item in items_data]
        variants = (
            Variant.objects
            .filter(model_code__in=model_codes)
            .select_related("product__series__category")
            .only(
                "model_code",
                "name_tr",
                "dimensions",
                "weight_kg",
                "list_price",
                "specs",
                "product__slug",
                "product__title_tr",
                "product__spec_layout",
                "product__series__slug",
                "product__series__name",
                "product__series__category__slug",
                "product__series__category__name",
            )
        )
        variant_map = {v.model_code: v for v in variants}
        
        # Get spec keys for labels
        all_spec_slugs = set()
        for v in variants:
            if v.specs:
                all_spec_slugs.update(v.specs.keys())
        spec_keys = {sk.slug: sk for sk in SpecKey.objects.filter(slug__in=all_spec_slugs)}
        
        # Build resolved items
        items_resolved = []
        message_lines = ["📋 Teklif Talebi", ""]
        
        # Add customer info
        if full_name or company:
            customer_line = ""
            if full_name:
                customer_line = f"Müşteri: {full_name}"
            if company:
                customer_line += f" ({company})" if customer_line else f"Firma: {company}"
            message_lines.append(customer_line)
            message_lines.append("")
        
        message_lines.append("📦 Ürünler:")
        
        not_found_codes = []
        
        for item in items_data:
            model_code = item["model_code"]
            qty = item.get("qty", 1)
            variant = variant_map.get(model_code)
            
            if variant:
                product = variant.product
                series = product.series if product else None
                category = series.category if series else None
                
                # Build spec_row from variant specs
                spec_row = []
                if variant.specs and product and product.spec_layout:
                    for spec_slug in product.spec_layout:
                        if spec_slug in variant.specs:
                            spec_key = spec_keys.get(spec_slug)
                            value = variant.specs[spec_slug]
                            spec_row.append({
                                "key": spec_slug,
                                "label_tr": spec_key.label_tr if spec_key else spec_slug,
                                "value": str(value),
                                "unit": spec_key.unit if spec_key else "",
                            })
                
                items_resolved.append({
                    "model_code": model_code,
                    "qty": qty,
                    "name_tr": variant.name_tr,
                    "product_slug": product.slug if product else None,
                    "product_title_tr": product.title_tr if product else None,
                    "series_slug": series.slug if series else None,
                    "category_slug": category.slug if category else None,
                    "dimensions": variant.dimensions or None,
                    "weight_kg": variant.weight_kg,
                    "list_price": variant.list_price,
                    "spec_row": spec_row if spec_row else None,
                    "error": None,
                })
                
                # Build message line
                series_info = f" ({series.name})" if series else ""
                group_info = f" - {product.title_tr}" if product else ""
                dims_info = f" [{variant.dimensions}]" if variant.dimensions else ""
                message_lines.append(
                    f"• {qty}x {model_code} - {variant.name_tr}{series_info}{group_info}{dims_info}"
                )
            else:
                items_resolved.append({
                    "model_code": model_code,
                    "qty": qty,
                    "name_tr": None,
                    "product_slug": None,
                    "product_title_tr": None,
                    "series_slug": None,
                    "category_slug": None,
                    "dimensions": None,
                    "weight_kg": None,
                    "list_price": None,
                    "spec_row": None,
                    "error": "not_found",
                })
                not_found_codes.append(model_code)
        
        # Add not found warning
        if not_found_codes:
            message_lines.append("")
            message_lines.append(f"⚠️ Bulunamayan kodlar: {', '.join(not_found_codes)}")
        
        # Add note
        if note:
            message_lines.append("")
            message_lines.append(f"📝 Not: {note}")
        
        message_tr = "\n".join(message_lines)
        
        response_data = {
            "items_resolved": items_resolved,
            "message_tr": message_tr,
            "message_en": None,  # Not implemented yet
        }
        
        return Response(response_data, status=status.HTTP_200_OK)
