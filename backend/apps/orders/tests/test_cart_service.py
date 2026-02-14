"""
Tests for CartService business logic.

Tests cover:
- Cart resolution logic
- Item operations with concurrency
- Merge logic
- Stock validation
"""

import uuid
from decimal import Decimal

from django.test import TestCase, TransactionTestCase
from django.db import transaction

from apps.accounts.models import User
from apps.catalog.models import Category, Product, Series, Variant
from apps.orders.models import Cart, CartItem
from apps.orders.services.cart_service import (
    CartItemNotFoundError,
    CartNotOpenError,
    CartService,
    CartServiceError,
    InsufficientStockError,
    InvalidQuantityError,
    VariantNotActiveError,
    VariantNotFoundError,
)


class CartServiceTestCase(TestCase):
    """Tests for CartService methods."""
    
    def setUp(self):
        """Set up test data."""
        self.user = User.objects.create_user(
            email="test@example.com",
            password="testpass123",
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
        self.variant = Variant.objects.create(
            product=self.product,
            model_code="TST001",
            name_tr="Test Varyant",
            list_price=Decimal("100.00"),
            stock_qty=10,
        )
        self.variant_limited = Variant.objects.create(
            product=self.product,
            model_code="TST002",
            name_tr="Limited Varyant",
            list_price=Decimal("200.00"),
            stock_qty=2,
        )
    
    def test_resolve_cart_creates_for_authenticated_user(self):
        """Test that resolve_cart creates cart for authenticated user."""
        cart = CartService.resolve_cart(user=self.user)
        
        self.assertIsNotNone(cart)
        self.assertEqual(cart.user, self.user)
        self.assertEqual(cart.status, Cart.Status.OPEN)
    
    def test_resolve_cart_returns_existing_user_cart(self):
        """Test that resolve_cart returns existing open cart for user."""
        existing_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        cart = CartService.resolve_cart(user=self.user)
        
        self.assertEqual(cart.id, existing_cart.id)
    
    def test_resolve_cart_creates_for_anonymous_with_token(self):
        """Test creating anonymous cart with provided token."""
        token = uuid.uuid4()
        cart = CartService.resolve_cart(cart_token=token)
        
        self.assertIsNotNone(cart)
        self.assertIsNone(cart.user)
        self.assertEqual(cart.token, token)
    
    def test_create_anonymous_cart(self):
        """Test creating a new anonymous cart."""
        cart = CartService.create_anonymous_cart()
        
        self.assertIsNotNone(cart)
        self.assertIsNone(cart.user)
        self.assertEqual(cart.status, Cart.Status.OPEN)
    
    def test_add_item_creates_cart_item(self):
        """Test adding item to cart."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        item = CartService.add_item(cart, self.variant.id, quantity=3)
        
        self.assertIsNotNone(item)
        self.assertEqual(item.quantity, 3)
        self.assertEqual(item.variant, self.variant)
        self.assertEqual(item.unit_price_snapshot, self.variant.list_price)
    
    def test_add_item_increments_existing(self):
        """Test that adding same variant increments quantity."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        CartService.add_item(cart, self.variant.id, quantity=2)
        item = CartService.add_item(cart, self.variant.id, quantity=3)
        
        self.assertEqual(item.quantity, 5)
        self.assertEqual(cart.items.count(), 1)  # No duplicate rows
    
    def test_add_item_validates_stock(self):
        """Test that add_item respects stock limits."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        with self.assertRaises(InsufficientStockError) as ctx:
            CartService.add_item(cart, self.variant_limited.id, quantity=5)
        
        self.assertEqual(ctx.exception.available, 2)
        self.assertEqual(ctx.exception.requested, 5)
        self.assertEqual(ctx.exception.variant_id, self.variant_limited.id)
    
    def test_add_item_validates_variant_exists(self):
        """Test that add_item validates variant existence."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        with self.assertRaises(VariantNotFoundError):
            CartService.add_item(cart, uuid.uuid4(), quantity=1)
    
    def test_add_item_validates_product_active(self):
        """Test that add_item validates product is active."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        # Create inactive product variant
        inactive_product = Product.objects.create(
            series=self.series,
            name="Inactive",
            slug="inactive",
            title_tr="İnaktif",
            status=Product.Status.DRAFT,
        )
        inactive_variant = Variant.objects.create(
            product=inactive_product,
            model_code="INV001",
            name_tr="İnaktif Varyant",
            stock_qty=5,
        )
        
        with self.assertRaises(VariantNotActiveError):
            CartService.add_item(cart, inactive_variant.id, quantity=1)
    
    def test_add_item_validates_quantity_positive(self):
        """Test that add_item validates positive quantity."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        with self.assertRaises(InvalidQuantityError):
            CartService.add_item(cart, self.variant.id, quantity=0)
        
        with self.assertRaises(InvalidQuantityError):
            CartService.add_item(cart, self.variant.id, quantity=-1)
    
    def test_add_item_validates_cart_open(self):
        """Test that add_item validates cart is open."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.CONVERTED)
        
        with self.assertRaises(CartNotOpenError):
            CartService.add_item(cart, self.variant.id, quantity=1)
    
    def test_set_item_quantity(self):
        """Test updating item quantity."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        item = CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        
        updated = CartService.set_item_quantity(cart, item.id, quantity=5)
        
        self.assertEqual(updated.quantity, 5)
    
    def test_set_item_quantity_zero_removes(self):
        """Test that setting quantity to 0 removes item."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        item = CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        
        result = CartService.set_item_quantity(cart, item.id, quantity=0)
        
        self.assertIsNone(result)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())
    
    def test_remove_item(self):
        """Test removing item from cart."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        item = CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        
        removed = CartService.remove_item(cart, item.id)
        
        self.assertTrue(removed)
        self.assertFalse(CartItem.objects.filter(id=item.id).exists())
    
    def test_clear_cart(self):
        """Test clearing all items from cart."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(cart=cart, variant=self.variant, quantity=2)
        CartItem.objects.create(cart=cart, variant=self.variant_limited, quantity=1)
        
        count = CartService.clear_cart(cart)
        
        self.assertEqual(count, 2)
        self.assertEqual(cart.items.count(), 0)
    
    def test_merge_carts(self):
        """Test merging two carts."""
        source = Cart.objects.create(status=Cart.Status.OPEN)
        target = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        CartItem.objects.create(cart=source, variant=self.variant, quantity=2)
        CartItem.objects.create(cart=target, variant=self.variant, quantity=1)
        CartItem.objects.create(cart=source, variant=self.variant_limited, quantity=1)
        
        result = CartService.merge_carts(source, target)
        
        self.assertEqual(result["merged_count"], 2)
        
        # Check target has merged items
        target_items = target.items.all()
        self.assertEqual(target_items.count(), 2)
        
        # Check quantity was added for same variant
        merged = target.items.get(variant=self.variant)
        self.assertEqual(merged.quantity, 3)  # 1 + 2
        
        # Check source is abandoned
        source.refresh_from_db()
        self.assertEqual(source.status, Cart.Status.ABANDONED)
    
    def test_merge_carts_prevents_self_merge(self):
        """Test that merging cart into itself is prevented."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        with self.assertRaises(CartServiceError):
            CartService.merge_carts(cart, cart)
    
    def test_compute_cart_totals(self):
        """Test computing cart totals."""
        cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        CartItem.objects.create(
            cart=cart,
            variant=self.variant,
            quantity=2,
            unit_price_snapshot=Decimal("100.00"),
        )
        CartItem.objects.create(
            cart=cart,
            variant=self.variant_limited,
            quantity=1,
            unit_price_snapshot=Decimal("200.00"),
        )
        
        totals = CartService.compute_cart_totals(cart)
        
        self.assertEqual(totals["subtotal"], Decimal("400.00"))  # 2*100 + 1*200
        self.assertEqual(totals["item_count"], 3)  # 2 + 1
        self.assertEqual(totals["line_count"], 2)
    
    def test_get_cart_by_token_security(self):
        """Test cart token security."""
        anon_cart = Cart.objects.create(status=Cart.Status.OPEN)
        user_cart = Cart.objects.create(user=self.user, status=Cart.Status.OPEN)
        
        # Anonymous access to anonymous cart works
        result = CartService.get_cart_by_token(anon_cart.token, user=None)
        self.assertEqual(result.id, anon_cart.id)
        
        # Anonymous access to user cart fails
        result = CartService.get_cart_by_token(user_cart.token, user=None)
        self.assertIsNone(result)
