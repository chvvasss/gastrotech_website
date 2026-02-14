"""
Tests for Cart Hardening - Master Prod Plus level.

Tests cover:
- Snapshot fields on CartItem
- 409 responses for stock violations
- Idempotency for add_item and merge
- Merge dry_run mode
- Token cart security
- has_pricing_gaps in totals
- Warnings in cart response
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
from apps.orders.models import Cart, CartItem, IdempotencyRecord


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
        
        # Variant with stock=10
        self.variant_in_stock = Variant.objects.create(
            product=self.product,
            model_code="TST001",
            name_tr="Test Varyant 1",
            list_price=Decimal("100.00"),
            stock_qty=10,
        )
        
        # Variant with limited stock=3
        self.variant_limited = Variant.objects.create(
            product=self.product,
            model_code="TST002",
            name_tr="Test Varyant 2",
            list_price=Decimal("200.00"),
            stock_qty=3,
        )
        
        # Variant out of stock
        self.variant_out_of_stock = Variant.objects.create(
            product=self.product,
            model_code="TST003",
            name_tr="Test Varyant 3",
            list_price=Decimal("300.00"),
            stock_qty=0,
        )
        
        # Variant with no price (for pricing gaps)
        self.variant_no_price = Variant.objects.create(
            product=self.product,
            model_code="TST004",
            name_tr="Test Varyant 4",
            list_price=None,
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
    
    def get_idempotency_headers(self, key):
        """Get Idempotency-Key headers."""
        return {"HTTP_IDEMPOTENCY_KEY": key}


class Stock409ResponseTests(CartTestMixin, TestCase):
    """Tests for 409 Conflict responses on stock violations."""
    
    def test_add_item_returns_409_for_insufficient_stock(self):
        """Test that adding item with quantity > stock returns 409."""
        # Create cart
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        headers = self.get_cart_token_headers(cart_token)
        
        url = reverse("api_v1:orders:cart_add_item")
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_limited.id), "quantity": 5},
            format="json",
            **headers,
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "insufficient_stock")
        self.assertEqual(response.data["variant_id"], str(self.variant_limited.id))
        self.assertEqual(response.data["requested"], 5)
        self.assertEqual(response.data["available"], 3)
    
    def test_add_item_returns_409_for_out_of_stock(self):
        """Test that adding out-of-stock item returns 409."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        headers = self.get_cart_token_headers(cart_token)
        
        url = reverse("api_v1:orders:cart_add_item")
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_out_of_stock.id), "quantity": 1},
            format="json",
            **headers,
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "insufficient_stock")
        self.assertEqual(response.data["available"], 0)
    
    def test_update_quantity_returns_409_for_insufficient_stock(self):
        """Test that updating quantity beyond stock returns 409."""
        # Create cart with item
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        item = CartItem.objects.create(
            cart=cart,
            variant=self.variant_limited,
            quantity=1,
            unit_price_snapshot=self.variant_limited.list_price,
        )
        
        url = reverse("api_v1:orders:cart_item_detail", args=[item.id])
        response = self.client.patch(
            url,
            {"quantity": 10},  # More than stock_qty=3
            format="json",
            **self.get_auth_headers(),
        )
        
        self.assertEqual(response.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response.data["detail"], "insufficient_stock")
        self.assertEqual(response.data["available"], 3)
    
    def test_add_same_variant_twice_returns_409_if_exceeds_stock(self):
        """Test that incrementing quantity beyond stock returns 409."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        headers = self.get_cart_token_headers(cart_token)
        
        url = reverse("api_v1:orders:cart_add_item")
        
        # First add: 2 items (within limit of 3)
        response1 = self.client.post(
            url,
            {"variant_id": str(self.variant_limited.id), "quantity": 2},
            format="json",
            **headers,
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        
        # Second add: 2 more (total 4 > limit of 3)
        response2 = self.client.post(
            url,
            {"variant_id": str(self.variant_limited.id), "quantity": 2},
            format="json",
            **headers,
        )
        
        self.assertEqual(response2.status_code, status.HTTP_409_CONFLICT)
        self.assertEqual(response2.data["detail"], "insufficient_stock")
        self.assertEqual(response2.data["requested"], 4)  # Total would be 4
        self.assertEqual(response2.data["available"], 3)


class IdempotencyTests(CartTestMixin, TestCase):
    """Tests for idempotency header behavior."""
    
    def test_idempotency_prevents_double_add(self):
        """Test that same idempotency key prevents duplicate add."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        headers = {
            **self.get_cart_token_headers(cart_token),
            **self.get_idempotency_headers("unique-key-12345"),
        }
        
        url = reverse("api_v1:orders:cart_add_item")
        
        # First request
        response1 = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 2},
            format="json",
            **headers,
        )
        self.assertEqual(response1.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response1.data["totals"]["item_count"], 2)
        
        # Second request with same key - should return cached response
        response2 = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 2},
            format="json",
            **headers,
        )
        self.assertEqual(response2.status_code, status.HTTP_201_CREATED)
        
        # Quantity should NOT have doubled
        self.assertEqual(response2.data["totals"]["item_count"], 2)
        
        # Verify only one item in DB
        cart = Cart.objects.get(token=cart_token)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 2)
    
    def test_idempotency_record_created(self):
        """Test that idempotency record is created."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        headers = {
            **self.get_cart_token_headers(cart_token),
            **self.get_idempotency_headers("test-key-abc"),
        }
        
        url = reverse("api_v1:orders:cart_add_item")
        self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 1},
            format="json",
            **headers,
        )
        
        # Verify record was created
        cart = Cart.objects.get(token=cart_token)
        record = IdempotencyRecord.objects.get(
            key="test-key-abc",
            scope=IdempotencyRecord.Scope.CART_ADD_ITEM,
            cart=cart,
        )
        self.assertEqual(record.status_code, 201)
        self.assertIn("totals", record.response_body)
    
    def test_different_idempotency_keys_add_separately(self):
        """Test that different keys process as separate requests."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        url = reverse("api_v1:orders:cart_add_item")
        
        # First request with key-1
        headers1 = {
            **self.get_cart_token_headers(cart_token),
            **self.get_idempotency_headers("key-1"),
        }
        response1 = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 2},
            format="json",
            **headers1,
        )
        self.assertEqual(response1.data["totals"]["item_count"], 2)
        
        # Second request with key-2 (different variant)
        headers2 = {
            **self.get_cart_token_headers(cart_token),
            **self.get_idempotency_headers("key-2"),
        }
        response2 = self.client.post(
            url,
            {"variant_id": str(self.variant_limited.id), "quantity": 1},
            format="json",
            **headers2,
        )
        self.assertEqual(response2.data["totals"]["item_count"], 3)  # 2 + 1


