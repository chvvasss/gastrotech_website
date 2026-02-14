"""
Tests for Cart API endpoints.

Tests cover:
- Anonymous cart creation and token usage
- Authenticated user cart operations
- Adding items with stock validation
- Quantity updates and removal
- Cart merge functionality
- Permission/security checks
"""

import uuid
from decimal import Decimal

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken

from apps.accounts.models import User
from apps.catalog.models import Category, Product, Series, Variant
from apps.orders.models import Cart, CartItem


class CartTestMixin:
    """Mixin for setting up cart test data."""
    
    def setUp(self):
        """Set up test data."""
        self.client = APIClient()
        
        # Create test user
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
            role=User.Role.EDITOR,
        )
        
        # Create second user for permission tests
        self.other_user = User.objects.create_user(
            email="other@example.com",
            password="testpass123",
            role=User.Role.EDITOR,
        )
        
        # Create catalog data
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
            series=self.series,
            name="Test Product",
            slug="test-product",
            title_tr="Test Ürün",
            status=Product.Status.ACTIVE,
        )
        
        # Create variants with different stock levels
        self.variant_in_stock = Variant.objects.create(
            product=self.product,
            model_code="TST001",
            name_tr="Test Varyant 1",
            list_price=Decimal("100.00"),
            stock_qty=10,
        )
        self.variant_limited_stock = Variant.objects.create(
            product=self.product,
            model_code="TST002",
            name_tr="Test Varyant 2",
            list_price=Decimal("200.00"),
            stock_qty=3,
        )
        self.variant_out_of_stock = Variant.objects.create(
            product=self.product,
            model_code="TST003",
            name_tr="Test Varyant 3",
            list_price=Decimal("300.00"),
            stock_qty=0,
        )
        
        # Create inactive product variant
        self.inactive_product = Product.objects.create(
            series=self.series,
            name="Inactive Product",
            slug="inactive-product",
            title_tr="İnaktif Ürün",
            status=Product.Status.DRAFT,
        )
        self.inactive_variant = Variant.objects.create(
            product=self.inactive_product,
            model_code="TST004",
            name_tr="İnaktif Varyant",
            list_price=Decimal("150.00"),
            stock_qty=5,
        )
    
    def get_auth_headers(self, user=None):
        """Get JWT auth headers for user."""
        user = user or self.user
        refresh = RefreshToken.for_user(user)
        return {"HTTP_AUTHORIZATION": f"Bearer {refresh.access_token}"}
    
    def get_cart_token_headers(self, token):
        """Get X-Cart-Token headers."""
        return {"HTTP_X_CART_TOKEN": str(token)}


