"""
Operations models for import jobs and audit logging.

This module provides enterprise-grade traceability and bulk operations.
"""

from django.conf import settings
from django.db import models

from apps.common.models import TimeStampedUUIDModel


class ImportJob(TimeStampedUUIDModel):
    """
    Tracks CSV/Excel import jobs for catalog data.
    
    Two-phase import system:
    1. validate() - Dry-run with comprehensive report generation
    2. commit() - Execute import with transaction safety
    
    Supports smart mode (auto-create missing entities) and strict mode.
    """
    
    class Kind(models.TextChoices):
        CATALOG_IMPORT = "catalog_import", "Catalog Import"
        VARIANTS_CSV = "variants_csv", "Variants CSV"
        PRODUCTS_CSV = "products_csv", "Products CSV"
        TAXONOMY_CSV = "taxonomy_csv", "Taxonomy CSV"
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        VALIDATING = "validating", "Validating"
        RUNNING = "running", "Running"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        PARTIAL = "partial", "Partial Success"
    
    class Mode(models.TextChoices):
        STRICT = "strict", "Strict (fail on missing references)"
        SMART = "smart", "Smart (create missing entities with approval)"
    
    kind = models.CharField(
        max_length=32,
        choices=Kind.choices,
        default=Kind.CATALOG_IMPORT,
        db_index=True,
        help_text="Type of import job",
    )
    status = models.CharField(
        max_length=16,
        choices=Status.choices,
        default=Status.PENDING,
        db_index=True,
        help_text="Current status of the import",
    )
    mode = models.CharField(
        max_length=16,
        choices=Mode.choices,
        default=Mode.STRICT,
        help_text="Import mode for handling missing references",
    )
    
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_jobs",
        help_text="User who created the import job",
    )
    
    input_file = models.ForeignKey(
        "catalog.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_jobs",
        help_text="Uploaded CSV/Excel file",
    )
    
    file_hash = models.CharField(
        max_length=64,
        blank=True,
        db_index=True,
        help_text="SHA-256 hash of input file for deduplication",
    )
    
    snapshot_file = models.ForeignKey(
        "catalog.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="import_snapshots",
        help_text="Snapshot of normalized data (JSON/XLSX)",
    )
    
    snapshot_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="SHA-256 hash of snapshot file",
    )
    
    is_preview = models.BooleanField(
        default=True,
        help_text="If true, only validate without making changes (dry-run)",
    )
    allow_partial = models.BooleanField(
        default=False,
        help_text="If true, allow partial success (some rows may fail)",
    )
    
    report_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="Validation/execution report with errors, counts, and valid_rows",
    )
    
    total_rows = models.PositiveIntegerField(default=0)
    created_count = models.PositiveIntegerField(default=0)
    updated_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    error_count = models.PositiveIntegerField(default=0)
    warning_count = models.PositiveIntegerField(default=0)
    
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Import Job"
        verbose_name_plural = "Import Jobs"
        indexes = [
            models.Index(fields=["file_hash"], name="ops_ij_file_hash_idx"),
            models.Index(fields=["status", "-created_at"], name="ops_ij_status_created_idx"),
        ]
    
    def __str__(self):
        return f"{self.get_kind_display()} - {self.get_status_display()} ({self.created_at.date() if self.created_at else 'pending'})"


class AuditLog(TimeStampedUUIDModel):
    """
    Tracks all significant changes in the admin system.
    
    Provides enterprise-grade auditability for compliance and debugging.
    """
    
    class Action(models.TextChoices):
        CREATE = "create", "Create"
        UPDATE = "update", "Update"
        DELETE = "delete", "Delete"
        STATUS_CHANGE = "status_change", "Status Change"
        MEDIA_UPLOAD = "media_upload", "Media Upload"
        MEDIA_DELETE = "media_delete", "Media Delete"
        MEDIA_REORDER = "media_reorder", "Media Reorder"
        TAXONOMY_GENERATE = "taxonomy_generate", "Taxonomy Generate"
        IMPORT_APPLY = "import_apply", "Import Apply"
        TEMPLATE_APPLY = "template_apply", "Template Apply"
        LOGIN = "login", "Login"
        LOGOUT = "logout", "Logout"
    
    # Actor
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
        help_text="User who performed the action",
    )
    actor_email = models.EmailField(
        blank=True,
        help_text="Email snapshot (in case user is deleted)",
    )
    
    # Action
    action = models.CharField(
        max_length=32,
        choices=Action.choices,
        db_index=True,
        help_text="Type of action performed",
    )
    
    # Entity (what was affected)
    entity_type = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Model/entity type (e.g., 'product', 'variant')",
    )
    entity_id = models.CharField(
        max_length=64,
        db_index=True,
        help_text="Entity ID (UUID or primary key)",
    )
    entity_label = models.CharField(
        max_length=255,
        blank=True,
        help_text="Human-readable label (e.g., product title)",
    )
    
    # Changes (JSON diff)
    before_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="State before the change (only changed fields)",
    )
    after_json = models.JSONField(
        default=dict,
        blank=True,
        help_text="State after the change (only changed fields)",
    )
    
    # Additional context
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional context (e.g., import job ID, batch info)",
    )
    
    # Request metadata
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="Client IP address",
    )
    user_agent = models.CharField(
        max_length=512,
        blank=True,
        help_text="Client user agent",
    )
    
    class Meta:
        ordering = ["-created_at"]
        verbose_name = "Audit Log"
        verbose_name_plural = "Audit Logs"
        indexes = [
            models.Index(fields=["entity_type", "entity_id"]),
            models.Index(fields=["actor", "created_at"]),
            models.Index(fields=["action", "created_at"]),
        ]
    
    def __str__(self):
        actor = self.actor_email or "System"
        return f"{actor} {self.action} {self.entity_type}:{self.entity_id}"
    
    @classmethod
    def log(
        cls,
        action: str,
        entity_type: str,
        entity_id: str,
        entity_label: str = "",
        actor=None,
        before: dict = None,
        after: dict = None,
        metadata: dict = None,
        request=None,
    ):
        """
        Create an audit log entry.
        
        Args:
            action: Action type (from Action choices)
            entity_type: Model/entity type name
            entity_id: Entity ID
            entity_label: Human-readable label
            actor: User who performed the action
            before: State before change (dict of changed fields)
            after: State after change (dict of changed fields)
            metadata: Additional context
            request: HTTP request (for IP/user-agent)
        """
        ip_address = None
        user_agent = ""
        
        if request:
            # Get IP from X-Forwarded-For or REMOTE_ADDR
            x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(",")[0].strip()
            else:
                ip_address = request.META.get("REMOTE_ADDR")
            
            user_agent = request.META.get("HTTP_USER_AGENT", "")[:512]
        
        return cls.objects.create(
            actor=actor,
            actor_email=actor.email if actor else "",
            action=action,
            entity_type=entity_type,
            entity_id=str(entity_id),
            entity_label=entity_label,
            before_json=before or {},
            after_json=after or {},
            metadata=metadata or {},
            ip_address=ip_address,
            user_agent=user_agent,
        )
