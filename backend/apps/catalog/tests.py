"""
Tests for catalog app.

Includes tests for:
- Admin media upload API
- Cache invalidation
"""

import io
import json
from PIL import Image

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import TestCase, override_settings
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from .models import Category, Media, Product, ProductMedia, Series, SpecKey, Variant
from .cache_keys import nav_key, spec_keys_key, taxonomy_tree_key


User = get_user_model()


def create_test_image():
    """Create a simple test image in memory."""
    file = io.BytesIO()
    image = Image.new("RGB", (100, 100), color="red")
    image.save(file, format="JPEG")
    file.seek(0)
    file.name = "test_image.jpg"
    return file


class AdminMediaUploadTest(TestCase):
    """Test admin media upload API."""
    
    def setUp(self):
        """Create test user and get JWT token."""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@test.com",
            password="testpassword123",
            role="admin",
            is_active=True,
        )
        
        # Get JWT token
        refresh = RefreshToken.for_user(self.admin_user)
        self.access_token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {self.access_token}")
        
        # Create test product
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
    
    def test_upload_media_requires_auth(self):
        """Test that media upload requires authentication."""
        # Remove credentials
        self.client.credentials()
        
        url = "/api/v1/admin/media/upload/"
        image_file = create_test_image()
        
        response = self.client.post(url, {"file": image_file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_upload_media_requires_admin_role(self):
        """Test that media upload requires admin or editor role."""
        # Create regular user
        regular_user = User.objects.create_user(
            email="regular@test.com",
            password="testpassword123",
            role="viewer",
            is_active=True,
        )
        
        # Get token for regular user
        refresh = RefreshToken.for_user(regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
        
        url = "/api/v1/admin/media/upload/"
        image_file = create_test_image()
        
        response = self.client.post(url, {"file": image_file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_upload_media_success(self):
        """Test successful media upload."""
        url = "/api/v1/admin/media/upload/"
        image_file = create_test_image()
        
        response = self.client.post(url, {"file": image_file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("file_url", response.data)
        self.assertIn("checksum_sha256", response.data)
        
        # Verify media was created in database
        media = Media.objects.get(id=response.data["id"])
        self.assertEqual(media.kind, Media.Kind.IMAGE)
        self.assertEqual(media.content_type, "image/jpeg")
        self.assertEqual(media.width, 100)
        self.assertEqual(media.height, 100)
        self.assertIsNotNone(media.bytes)
        self.assertIsNotNone(media.checksum_sha256)
    
    def test_upload_media_file_required(self):
        """Test that file is required for upload."""
        url = "/api/v1/admin/media/upload/"
        
        response = self.client.post(url, {}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
    
    @override_settings(MAX_MEDIA_UPLOAD_BYTES=100)
    def test_upload_media_file_too_large(self):
        """Test that large files are rejected."""
        url = "/api/v1/admin/media/upload/"
        
        # Create a larger image that exceeds the limit
        file = io.BytesIO()
        image = Image.new("RGB", (200, 200), color="blue")
        image.save(file, format="JPEG")
        file.seek(0)
        file.name = "large_image.jpg"
        
        response = self.client.post(url, {"file": file}, format="multipart")
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("too large", response.data["error"].lower())
    
    def test_upload_product_media_success(self):
        """Test successful product media upload."""
        url = f"/api/v1/admin/products/{self.product.id}/media/upload/"
        image_file = create_test_image()
        
        response = self.client.post(
            url,
            {
                "file": image_file,
                "alt": "Test alt text",
                "is_primary": "true",
            },
            format="multipart",
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("media_id", response.data)
        self.assertEqual(response.data["alt"], "Test alt text")
        self.assertTrue(response.data["is_primary"])
        
        # Verify ProductMedia was created
        pm = ProductMedia.objects.get(id=response.data["id"])
        self.assertEqual(pm.product, self.product)
        self.assertTrue(pm.is_primary)
    
    def test_upload_product_media_auto_sort_order(self):
        """Test that sort_order is auto-calculated when not provided."""
        url = f"/api/v1/admin/products/{self.product.id}/media/upload/"
        
        # Upload first image
        image1 = create_test_image()
        response1 = self.client.post(url, {"file": image1}, format="multipart")
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data["sort_order"], 10)
        
        # Upload second image
        image2 = create_test_image()
        response2 = self.client.post(url, {"file": image2}, format="multipart")
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response2.data["sort_order"], 20)
    
    def test_product_media_reorder(self):
        """Test reordering product media."""
        # First upload two images
        upload_url = f"/api/v1/admin/products/{self.product.id}/media/upload/"
        
        image1 = create_test_image()
        response1 = self.client.post(upload_url, {"file": image1}, format="multipart")
        pm1_id = response1.data["id"]
        
        image2 = create_test_image()
        response2 = self.client.post(upload_url, {"file": image2}, format="multipart")
        pm2_id = response2.data["id"]
        
        # Reorder
        reorder_url = f"/api/v1/admin/products/{self.product.id}/media/reorder/"
        response = self.client.patch(
            reorder_url,
            {
                "items": [
                    {"product_media_id": pm2_id, "sort_order": 5, "is_primary": True},
                    {"product_media_id": pm1_id, "sort_order": 15},
                ]
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated"], 2)
        
        # Verify order changed
        pm1 = ProductMedia.objects.get(id=pm1_id)
        pm2 = ProductMedia.objects.get(id=pm2_id)
        
        self.assertEqual(pm1.sort_order, 15)
        self.assertFalse(pm1.is_primary)
        self.assertEqual(pm2.sort_order, 5)
        self.assertTrue(pm2.is_primary)
    
    def test_product_media_reorder_only_one_primary(self):
        """Test that only one item can be primary."""
        upload_url = f"/api/v1/admin/products/{self.product.id}/media/upload/"
        
        image1 = create_test_image()
        response1 = self.client.post(upload_url, {"file": image1}, format="multipart")
        pm1_id = response1.data["id"]
        
        image2 = create_test_image()
        response2 = self.client.post(upload_url, {"file": image2}, format="multipart")
        pm2_id = response2.data["id"]
        
        # Try to set both as primary
        reorder_url = f"/api/v1/admin/products/{self.product.id}/media/reorder/"
        response = self.client.patch(
            reorder_url,
            {
                "items": [
                    {"product_media_id": pm1_id, "is_primary": True},
                    {"product_media_id": pm2_id, "is_primary": True},
                ]
            },
            format="json",
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("error", response.data)
        self.assertIn("primary", response.data["error"].lower())
    
    def test_product_media_delete(self):
        """Test deleting product media."""
        # Upload an image
        upload_url = f"/api/v1/admin/products/{self.product.id}/media/upload/"
        image = create_test_image()
        response = self.client.post(upload_url, {"file": image}, format="multipart")
        pm_id = response.data["id"]
        media_id = response.data["media_id"]
        
        # Delete product media
        delete_url = f"/api/v1/admin/products/{self.product.id}/media/{pm_id}/"
        response = self.client.delete(delete_url)
        
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        
        # Verify ProductMedia was deleted
        self.assertFalse(ProductMedia.objects.filter(id=pm_id).exists())
        
        # Media should still exist (not auto-deleted)
        self.assertTrue(Media.objects.filter(id=media_id).exists())


class CacheInvalidationTest(TestCase):
    """Test cache invalidation on model changes."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        cache.clear()
    
    def test_nav_cache_cleared_on_category_save(self):
        """Test that nav cache is cleared when a category is saved."""
        # Prime the cache
        cache.set(nav_key(), {"test": "data"}, 300)
        self.assertIsNotNone(cache.get(nav_key()))
        
        # Create a category (triggers post_save signal)
        Category.objects.create(name="Test Category", slug="test-category")
        
        # Cache should be cleared
        self.assertIsNone(cache.get(nav_key()))
    
    def test_nav_cache_cleared_on_category_delete(self):
        """Test that nav cache is cleared when a category is deleted."""
        category = Category.objects.create(name="Test Category", slug="test-category")
        
        # Prime the cache
        cache.set(nav_key(), {"test": "data"}, 300)
        self.assertIsNotNone(cache.get(nav_key()))
        
        # Delete the category
        category.delete()
        
        # Cache should be cleared
        self.assertIsNone(cache.get(nav_key()))
    
    def test_nav_cache_cleared_on_series_save(self):
        """Test that nav cache is cleared when a series is saved."""
        category = Category.objects.create(name="Test Category", slug="test-category")
        
        # Prime the cache
        cache.set(nav_key(), {"test": "data"}, 300)
        self.assertIsNotNone(cache.get(nav_key()))
        
        # Create a series
        Series.objects.create(
            category=category,
            name="Test Series",
            slug="test-series",
        )
        
        # Cache should be cleared
        self.assertIsNone(cache.get(nav_key()))
    
    def test_spec_keys_cache_cleared_on_spec_key_save(self):
        """Test that spec keys cache is cleared when a spec key is saved."""
        # Prime the cache
        cache.set(spec_keys_key(), [{"slug": "old-key"}], 300)
        self.assertIsNotNone(cache.get(spec_keys_key()))
        
        # Create a spec key
        SpecKey.objects.create(slug="new-key", label_tr="New Key")
        
        # Cache should be cleared
        self.assertIsNone(cache.get(spec_keys_key()))
    
    def test_spec_keys_cache_cleared_on_spec_key_delete(self):
        """Test that spec keys cache is cleared when a spec key is deleted."""
        spec_key = SpecKey.objects.create(slug="test-key", label_tr="Test Key")
        
        # Prime the cache
        cache.set(spec_keys_key(), [{"slug": "test-key"}], 300)
        self.assertIsNotNone(cache.get(spec_keys_key()))
        
        # Delete the spec key
        spec_key.delete()
        
        # Cache should be cleared
        self.assertIsNone(cache.get(spec_keys_key()))
    
    def test_nav_endpoint_updates_after_series_change(self):
        """Integration test: nav response changes after series is created."""
        # First call to /nav (should be empty or minimal)
        response1 = self.client.get("/api/v1/nav/")
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        initial_count = len(response1.data)
        
        # Create category and series
        category = Category.objects.create(
            name="New Category",
            slug="new-category",
        )
        Series.objects.create(
            category=category,
            name="New Series",
            slug="new-series",
        )
        
        # Second call to /nav (should include new data)
        response2 = self.client.get("/api/v1/nav/")
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        
        # Find the new category in response
        category_found = any(c["slug"] == "new-category" for c in response2.data)
        self.assertTrue(category_found, "New category should appear in nav after creation")


class MediaAPITest(TestCase):
    """Test media file streaming endpoint."""
    
    def setUp(self):
        """Create test media."""
        self.client = APIClient()
        
        # Create a media with image data
        image_file = create_test_image()
        image_data = image_file.read()
        
        import hashlib
        self.media = Media.objects.create(
            kind=Media.Kind.IMAGE,
            filename="test.jpg",
            content_type="image/jpeg",
            bytes=image_data,
            size_bytes=len(image_data),
            width=100,
            height=100,
            checksum_sha256=hashlib.sha256(image_data).hexdigest(),
        )
    
    def test_media_file_streaming(self):
        """Test that media file can be streamed."""
        url = f"/api/v1/media/{self.media.id}/file/"
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response["Content-Type"], "image/jpeg")
        self.assertIn("ETag", response)
    
    def test_media_file_304_not_modified(self):
        """Test 304 response when ETag matches."""
        url = f"/api/v1/media/{self.media.id}/file/"
        
        # First request to get ETag
        response1 = self.client.get(url)
        etag = response1["ETag"]
        
        # Second request with If-None-Match
        response2 = self.client.get(url, HTTP_IF_NONE_MATCH=etag)
        
        self.assertEqual(response2.status_code, status.HTTP_304_NOT_MODIFIED)
