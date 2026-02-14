"""
Django admin configuration for Blog models.
"""

from django.contrib import admin

from .models import BlogCategory, BlogPost, BlogTag


@admin.register(BlogCategory)
class BlogCategoryAdmin(admin.ModelAdmin):
    list_display = ["name_tr", "slug", "order", "is_active", "created_at"]
    list_filter = ["is_active"]
    search_fields = ["name_tr", "name_en"]
    prepopulated_fields = {"slug": ("name_tr",)}
    ordering = ["order", "name_tr"]


@admin.register(BlogTag)
class BlogTagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["name"]


@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = [
        "title",
        "category",
        "author",
        "status",
        "is_featured",
        "published_at",
        "view_count",
    ]
    list_filter = ["status", "is_featured", "category"]
    search_fields = ["title", "excerpt", "content"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["author", "cover_media"]
    filter_horizontal = ["tags"]
    date_hierarchy = "published_at"
    ordering = ["-created_at"]
    
    fieldsets = (
        (None, {
            "fields": ("title", "slug", "excerpt", "content")
        }),
        ("Media", {
            "fields": ("cover_media",)
        }),
        ("Categorization", {
            "fields": ("category", "tags")
        }),
        ("Publishing", {
            "fields": ("author", "status", "published_at", "is_featured")
        }),
        ("SEO", {
            "fields": ("meta_title", "meta_description"),
            "classes": ("collapse",)
        }),
        ("Metrics", {
            "fields": ("view_count", "reading_time_min"),
            "classes": ("collapse",)
        }),
    )
    
    readonly_fields = ["view_count", "reading_time_min"]
