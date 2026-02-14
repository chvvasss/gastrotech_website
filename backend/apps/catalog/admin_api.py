"""
Admin API views for catalog management.

These endpoints require admin or editor role and provide:
- Media upload with security hardening
- Product media management (upload, reorder, delete)

Security measures:
- Magic bytes validation (file signature verification)
- Content type validation
- File size limits
- Safe image decode test with Pillow
- Filename sanitization
- Rate limiting
"""

import hashlib
import io
import logging
import os
import re
from typing import Optional, Tuple

from django.conf import settings
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from rest_framework.views import APIView

from apps.api.permissions import IsAdminOrEditor
from apps.common.logging import SecurityLogger
from .models import Media, Product, ProductMedia
from .serializers import MediaMetadataSerializer
from .services.json_import_service import JsonImportService
from apps.ops.models import ImportJob

logger = logging.getLogger(__name__)
security_log = SecurityLogger()


# File signature (magic bytes) definitions
# Format: {content_type: [(signature_bytes, offset), ...]}
MAGIC_BYTES = {
    # Images
    "image/jpeg": [(b"\xff\xd8\xff", 0)],
    "image/png": [(b"\x89PNG\r\n\x1a\n", 0)],
    "image/gif": [(b"GIF87a", 0), (b"GIF89a", 0)],
    "image/webp": [(b"RIFF", 0), (b"WEBP", 8)],  # RIFF at 0, WEBP at 8
    "image/bmp": [(b"BM", 0)],
    "image/tiff": [(b"II\x2a\x00", 0), (b"MM\x00\x2a", 0)],  # Little/Big endian
    "image/svg+xml": [(b"<?xml", 0), (b"<svg", 0)],  # Note: SVG needs extra sanitization
    # Documents
    "application/pdf": [(b"%PDF", 0)],
    # Videos
    "video/mp4": [(b"\x00\x00\x00", 0), (b"ftyp", 4)],  # Various MP4 signatures
    "video/webm": [(b"\x1a\x45\xdf\xa3", 0)],  # WebM/Matroska
    "video/quicktime": [(b"\x00\x00\x00", 0), (b"moov", 4)],
}

# Allowed content types for each media kind
ALLOWED_CONTENT_TYPES = {
    Media.Kind.IMAGE: {
        "image/jpeg", "image/png", "image/gif", "image/webp",
        "image/bmp", "image/tiff",
        # Note: SVG excluded by default for security
    },
    Media.Kind.PDF: {"application/pdf"},
    Media.Kind.VIDEO: {"video/mp4", "video/webm", "video/quicktime"},
}

# Extension to content type mapping
EXTENSION_TO_CONTENT_TYPE = {
    ".jpg": "image/jpeg",
    ".jpeg": "image/jpeg",
    ".png": "image/png",
    ".gif": "image/gif",
    ".webp": "image/webp",
    ".bmp": "image/bmp",
    ".tiff": "image/tiff",
    ".tif": "image/tiff",
    ".pdf": "application/pdf",
    ".mp4": "video/mp4",
    ".webm": "video/webm",
    ".mov": "video/quicktime",
}


class UploadRateThrottle(UserRateThrottle):
    """Custom throttle for file uploads."""
    scope = "uploads"


def get_client_ip(request) -> str:
    """Extract client IP from request, accounting for proxies."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "unknown")


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent path traversal and other attacks.

    - Remove path components
    - Replace dangerous characters
    - Limit length
    """
    if not filename:
        return "unnamed_file"

    # Get just the filename (no path)
    filename = os.path.basename(filename)

    # Remove null bytes and path separators
    filename = filename.replace("\x00", "").replace("/", "_").replace("\\", "_")

    # Remove or replace other dangerous characters
    # Keep alphanumeric, dots, dashes, underscores
    filename = re.sub(r"[^\w.\-]", "_", filename)

    # Prevent double extensions that might bypass checks
    # e.g., "file.php.jpg" -> "file_php.jpg"
    parts = filename.rsplit(".", 1)
    if len(parts) == 2:
        name, ext = parts
        name = name.replace(".", "_")
        filename = f"{name}.{ext}"

    # Limit length (preserve extension)
    if len(filename) > 255:
        parts = filename.rsplit(".", 1)
        if len(parts) == 2:
            name, ext = parts
            max_name_len = 255 - len(ext) - 1
            filename = f"{name[:max_name_len]}.{ext}"
        else:
            filename = filename[:255]

    return filename