class AnonymousCartAPITests(CartTestMixin, TestCase):
    """Tests for anonymous cart operations."""
    
    def test_create_anonymous_cart_token(self):
        """Test creating an anonymous cart token."""
        url = reverse("api_v1:orders:cart_create_token")
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("cart_token", response.data)
        self.assertIn("cart", response.data)
        
        # Verify cart was created
        cart_token = response.data["cart_token"]
        cart = Cart.objects.get(token=cart_token)
        self.assertIsNone(cart.user)
        self.assertEqual(cart.status, Cart.Status.OPEN)
    
    def test_get_cart_with_token(self):
        """Test getting cart with X-Cart-Token header."""
        # First create a cart
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        # Get cart using token
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url, **self.get_cart_token_headers(cart_token))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(str(response.data["token"]), str(cart_token))
    
    def test_get_cart_without_token_fails(self):
        """Test that anonymous access without token fails."""
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
    
    def test_add_item_to_anonymous_cart(self):
        """Test adding item to anonymous cart."""
        # Create cart
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        # Add item
        url = reverse("api_v1:orders:cart_add_item")
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 2},
            format="json",
            **self.get_cart_token_headers(cart_token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["items"]), 1)
        self.assertEqual(response.data["items"][0]["quantity"], 2)
        self.assertEqual(response.data["totals"]["item_count"], 2)
    
    def test_add_same_variant_increments_quantity(self):
        """Test that adding the same variant increments quantity (no duplicate rows)."""
        # Create cart
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        headers = self.get_cart_token_headers(cart_token)
        
        url = reverse("api_v1:orders:cart_add_item")
        
        # Add first time
        self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 2},
            format="json",
            **headers,
        )
        
        # Add again
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 3},
            format="json",
            **headers,
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["items"]), 1)  # Still only 1 item row
        self.assertEqual(response.data["items"][0]["quantity"], 5)  # 2 + 3
    
    def test_add_item_respects_stock_limit(self):
        """Test that adding items respects stock limits (returns 409)."""
        # Create cart
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        headers = self.get_cart_token_headers(cart_token)
        
        url = reverse("api_v1:orders:cart_add_item")
        
        # Try to add more than stock
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_limited_stock.id), "quantity": 5},
            format="json",
            **headers,
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "insufficient_stock")
        self.assertEqual(response.data["available"], 3)
    
    def test_add_out_of_stock_item_fails(self):
        """Test that adding out-of-stock item fails (returns 409)."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        url = reverse("api_v1:orders:cart_add_item")
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_out_of_stock.id), "quantity": 1},
            format="json",
            **self.get_cart_token_headers(cart_token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "insufficient_stock")
    
    def test_add_inactive_product_variant_fails(self):
        """Test that adding variant of inactive product fails."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        url = reverse("api_v1:orders:cart_add_item")
        response = self.client.post(
            url,
            {"variant_id": str(self.inactive_variant.id), "quantity": 1},
            format="json",
            **self.get_cart_token_headers(cart_token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("not active", response.data["detail"].lower())


class AuthenticatedCartAPITests(CartTestMixin, TestCase):
    """Tests for authenticated user cart operations."""
    
    def test_get_cart_creates_for_user(self):
        """Test getting cart creates one for authenticated user."""
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url, **self.get_auth_headers())
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_anonymous"])
        
        # Verify cart was created for user
        cart = Cart.objects.get(user=self.user)
        self.assertEqual(cart.status, Cart.Status.OPEN)
    
    def test_user_gets_same_cart_on_multiple_requests(self):
        """Test that user gets the same cart on multiple requests."""
        url = reverse("api_v1:orders:cart_detail")
        
        response1 = self.client.get(url, **self.get_auth_headers())
        cart_id_1 = response1.data["id"]
        
        response2 = self.client.get(url, **self.get_auth_headers())
        cart_id_2 = response2.data["id"]
        
        self.assertEqual(cart_id_1, cart_id_2)
    
    def test_add_item_for_authenticated_user(self):
        """Test adding item for authenticated user."""
        url = reverse("api_v1:orders:cart_add_item")
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 1},
            format="json",
            **self.get_auth_headers(),
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["totals"]["item_count"], 1)


class CartItemOperationsTests(CartTestMixin, TestCase):
    """Tests for cart item update and removal operations."""
    
    def setUp(self):
        super().setUp()
        # Create a cart with items
        self.cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        self.cart_item = CartItem.objects.create(
            cart=self.cart,
            variant=self.variant_in_stock,
            quantity=2,
            unit_price_snapshot=self.variant_in_stock.list_price,
        )
    
    def test_update_item_quantity(self):
        """Test updating cart item quantity."""
        url = reverse("api_v1:orders:cart_item_detail", args=[self.cart_item.id])
        response = self.client.patch(
            url,
            {"quantity": 5},
            format="json",
            **self.get_auth_headers(),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Verify update
        self.cart_item.refresh_from_db()
        self.assertEqual(self.cart_item.quantity, 5)
    
    def test_set_quantity_zero_removes_item(self):
        """Test that setting quantity to 0 removes the item."""
        url = reverse("api_v1:orders:cart_item_detail", args=[self.cart_item.id])
        response = self.client.patch(
            url,
            {"quantity": 0},
            format="json",
            **self.get_auth_headers(),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)
        
        # Verify deletion
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())
    
    def test_delete_item(self):
        """Test deleting cart item."""
        url = reverse("api_v1:orders:cart_item_detail", args=[self.cart_item.id])
        response = self.client.delete(url, **self.get_auth_headers())
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(CartItem.objects.filter(id=self.cart_item.id).exists())
    
    def test_clear_cart(self):
        """Test clearing all items from cart."""
        # Add another item
        CartItem.objects.create(
            cart=self.cart,
            variant=self.variant_limited_stock,
            quantity=1,
        )
        
        url = reverse("api_v1:orders:cart_clear")
        response = self.client.delete(url, **self.get_auth_headers())
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["items"]), 0)
        self.assertEqual(self.cart.items.count(), 0)


