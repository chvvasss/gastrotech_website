"""
Admin API views for inquiries management.

These endpoints require admin or editor role.
"""

from django.db.models import Count
from drf_spectacular.utils import extend_schema, OpenApiParameter
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAdminOrEditor
from .models import Inquiry, InquiryItem
from .admin_serializers import (
    InquiryListSerializer,
    InquiryDetailSerializer,
    InquiryUpdateSerializer,
)


class InquiryListView(APIView):
    """
    GET /api/v1/admin/inquiries
    
    List all inquiries with filtering and pagination.
    """
    
    permission_classes = [IsAdminOrEditor]
    
    @extend_schema(
        summary="List inquiries",
        description="List all inquiries with optional filtering by status and search.",
        parameters=[
            OpenApiParameter(name="page", type=int, description="Page number"),
            OpenApiParameter(name="page_size", type=int, description="Items per page (default 20)"),
            OpenApiParameter(name="status", type=str, description="Filter by status (new, in_progress, closed)"),
            OpenApiParameter(name="search", type=str, description="Search by name or email"),
            OpenApiParameter(name="ordering", type=str, description="Order by field (e.g., -created_at)"),
        ],
        responses={200: InquiryListSerializer(many=True)},
        tags=["Admin - Inquiries"],
    )
    def get(self, request):
        queryset = Inquiry.objects.annotate(
            items_count_annotated=Count("items")
        ).order_by("-created_at")
        
        # Filter by status
        status_filter = request.query_params.get("status")
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Search
        search = request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                full_name__icontains=search
            ) | queryset.filter(
                email__icontains=search
            )
        
        # Ordering
        ordering = request.query_params.get("ordering", "-created_at")
        if ordering:
            # Validate ordering field
            valid_fields = ["created_at", "-created_at", "status", "-status", "full_name", "-full_name"]
            if ordering in valid_fields:
                queryset = queryset.order_by(ordering)
        
        # Pagination
        page = int(request.query_params.get("page", 1))
        page_size = int(request.query_params.get("page_size", 20))
        page_size = min(page_size, 100)  # Max 100 items per page
        
        total_count = queryset.count()
        start = (page - 1) * page_size
        end = start + page_size
        
        items = queryset[start:end]
        serializer = InquiryListSerializer(items, many=True)
        
        return Response({
            "count": total_count,
            "next": f"?page={page + 1}" if end < total_count else None,
            "previous": f"?page={page - 1}" if page > 1 else None,
            "results": serializer.data,
        })


class InquiryDetailView(APIView):
    """
    GET/PATCH /api/v1/admin/inquiries/{id}
    
    Get or update inquiry details.
    """
    
    permission_classes = [IsAdminOrEditor]
    
    @extend_schema(
        summary="Get inquiry detail",
        description="Get full inquiry details including items.",
        responses={200: InquiryDetailSerializer},
        tags=["Admin - Inquiries"],
    )
    def get(self, request, inquiry_id):
        try:
            inquiry = Inquiry.objects.prefetch_related("items").get(id=inquiry_id)
        except Inquiry.DoesNotExist:
            return Response(
                {"error": "Inquiry not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = InquiryDetailSerializer(inquiry)
        return Response(serializer.data)
    
    @extend_schema(
        summary="Update inquiry",
        description="Update inquiry status or internal note.",
        request=InquiryUpdateSerializer,
        responses={200: InquiryDetailSerializer},
        tags=["Admin - Inquiries"],
    )
    def patch(self, request, inquiry_id):
        try:
            inquiry = Inquiry.objects.prefetch_related("items").get(id=inquiry_id)
        except Inquiry.DoesNotExist:
            return Response(
                {"error": "Inquiry not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        serializer = InquiryUpdateSerializer(data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        # Update fields
        if "status" in serializer.validated_data:
            inquiry.status = serializer.validated_data["status"]
        if "internal_note" in serializer.validated_data:
            inquiry.internal_note = serializer.validated_data["internal_note"]
        
        inquiry.save()
        
        response_serializer = InquiryDetailSerializer(inquiry)
        return Response(response_serializer.data)
