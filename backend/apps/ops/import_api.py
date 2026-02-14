"""
DRF API Endpoints for Import Operations.

Endpoints:
- POST /api/admin/import-jobs/validate/ - Upload and validate file (dry-run)
- POST /api/admin/import-jobs/{id}/commit/ - Execute import
- GET /api/admin/import-jobs/{id}/report/ - Download XLSX report
- GET /api/admin/import-jobs/template/ - Download import template
- GET /api/admin/import-jobs/ - List import jobs
- GET /api/admin/import-jobs/{id}/ - Get import job detail
"""

import logging
from django.http import HttpResponse
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse

from apps.catalog.models import Media
from apps.ops.models import ImportJob
from apps.ops.import_serializers import (
    ImportJobListSerializer,
    ImportJobDetailSerializer,
    ValidateImportSerializer,
    CommitImportSerializer,
    TemplateDownloadSerializer,
)
from apps.ops.services.unified_import import UnifiedImportService
from apps.ops.services.report_generator import ImportReportGenerator

logger = logging.getLogger(__name__)


def sanitize_for_json(obj):
    """Recursively convert Decimal and other non-JSON types to strings."""
    from decimal import Decimal
    if isinstance(obj, Decimal):
        return str(obj)
    elif isinstance(obj, dict):
        return {k: sanitize_for_json(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_for_json(item) for item in obj]
    return obj


class ImportJobViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Import Job management.

    Provides:
    - List/detail views for import job history
    - validate: Upload and validate import file (dry-run)
    - commit: Execute validated import
    - report: Download XLSX report
    - template: Download import template
    """

    queryset = ImportJob.objects.all().order_by('-created_at')
    permission_classes = [IsAuthenticated, IsAdminUser]
    serializer_class = ImportJobListSerializer

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ImportJobDetailSerializer
        return ImportJobListSerializer

    @extend_schema(
        request=ValidateImportSerializer,
        responses={
            200: ImportJobDetailSerializer,
            400: OpenApiResponse(description="Validation failed"),
        },
        description="Upload and validate import file (dry-run). Returns comprehensive report with issues and candidates.",
    )
    @action(detail=False, methods=['post'], url_path='validate')
    def validate_import(self, request):
        """
        Phase 1: Upload and validate import file (dry-run).

        Flow:
        1. Upload file (multipart/form-data)
        2. Store file in Media
        3. Run UnifiedImportService.validate()
        4. Create ImportJob with report_json
        5. Return job with validation results

        Returns:
            ImportJob with:
            - report_json: Comprehensive validation report
            - status: validation_passed / validation_warnings / failed_validation
            - Candidates (if smart mode)
        """
        serializer = ValidateImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        file = serializer.validated_data['file']
        mode = serializer.validated_data['mode']
        kind = serializer.validated_data['kind']

        logger.info(f"[API] Validate import: {file.name}, mode={mode}, kind={kind}")

        try:
            # Step 1: Read file bytes
            file_bytes = file.read()
            file_hash = UnifiedImportService.compute_file_hash(file_bytes)

            # Step 2: Check for duplicate (idempotency)
            existing_job = ImportJob.objects.filter(
                file_hash=file_hash,
                status__in=['success', 'partial'],
            ).order_by('-created_at').first()

            if existing_job:
                logger.info(f"[API] Duplicate file detected (hash={file_hash}), returning existing job {existing_job.id}")
                return Response(
                    {
                        'message': 'This file has already been imported successfully',
                        'existing_job_id': str(existing_job.id),
                        'job': ImportJobDetailSerializer(existing_job).data,
                    },
                    status=status.HTTP_200_OK
                )

            # Step 3: Store file in Media
            input_media = Media.objects.create(
                kind='file',
                filename=file.name,
                content_type=file.content_type,
                bytes=file_bytes,
                size_bytes=len(file_bytes),
            )

            # Step 4: Run validation
            service = UnifiedImportService(mode=mode)
            report = service.validate(file_bytes, file.name)

            total_rows = (
                report['counts'].get('total_product_rows', 0) +
                report['counts'].get('total_variant_rows', 0)
            )

            # Extract snapshot info from report
            snapshot_info = report.get('snapshot', {})
            snapshot_media_id = snapshot_info.get('media_id')
            snapshot_hash = snapshot_info.get('hash')

            # CRITICAL: Verify snapshot was created successfully
            # If snapshot is missing, validation failed silently - report error
            if not snapshot_media_id and report.get('status') not in ['failed_validation', 'validation_fatal_error']:
                logger.error(f"[API] Validation completed but snapshot not created. Report status: {report.get('status')}")
                return Response(
                    {'error': 'Validation failed: snapshot could not be created. Please check server logs or try again.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            job = ImportJob.objects.create(
                kind=kind,
                mode=mode,
                status='validating',
                created_by=request.user,
                input_file=input_media,
                file_hash=file_hash,
                snapshot_file_id=snapshot_media_id,  # CRITICAL: Store snapshot ref
                snapshot_hash=snapshot_hash,         # CRITICAL: Store snapshot hash
                is_preview=True,
                report_json=sanitize_for_json(report),  # Sanitize Decimals
                total_rows=total_rows,
                error_count=report['counts'].get('error_rows', 0),
                warning_count=report['counts'].get('warning_rows', 0),
            )

            # Update status based on validation result
            report_status = report.get('status')
            if report_status in ['failed_validation', 'validation_fatal_error']:
                job.status = 'failed'
            elif report_status == 'validation_warnings':
                job.status = 'partial'
            elif report_status == 'validation_passed' and snapshot_media_id:
                job.status = 'pending'  # Ready to commit
            elif report_status == 'validation_passed' and not snapshot_media_id:
                # Validation passed but snapshot creation failed - this is critical
                logger.error(f"[API] Validation passed but snapshot missing. This is a bug.")
                job.status = 'failed'
                # Add error to report_json so frontend shows the real issue
                report_with_error = job.report_json.copy() if job.report_json else {}
                if 'issues' not in report_with_error:
                    report_with_error['issues'] = []
                report_with_error['issues'].append({
                    'row': None,
                    'column': None,
                    'value': None,
                    'severity': 'error',
                    'code': 'snapshot_creation_failed',
                    'message': 'Dahili hata: Snapshot oluşturulamadı. Lütfen tekrar deneyin veya sistem yöneticisiyle iletişime geçin.',
                    'expected': None,
                })
                report_with_error['status'] = 'failed_validation'
                job.report_json = report_with_error
                job.error_count = 1  # Ensure error count reflects the issue
            else:
                # Unknown status - mark as failed
                logger.warning(f"[API] Unexpected validation state: status={report_status}, has_snapshot={bool(snapshot_media_id)}")
                job.status = 'failed'

            job.save()

            logger.info(f"[API] Validation complete: job {job.id}, status={job.status}")

            return Response(
                ImportJobDetailSerializer(job).data,
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception(f"[API] Validation error")
            return Response(
                {'error': f'Validation failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        request=CommitImportSerializer,
        responses={
            200: OpenApiResponse(description="Import committed successfully"),
            400: OpenApiResponse(description="Commit failed"),
        },
        description="Execute validated import (Phase 2). Writes to database with transaction safety.",
    )
    @action(detail=True, methods=['post'], url_path='commit')
    def commit_import(self, request, pk=None):
        """
        Phase 2: Execute validated import.

        Flow:
        1. Load ImportJob
        2. Validate job state (must be pending/validation_passed)
        3. Run UnifiedImportService.commit()
        4. Update job status
        5. Return execution report with DB verification

        Returns:
            Execution report with:
            - counts: created/updated products/variants
            - verification: DB sample check (proof of write)
        """
        job = self.get_object()

        serializer = CommitImportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        allow_partial = serializer.validated_data['allow_partial']

        logger.info(f"[API] Commit import: job {job.id}, allow_partial={allow_partial}")

        try:
            # Validate job state
            if job.status not in ['pending', 'partial']:
                return Response(
                    {'error': f'Job is in invalid state for commit: {job.status}. Please re-validate the file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Validate snapshot exists (required for deterministic commit)
            if not job.snapshot_file:
                logger.error(f"[API] Commit failed: job {job.id} has no snapshot. status={job.status}")
                return Response(
                    {'error': 'Import job has no validation snapshot. This may occur if validation failed silently. Please re-upload and validate the file.'},
                    status=status.HTTP_400_BAD_REQUEST
                )

            # Execute commit
            service = UnifiedImportService(mode=job.mode)
            result = service.commit(str(job.id), allow_partial=allow_partial)

            job.refresh_from_db()
            job.completed_at = timezone.now()
            job.save()

            logger.info(f"[API] Commit complete: job {job.id}, status={job.status}")

            return Response(
                {
                    'message': 'Import committed successfully',
                    'job_id': str(job.id),
                    'status': job.status,
                    'result': result,
                },
                status=status.HTTP_200_OK
            )

        except Exception as e:
            logger.exception(f"[API] Commit error for job {job.id}")
            return Response(
                {'error': f'Commit failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )

    @extend_schema(
        responses={
            200: OpenApiResponse(
                description="XLSX report file",
                response=bytes,
            ),
            404: OpenApiResponse(description="Job not found"),
        },
        description="Download comprehensive XLSX report with validation results, issues, candidates, and normalization summary.",
    )
    @action(detail=True, methods=['get'], url_path='report')
    def download_report(self, request, pk=None):
        """
        Download XLSX report for import job.

        Report includes:
        - Summary sheet (counts, status)
        - Issues sheet (errors/warnings)
        - Data sheet (normalized rows, re-import ready)
        - Candidates sheet (missing entities)
        - Normalization sheet (merges, disambiguations)

        Returns:
            XLSX file download
        """
        job = self.get_object()

        logger.info(f"[API] Download report: job {job.id}")

        try:
            # Generate XLSX report
            generator = ImportReportGenerator()
            xlsx_bytes = generator.generate(job.report_json)

            # Return as file download
            response = HttpResponse(
                xlsx_bytes,
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = f'attachment; filename="import_report_{job.id}.xlsx"'

            return response

        except Exception as e:
            logger.exception(f"[API] Report generation error for job {job.id}")
            return Response(
                {'error': f'Report generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    @extend_schema(
        parameters=[
            OpenApiParameter(name='fmt', type=str, enum=['xlsx', 'csv'], default='xlsx'),
            OpenApiParameter(name='include_examples', type=bool, default=True),
        ],
        responses={
            200: OpenApiResponse(
                description="Template file (XLSX or CSV)",
                response=bytes,
            ),
        },
        description="Download import template with column definitions and example rows.",
    )
    @action(detail=False, methods=['get'], url_path='template')
    def download_template(self, request):
        """
        Download import template.

        Template includes:
        - Required columns (model_code, product_slug, name_tr, series_slug, title_tr)
        - Optional columns (dimensions, list_price, etc.)
        - Example rows (if include_examples=true)
        - spec_* columns for flexible specifications

        Query params:
            fmt: xlsx or csv (default: xlsx)
            include_examples: Include example rows (default: true)

        Returns:
            Template file download
        """
        serializer = TemplateDownloadSerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)

        format_type = serializer.validated_data['fmt']
        include_examples = serializer.validated_data['include_examples']

        logger.info(f"[API] Download template: format={format_type}, include_examples={include_examples}")

        try:
            # Generate template
            template_bytes = self._generate_template(format_type, include_examples)

            # Return as file download
            content_type = (
                'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
                if format_type == 'xlsx'
                else 'text/csv'
            )
            filename = f'import_template.{format_type}'

            response = HttpResponse(template_bytes, content_type=content_type)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'

            return response

        except Exception as e:
            logger.exception("[API] Template generation error")
            return Response(
                {'error': f'Template generation failed: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def _generate_template(self, format_type: str, include_examples: bool) -> bytes:
        """Generate import template file."""
        import pandas as pd
        import io

        # Define columns
        columns = [
            # Required variant fields
            'model_code',
            'product_slug',
            'name_tr',
            # Optional variant fields
            'name_en',
            'dimensions',
            'list_price',
            'weight_kg',
            'stock_qty',
            'sku',
            # Required product fields (for new products)
            'series_slug',
            'title_tr',
            # Optional product fields
            'title_en',
            'brand_slug',
            'status',
            # Example spec columns
            'spec_voltage',
            'spec_power',
            'spec_fuel_type',
        ]

        # Example rows
        if include_examples:
            examples = [
                {
                    'model_code': 'GKO-6010',
                    'product_slug': 'gazli-ocak-6-gozlu',
                    'name_tr': '6 Gözlü Gazlı Ocak',
                    'name_en': '6 Burner Gas Stove',
                    'dimensions': '600x700x280',
                    'list_price': '15000.00',
                    'weight_kg': '85.5',
                    'stock_qty': '10',
                    'series_slug': '600-series',
                    'title_tr': 'Gazlı Ocak',
                    'title_en': 'Gas Stove',
                    'brand_slug': 'gastrotech',
                    'status': 'active',
                    'spec_voltage': '220V',
                    'spec_power': '12kW',
                    'spec_fuel_type': 'LPG/NG',
                },
                {
                    'model_code': 'GKO-6020',
                    'product_slug': 'gazli-ocak-6-gozlu',
                    'name_tr': '8 Gözlü Gazlı Ocak',
                    'name_en': '8 Burner Gas Stove',
                    'dimensions': '800x700x280',
                    'list_price': '18000.00',
                    'weight_kg': '95.0',
                    'stock_qty': '5',
                    'series_slug': '600-series',
                    'title_tr': 'Gazlı Ocak',
                    'title_en': 'Gas Stove',
                    'brand_slug': 'gastrotech',
                    'status': 'active',
                    'spec_voltage': '220V',
                    'spec_power': '16kW',
                    'spec_fuel_type': 'LPG/NG',
                },
            ]
            df = pd.DataFrame(examples)
        else:
            # Empty template
            df = pd.DataFrame(columns=columns)

        # Generate file
        output = io.BytesIO()

        if format_type == 'xlsx':
            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Import Data')

                # Add instructions sheet
                instructions = pd.DataFrame({
                    'Column': [
                        'model_code',
                        'product_slug',
                        'name_tr',
                        'series_slug',
                        'title_tr',
                        'spec_*',
                    ],
                    'Required': [
                        'Yes',
                        'Yes',
                        'Yes',
                        'Yes (for new products)',
                        'Yes (for new products)',
                        'No',
                    ],
                    'Description': [
                        'Unique model code (e.g., GKO-6010)',
                        'Product slug (URL-friendly identifier)',
                        'Variant name in Turkish',
                        'Series slug (e.g., 600-series)',
                        'Product title in Turkish',
                        'Flexible specs: prefix with spec_ (e.g., spec_voltage)',
                    ],
                })
                instructions.to_excel(writer, index=False, sheet_name='Instructions')

        else:  # CSV
            df.to_csv(output, index=False, sep=';')

        output.seek(0)
        return output.getvalue()
