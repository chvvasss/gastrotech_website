"""
Blog models for Gastrotech content management.

This module implements the blog domain:
- BlogCategory: Blog post categories (Trendler, Rehber, Haberler, etc.)
- BlogTag: Tags for post categorization (many-to-many)
- BlogPost: Blog posts with rich content, SEO, and author tracking
"""

from django.conf import settings
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedUUIDModel
from apps.common.slugify_tr import slugify_tr


class BlogCategory(TimeStampedUUIDModel):
    """
    Blog post category.
    
    Examples: Trendler, Sürdürülebilirlik, Rehber, Bakım, Haberler
    """
    
    name_tr = models.CharField(
        max_length=100,
        help_text="Category name in Turkish",
    )
    name_en = models.CharField(
        max_length=100,
        blank=True,
        help_text="Category name in English",
    )
    slug = models.SlugField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text="URL-friendly slug",
    )
    description = models.TextField(
        blank=True,
        help_text="Category description",
    )
    order = models.PositiveIntegerField(
        default=0,
        db_index=True,
        help_text="Display order",
    )
    is_active = models.BooleanField(
        default=True,
        db_index=True,
        help_text="Whether category is active",
    )
    
    class Meta:
        verbose_name = "blog category"
        verbose_name_plural = "blog categories"
        ordering = ["order", "name_tr"]
    
    def __str__(self):
        return self.name_tr
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_tr(self.name_tr)
        super().save(*args, **kwargs)


class BlogTag(TimeStampedUUIDModel):
    """
    Blog post tag for flexible categorization.
    
    Tags allow posts to be grouped by topics across categories.
    """
    
    name = models.CharField(
        max_length=50,
        unique=True,
        help_text="Tag name",
    )
    slug = models.SlugField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text="URL-friendly slug",
    )
    
    class Meta:
        verbose_name = "blog tag"
        verbose_name_plural = "blog tags"
        ordering = ["name"]
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify_tr(self.name)
        super().save(*args, **kwargs)


class BlogPost(TimeStampedUUIDModel):
    """
    Blog post with rich content and SEO support.
    
    Supports draft/published/archived workflow and author attribution.
    """
    
    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        ARCHIVED = "archived", "Archived"
    
    # Basic content
    title = models.CharField(
        max_length=200,
        help_text="Post title",
    )
    slug = models.SlugField(
        max_length=220,
        unique=True,
        db_index=True,
        help_text="URL-friendly slug",
    )
    excerpt = models.TextField(
        max_length=500,
        help_text="Short excerpt for previews (max 500 chars)",
    )
    content = models.TextField(
        help_text="Full post content (HTML or Markdown)",
    )
    
    # Media
    cover_media = models.ForeignKey(
        "catalog.Media",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_post_covers",
        help_text="Cover image for the post",
    )
    
    # Categorization
    category = models.ForeignKey(
        BlogCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="posts",
        help_text="Post category",
    )
    tags = models.ManyToManyField(
        BlogTag,
        blank=True,
        related_name="posts",
        help_text="Post tags",
    )
    
    # Author
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="blog_posts",
        help_text="Post author",
    )
    
    # Publishing
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
        db_index=True,
        help_text="Publication status",
    )
    published_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Publication date/time",
    )
    is_featured = models.BooleanField(
        default=False,
        db_index=True,
        help_text="Show in featured section",
    )
    
    # Metrics
    view_count = models.PositiveIntegerField(
        default=0,
        help_text="Number of views",
    )
    reading_time_min = models.PositiveSmallIntegerField(
        default=1,
        help_text="Estimated reading time in minutes",
    )
    
    # SEO
    meta_title = models.CharField(
        max_length=70,
        blank=True,
        help_text="SEO title (max 70 chars)",
    )
    meta_description = models.CharField(
        max_length=160,
        blank=True,
        help_text="SEO meta description (max 160 chars)",
    )
    
    class Meta:
        verbose_name = "blog post"
        verbose_name_plural = "blog posts"
        ordering = ["-published_at", "-created_at"]
        indexes = [
            models.Index(fields=["status", "-published_at"]),
            models.Index(fields=["is_featured", "-published_at"]),
            models.Index(fields=["category", "-published_at"]),
        ]
    
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Auto-generate slug
        if not self.slug:
            self.slug = slugify_tr(self.title)
        
        # Set published_at when publishing
        if self.status == self.Status.PUBLISHED and not self.published_at:
            self.published_at = timezone.now()
        
        # Calculate reading time (avg 200 words per minute)
        if self.content:
            word_count = len(self.content.split())
            self.reading_time_min = max(1, round(word_count / 200))
        
        super().save(*args, **kwargs)
    
    @property
    def is_published(self):
        """Check if post is published and publication date has passed."""
        if self.status != self.Status.PUBLISHED:
            return False
        if not self.published_at:
            return False
        return self.published_at <= timezone.now()
    
    def increment_view_count(self):
        """Increment view count atomically."""
        BlogPost.objects.filter(pk=self.pk).update(
            view_count=models.F("view_count") + 1
        )
