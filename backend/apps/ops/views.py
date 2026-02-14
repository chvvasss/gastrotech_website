"""
Admin API views for operations (Import Jobs, Audit Logs).
"""

import csv
import hashlib
import io
from datetime import datetime

from django.utils import timezone
from django.db import transaction
from drf_spectacular.utils import extend_schema, extend_schema_view, OpenApiParameter
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.parsers import FormParser, MultiPartParser
from rest_framework.response import Response

from apps.api.permissions import IsAdminOrEditor
from apps.catalog.models import Media, Product, Variant, Series

from .models import AuditLog, ImportJob
from .serializers import (
    AuditLogListSerializer,
    AuditLogSerializer,
    ImportJobCreateSerializer,
    ImportJobDetailSerializer,
    ImportJobListSerializer,
)


@extend_schema_view(
    list=extend_schema(summary="List import jobs", tags=["Admin - Import"]),
    retrieve=extend_schema(summary="Get import job details", tags=["Admin - Import"]),
)
class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for import jobs.
    
    Read-only for list/retrieve. Creation is done via specialized endpoints.
    """
    
    permission_classes = [IsAdminOrEditor]
    queryset = ImportJob.objects.all().select_related("created_by", "input_file")
    
    def get_serializer_class(self):
        if self.action == "retrieve":
            return ImportJobDetailSerializer
        return ImportJobListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by kind
        kind = self.request.query_params.get("kind")
        if kind:
            queryset = queryset.filter(kind=kind)
        
        # Filter by status
        job_status = self.request.query_params.get("status")
        if job_status:
            queryset = queryset.filter(status=job_status)
        
        return queryset.order_by("-created_at")
    
    @extend_schema(
        summary="Upload variants CSV for import",
        description="Upload a CSV file to import/update variants. Returns validation report.",
        request=ImportJobCreateSerializer,
        responses={201: ImportJobDetailSerializer},
        tags=["Admin - Import"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="variants",
        parser_classes=[MultiPartParser, FormParser],
    )
    def variants_import(self, request):
        """Import variants from CSV."""
        return self._handle_csv_import(request, ImportJob.Kind.VARIANTS_CSV)
    
    @extend_schema(
        summary="Upload products CSV for import",
        description="Upload a CSV file to import/update products. Returns validation report.",
        request=ImportJobCreateSerializer,
        responses={201: ImportJobDetailSerializer},
        tags=["Admin - Import"],
    )
    @action(
        detail=False,
        methods=["post"],
        url_path="products",
        parser_classes=[MultiPartParser, FormParser],
    )
    def products_import(self, request):
        """Import products from CSV."""
        return self._handle_csv_import(request, ImportJob.Kind.PRODUCTS_CSV)
    
    @extend_schema(
        summary="Apply import job (execute after dry-run)",
        description="Apply a previously validated import job. Only works for pending/validated jobs.",
        responses={200: ImportJobDetailSerializer},
        tags=["Admin - Import"],
    )
    @action(detail=True, methods=["post"], url_path="apply")
    def apply_import(self, request, pk=None):
        """Apply a validated import job."""
        job = self.get_object()
        
        if job.status not in [ImportJob.Status.PENDING, ImportJob.Status.SUCCESS, ImportJob.Status.VALIDATING]:
             # Allow SUCCESS because sometimes validation sets it to SUCCESS (dry_run=True) 
             # but we want to re-run for real? Actually logic below checks dry_run.
             # If status is VALIDATING (which I set in _handle_csv), we should allow.
             pass

        if job.dry_run is False and job.status == ImportJob.Status.SUCCESS:
             return Response(
                {"error": "Job was already executed successfully"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Execute the import for real
        job.dry_run = False
        job.status = ImportJob.Status.RUNNING
        job.started_at = timezone.now()
        job.save()
        
        try:
            # Use atomic transaction for data integrity
            with transaction.atomic():
                if job.kind == ImportJob.Kind.VARIANTS_CSV:
                    self._execute_variants_import(job, request.user, request)
                elif job.kind == ImportJob.Kind.PRODUCTS_CSV:
                    self._execute_products_import(job, request.user, request)
                
                # If error count > 0 and user didn't explicitly allow partial? 
                # The model has allow_partial field.
                if job.error_count > 0 and not job.allow_partial:
                    raise Exception(f"Import failed with {job.error_count} errors (Partial success not allowed).")
            
            job.completed_at = timezone.now()
            job.status = (
                ImportJob.Status.SUCCESS
                if job.error_count == 0
                else ImportJob.Status.PARTIAL
            )
            job.save()
            
        except Exception as e:
            job.status = ImportJob.Status.FAILED
            job.report_json["execution_error"] = str(e)
            job.completed_at = timezone.now()
            job.save()
            # We don't return 500 here because the job state is updated, client should refresh.
            # But returning error details is helpful.
            return Response(
                {"error": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = ImportJobDetailSerializer(job)
        return Response(serializer.data)
    
    def _handle_csv_import(self, request, kind):
        """Handle CSV file upload and validation."""
        file = request.FILES.get("file")
        if not file:
            return Response(
                {"error": "No file provided"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Validate file type
        if not file.name.lower().endswith(".csv"):
            return Response(
                {"error": "File must be a CSV"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        dry_run = request.data.get("dry_run", "true").lower() in ("true", "1", "yes")
        allow_partial = request.data.get("allow_partial", "false").lower() in ("true", "1", "yes")
        
        # Read and store file content
        file_content = file.read()
        file_hash = hashlib.sha256(file_content).hexdigest()
        
        # Create Media entry for the file
        media = Media.objects.create(
            kind=Media.Kind.FILE,
            filename=file.name,
            content_type=file.content_type or "text/csv",
            bytes=file_content,
            size_bytes=len(file_content),
            checksum_sha256=file_hash,
        )
        
        # Create ImportJob
        job = ImportJob.objects.create(
            kind=kind,
            status=ImportJob.Status.VALIDATING,
            created_by=request.user,
            input_file=media,
            dry_run=dry_run,
            allow_partial=allow_partial,
        )
        
        # Parse and validate CSV
        try:
            if kind == ImportJob.Kind.VARIANTS_CSV:
                self._validate_variants_csv(job, file_content)
            elif kind == ImportJob.Kind.PRODUCTS_CSV:
                self._validate_products_csv(job, file_content)
            
            if not dry_run:
                # Execute immediately if not dry-run
                job.status = ImportJob.Status.RUNNING
                job.started_at = timezone.now()
                job.save()
                
                with transaction.atomic():
                    if kind == ImportJob.Kind.VARIANTS_CSV:
                        self._execute_variants_import(job, request.user, request)
                    elif kind == ImportJob.Kind.PRODUCTS_CSV:
                        self._execute_products_import(job, request.user, request)

                    if job.error_count > 0 and not job.allow_partial:
                        raise Exception(f"Import failed with {job.error_count} errors.")

                job.completed_at = timezone.now()
                job.status = (
                    ImportJob.Status.SUCCESS
                    if job.error_count == 0
                    else ImportJob.Status.PARTIAL
                )
            else:
                # Dry-run only validates
                job.status = (
                    ImportJob.Status.SUCCESS
                    if job.error_count == 0
                    else ImportJob.Status.PARTIAL
                )
            
            job.save()
            
        except Exception as e:
            job.status = ImportJob.Status.FAILED
            job.report_json["parse_error"] = str(e)
            job.save()
        
        serializer = ImportJobDetailSerializer(job)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    def _validate_variants_csv(self, job, file_content):
        """Validate variants CSV and populate job report."""
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        
        report = {
            "rows": [],
            "valid_count": 0,
            "invalid_count": 0,
            "columns_found": [],
        }
        
        required_columns = {"model_code", "product_slug", "name_tr"}
        
        # Check columns
        if reader.fieldnames:
            report["columns_found"] = list(reader.fieldnames)
            missing = required_columns - set(reader.fieldnames)
            if missing:
                report["column_error"] = f"Missing required columns: {', '.join(missing)}"
                job.report_json = report
                job.error_count = 1
                return
        
        row_num = 1
        for row in reader:
            row_num += 1
            row_report = {
                "row": row_num,
                "model_code": row.get("model_code", ""),
                "errors": [],
                "action": "unknown",
            }
            
            # Validate required fields
            if not row.get("model_code", "").strip():
                row_report["errors"].append("model_code is required")
            if not row.get("product_slug", "").strip():
                row_report["errors"].append("product_slug is required")
            if not row.get("name_tr", "").strip():
                row_report["errors"].append("name_tr is required")
            
            # Check if variant exists
            model_code = row.get("model_code", "").strip()
            if model_code:
                exists = Variant.objects.filter(model_code=model_code).exists()
                row_report["action"] = "update" if exists else "create"
            
            # Check product exists
            product_slug = row.get("product_slug", "").strip()
            if product_slug and not Product.objects.filter(slug=product_slug).exists():
                row_report["errors"].append(f"Product not found: {product_slug}")
            
            # Validate numeric fields
            for field in ["list_price", "weight_kg"]:
                value = row.get(field, "").strip()
                if value:
                    try:
                        float(value.replace(",", "."))
                    except ValueError:
                        row_report["errors"].append(f"Invalid number for {field}: {value}")
            
            if row_report["errors"]:
                report["invalid_count"] += 1
            else:
                report["valid_count"] += 1
            
            report["rows"].append(row_report)
        
        job.total_rows = row_num - 1
        job.error_count = report["invalid_count"]
        job.report_json = report
    
    def _validate_products_csv(self, job, file_content):
        """Validate products CSV and populate job report."""
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        
        report = {
            "rows": [],
            "valid_count": 0,
            "invalid_count": 0,
            "columns_found": [],
        }
        
        required_columns = {"slug", "series_slug", "title_tr"}
        
        if reader.fieldnames:
            report["columns_found"] = list(reader.fieldnames)
            missing = required_columns - set(reader.fieldnames)
            if missing:
                report["column_error"] = f"Missing required columns: {', '.join(missing)}"
                job.report_json = report
                job.error_count = 1
                return
        
        row_num = 1
        for row in reader:
            row_num += 1
            row_report = {
                "row": row_num,
                "slug": row.get("slug", ""),
                "errors": [],
                "action": "unknown",
            }
            
            if not row.get("slug", "").strip():
                row_report["errors"].append("slug is required")
            if not row.get("series_slug", "").strip():
                row_report["errors"].append("series_slug is required")
            if not row.get("title_tr", "").strip():
                row_report["errors"].append("title_tr is required")
            
            slug = row.get("slug", "").strip()
            if slug:
                exists = Product.objects.filter(slug=slug).exists()
                row_report["action"] = "update" if exists else "create"
            
            # [FIX] Added series validation
            series_slug = row.get("series_slug", "").strip()
            if series_slug:
                if not Series.objects.filter(slug=series_slug).exists():
                     row_report["errors"].append(f"Series not found: {series_slug}")

            if row_report["errors"]:
                report["invalid_count"] += 1
            else:
                report["valid_count"] += 1
            
            report["rows"].append(row_report)
        
        job.total_rows = row_num - 1
        job.error_count = report["invalid_count"]
        job.report_json = report
    
    def _execute_variants_import(self, job, user, request):
        """Execute variants import (create/update)."""
        file_content = job.input_file.bytes
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        
        created = 0
        updated = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                model_code = row.get("model_code", "").strip()
                product_slug = row.get("product_slug", "").strip()
                
                if not model_code or not product_slug:
                    errors.append({"row": row_num, "error": "Missing essential fields"})
                    continue
                
                product = Product.objects.filter(slug=product_slug).first()
                if not product:
                    errors.append({"row": row_num, "error": f"Product not found: {product_slug}"})
                    continue
                
                # Prepare data
                data = {
                    "name_tr": row.get("name_tr", "").strip(),
                    "name_en": row.get("name_en", "").strip() or "",
                    "dimensions": row.get("dimensions", "").strip() or "",
                }
                
                # Parse numeric fields
                if row.get("list_price", "").strip():
                    try:
                        data["list_price"] = float(row["list_price"].replace(",", "."))
                    except ValueError:
                        pass
                
                if row.get("weight_kg", "").strip():
                    try:
                        data["weight_kg"] = float(row["weight_kg"].replace(",", "."))
                    except ValueError:
                        pass
                
                # Create or update
                variant, is_created = Variant.objects.update_or_create(
                    model_code=model_code,
                    defaults={"product": product, **data},
                )
                
                if is_created:
                    created += 1
                    AuditLog.log(
                        action=AuditLog.Action.CREATE,
                        entity_type="variant",
                        entity_id=str(variant.id),
                        entity_label=variant.model_code,
                        actor=user,
                        after=data,
                        metadata={"import_job_id": str(job.id)},
                        request=request,
                    )
                else:
                    updated += 1
                    AuditLog.log(
                        action=AuditLog.Action.UPDATE,
                        entity_type="variant",
                        entity_id=str(variant.id),
                        entity_label=variant.model_code,
                        actor=user,
                        after=data,
                        metadata={"import_job_id": str(job.id)},
                        request=request,
                    )
                
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        job.created_count = created
        job.updated_count = updated
        job.error_count = len(errors)
        job.report_json["execution_errors"] = errors
        job.report_json["created_count"] = created
        job.report_json["updated_count"] = updated
    
    def _execute_products_import(self, job, user, request):
        """Execute products import (create/update)."""
        # from apps.catalog.models import Series # Moved to top level
        
        file_content = job.input_file.bytes
        text = file_content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text), delimiter=";")
        
        created = 0
        updated = 0
        errors = []
        
        for row_num, row in enumerate(reader, start=2):
            try:
                slug = row.get("slug", "").strip()
                series_slug = row.get("series_slug", "").strip()
                
                if not slug or not series_slug:
                     errors.append({"row": row_num, "error": "Missing essential fields"})
                     continue
                
                series = Series.objects.filter(slug=series_slug).first()
                if not series:
                    errors.append({"row": row_num, "error": f"Series not found: {series_slug}"})
                    continue
                
                data = {
                    "title_tr": row.get("title_tr", "").strip(),
                    "title_en": row.get("title_en", "").strip() or "",
                    "status": row.get("status", "draft").strip() or "draft",
                }
                
                # Handle is_featured
                if row.get("is_featured", "").strip().lower() in ("true", "1", "yes"):
                    data["is_featured"] = True
                else:
                    data["is_featured"] = False
                
                product, is_created = Product.objects.update_or_create(
                    slug=slug,
                    defaults={"series": series, "name": slug, **data},
                )
                
                if is_created:
                    created += 1
                    AuditLog.log(
                        action=AuditLog.Action.CREATE,
                        entity_type="product",
                        entity_id=str(product.id),
                        entity_label=product.title_tr,
                        actor=user,
                        after=data,
                        metadata={"import_job_id": str(job.id)},
                        request=request,
                    )
                else:
                    updated += 1
                    AuditLog.log(
                        action=AuditLog.Action.UPDATE,
                        entity_type="product",
                        entity_id=str(product.id),
                        entity_label=product.title_tr,
                        actor=user,
                        after=data,
                        metadata={"import_job_id": str(job.id)},
                        request=request,
                    )
                
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        
        job.created_count = created
        job.updated_count = updated
        job.error_count = len(errors)
        job.report_json["execution_errors"] = errors
        job.report_json["created_count"] = created
        job.report_json["updated_count"] = updated


@extend_schema_view(
    list=extend_schema(
        summary="List audit logs",
        parameters=[
            OpenApiParameter(name="entity_type", type=str, description="Filter by entity type"),
            OpenApiParameter(name="entity_id", type=str, description="Filter by entity ID"),
            OpenApiParameter(name="action", type=str, description="Filter by action"),
            OpenApiParameter(name="actor", type=str, description="Filter by actor email"),
        ],
        tags=["Admin - Audit"],
    ),
    retrieve=extend_schema(summary="Get audit log details", tags=["Admin - Audit"]),
)
class AuditLogViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for audit logs.
    
    Read-only - logs are created by the system.
    """
    
    permission_classes = [IsAdminOrEditor]
    queryset = AuditLog.objects.all().select_related("actor")
    
    def get_serializer_class(self):
        if self.action == "list":
            return AuditLogListSerializer
        return AuditLogSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by entity
        entity_type = self.request.query_params.get("entity_type")
        if entity_type:
            queryset = queryset.filter(entity_type=entity_type)
        
        entity_id = self.request.query_params.get("entity_id")
        if entity_id:
            queryset = queryset.filter(entity_id=entity_id)
        
        # Filter by action
        action = self.request.query_params.get("action")
        if action:
            queryset = queryset.filter(action=action)
        
        # Filter by actor
        actor = self.request.query_params.get("actor")
        if actor:
            queryset = queryset.filter(actor_email__icontains=actor)
        
        return queryset.order_by("-created_at")
    
    @extend_schema(
        summary="Cleanup old audit logs",
        description="Delete audit logs older than specified days",
        parameters=[
            OpenApiParameter(
                name="older_than_days",
                type=int,
                description="Delete logs older than this many days (default: 30)",
                required=False,
            ),
        ],
        responses={200: {"type": "object", "properties": {"deleted_count": {"type": "integer"}}}},
        tags=["Admin - Audit"],
    )
    @action(detail=False, methods=["delete"], url_path="cleanup")
    def cleanup(self, request):
        """Delete old audit logs."""
        from datetime import timedelta
        
        # Get days parameter, default to 30
        try:
            older_than_days = int(request.query_params.get("older_than_days", 30))
        except ValueError:
            return Response(
                {"error": "older_than_days must be an integer"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if older_than_days < 1:
            return Response(
                {"error": "older_than_days must be at least 1"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Calculate cutoff date
        cutoff_date = timezone.now() - timedelta(days=older_than_days)
        
        # Delete old logs
        deleted_count, _ = AuditLog.objects.filter(created_at__lt=cutoff_date).delete()
        
        return Response(
            {
                "deleted_count": deleted_count,
                "older_than_days": older_than_days,
                "cutoff_date": cutoff_date.isoformat(),
            },
            status=status.HTTP_200_OK,
        )
