"""
Stats API for dashboard.

Provides comprehensive statistics for the admin dashboard including:
- Catalog metrics (categories, series, products, variants)
- Inquiry metrics with date ranges
- Time-series data for charts
- Recent activity lists
"""

from datetime import timedelta

from django.db.models import Count, Q
from django.db.models.functions import TruncDate
from django.utils import timezone
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAdminOrEditor
from apps.inquiries.models import Inquiry, InquiryItem
from .models import Category, Media, Product, ProductMedia, Series, TaxonomyNode, Variant


class StatsView(APIView):
    """
    GET /api/v1/admin/stats/?range=7d
    
    Get comprehensive dashboard statistics.
    
    Range options: 7d, 14d, 30d, 90d (default: 30d)
    """
    
    permission_classes = [IsAdminOrEditor]
    
    @extend_schema(
        summary="Get dashboard stats",
        description="Get comprehensive statistics for dashboard cards and charts.",
        parameters=[
            OpenApiParameter(
                name="range",
                type=str,
                location=OpenApiParameter.QUERY,
                description="Date range: 7d, 14d, 30d, 90d",
                required=False,
                default="30d",
            ),
        ],
        responses={
            200: {
                "type": "object",
                "properties": {
                    # Catalog metrics
                    "categories_total": {"type": "integer"},
                    "series_total": {"type": "integer"},
                    "taxonomy_nodes_total": {"type": "integer"},
                    "products_total": {"type": "integer"},
                    "products_active": {"type": "integer"},
                    "products_draft": {"type": "integer"},
                    "products_archived": {"type": "integer"},
                    "variants_total": {"type": "integer"},
                    # Media metrics
                    "media_total": {"type": "integer"},
                    "media_unreferenced_total": {"type": "integer"},
                    # Inquiry metrics
                    "inquiries_total": {"type": "integer"},
                    "inquiries_new_range": {"type": "integer"},
                    "inquiries_open": {"type": "integer"},
                    "inquiries_closed": {"type": "integer"},
                    "inquiry_items_total": {"type": "integer"},
                    # Chart data
                    "inquiries_by_day": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "date": {"type": "string"},
                                "count": {"type": "integer"},
                            },
                        },
                    },
                    "products_by_status": {
                        "type": "object",
                        "properties": {
                            "active": {"type": "integer"},
                            "draft": {"type": "integer"},
                            "archived": {"type": "integer"},
                        },
                    },
                    "top_requested_variants": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "model_code": {"type": "string"},
                                "name_tr": {"type": "string"},
                                "count": {"type": "integer"},
                            },
                        },
                    },
                    # Recent activity
                    "recently_updated_products": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "title_tr": {"type": "string"},
                                "slug": {"type": "string"},
                                "status": {"type": "string"},
                                "updated_at": {"type": "string"},
                            },
                        },
                    },
                    "recently_updated_inquiries": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "id": {"type": "string"},
                                "full_name": {"type": "string"},
                                "company": {"type": "string"},
                                "status": {"type": "string"},
                                "items_count": {"type": "integer"},
                                "created_at": {"type": "string"},
                            },
                        },
                    },
                },
            }
        },
        tags=["Admin - Stats"],
    )
    def get(self, request):
        # Parse range parameter
        range_param = request.query_params.get("range", "30d")
        days_map = {"7d": 7, "14d": 14, "30d": 30, "90d": 90}
        days = days_map.get(range_param, 30)
        
        range_start = timezone.now() - timedelta(days=days)
        
        # Catalog metrics
        categories_total = Category.objects.count()
        series_total = Series.objects.count()
        taxonomy_nodes_total = TaxonomyNode.objects.count()
        
        products_total = Product.objects.count()
        products_active = Product.objects.filter(status="active").count()
        products_draft = Product.objects.filter(status="draft").count()
        products_archived = Product.objects.filter(status="archived").count()
        
        variants_total = Variant.objects.count()
        
        # Media metrics
        media_total = Media.objects.count()
        referenced_media_ids = ProductMedia.objects.values_list("media_id", flat=True).distinct()
        media_unreferenced_total = Media.objects.exclude(id__in=referenced_media_ids).count()
        
        # Inquiry metrics
        inquiries_total = Inquiry.objects.count()
        inquiries_new_range = Inquiry.objects.filter(
            status="new",
            created_at__gte=range_start,
        ).count()
        inquiries_open = Inquiry.objects.filter(
            status__in=["new", "in_progress"]
        ).count()
        inquiries_closed = Inquiry.objects.filter(status="closed").count()
        inquiry_items_total = InquiryItem.objects.count()
        
        # Chart: Inquiries by day (within range)
        inquiries_by_day = list(
            Inquiry.objects.filter(created_at__gte=range_start)
            .annotate(date=TruncDate("created_at"))
            .values("date")
            .annotate(count=Count("id"))
            .order_by("date")
        )
        # Convert date to string for JSON serialization
        inquiries_by_day = [
            {"date": item["date"].isoformat() if item["date"] else None, "count": item["count"]}
            for item in inquiries_by_day
        ]
        
        # Chart: Products by status
        products_by_status = {
            "active": products_active,
            "draft": products_draft,
            "archived": products_archived,
        }
        
        # Chart: Top requested variants (from InquiryItem aggregation)
        top_requested_variants = list(
            InquiryItem.objects
            .filter(inquiry__created_at__gte=range_start)
            .values("model_code_snapshot")
            .annotate(count=Count("id"))
            .order_by("-count")[:10]
        )
        # Enrich with variant names
        model_codes = [item["model_code_snapshot"] for item in top_requested_variants]
        variants_map = {
            v.model_code: v.name_tr
            for v in Variant.objects.filter(model_code__in=model_codes)
        }
        top_requested_variants = [
            {
                "model_code": item["model_code_snapshot"],
                "name_tr": variants_map.get(item["model_code_snapshot"], ""),
                "count": item["count"],
            }
            for item in top_requested_variants
        ]
        
        # Recent activity: Products
        recently_updated_products = list(
            Product.objects
            .order_by("-updated_at")[:10]
            .values("title_tr", "slug", "status", "updated_at")
        )
        recently_updated_products = [
            {
                "title_tr": item["title_tr"],
                "slug": item["slug"],
                "status": item["status"],
                "updated_at": item["updated_at"].isoformat() if item["updated_at"] else None,
            }
            for item in recently_updated_products
        ]
        
        # Recent activity: Inquiries
        recently_updated_inquiries = list(
            Inquiry.objects
            .annotate(items_count=Count("items"))
            .order_by("-created_at")[:10]
            .values("id", "full_name", "company", "status", "items_count", "created_at")
        )
        recently_updated_inquiries = [
            {
                "id": str(item["id"]),
                "full_name": item["full_name"],
                "company": item["company"] or "",
                "status": item["status"],
                "items_count": item["items_count"],
                "created_at": item["created_at"].isoformat() if item["created_at"] else None,
            }
            for item in recently_updated_inquiries
        ]
        
        return Response({
            # Catalog metrics
            "categories_total": categories_total,
            "series_total": series_total,
            "taxonomy_nodes_total": taxonomy_nodes_total,
            "products_total": products_total,
            "products_active": products_active,
            "products_draft": products_draft,
            "products_archived": products_archived,
            "variants_total": variants_total,
            # Media metrics
            "media_total": media_total,
            "media_unreferenced_total": media_unreferenced_total,
            # Inquiry metrics
            "inquiries_total": inquiries_total,
            "inquiries_new_range": inquiries_new_range,
            "inquiries_open": inquiries_open,
            "inquiries_closed": inquiries_closed,
            "inquiry_items_total": inquiry_items_total,
            # Charts
            "inquiries_by_day": inquiries_by_day,
            "products_by_status": products_by_status,
            "top_requested_variants": top_requested_variants,
            # Recent activity
            "recently_updated_products": recently_updated_products,
            "recently_updated_inquiries": recently_updated_inquiries,
        })
