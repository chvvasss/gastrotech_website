from django.contrib import admin

from .models import AuditLog, ImportJob


@admin.register(ImportJob)
class ImportJobAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "kind",
        "mode",
        "status",
        "created_by",
        "total_rows",
        "created_count",
        "updated_count",
        "error_count",
        "warning_count",
        "is_preview",
        "created_at",
    ]
    list_filter = ["kind", "mode", "status", "is_preview", "created_at"]
    search_fields = ["id", "created_by__email"]
    readonly_fields = [
        "id",
        "created_at",
        "updated_at",
        "started_at",
        "completed_at",
        "report_json",
    ]
    date_hierarchy = "created_at"


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "action",
        "entity_type",
        "entity_id",
        "entity_label",
        "actor_email",
        "ip_address",
        "created_at",
    ]
    list_filter = ["action", "entity_type", "created_at"]
    search_fields = [
        "entity_id",
        "entity_label",
        "actor_email",
        "ip_address",
    ]
    readonly_fields = [
        "id",
        "created_at",
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
    ]
    date_hierarchy = "created_at"
    
    def has_add_permission(self, request):
        return False
    
    def has_change_permission(self, request, obj=None):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False