class MergeDryRunTests(CartTestMixin, TestCase):
    """Tests for merge dry_run functionality."""
    
    def test_merge_dry_run_does_not_modify_db(self):
        """Test that dry_run=1 doesn't commit changes."""
        # Create anonymous cart with items
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_in_stock,
            quantity=3,
        )
        
        # Create user cart
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        # Merge with dry_run
        url = reverse("api_v1:orders:cart_merge") + "?dry_run=1"
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["dry_run"])
        self.assertEqual(response.data["merged_count"], 1)
        
        # Verify DB was NOT modified
        anon_cart.refresh_from_db()
        self.assertEqual(anon_cart.status, Cart.Status.OPEN)  # Not abandoned
        self.assertEqual(anon_cart.items.count(), 1)  # Items still there
        
        user_cart.refresh_from_db()
        self.assertEqual(user_cart.items.count(), 0)  # No items merged
    
    def test_merge_dry_run_returns_predicted_items(self):
        """Test that dry_run returns predicted_items."""
        # Create anonymous cart
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_in_stock,
            quantity=2,
        )
        
        # Create user cart with same variant
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=user_cart,
            variant=self.variant_in_stock,
            quantity=1,
        )
        
        # Merge with dry_run
        url = reverse("api_v1:orders:cart_merge") + "?dry_run=1"
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("predicted_items", response.data)
        
        # Should show merged quantity
        predicted = response.data["predicted_items"]
        self.assertEqual(len(predicted), 1)
        self.assertEqual(predicted[0]["quantity"], 3)  # 1 + 2
    
    def test_merge_dry_run_returns_warnings(self):
        """Test that dry_run returns warnings for stock issues."""
        # Create anonymous cart with item exceeding stock
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_limited,
            quantity=5,  # More than stock=3
        )
        
        # Create user cart
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        # Merge with dry_run
        url = reverse("api_v1:orders:cart_merge") + "?dry_run=1"
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(len(response.data["warnings"]) > 0)
        
        warning = response.data["warnings"][0]
        self.assertEqual(warning["reason"], "insufficient_stock")
        self.assertEqual(warning["requested"], 5)
        self.assertEqual(warning["available"], 3)


