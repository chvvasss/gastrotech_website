# Generated manually for Cart models

import uuid

import django.core.validators
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("catalog", "0006_alter_media_kind"),
    ]

    operations = [
        migrations.CreateModel(
            name="Cart",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                (
                    "token",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        help_text="Unique token for anonymous cart identification",
                        unique=True,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("open", "Open"),
                            ("converted", "Converted to Order"),
                            ("abandoned", "Abandoned"),
                        ],
                        db_index=True,
                        default="open",
                        help_text="Cart status",
                        max_length=20,
                    ),
                ),
                (
                    "currency",
                    models.CharField(
                        default="TRY",
                        help_text="Cart currency code (ISO 4217)",
                        max_length=3,
                    ),
                ),
                (
                    "expires_at",
                    models.DateTimeField(
                        blank=True,
                        db_index=True,
                        help_text="Optional expiration timestamp for cleanup",
                        null=True,
                    ),
                ),
                (
                    "ip_address",
                    models.GenericIPAddressField(
                        blank=True,
                        help_text="IP address when cart was created",
                        null=True,
                    ),
                ),
                (
                    "user_agent",
                    models.TextField(
                        blank=True,
                        help_text="User agent when cart was created",
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        help_text="Owner user (null for anonymous carts)",
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="carts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "cart",
                "verbose_name_plural": "carts",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="CartItem",
            fields=[
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique identifier for this record",
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="Timestamp when this record was created",
                    ),
                ),
                (
                    "updated_at",
                    models.DateTimeField(
                        auto_now=True,
                        help_text="Timestamp when this record was last updated",
                    ),
                ),
                (
                    "quantity",
                    models.PositiveIntegerField(
                        default=1,
                        help_text="Quantity in cart",
                        validators=[django.core.validators.MinValueValidator(1)],
                    ),
                ),
                (
                    "unit_price_snapshot",
                    models.DecimalField(
                        blank=True,
                        decimal_places=2,
                        help_text="Unit price at time of adding to cart",
                        max_digits=12,
                        null=True,
                    ),
                ),
                (
                    "currency_snapshot",
                    models.CharField(
                        default="TRY",
                        help_text="Currency at time of adding to cart",
                        max_length=3,
                    ),
                ),
                (
                    "added_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        help_text="Timestamp when item was first added",
                    ),
                ),
                (
                    "cart",
                    models.ForeignKey(
                        help_text="Parent cart",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="items",
                        to="orders.cart",
                    ),
                ),
                (
                    "variant",
                    models.ForeignKey(
                        help_text="Product variant",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="cart_items",
                        to="catalog.variant",
                    ),
                ),
            ],
            options={
                "verbose_name": "cart item",
                "verbose_name_plural": "cart items",
                "ordering": ["added_at"],
            },
        ),
        # Add indexes for Cart
        migrations.AddIndex(
            model_name="cart",
            index=models.Index(fields=["user", "status"], name="orders_cart_user_id_status_idx"),
        ),
        migrations.AddIndex(
            model_name="cart",
            index=models.Index(fields=["token"], name="orders_cart_token_idx"),
        ),
        migrations.AddIndex(
            model_name="cart",
            index=models.Index(fields=["status", "expires_at"], name="orders_cart_status_expires_idx"),
        ),
        migrations.AddIndex(
            model_name="cart",
            index=models.Index(fields=["created_at"], name="orders_cart_created_at_idx"),
        ),
        # Add indexes for CartItem
        migrations.AddIndex(
            model_name="cartitem",
            index=models.Index(fields=["cart"], name="orders_cartitem_cart_idx"),
        ),
        migrations.AddIndex(
            model_name="cartitem",
            index=models.Index(fields=["variant"], name="orders_cartitem_variant_idx"),
        ),
        migrations.AddIndex(
            model_name="cartitem",
            index=models.Index(fields=["added_at"], name="orders_cartitem_added_at_idx"),
        ),
        # Add unique constraint for CartItem
        migrations.AddConstraint(
            model_name="cartitem",
            constraint=models.UniqueConstraint(
                fields=["cart", "variant"],
                name="unique_cart_variant",
            ),
        ),
    ]