def validate_magic_bytes(content: bytes, expected_type: str) -> bool:
    """
    Validate file content against expected magic bytes.

    Returns True if the file signature matches the expected content type.
    """
    signatures = MAGIC_BYTES.get(expected_type)
    if not signatures:
        # Unknown type - can't validate magic bytes
        return True

    for signature, offset in signatures:
        if len(content) > offset + len(signature):
            if content[offset:offset + len(signature)] == signature:
                return True

    return False


def detect_content_type(content: bytes, filename: str) -> Optional[str]:
    """
    Detect content type from magic bytes and filename.

    Priority:
    1. Magic bytes detection
    2. Extension-based fallback
    """
    # Try magic bytes detection
    for content_type, signatures in MAGIC_BYTES.items():
        for signature, offset in signatures:
            if len(content) > offset + len(signature):
                if content[offset:offset + len(signature)] == signature:
                    return content_type

    # Fallback to extension
    ext = os.path.splitext(filename.lower())[1]
    return EXTENSION_TO_CONTENT_TYPE.get(ext)


def validate_image_content(content: bytes) -> Tuple[bool, Optional[int], Optional[int]]:
    """
    Validate image by actually decoding it with Pillow.

    Returns (is_valid, width, height).
    This prevents image bombs and validates the file is actually an image.
    """
    try:
        from PIL import Image

        # Set size limits to prevent decompression bombs
        Image.MAX_IMAGE_PIXELS = 100_000_000  # 100 megapixels

        img = Image.open(io.BytesIO(content))

        # Force decode by accessing pixel data
        img.load()

        # Check dimensions are reasonable
        if img.width > 10000 or img.height > 10000:
            return False, None, None

        return True, img.width, img.height

    except Exception as e:
        logger.warning(f"Image validation failed: {e}")
        return False, None, None


def validate_pdf_content(content: bytes) -> bool:
    """
    Basic PDF validation.

    Checks for PDF header and doesn't contain dangerous patterns.
    """
    if not content.startswith(b"%PDF"):
        return False

    # Check for potentially dangerous patterns
    # (JavaScript, auto-actions, etc.)
    dangerous_patterns = [
        b"/JavaScript",
        b"/JS",
        b"/OpenAction",
        b"/AA",  # Additional Actions
        b"/Launch",
        b"/EmbeddedFile",
    ]

    content_lower = content.lower()
    for pattern in dangerous_patterns:
        if pattern.lower() in content_lower:
            logger.warning(f"PDF contains potentially dangerous pattern: {pattern}")
            # Don't reject, just log - many legitimate PDFs have these

    return True


