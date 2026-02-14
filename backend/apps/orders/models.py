"""
Order models for B2B order management.

This module contains models for managing shopping carts and order items.
The architecture is payment-ready with planned support for:
- Cart management (anonymous and authenticated)
- Order status tracking
- Payment intent integration (Stripe-ready)
- Invoice generation

Cart System:
- Cart: Shopping cart with support for both anonymous (token-based) and authenticated users
- CartItem: Line items with variant reference, quantity, price snapshot

Idempotency:
- IdempotencyRecord: Prevents duplicate operations via Idempotency-Key header
"""

import uuid
from datetime import timedelta
from decimal import Decimal

from django.conf import settings
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

from apps.common.models import TimeStampedUUIDModel


class IdempotencyRecord(models.Model):
    """
    Record for idempotent operations.
    
    Prevents duplicate operations (e.g., double-add, double-merge) by tracking
    operation keys and storing responses for replay.
    
    Lifecycle:
    - Records are valid for 24 hours from creation
    - Expired records can be cleaned up by a scheduled task
    """
    
    class Scope(models.TextChoices):
        CART_ADD_ITEM = "cart:add_item", "Cart Add Item"
        CART_MERGE = "cart:merge", "Cart Merge"
    
    key = models.CharField(
        max_length=255,
        db_index=True,
        help_text="Idempotency key from client (Idempotency-Key header)",
    )
    scope = models.CharField(
        max_length=32,
        choices=Scope.choices,
        help_text="Operation scope",
    )
    cart = models.ForeignKey(
        "Cart",
        on_delete=models.CASCADE,
        related_name="idempotency_records",
        help_text="Associated cart",
    )
    request_hash = models.CharField(
        max_length=64,
        blank=True,
        help_text="Hash of request payload for validation",
    )
    response_body = models.JSONField(
        default=dict,
        help_text="Stored response for replay",
    )
    status_code = models.PositiveSmallIntegerField(
        default=200,
        help_text="HTTP status code of stored response",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True,
        help_text="When this record was created",
    )
    
    class Meta:
        verbose_name = "idempotency record"
        verbose_name_plural = "idempotency records"
        constraints = [
            models.UniqueConstraint(
                fields=["key", "scope", "cart"],
                name="unique_idempotency_key_scope_cart",
            ),
        ]
        indexes = [
            models.Index(fields=["key", "scope", "cart"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        return f"{self.scope}:{self.key[:16]}... (cart={self.cart_id})"
    
    @property
    def is_expired(self) -> bool:
        """Check if record is older than 24 hours."""
        return timezone.now() > self.created_at + timedelta(hours=24)
    
    @classmethod
    def cleanup_expired(cls) -> int:
        """Delete records older than 24 hours. Returns count deleted."""
        cutoff = timezone.now() - timedelta(hours=24)
        deleted, _ = cls.objects.filter(created_at__lt=cutoff).delete()
        return deleted


class Cart(TimeStampedUUIDModel):
    """
    Shopping cart model.
    
    Supports both anonymous users (identified by token) and authenticated users.
    A user can have only one open cart at a time (enforced in service layer).
    
    For anonymous users:
    - user is NULL
    - token is used for identification via X-Cart-Token header
    
    For authenticated users:
    - user is set
    - token is still generated (useful for merge operations)
    
    Payment-ready fields:
    - currency: Cart currency (default TRY)
    - expires_at: Optional expiration for abandoned cart cleanup
    """
    
    class Status(models.TextChoices):
        OPEN = "open", "Open"
        CONVERTED = "converted", "Converted to Order"
        ABANDONED = "abandoned", "Abandoned"
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="carts",
        help_text="Owner user (null for anonymous carts)",
    )
    token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        db_index=True,
        help_text="Unique token for anonymous cart identification",
    )
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.OPEN,
        db_index=True,
        help_text="Cart status",
    )
    currency = models.CharField(
        max_length=3,
        default="TRY",
        help_text="Cart currency code (ISO 4217)",
    )
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        db_index=True,
        help_text="Optional expiration timestamp for cleanup",
    )
    
    # Metadata for analytics
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        help_text="IP address when cart was created",
    )
    user_agent = models.TextField(
        blank=True,
        help_text="User agent when cart was created",
    )
    
    class Meta:
        verbose_name = "cart"
        verbose_name_plural = "carts"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "status"]),
            models.Index(fields=["token"]),
            models.Index(fields=["status", "expires_at"]),
            models.Index(fields=["created_at"]),
        ]
    
    def __str__(self):
        if self.user:
            return f"Cart {self.token.hex[:8]} ({self.user.email}) - {self.status}"
        return f"Cart {self.token.hex[:8]} (anonymous) - {self.status}"
    
    @property
    def is_open(self) -> bool:
        """Check if cart is in open state."""
        return self.status == self.Status.OPEN
    
    @property
    def item_count(self) -> int:
        """Total number of items in cart (sum of quantities)."""
        return sum(item.quantity for item in self.items.all())
    
    @property
    def subtotal(self) -> Decimal:
        """
        Calculate cart subtotal.
        
        Uses unit_price_snapshot if available, otherwise falls back to variant price.
        """
        total = Decimal("0.00")
        for item in self.items.select_related("variant"):
            price = item.unit_price_snapshot or item.variant.get_display_price() or Decimal("0.00")
            total += price * item.quantity
        return total
    
    def compute_totals(self) -> dict:
        """
        Compute cart totals with detailed breakdown.
        
        Returns:
            dict with subtotal, item_count, line_count, currency, has_pricing_gaps
        """
        items = self.items.select_related("variant")
        subtotal = Decimal("0.00")
        item_count = 0
        has_pricing_gaps = False
        
        for item in items:
            price = item.unit_price_snapshot or item.variant.get_display_price()
            if price is None:
                has_pricing_gaps = True
                price = Decimal("0.00")
            subtotal += price * item.quantity
            item_count += item.quantity
        
        return {
            "subtotal": subtotal,
            "item_count": item_count,
            "line_count": items.count(),
            "currency": self.currency,
            "has_pricing_gaps": has_pricing_gaps,
        }