class MergeStockEnforcementTests(CartTestMixin, TestCase):
    """Tests for stock enforcement during merge."""
    
    def test_merge_caps_quantity_to_stock_limit(self):
        """Test that merge caps quantities to stock limit with warning."""
        # Create anonymous cart with item quantity=5
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_limited,  # stock=3
            quantity=5,
        )
        
        # Create user cart
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        # Merge
        url = reverse("api_v1:orders:cart_merge")
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        
        # Should have warning
        self.assertTrue(len(response.data["warnings"]) > 0)
        
        # Item should be capped to stock limit
        user_cart.refresh_from_db()
        item = user_cart.items.first()
        self.assertEqual(item.quantity, 3)  # Capped to stock
    
    def test_merge_skips_out_of_stock_items(self):
        """Test that out-of-stock items are skipped during merge."""
        # Create anonymous cart with out-of-stock item
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_out_of_stock,
            quantity=1,
        )
        
        # Create user cart
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        # Merge
        url = reverse("api_v1:orders:cart_merge")
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["skipped_count"], 1)
        
        # User cart should be empty
        user_cart.refresh_from_db()
        self.assertEqual(user_cart.items.count(), 0)


class SnapshotFieldsTests(CartTestMixin, TestCase):
    """Tests for CartItem snapshot fields."""
    
    def test_add_item_captures_snapshots(self):
        """Test that adding item captures all snapshot fields."""
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        url = reverse("api_v1:orders:cart_add_item")
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 1},
            format="json",
            **self.get_cart_token_headers(cart_token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        # Verify snapshots in response
        item = response.data["items"][0]
        self.assertEqual(Decimal(item["unit_price_snapshot"]), Decimal("100.00"))
        self.assertEqual(item["currency_snapshot"], "TRY")
        self.assertEqual(item["product_name_snapshot"], "Test Ürün")
        self.assertIn("TST001", item["variant_label_snapshot"])
    
    def test_snapshot_preserved_after_variant_change(self):
        """Test that snapshots are preserved even if variant changes."""
        # Create cart with item
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        item = CartItem.objects.create(
            cart=cart,
            variant=self.variant_in_stock,
            quantity=1,
            unit_price_snapshot=Decimal("100.00"),
            product_name_snapshot="Original Product Name",
            variant_label_snapshot="TST001 - Original Label",
        )
        
        # Change variant price
        self.variant_in_stock.list_price = Decimal("150.00")
        self.variant_in_stock.save()
        
        # Get cart
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url, **self.get_auth_headers())
        
        # Snapshots should still have original values
        item_data = response.data["items"][0]
        self.assertEqual(Decimal(item_data["unit_price_snapshot"]), Decimal("100.00"))
        self.assertEqual(item_data["product_name_snapshot"], "Original Product Name")


class PricingGapsTests(CartTestMixin, TestCase):
    """Tests for has_pricing_gaps in totals."""
    
    def test_has_pricing_gaps_false_when_all_priced(self):
        """Test that has_pricing_gaps is false when all items have prices."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=cart,
            variant=self.variant_in_stock,
            quantity=1,
            unit_price_snapshot=Decimal("100.00"),
        )
        
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url, **self.get_auth_headers())
        
        self.assertFalse(response.data["totals"]["has_pricing_gaps"])
    
    def test_has_pricing_gaps_true_when_missing_price(self):
        """Test that has_pricing_gaps is true when item has no price."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=cart,
            variant=self.variant_no_price,  # list_price=None
            quantity=1,
            unit_price_snapshot=None,
        )
        
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url, **self.get_auth_headers())
        
        self.assertTrue(response.data["totals"]["has_pricing_gaps"])