class CartMergeTests(CartTestMixin, TestCase):
    """Tests for merging anonymous cart into user cart."""
    
    def test_merge_anonymous_cart_into_user_cart(self):
        """Test merging anonymous cart into authenticated user's cart."""
        # Create anonymous cart with items
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_in_stock,
            quantity=2,
        )
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_limited_stock,
            quantity=1,
        )
        
        # Create user cart with one item
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=user_cart,
            variant=self.variant_in_stock,  # Same as anonymous cart
            quantity=1,
        )
        
        # Merge
        url = reverse("api_v1:orders:cart_merge")
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["merged_count"], 2)
        
        # Verify user cart has merged items
        user_cart.refresh_from_db()
        self.assertEqual(user_cart.items.count(), 2)
        
        # Verify quantities were added for same variant
        merged_item = user_cart.items.get(variant=self.variant_in_stock)
        self.assertEqual(merged_item.quantity, 3)  # 1 + 2
        
        # Verify anonymous cart is abandoned
        anon_cart.refresh_from_db()
        self.assertEqual(anon_cart.status, Cart.Status.ABANDONED)
    
    def test_merge_requires_authentication(self):
        """Test that merge endpoint requires authentication."""
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        
        url = reverse("api_v1:orders:cart_merge")
        response = self.client.post(
            url,
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        # Should require auth
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_merge_requires_cart_token(self):
        """Test that merge endpoint requires X-Cart-Token header."""
        url = reverse("api_v1:orders:cart_merge")
        response = self.client.post(url, **self.get_auth_headers())
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class CartPermissionTests(CartTestMixin, TestCase):
    """Tests for cart permission and security."""
    
    def test_cannot_access_other_users_cart_via_token(self):
        """Test that a user cannot access another user's cart via token."""
        # Create a cart for other_user
        other_cart = Cart.objects.create(user=self.other_user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=other_cart,
            variant=self.variant_in_stock,
            quantity=5,
        )
        
        # Try to access using token
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(
            url,
            **self.get_cart_token_headers(other_cart.token),
        )
        
        # Should not find the cart (security) - returns 404 for security
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_authenticated_user_cannot_merge_others_anonymous_cart(self):
        """Test that users can only merge truly anonymous carts."""
        # Create a cart belonging to other_user
        other_cart = Cart.objects.create(user=self.other_user, status=Cart.Status.OPEN)
        
        # Try to merge it as self.user
        url = reverse("api_v1:orders:cart_merge")
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(other_cart.token),
        )
        
        # Should not find the cart (it's not anonymous)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class CartTotalsTests(CartTestMixin, TestCase):
    """Tests for cart total calculations."""
    
    def test_cart_totals_calculation(self):
        """Test that cart totals are calculated correctly."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=cart,
            variant=self.variant_in_stock,
            quantity=2,
            unit_price_snapshot=Decimal("100.00"),
        )
        CartItem.objects.create(
            cart=cart,
            variant=self.variant_limited_stock,
            quantity=3,
            unit_price_snapshot=Decimal("200.00"),
        )
        
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url, **self.get_auth_headers())
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # 2 * 100 + 3 * 200 = 800
        self.assertEqual(Decimal(response.data["totals"]["subtotal"]), Decimal("800.00"))
        self.assertEqual(response.data["totals"]["item_count"], 5)  # 2 + 3
        self.assertEqual(response.data["totals"]["line_count"], 2)
