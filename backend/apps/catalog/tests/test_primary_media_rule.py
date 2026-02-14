"""
Tests for primary media constraint (only one primary image per product).
"""

from django.core.exceptions import ValidationError
from django.test import TestCase

from apps.catalog.models import (
    Category,
    Media,
    Product,
    ProductMedia,
    Series,
)


class PrimaryMediaRuleTest(TestCase):
    """Test that only one primary image is allowed per product."""
    
    def setUp(self):
        """Create test data."""
        self.category = Category.objects.create(
            name="Test Category",
            slug="test-category",
        )
        self.series = Series.objects.create(
            category=self.category,
            name="Test Series",
            slug="test-series",
        )
        self.product = Product.objects.create(
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            series=self.series,
        )
        
        # Create test media
        self.media1 = Media.objects.create(
            kind="image",
            filename="image1.jpg",
            content_type="image/jpeg",
            bytes=b"fake image data 1",
            width=800,
            height=600,
        )
        self.media2 = Media.objects.create(
            kind="image",
            filename="image2.jpg",
            content_type="image/jpeg",
            bytes=b"fake image data 2",
            width=800,
            height=600,
        )
        self.media3 = Media.objects.create(
            kind="image",
            filename="image3.jpg",
            content_type="image/jpeg",
            bytes=b"fake image data 3",
            width=800,
            height=600,
        )
    
    def test_single_primary_allowed(self):
        """One primary image should be allowed."""
        pm = ProductMedia.objects.create(
            product=self.product,
            media=self.media1,
            is_primary=True,
        )
        
        self.assertTrue(pm.is_primary)
        self.assertEqual(
            ProductMedia.objects.filter(
                product=self.product, is_primary=True
            ).count(),
            1,
        )
    
    def test_setting_new_primary_unsets_old(self):
        """Setting a new primary should unset the old primary."""
        pm1 = ProductMedia.objects.create(
            product=self.product,
            media=self.media1,
            is_primary=True,
        )
        
        # Create second image as primary
        pm2 = ProductMedia.objects.create(
            product=self.product,
            media=self.media2,
            is_primary=True,
        )
        
        # Refresh from database
        pm1.refresh_from_db()
        
        # pm1 should no longer be primary
        self.assertFalse(pm1.is_primary)
        self.assertTrue(pm2.is_primary)
        
        # Only one primary should exist
        self.assertEqual(
            ProductMedia.objects.filter(
                product=self.product, is_primary=True
            ).count(),
            1,
        )
    
    def test_non_primary_images_allowed(self):
        """Multiple non-primary images should be allowed."""
        pm1 = ProductMedia.objects.create(
            product=self.product,
            media=self.media1,
            is_primary=False,
        )
        pm2 = ProductMedia.objects.create(
            product=self.product,
            media=self.media2,
            is_primary=False,
        )
        pm3 = ProductMedia.objects.create(
            product=self.product,
            media=self.media3,
            is_primary=False,
        )
        
        self.assertEqual(self.product.product_media.count(), 3)
        self.assertEqual(
            ProductMedia.objects.filter(
                product=self.product, is_primary=False
            ).count(),
            3,
        )
    
    def test_primary_image_property(self):
        """Test Product.primary_image property returns correct image."""
        # No images - should return None
        self.assertIsNone(self.product.primary_image)
        
        # Add non-primary image
        pm1 = ProductMedia.objects.create(
            product=self.product,
            media=self.media1,
            sort_order=2,
            is_primary=False,
        )
        
        # Should return first by sort_order as fallback
        self.assertEqual(self.product.primary_image, self.media1)
        
        # Add primary image
        pm2 = ProductMedia.objects.create(
            product=self.product,
            media=self.media2,
            sort_order=1,
            is_primary=True,
        )
        
        # Should return actual primary
        self.assertEqual(self.product.primary_image, self.media2)
    
    def test_clean_validation(self):
        """Test that clean() raises ValidationError for duplicate primary."""
        ProductMedia.objects.create(
            product=self.product,
            media=self.media1,
            is_primary=True,
        )
        
        # Create second primary without saving
        pm2 = ProductMedia(
            product=self.product,
            media=self.media2,
            is_primary=True,
        )
        
        # clean() should raise ValidationError
        with self.assertRaises(ValidationError):
            pm2.clean()
    
    def test_sort_order_respected(self):
        """Test that sort_order is respected for fallback."""
        pm1 = ProductMedia.objects.create(
            product=self.product,
            media=self.media1,
            sort_order=3,
        )
        pm2 = ProductMedia.objects.create(
            product=self.product,
            media=self.media2,
            sort_order=1,
        )
        pm3 = ProductMedia.objects.create(
            product=self.product,
            media=self.media3,
            sort_order=2,
        )
        
        # Should return media2 (lowest sort_order)
        self.assertEqual(self.product.primary_image, self.media2)


class MediaChecksumTest(TestCase):
    """Test media checksum computation."""
    
    def test_checksum_computed_on_save(self):
        """Checksum should be computed automatically on save."""
        data = b"test binary data for checksum"
        expected_checksum = Media.compute_sha256(data)
        
        media = Media.objects.create(
            kind="image",
            filename="test.jpg",
            content_type="image/jpeg",
            bytes=data,
        )
        
        self.assertEqual(media.checksum_sha256, expected_checksum)
        self.assertEqual(media.size_bytes, len(data))
    
    def test_checksum_changes_with_data(self):
        """Different data should produce different checksums."""
        data1 = b"data one"
        data2 = b"data two"
        
        media1 = Media.objects.create(
            kind="image",
            filename="test1.jpg",
            content_type="image/jpeg",
            bytes=data1,
        )
        media2 = Media.objects.create(
            kind="image",
            filename="test2.jpg",
            content_type="image/jpeg",
            bytes=data2,
        )
        
        self.assertNotEqual(media1.checksum_sha256, media2.checksum_sha256)
