"""
Tests for admin API endpoints.
"""

import io

from django.test import TestCase
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.catalog.models import Category, Media, Product, ProductMedia, Series


class AdminMediaUploadTest(TestCase):
    """Test admin media upload API."""
    
    def setUp(self):
        """Create test user and get JWT token."""
        self.client = APIClient()
        
        # Create admin user
        self.admin_user = User.objects.create_user(
            email="admin@gastrotech.com",
            password="testpass123",
            role="admin",
        )
        
        # Create editor user
        self.editor_user = User.objects.create_user(
            email="editor@gastrotech.com",
            password="testpass123",
            role="editor",
        )
        
        # Create regular user
        self.regular_user = User.objects.create_user(
            email="user@example.com",
            password="testpass123",
            role="viewer",
        )
        
        # Create product for testing
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
    
    def get_token_for_user(self, user):
        """Generate JWT token for user."""
        refresh = RefreshToken.for_user(user)
        return str(refresh.access_token)
    
    def create_test_image(self):
        """Create a minimal valid image for testing."""
        # Create a 1x1 white PNG
        import base64
        # Minimal 1x1 white PNG
        png_data = base64.b64decode(
            "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8"
            "z8BQDwAEhQGAhKmMIQAAAABJRU5ErkJggg=="
        )
        return io.BytesIO(png_data)
    
    def test_media_upload_as_admin(self):
        """Test media upload with admin user."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        
        url = "/api/v1/admin/media/upload/"
        image_data = self.create_test_image().getvalue()
        
        # Use SimpleUploadedFile for proper content type handling
        uploaded_file = SimpleUploadedFile(
            name="test.png",
            content=image_data,
            content_type="image/png",
        )
        
        response = self.client.post(
            url,
            {"file": uploaded_file},
            format="multipart",
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("file_url", response.data)
        self.assertEqual(response.data["kind"], "image")
        
        # Verify media was created
        media = Media.objects.get(id=response.data["id"])
        self.assertEqual(media.kind, "image")
        self.assertEqual(media.content_type, "image/png")
    
    def test_media_upload_as_editor(self):
        """Test media upload with editor user."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        token = self.get_token_for_user(self.editor_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        
        url = "/api/v1/admin/media/upload/"
        image_data = self.create_test_image().getvalue()
        uploaded_file = SimpleUploadedFile(
            name="test.png",
            content=image_data,
            content_type="image/png",
        )
        
        response = self.client.post(
            url,
            {"file": uploaded_file},
            format="multipart",
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
    
    def test_media_upload_as_regular_user_forbidden(self):
        """Test that regular users cannot upload media."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        token = self.get_token_for_user(self.regular_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        
        url = "/api/v1/admin/media/upload/"
        image_data = self.create_test_image().getvalue()
        uploaded_file = SimpleUploadedFile(
            name="test.png",
            content=image_data,
            content_type="image/png",
        )
        
        response = self.client.post(
            url,
            {"file": uploaded_file},
            format="multipart",
        )
        
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
    
    def test_media_upload_unauthenticated(self):
        """Test that unauthenticated requests are rejected."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        url = "/api/v1/admin/media/upload/"
        image_data = self.create_test_image().getvalue()
        uploaded_file = SimpleUploadedFile(
            name="test.png",
            content=image_data,
            content_type="image/png",
        )
        
        response = self.client.post(
            url,
            {"file": uploaded_file},
            format="multipart",
        )
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_product_media_upload(self):
        """Test uploading media directly to a product."""
        from django.core.files.uploadedfile import SimpleUploadedFile
        
        token = self.get_token_for_user(self.admin_user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {token}")
        
        url = f"/api/v1/admin/products/{self.product.id}/media/upload/"
        image_data = self.create_test_image().getvalue()
        uploaded_file = SimpleUploadedFile(
            name="product-image.png",
            content=image_data,
            content_type="image/png",
        )
        
        response = self.client.post(
            url,
            {
                "file": uploaded_file,
                "alt": "Product image",
                "is_primary": "true",
            },
            format="multipart",
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("id", response.data)
        self.assertIn("media_id", response.data)
        self.assertTrue(response.data["is_primary"])
        
        # Verify ProductMedia was created
        pm = ProductMedia.objects.get(id=response.data["id"])
        self.assertEqual(pm.product, self.product)
        self.assertEqual(pm.alt, "Product image")
        self.assertTrue(pm.is_primary)