class CartItem(TimeStampedUUIDModel):
    """
    Individual item in a shopping cart.
    
    References a ProductVariant and stores quantity and price snapshot.
    
    Price snapshot is taken at the time of adding to cart to ensure
    consistent pricing even if variant price changes.
    
    Snapshot fields (payment-ready):
    - unit_price_snapshot: Price at time of add
    - currency_snapshot: Currency code at time of add
    - product_name_snapshot: Product name for historical reference
    - variant_label_snapshot: Variant display label for receipts
    
    Constraints:
    - Unique (cart, variant) to prevent duplicate rows
    - Quantity must be positive
    """
    
    cart = models.ForeignKey(
        Cart,
        on_delete=models.CASCADE,
        related_name="items",
        help_text="Parent cart",
    )
    variant = models.ForeignKey(
        "catalog.Variant",
        on_delete=models.CASCADE,
        related_name="cart_items",
        help_text="Product variant",
    )
    quantity = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="Quantity in cart",
    )
    unit_price_snapshot = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        help_text="Unit price at time of adding to cart",
    )
    currency_snapshot = models.CharField(
        max_length=3,
        default="TRY",
        help_text="Currency at time of adding to cart",
    )
    product_name_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Product name at time of adding (for receipts/history)",
    )
    variant_label_snapshot = models.CharField(
        max_length=255,
        blank=True,
        default="",
        help_text="Variant label (model_code + name) at time of adding",
    )
    added_at = models.DateTimeField(
        auto_now_add=True,
        help_text="Timestamp when item was first added",
    )
    
    class Meta:
        verbose_name = "cart item"
        verbose_name_plural = "cart items"
        ordering = ["added_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_cart_variant",
            ),
        ]
        indexes = [
            models.Index(fields=["cart"]),
            models.Index(fields=["variant"]),
            models.Index(fields=["added_at"]),
        ]
    
    def __str__(self):
        return f"{self.variant.model_code} x {self.quantity}"
    
    @property
    def line_total(self) -> Decimal:
        """Calculate line total (unit price * quantity)."""
        price = self.unit_price_snapshot or self.variant.get_display_price() or Decimal("0.00")
        return price * self.quantity
    
    def save(self, *args, **kwargs):
        """Capture snapshots if not set."""
        if self.variant_id:
            # Capture price snapshot
            if self.unit_price_snapshot is None:
                self.unit_price_snapshot = self.variant.get_display_price()
            
            # Capture product name snapshot
            if not self.product_name_snapshot:
                self.product_name_snapshot = (
                    self.variant.product.title_tr 
                    or self.variant.product.name 
                    or ""
                )[:255]
            
            # Capture variant label snapshot
            if not self.variant_label_snapshot:
                label_parts = [self.variant.model_code]
                if self.variant.name_tr:
                    label_parts.append(self.variant.name_tr)
                self.variant_label_snapshot = " - ".join(label_parts)[:255]
        
        super().save(*args, **kwargs)
