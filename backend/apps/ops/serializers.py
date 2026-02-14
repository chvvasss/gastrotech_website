"""
Serializers for operations API.
"""

from rest_framework import serializers

from .models import AuditLog, ImportJob


class ImportJobListSerializer(serializers.ModelSerializer):
    """List serializer for import jobs."""
    
    created_by_email = serializers.CharField(source="created_by.email", read_only=True, allow_null=True)
    
    class Meta:
        model = ImportJob
        fields = [
            "id",
            "kind",
            "status",
            "created_by",
            "created_by_email",
            "dry_run",
            "allow_partial",
            "total_rows",
            "created_count",
            "updated_count",
            "skipped_count",
            "error_count",
            "started_at",
            "completed_at",
            "created_at",
        ]


class ImportJobDetailSerializer(serializers.ModelSerializer):
    """Detail serializer for import jobs (includes report)."""
    
    created_by_email = serializers.CharField(source="created_by.email", read_only=True, allow_null=True)
    input_file_url = serializers.SerializerMethodField()
    
    class Meta:
        model = ImportJob
        fields = [
            "id",
            "kind",
            "status",
            "created_by",
            "created_by_email",
            "input_file",
            "input_file_url",
            "dry_run",
            "allow_partial",
            "report_json",
            "total_rows",
            "created_count",
            "updated_count",
            "skipped_count",
            "error_count",
            "started_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
    
    def get_input_file_url(self, obj):
        if obj.input_file_id:
            return f"/api/v1/media/{obj.input_file_id}/file"
        return None


class ImportJobCreateSerializer(serializers.Serializer):
    """Serializer for creating an import job."""
    
    kind = serializers.ChoiceField(choices=ImportJob.Kind.choices)
    dry_run = serializers.BooleanField(default=True)
    allow_partial = serializers.BooleanField(default=False)
    file = serializers.FileField()


class AuditLogSerializer(serializers.ModelSerializer):
    """Serializer for audit log entries."""
    
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor",
            "actor_email",
            "action",
            "entity_type",
            "entity_id",
            "entity_label",
            "before_json",
            "after_json",
            "metadata",
            "ip_address",
            "user_agent",
            "created_at",
        ]


class AuditLogListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for audit log listing."""
    
    class Meta:
        model = AuditLog
        fields = [
            "id",
            "actor_email",
            "action",
            "entity_type",
            "entity_id",
            "entity_label",
            "created_at",
        ]
