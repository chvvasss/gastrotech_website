"""
Admin API for Product Info Sheet management with QR code generation.

Provides CRUD operations and QR code regeneration endpoint.
"""

import logging

from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.api.permissions import IsAdminOrEditor

from .models_qr import ProductInfoSheet

logger = logging.getLogger(__name__)


class ProductInfoSheetSerializer(serializers.ModelSerializer):
    """Serializer for ProductInfoSheet with computed URL fields."""

    pdf_url = serializers.SerializerMethodField()
    qr_url = serializers.SerializerMethodField()

    class Meta:
        model = ProductInfoSheet
        fields = [
            "id",
            "title",
            "pdf_file",
            "pdf_url",
            "qr_code",
            "qr_url",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "qr_code", "created_at", "updated_at"]

    def get_pdf_url(self, obj):
        """Return relative media URL for PDF (served via gateway /media/ proxy)."""
        if obj.pdf_file:
            return obj.pdf_file.url  # e.g. /media/info_sheets/pdfs/xxx.pdf
        return None

    def get_qr_url(self, obj):
        """Return relative media URL for QR code (served via gateway /media/ proxy)."""
        if obj.qr_code:
            return obj.qr_code.url  # e.g. /media/info_sheets/qrcodes/xxx.png
        return None


class ProductInfoSheetCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating ProductInfoSheet."""

    class Meta:
        model = ProductInfoSheet
        fields = ["title", "pdf_file"]


class ProductInfoSheetViewSet(viewsets.ModelViewSet):
    """
    Admin CRUD for Product Info Sheets.

    Endpoints:
    - GET    /api/v1/admin/info-sheets/          — List all
    - POST   /api/v1/admin/info-sheets/          — Create (upload PDF)
    - GET    /api/v1/admin/info-sheets/{id}/      — Detail
    - PATCH  /api/v1/admin/info-sheets/{id}/      — Update
    - DELETE /api/v1/admin/info-sheets/{id}/      — Delete
    - POST   /api/v1/admin/info-sheets/{id}/regenerate-qr/ — Regenerate QR
    """

    queryset = ProductInfoSheet.objects.all()
    permission_classes = [IsAdminOrEditor]
    parser_classes = [MultiPartParser, FormParser]
    pagination_class = None  # No pagination for simplicity

    def get_serializer_class(self):
        if self.action in ("create", "update", "partial_update"):
            return ProductInfoSheetCreateSerializer
        return ProductInfoSheetSerializer

    def perform_create(self, serializer):
        """Save and generate QR code with absolute URL."""
        instance = serializer.save()
        # Regenerate QR with request-based absolute URL
        base_url = self._get_base_url()
        instance.generate_qr_code(base_url=base_url)
        ProductInfoSheet.objects.filter(pk=instance.pk).update(
            qr_code=instance.qr_code.name
        )
        logger.info(f"Created info sheet: {instance.title} (id={instance.id})")

    def perform_update(self, serializer):
        """Update and regenerate QR if PDF changed."""
        instance = serializer.save()
        base_url = self._get_base_url()
        instance.generate_qr_code(base_url=base_url)
        ProductInfoSheet.objects.filter(pk=instance.pk).update(
            qr_code=instance.qr_code.name
        )
        logger.info(f"Updated info sheet: {instance.title} (id={instance.id})")

    def create(self, request, *args, **kwargs):
        """Override to return full serializer data after creation."""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        # Re-fetch to get updated qr_code
        instance = ProductInfoSheet.objects.get(pk=serializer.instance.pk)
        output_serializer = ProductInfoSheetSerializer(
            instance, context={"request": request}
        )
        return Response(output_serializer.data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        """Override to return full serializer data after update."""
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        # Re-fetch to get updated qr_code
        instance.refresh_from_db()
        output_serializer = ProductInfoSheetSerializer(
            instance, context={"request": request}
        )
        return Response(output_serializer.data)

    @action(detail=True, methods=["post"], url_path="regenerate-qr")
    def regenerate_qr(self, request, pk=None):
        """Regenerate QR code for an existing info sheet."""
        instance = self.get_object()
        base_url = self._get_base_url()
        instance.generate_qr_code(base_url=base_url)
        ProductInfoSheet.objects.filter(pk=instance.pk).update(
            qr_code=instance.qr_code.name
        )
        instance.refresh_from_db()
        serializer = ProductInfoSheetSerializer(
            instance, context={"request": request}
        )
        logger.info(f"Regenerated QR for: {instance.title} (id={instance.id})")
        return Response(serializer.data)

    def _get_base_url(self):
        """Get base URL from request for building absolute PDF URLs."""
        request = self.request
        if request:
            return f"{request.scheme}://{request.get_host()}"
        return None
