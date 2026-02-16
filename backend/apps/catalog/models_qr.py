"""
Product Info Sheet model with automatic QR code generation.

Stores uploaded PDF documents and generates QR codes
that point to the PDF's public URL.
"""

import io
import os
import uuid

import qrcode
from django.conf import settings
from django.core.files.base import ContentFile
from django.db import models

from apps.common.models import TimeStampedUUIDModel


def info_sheet_pdf_path(instance, filename):
    """Upload PDF to media/info_sheets/pdfs/<uuid>_<filename>"""
    ext = os.path.splitext(filename)[1]
    safe_name = f"{uuid.uuid4().hex[:8]}_{filename}"
    return f"info_sheets/pdfs/{safe_name}"


def info_sheet_qr_path(instance, filename):
    """Upload QR code to media/info_sheets/qrcodes/<uuid>.png"""
    return f"info_sheets/qrcodes/{filename}"


class ProductInfoSheet(TimeStampedUUIDModel):
    """
    Ürün bilgilendirme formu.

    PDF dosyası yüklendiğinde otomatik olarak QR kod üretilir.
    QR kod, PDF'nin public URL'ini encode eder.
    """

    title = models.CharField(
        max_length=200,
        help_text="Belge başlığı (örn: 'GT-600 Serisi Ürün Bilgi Formu')",
    )
    pdf_file = models.FileField(
        upload_to=info_sheet_pdf_path,
        help_text="PDF formatında ürün bilgilendirme formu",
    )
    qr_code = models.ImageField(
        upload_to=info_sheet_qr_path,
        blank=True,
        null=True,
        help_text="Otomatik üretilen QR kod (PNG)",
    )

    class Meta:
        verbose_name = "ürün bilgi formu"
        verbose_name_plural = "ürün bilgi formları"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    def get_pdf_url(self):
        """Return the full public URL for the PDF file."""
        if not self.pdf_file:
            return None
        # Build absolute URL using MEDIA_URL
        return f"{settings.MEDIA_URL}{self.pdf_file.name}"

    def generate_qr_code(self, base_url=None):
        """
        Generate a QR code PNG that encodes the PDF's URL.

        Args:
            base_url: Optional base URL prefix (e.g., 'https://example.com').
                      If not provided, uses relative media URL.
        """
        pdf_url = self.get_pdf_url()
        if not pdf_url:
            return

        # If base_url provided, create absolute URL
        if base_url:
            full_url = f"{base_url.rstrip('/')}{pdf_url}"
        else:
            full_url = pdf_url

        # Create QR code with high error correction
        qr = qrcode.QRCode(
            version=None,  # Auto-size
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=10,
            border=4,
        )
        qr.add_data(full_url)
        qr.make(fit=True)

        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")

        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)

        # Save as ImageField
        filename = f"{self.id}.png"
        self.qr_code.save(filename, ContentFile(buffer.read()), save=False)

    def save(self, *args, **kwargs):
        """Override save to auto-generate QR code when PDF changes."""
        # Check if this is a new instance or PDF has changed
        is_new = self._state.adding
        pdf_changed = False

        if not is_new:
            try:
                old = ProductInfoSheet.objects.get(pk=self.pk)
                if old.pdf_file != self.pdf_file:
                    pdf_changed = True
            except ProductInfoSheet.DoesNotExist:
                is_new = True

        # First save to get the file path
        super().save(*args, **kwargs)

        # Generate QR code if new or PDF changed
        if is_new or pdf_changed:
            self.generate_qr_code()
            # Save again to persist QR code (avoid recursion by using update)
            ProductInfoSheet.objects.filter(pk=self.pk).update(
                qr_code=self.qr_code.name
            )
