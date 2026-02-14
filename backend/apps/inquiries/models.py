"""
Inquiry model for B2B lead management.

Captures "Teklif İste" (Request Quote) form submissions.
"""

from django.db import models

from apps.common.models import TimeStampedUUIDModel


class Inquiry(TimeStampedUUIDModel):
    """
    B2B inquiry / lead capture model.
    
    Stores contact information and product interest for follow-up.
    """
    
    class Status(models.TextChoices):
        NEW = "new", "New"
        IN_PROGRESS = "in_progress", "In Progress"
        CLOSED = "closed", "Closed"
    
    # Contact information
    full_name = models.CharField(
        max_length=200,
        help_text="Full name of the inquirer",
    )
    email = models.EmailField(
        help_text="Email address",
    )
    phone = models.CharField(
        max_length=30,
        blank=True,
        help_text="Phone number",
    )
    company = models.CharField(
        max_length=200,
        blank=True,
        help_text="Company name",
    )
    message = models.TextField(
        blank=True,
        help_text="Inquiry message",
    )
    
    # Product references
    product = models.ForeignKey(
        "catalog.Product",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        help_text="Related product (if any)",
    )
    variant = models.ForeignKey(
        "catalog.Variant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiries",
        help_text="Related variant (if any)",
    )
    
    # Snapshot fields (preserved even if product/variant is deleted)
    product_slug_snapshot = models.CharField(
        max_length=255,
        blank=True,
        help_text="Product slug at time of inquiry",
    )
    model_code_snapshot = models.CharField(
        max_length=32,
        blank=True,
        help_text="Model code at time of inquiry",
    )
    
    # Tracking
    source_url = models.URLField(
        blank=True,
        help_text="URL where the inquiry was submitted from",
    )
    utm_source = models.CharField(
        max_length=100,
        blank=True,
        help_text="UTM source parameter",
    )
    utm_medium = models.CharField(
        max_length=100,
        blank=True,
        help_text="UTM medium parameter",
    )
    utm_campaign = models.CharField(
        max_length=100,
        blank=True,
        help_text="UTM campaign parameter",
    )
    
    # Status management
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.NEW,
        db_index=True,
        help_text="Inquiry status",
    )
    internal_note = models.TextField(
        blank=True,
        help_text="Internal notes (not visible to customer)",
    )
    
    class Meta:
        verbose_name = "inquiry"
        verbose_name_plural = "inquiries"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["status"]),
            models.Index(fields=["-created_at"]),
            models.Index(fields=["email"]),
        ]
    
    def __str__(self):
        product_info = ""
        if self.product_slug_snapshot:
            product_info = f" - {self.product_slug_snapshot}"
        if self.model_code_snapshot:
            product_info = f" - {self.model_code_snapshot}"
        return f"{self.full_name} ({self.email}){product_info}"
    
    def save(self, *args, **kwargs):
        """Snapshot product/variant identifiers on save."""
        # Snapshot product slug
        if self.product and not self.product_slug_snapshot:
            self.product_slug_snapshot = self.product.slug
        
        # Snapshot model code
        if self.variant and not self.model_code_snapshot:
            self.model_code_snapshot = self.variant.model_code
        
        super().save(*args, **kwargs)
    
    @property
    def items_count(self):
        """Return count of inquiry items."""
        return self.items.count()
    
    @property
    def items_summary(self):
        """Return summary of first 3 items."""
        items = self.items.all()[:3]
        codes = [item.model_code_snapshot or "?" for item in items]
        summary = ", ".join(codes)
        total = self.items.count()
        if total > 3:
            summary += f" (+{total - 3} more)"
        return summary


class InquiryItem(models.Model):
    """
    Individual item in a multi-item quote request.
    
    Stores each product/variant requested with quantity.
    """
    
    inquiry = models.ForeignKey(
        Inquiry,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Parent inquiry",
    )
    variant = models.ForeignKey(
        "catalog.Variant",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="inquiry_items",
        help_text="Related variant (if exists)",
    )
    qty = models.PositiveIntegerField(
        default=1,
        help_text="Quantity requested",
    )
    
    # Snapshot fields (preserved even if variant is deleted)
    product_slug_snapshot = models.CharField(
        max_length=255,
        blank=True,
        help_text="Product slug at time of inquiry",
    )
    product_title_tr_snapshot = models.CharField(
        max_length=200,
        blank=True,
        help_text="Product Turkish title at time of inquiry",
    )
    series_slug_snapshot = models.CharField(
        max_length=160,
        blank=True,
        help_text="Series slug at time of inquiry",
    )
    model_code_snapshot = models.CharField(
        max_length=32,
        blank=True,
        help_text="Model code at time of inquiry",
    )
    model_name_tr_snapshot = models.CharField(
        max_length=200,
        blank=True,
        help_text="Model Turkish name at time of inquiry",
    )
    
    class Meta:
        verbose_name = "inquiry item"
        verbose_name_plural = "inquiry items"
        ordering = ["id"]
    
    def __str__(self):
        return f"{self.model_code_snapshot or '?'} x{self.qty}"
    
    def save(self, *args, **kwargs):
        """Snapshot variant data on save."""
        if self.variant:
            if not self.model_code_snapshot:
                self.model_code_snapshot = self.variant.model_code
            if not self.model_name_tr_snapshot:
                self.model_name_tr_snapshot = self.variant.name_tr
            if self.variant.product:
                if not self.product_slug_snapshot:
                    self.product_slug_snapshot = self.variant.product.slug
                if not self.product_title_tr_snapshot:
                    self.product_title_tr_snapshot = self.variant.product.title_tr
                if self.variant.product.series:
                    if not self.series_slug_snapshot:
                        self.series_slug_snapshot = self.variant.product.series.slug
        
        super().save(*args, **kwargs)
