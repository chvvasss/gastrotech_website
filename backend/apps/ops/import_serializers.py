"""
Serializers for Import API endpoints.
"""

from rest_framework import serializers
from apps.ops.models import ImportJob


class ImportJobListSerializer(serializers.ModelSerializer):
    """Serializer for import job list view."""

    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)

    class Meta:
        model = ImportJob
        fields = [
            'id',
            'kind',
            'kind_display',
            'status',
            'status_display',
            'mode',
            'mode_display',
            'created_by_email',
            'created_at',
            'completed_at',
            'total_rows',
            'created_count',
            'updated_count',
            'error_count',
            'warning_count',
        ]
        read_only_fields = fields


class ImportJobDetailSerializer(serializers.ModelSerializer):
    """Serializer for import job detail view."""

    created_by_email = serializers.EmailField(source='created_by.email', read_only=True)
    kind_display = serializers.CharField(source='get_kind_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    mode_display = serializers.CharField(source='get_mode_display', read_only=True)

    class Meta:
        model = ImportJob
        fields = [
            'id',
            'kind',
            'kind_display',
            'status',
            'status_display',
            'mode',
            'mode_display',
            'created_by',
            'created_by_email',
            'input_file',
            'file_hash',
            'snapshot_file',
            'snapshot_hash',
            'is_preview',
            'allow_partial',
            'report_json',
            'total_rows',
            'created_count',
            'updated_count',
            'skipped_count',
            'error_count',
            'warning_count',
            'started_at',
            'completed_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = fields


class ValidateImportSerializer(serializers.Serializer):
    """Serializer for validate import endpoint (multipart upload)."""

    file = serializers.FileField(
        help_text="Excel or CSV file to import (max 10MB)",
    )
    mode = serializers.ChoiceField(
        choices=['strict', 'smart'],
        default='strict',
        help_text="strict: fail on missing refs, smart: create candidates with approval",
    )
    kind = serializers.ChoiceField(
        choices=['catalog_import'],
        default='catalog_import',
        help_text="Type of import (only catalog_import supported for now)",
    )
    treat_slash_as_hierarchy = serializers.BooleanField(
        default=True,
        help_text="If true, '/' in category fields creates hierarchical categories (e.g., 'Root / Sub / Leaf')",
    )
    allow_create_missing_categories = serializers.BooleanField(
        default=True,
        help_text="If true (and mode=smart), automatically create missing categories in hierarchy",
    )

    def validate_file(self, value):
        """Validate file extension and size."""
        # Check file extension
        filename = value.name.lower()
        if not (filename.endswith('.xlsx') or filename.endswith('.xls') or filename.endswith('.csv')):
            raise serializers.ValidationError(
                "Invalid file format. Only .xlsx, .xls, and .csv files are supported."
            )

        # Check file size (10MB limit)
        max_size = 10 * 1024 * 1024  # 10MB
        if value.size > max_size:
            raise serializers.ValidationError(
                f"File too large. Maximum size is {max_size / (1024 * 1024):.1f}MB."
            )

        return value


class CommitImportSerializer(serializers.Serializer):
    """Serializer for commit import endpoint."""

    allow_partial = serializers.BooleanField(
        default=False,
        help_text="If true, commit valid rows even if some rows have errors",
    )
    treat_slash_as_hierarchy = serializers.BooleanField(
        default=True,
        help_text="If true, '/' in category fields creates hierarchical categories",
    )
    allow_create_missing_categories = serializers.BooleanField(
        default=True,
        help_text="If true, automatically create missing categories in hierarchy",
    )


class TemplateDownloadSerializer(serializers.Serializer):
    """Serializer for template download endpoint (query params)."""

    fmt = serializers.ChoiceField(
        choices=['xlsx', 'csv'],
        default='xlsx',
        help_text="Template format",
    )
    include_examples = serializers.BooleanField(
        default=True,
        help_text="Include example rows in template",
    )