class MediaUploadView(APIView):
    """
    Upload media file directly.

    POST /api/v1/admin/media/upload
    - Accepts multipart/form-data with "file" field
    - Returns Media metadata

    Security:
    - Magic bytes validation
    - File size limits
    - Image decode validation
    - Filename sanitization
    - Rate limiting
    """

    permission_classes = [IsAdminOrEditor]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [UploadRateThrottle]

    @extend_schema(
        summary="Upload media file",
        description="Upload an image, PDF, or video file. Returns media metadata.",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                },
                "required": ["file"],
            }
        },
        responses={
            201: MediaMetadataSerializer,
            400: {"description": "Invalid file or file too large"},
            415: {"description": "Unsupported media type"},
            429: {"description": "Rate limit exceeded"},
        },
        tags=["Admin - Media"],
    )
    def post(self, request):
        client_ip = get_client_ip(request)
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"error": "No file provided", "code": "NO_FILE"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Validate file size
        max_size = getattr(settings, "MAX_MEDIA_UPLOAD_BYTES", 10 * 1024 * 1024)
        if file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            security_log.upload_rejected(file.name, f"File too large ({file.size} bytes)", client_ip)
            return Response(
                {
                    "error": f"File too large. Maximum size is {max_mb:.1f} MB.",
                    "code": "FILE_TOO_LARGE",
                    "max_size_bytes": max_size,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Sanitize filename
        safe_filename = sanitize_filename(file.name)

        # 3. Read file content
        file_content = file.read()

        # 4. Detect and validate content type
        declared_type = file.content_type or ""
        detected_type = detect_content_type(file_content, safe_filename)

        if not detected_type:
            security_log.upload_rejected(file.name, "Unknown file type", client_ip)
            return Response(
                {
                    "error": "Could not determine file type. Please upload a supported format.",
                    "code": "UNKNOWN_FILE_TYPE",
                    "supported_formats": ["JPEG", "PNG", "GIF", "WebP", "PDF", "MP4", "WebM"],
                },
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # 5. Validate magic bytes match detected type
        if not validate_magic_bytes(file_content, detected_type):
            security_log.upload_rejected(
                file.name,
                f"Magic bytes mismatch (declared: {declared_type}, detected: {detected_type})",
                client_ip,
            )
            return Response(
                {
                    "error": "File content does not match its type. The file may be corrupted or misnamed.",
                    "code": "CONTENT_TYPE_MISMATCH",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 6. Determine media kind
        if detected_type.startswith("image/"):
            kind = Media.Kind.IMAGE
        elif detected_type == "application/pdf":
            kind = Media.Kind.PDF
        elif detected_type.startswith("video/"):
            kind = Media.Kind.VIDEO
        else:
            kind = Media.Kind.IMAGE

        # 7. Validate content type is in allowed list
        allowed = ALLOWED_CONTENT_TYPES.get(kind, set())
        if detected_type not in allowed:
            security_log.upload_rejected(file.name, f"Disallowed content type: {detected_type}", client_ip)
            return Response(
                {
                    "error": f"File type '{detected_type}' is not allowed for {kind}.",
                    "code": "DISALLOWED_CONTENT_TYPE",
                    "allowed_types": list(allowed),
                },
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # 8. Content-specific validation
        width = None
        height = None

        if kind == Media.Kind.IMAGE:
            is_valid, width, height = validate_image_content(file_content)
            if not is_valid:
                security_log.upload_rejected(file.name, "Image decode validation failed", client_ip)
                return Response(
                    {
                        "error": "Invalid image file. The file could not be decoded or has invalid dimensions.",
                        "code": "INVALID_IMAGE",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        elif kind == Media.Kind.PDF:
            if not validate_pdf_content(file_content):
                security_log.upload_rejected(file.name, "PDF validation failed", client_ip)
                return Response(
                    {
                        "error": "Invalid PDF file.",
                        "code": "INVALID_PDF",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 9. Create media object
        media = Media.objects.create(
            kind=kind,
            filename=safe_filename,
            content_type=detected_type,
            bytes=file_content,
            size_bytes=len(file_content),
            width=width,
            height=height,
            checksum_sha256=hashlib.sha256(file_content).hexdigest(),
        )

        logger.info(
            f"Media uploaded successfully: {media.id} ({safe_filename}, {detected_type}, {len(file_content)} bytes)",
            extra={"media_id": str(media.id), "client_ip": client_ip},
        )

        serializer = MediaMetadataSerializer(media, context={"request": request})
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class ProductMediaUploadView(APIView):
    """
    Upload media and attach to product.

    POST /api/v1/admin/products/{product_id}/media/upload
    """

    permission_classes = [IsAdminOrEditor]
    parser_classes = [MultiPartParser, FormParser]
    throttle_classes = [UploadRateThrottle]

    @extend_schema(
        summary="Upload media for product",
        description="Upload a file and create ProductMedia association.",
        request={
            "multipart/form-data": {
                "type": "object",
                "properties": {
                    "file": {"type": "string", "format": "binary"},
                    "alt": {"type": "string"},
                    "sort_order": {"type": "integer"},
                    "is_primary": {"type": "boolean"},
                },
                "required": ["file"],
            }
        },
        responses={
            201: {"description": "Product media created successfully"},
            400: {"description": "Invalid file or validation error"},
            404: {"description": "Product not found"},
            415: {"description": "Unsupported media type"},
            429: {"description": "Rate limit exceeded"},
        },
        tags=["Admin - Media"],
    )
    def post(self, request, product_id):
        client_ip = get_client_ip(request)
        product = get_object_or_404(Product, id=product_id)
        file = request.FILES.get("file")

        if not file:
            return Response(
                {"error": "No file provided", "code": "NO_FILE"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 1. Validate file size
        max_size = getattr(settings, "MAX_MEDIA_UPLOAD_BYTES", 10 * 1024 * 1024)
        if file.size > max_size:
            max_mb = max_size / (1024 * 1024)
            security_log.upload_rejected(file.name, f"File too large ({file.size} bytes)", client_ip)
            return Response(
                {
                    "error": f"File too large. Maximum size is {max_mb:.1f} MB.",
                    "code": "FILE_TOO_LARGE",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 2. Sanitize filename
        safe_filename = sanitize_filename(file.name)

        # 3. Read file content
        file_content = file.read()

        # 4. Detect and validate content type
        detected_type = detect_content_type(file_content, safe_filename)

        if not detected_type:
            security_log.upload_rejected(file.name, "Unknown file type", client_ip)
            return Response(
                {
                    "error": "Could not determine file type.",
                    "code": "UNKNOWN_FILE_TYPE",
                },
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # 5. Validate magic bytes
        if not validate_magic_bytes(file_content, detected_type):
            security_log.upload_rejected(file.name, "Magic bytes mismatch", client_ip)
            return Response(
                {
                    "error": "File content does not match its type.",
                    "code": "CONTENT_TYPE_MISMATCH",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # 6. Determine media kind
        if detected_type.startswith("image/"):
            kind = Media.Kind.IMAGE
        elif detected_type == "application/pdf":
            kind = Media.Kind.PDF
        elif detected_type.startswith("video/"):
            kind = Media.Kind.VIDEO
        else:
            kind = Media.Kind.IMAGE

        # 7. Validate content type is allowed
        allowed = ALLOWED_CONTENT_TYPES.get(kind, set())
        if detected_type not in allowed:
            security_log.upload_rejected(file.name, f"Disallowed content type: {detected_type}", client_ip)
            return Response(
                {
                    "error": f"File type '{detected_type}' is not allowed.",
                    "code": "DISALLOWED_CONTENT_TYPE",
                },
                status=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE,
            )

        # 8. Content validation
        width = None
        height = None

        if kind == Media.Kind.IMAGE:
            is_valid, width, height = validate_image_content(file_content)
            if not is_valid:
                security_log.upload_rejected(file.name, "Image decode failed", client_ip)
                return Response(
                    {
                        "error": "Invalid image file.",
                        "code": "INVALID_IMAGE",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )

        # 9. Create media
        media = Media.objects.create(
            kind=kind,
            filename=safe_filename,
            content_type=detected_type,
            bytes=file_content,
            size_bytes=len(file_content),
            width=width,
            height=height,
            checksum_sha256=hashlib.sha256(file_content).hexdigest(),
        )

        # 10. Parse optional fields
        alt = request.data.get("alt", "")
        sort_order = request.data.get("sort_order")
        is_primary_raw = request.data.get("is_primary", "")
        is_primary = (
            str(is_primary_raw).lower() in ("true", "1", "yes")
            if is_primary_raw
            else False
        )

        # Calculate sort_order if not provided
        if sort_order is None:
            max_order = product.product_media.order_by("-sort_order").values_list(
                "sort_order", flat=True
            ).first() or 0
            sort_order = max_order + 10
        else:
            sort_order = int(sort_order)

        # Handle is_primary (unset others if setting as primary)
        if is_primary:
            product.product_media.filter(is_primary=True).update(is_primary=False)

        # 11. Create ProductMedia
        pm = ProductMedia.objects.create(
            product=product,
            media=media,
            alt=alt,
            sort_order=sort_order,
            is_primary=is_primary,
        )

        logger.info(
            f"Product media uploaded: {pm.id} for product {product.id}",
            extra={"product_media_id": str(pm.id), "product_id": str(product.id)},
        )

        return Response({
            "id": str(pm.id),
            "media_id": str(media.id),
            "file_url": f"/api/v1/media/{media.id}/file",
            "alt": pm.alt,
            "sort_order": pm.sort_order,
            "is_primary": pm.is_primary,
        }, status=status.HTTP_201_CREATED)


class ProductMediaReorderView(APIView):
    """
    Reorder product media.

    PATCH /api/v1/admin/products/{product_id}/media/reorder
    """

    permission_classes = [IsAdminOrEditor]

    @extend_schema(
        summary="Reorder product media",
        description="Update sort_order and is_primary for product media items.",
        request={
            "application/json": {
                "type": "object",
                "properties": {
                    "items": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "product_media_id": {"type": "string", "format": "uuid"},
                                "sort_order": {"type": "integer"},
                                "is_primary": {"type": "boolean"},
                            },
                            "required": ["product_media_id"],
                        },
                    },
                },
                "required": ["items"],
            }
        },
        responses={
            200: {"description": "Media reordered successfully"},
            400: {"description": "Validation error"},
            404: {"description": "Product or media not found"},
        },
        tags=["Admin - Media"],
    )
    def patch(self, request, product_id):
        product = get_object_or_404(Product, id=product_id)
        items = request.data.get("items", [])

        if not items:
            return Response(
                {"error": "No items provided", "code": "NO_ITEMS"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check for single primary
        primary_count = sum(1 for item in items if item.get("is_primary"))
        if primary_count > 1:
            return Response(
                {"error": "Only one item can be primary", "code": "MULTIPLE_PRIMARY"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # If setting a new primary, unset all existing
        if primary_count == 1:
            product.product_media.filter(is_primary=True).update(is_primary=False)

        updated = 0
        for item in items:
            pm_id = item.get("product_media_id")
            try:
                pm = ProductMedia.objects.get(id=pm_id, product=product)
            except ProductMedia.DoesNotExist:
                continue

            if "sort_order" in item:
                pm.sort_order = int(item["sort_order"])
            if "is_primary" in item:
                pm.is_primary = bool(item["is_primary"])

            pm.save()
            updated += 1

        return Response({
            "updated": updated,
            "message": f"Updated {updated} media item(s)",
        })


class ProductMediaDeleteView(APIView):
    """
    Delete product media association.

    DELETE /api/v1/admin/products/{product_id}/media/{product_media_id}

    Note: This does NOT delete the Media object itself, only the association.
    """

    permission_classes = [IsAdminOrEditor]

    @extend_schema(
        summary="Delete product media",
        description="Remove media from product. Does not delete the media file itself.",
        responses={
            204: {"description": "Media removed from product"},
            404: {"description": "Product or media not found"},
        },
        tags=["Admin - Media"],
    )
    def delete(self, request, product_id, product_media_id):
        product = get_object_or_404(Product, id=product_id)
        pm = get_object_or_404(ProductMedia, id=product_media_id, product=product)

        logger.info(
            f"Product media deleted: {pm.id} from product {product.id}",
            extra={"product_media_id": str(pm.id), "product_id": str(product.id)},
        )

        pm.delete()

        return Response(status=status.HTTP_204_NO_CONTENT)


class JsonImportPreviewView(APIView):
    """
    Validate JSON import data.
    
    POST /api/v1/admin/catalog/import/json/preview/
    """
    permission_classes = [IsAdminOrEditor]

    @extend_schema(
        summary="Preview JSON import",
        request={"application/json": [{"type": "object"}]}, # Simplified schema
        responses={200: {"description": "Preview results"}},
    )
    def post(self, request):
        data = request.data
        if not isinstance(data, list):
            return Response({"error": "Input must be a list of products"}, status=400)
            
        result = JsonImportService.preview(data)
        return Response(result)


class JsonImportCommitView(APIView):
    """
    Execute JSON import.
    
    POST /api/v1/admin/catalog/import/json/commit/
    """
    permission_classes = [IsAdminOrEditor]

    @extend_schema(
        summary="Commit JSON import",
        request={"application/json": {"dry_run_id": "string"}}, 
        responses={200: {"description": "Import results"}},
    )
    def post(self, request):
        data = None
        
        # Handle input: either {"dry_run_id": "..."} or raw list [...]
        if isinstance(request.data, dict):
            dry_run_id = request.data.get("dry_run_id")
            if dry_run_id:
                from django.core.cache import cache
                data = cache.get(f"json_import_{dry_run_id}")
        elif isinstance(request.data, list):
            data = request.data

        if not data:
            return Response({"error": "Invalid dry_run_id or missing data"}, status=400)

        # Run Commit
        result = JsonImportService.commit(data)
        
        if result.get("success"):
            # Create ImportJob for Undo/Audit
            stats = result.get("stats", {})
            job = ImportJob.objects.create(
                kind=ImportJob.Kind.CATALOG_IMPORT,
                status=ImportJob.Status.SUCCESS,
                created_by=request.user,
                mode=ImportJob.Mode.SMART, # Assuming smart/mixed
                total_rows=len(data),
                created_count=stats.get("products_created", 0) + stats.get("variants_created", 0),
                updated_count=stats.get("products_updated", 0) + stats.get("variants_updated", 0),
                error_count=len(stats.get("errors", [])),
                report_json={
                    "created_product_ids": stats.get("created_product_ids", []),
                    "stats": stats
                }
            )
            result["job_id"] = str(job.id)

        return Response(result)


class JsonImportUndoView(APIView):
    """
    Undo a specific import job.
    
    POST /api/v1/admin/catalog/import/json/undo/{job_id}/
    """
    permission_classes = [IsAdminOrEditor]

    def post(self, request, job_id):
        job = get_object_or_404(ImportJob, id=job_id)
        
        # Security check: only allow undoing recent Catalog Imports
        if job.kind != ImportJob.Kind.CATALOG_IMPORT:
            return Response({"error": "Can only undo Catalog Imports"}, status=400)
            
        report = job.report_json or {}
        product_ids = report.get("created_product_ids", [])
        
        if not product_ids:
             return Response({"message": "No products to undo for this job"})

        deleted_count, _ = Product.objects.filter(id__in=product_ids).delete()
        
        # Mark job as rolled back (or just log it)
        job.status = "rolled_back" # custom/ad-hoc status update or add to choices
        job.save()

        return Response({"success": True, "deleted_products": deleted_count})
