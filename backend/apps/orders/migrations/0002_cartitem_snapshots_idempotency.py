# Generated for Cart hardening

import uuid

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("orders", "0001_initial"),
    ]

    operations = [
        # Add snapshot fields to CartItem
        migrations.AddField(
            model_name="cartitem",
            name="product_name_snapshot",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Product name at time of adding (for receipts/history)",
                max_length=255,
            ),
        ),
        migrations.AddField(
            model_name="cartitem",
            name="variant_label_snapshot",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Variant label (model_code + name) at time of adding",
                max_length=255,
            ),
        ),
        # Create IdempotencyRecord model
        migrations.CreateModel(
            name="IdempotencyRecord",
            fields=[
                (
                    "id",
                    models.BigAutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                ),
                (
                    "key",
                    models.CharField(
                        db_index=True,
                        help_text="Idempotency key from client (Idempotency-Key header)",
                        max_length=255,
                    ),
                ),
                (
                    "scope",
                    models.CharField(
                        choices=[
                            ("cart:add_item", "Cart Add Item"),
                            ("cart:merge", "Cart Merge"),
                        ],
                        help_text="Operation scope",
                        max_length=32,
                    ),
                ),
                (
                    "request_hash",
                    models.CharField(
                        blank=True,
                        help_text="Hash of request payload for validation",
                        max_length=64,
                    ),
                ),
                (
                    "response_body",
                    models.JSONField(
                        default=dict,
                        help_text="Stored response for replay",
                    ),
                ),
                (
                    "status_code",
                    models.PositiveSmallIntegerField(
                        default=200,
                        help_text="HTTP status code of stored response",
                    ),
                ),
                (
                    "created_at",
                    models.DateTimeField(
                        auto_now_add=True,
                        db_index=True,
                        help_text="When this record was created",
                    ),
                ),
                (
                    "cart",
                    models.ForeignKey(
                        help_text="Associated cart",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="idempotency_records",
                        to="orders.cart",
                    ),
                ),
            ],
            options={
                "verbose_name": "idempotency record",
                "verbose_name_plural": "idempotency records",
            },
        ),
        # Add indexes for IdempotencyRecord
        migrations.AddIndex(
            model_name="idempotencyrecord",
            index=models.Index(
                fields=["key", "scope", "cart"],
                name="orders_idem_key_scope_cart_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="idempotencyrecord",
            index=models.Index(
                fields=["created_at"],
                name="orders_idem_created_idx",
            ),
        ),
        # Add unique constraint for IdempotencyRecord
        migrations.AddConstraint(
            model_name="idempotencyrecord",
            constraint=models.UniqueConstraint(
                fields=["key", "scope", "cart"],
                name="unique_idempotency_key_scope_cart",
            ),
        ),
    ]