class CartWarningsTests(CartTestMixin, TestCase):
    """Tests for warnings in cart response."""
    
    def test_warnings_for_items_exceeding_current_stock(self):
        """Test that warnings are returned for items exceeding stock."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=cart,
            variant=self.variant_limited,
            quantity=5,  # Added when stock was higher, now stock=3
            unit_price_snapshot=Decimal("200.00"),
        )
        
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(url, **self.get_auth_headers())
        
        # Should have warning
        self.assertTrue(len(response.data["warnings"]) > 0)
        warning = response.data["warnings"][0]
        self.assertEqual(warning["reason"], "insufficient_stock")
        self.assertEqual(warning["requested"], 5)
        self.assertEqual(warning["available"], 3)


class TokenCartSecurityTests(CartTestMixin, TestCase):
    """Tests for token cart security."""
    
    def test_anonymous_cannot_access_user_cart_via_token(self):
        """Test that anonymous requests cannot access user's cart."""
        # Create cart for user
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        # Try to access via token (anonymous)
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(
            url,
            **self.get_cart_token_headers(user_cart.token),
        )
        
        # Should not find the cart
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
    
    def test_cart_requires_correct_token(self):
        """Test that cart requires correct token."""
        # Create anonymous cart
        create_url = reverse("api_v1:orders:cart_create_token")
        create_response = self.client.post(create_url)
        cart_token = create_response.data["cart_token"]
        
        # Try to access with wrong token
        url = reverse("api_v1:orders:cart_detail")
        response = self.client.get(
            url,
            **self.get_cart_token_headers(uuid.uuid4()),  # Random token
        )
        
        # Should return a different cart (newly created)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotEqual(str(response.data["token"]), str(cart_token))


class AuthenticatedMergeTests(CartTestMixin, TestCase):
    """Tests for authenticated merge scenarios."""
    
    def test_authenticated_merge_combines_quantities(self):
        """Test that merge correctly combines quantities."""
        # Create anonymous cart
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_in_stock,
            quantity=2,
        )
        
        # Create user cart with same variant
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=user_cart,
            variant=self.variant_in_stock,
            quantity=3,
        )
        
        # Merge
        url = reverse("api_v1:orders:cart_merge")
        response = self.client.post(
            url,
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
        )
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["merged_count"], 1)
        
        # Verify combined quantity
        user_cart.refresh_from_db()
        item = user_cart.items.first()
        self.assertEqual(item.quantity, 5)  # 3 + 2
        
        # Verify anonymous cart is abandoned
        anon_cart.refresh_from_db()
        self.assertEqual(anon_cart.status, Cart.Status.ABANDONED)
    
    def test_merge_idempotency(self):
        """Test that merge is idempotent with same key."""
        # Create anonymous cart
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart,
            variant=self.variant_in_stock,
            quantity=2,
        )
        
        # Create user cart
        Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        headers = {
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart.token),
            **self.get_idempotency_headers("merge-key-123"),
        }
        
        url = reverse("api_v1:orders:cart_merge")
        
        # First merge
        response1 = self.client.post(url, **headers)
        self.assertEqual(response1.status_code, status.HTTP_200_OK)
        
        # Create new anonymous cart (trying to merge again with same key)
        anon_cart2 = Cart.objects.create(status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=anon_cart2,
            variant=self.variant_limited,
            quantity=1,
        )
        
        # Second merge with same key should return cached response
        headers2 = {
            **self.get_auth_headers(),
            **self.get_cart_token_headers(anon_cart2.token),
            **self.get_idempotency_headers("merge-key-123"),
        }
        response2 = self.client.post(url, **headers2)
        
        # Should return cached response from first merge
        self.assertEqual(response2.status_code, status.HTTP_200_OK)
        self.assertEqual(response1.data["merged_count"], response2.data["merged_count"])


class AddItemNoDuplicateRowsTests(CartTestMixin, TestCase):
    """Tests that adding same variant increments quantity."""
    
    def test_add_same_variant_twice_no_duplicate_rows(self):
        """Test that adding same variant doesn't create duplicate rows."""
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
        
        # Add second time
        response = self.client.post(
            url,
            {"variant_id": str(self.variant_in_stock.id), "quantity": 3},
            format="json",
            **headers,
        )
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(len(response.data["items"]), 1)  # Still only 1 row
        self.assertEqual(response.data["items"][0]["quantity"], 5)  # 2 + 3
        
        # Verify in DB
        cart = Cart.objects.get(token=cart_token)
        self.assertEqual(cart.items.count(), 1)
        self.assertEqual(cart.items.first().quantity, 5)
