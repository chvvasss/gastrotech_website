"""
Cart service layer for managing shopping cart operations.

This module provides atomic, thread-safe cart operations with proper
concurrency handling using database transactions and row locking.

Key features:
- Anonymous cart support via UUID tokens
- Authenticated user cart management
- Cart merge on login
- Stock validation (returns 409-compatible errors)
- Price snapshot capture
- Currency validation (single-currency cart)
- Idempotency support
- Merge dry_run mode
- Atomic operations with select_for_update()
"""

import hashlib
import json
import logging
import uuid
from decimal import Decimal
from typing import Optional, Tuple, List, Dict, Any

from django.db import transaction, IntegrityError
from django.db.models import F

from apps.catalog.models import Variant
from apps.orders.models import Cart, CartItem, IdempotencyRecord

logger = logging.getLogger(__name__)


class CartServiceError(Exception):
    """Base exception for cart service errors."""
    pass


class VariantNotFoundError(CartServiceError):
    """Raised when variant does not exist."""
    pass


class VariantNotActiveError(CartServiceError):
    """Raised when variant is not active."""
    pass


class InsufficientStockError(CartServiceError):
    """
    Raised when requested quantity exceeds stock.
    
    Returns 409-compatible error with structured info.
    """
    
    def __init__(
        self,
        message: str,
        variant_id: uuid.UUID,
        requested: int,
        available: int,
    ):
        super().__init__(message)
        self.variant_id = variant_id
        self.requested = requested
        self.available = available
        self.available_stock = available  # Backward compat
    
    def to_dict(self) -> dict:
        """Return 409-compatible error body."""
        return {
            "detail": "insufficient_stock",
            "variant_id": str(self.variant_id),
            "requested": self.requested,
            "available": self.available,
        }


class MixedCurrencyError(CartServiceError):
    """
    Raised when trying to add variant with different currency to cart.
    
    Returns 409 with mixed_currency detail.
    """
    
    def __init__(
        self,
        message: str,
        cart_currency: str,
        variant_currency: str,
    ):
        super().__init__(message)
        self.cart_currency = cart_currency
        self.variant_currency = variant_currency
    
    def to_dict(self) -> dict:
        """Return 409-compatible error body."""
        return {
            "detail": "mixed_currency",
            "cart_currency": self.cart_currency,
            "variant_currency": self.variant_currency,
        }


class InvalidQuantityError(CartServiceError):
    """Raised when quantity is invalid."""
    pass


class CartNotOpenError(CartServiceError):
    """Raised when cart is not in open state."""
    pass


class CartItemNotFoundError(CartServiceError):
    """Raised when cart item does not exist."""
    pass


class IdempotencyConflictError(CartServiceError):
    """Raised when idempotency check finds existing response."""
    
    def __init__(self, record: IdempotencyRecord):
        super().__init__("Idempotent request replay")
        self.record = record


class CartService:
    """
    Service class for cart operations.
    
    All methods that modify data use atomic transactions and
    appropriate row locking to ensure data integrity.
    """
    
    @staticmethod
    @transaction.atomic
    def resolve_cart(
        user=None,
        cart_token: Optional[uuid.UUID] = None,
        create_if_missing: bool = True,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Optional[Cart]:
        """
        Resolve cart for user or token.
        
        Logic:
        1. If user is authenticated:
           a. Get or create open cart for user
           b. If cart_token provided and belongs to anonymous cart:
              merge anonymous cart into user cart
        2. If user is not authenticated:
           a. If cart_token provided: get or create cart by token
           b. If no token and create_if_missing: create new anonymous cart
           
        Args:
            user: Authenticated user or None
            cart_token: Optional cart token UUID
            create_if_missing: Whether to create cart if not found
            ip_address: Optional IP address for new carts
            user_agent: Optional user agent for new carts
            
        Returns:
            Cart instance or None if not found and create_if_missing is False
        """
        if user and user.is_authenticated:
            return CartService._resolve_authenticated_cart(
                user=user,
                cart_token=cart_token,
                create_if_missing=create_if_missing,
                ip_address=ip_address,
                user_agent=user_agent,
            )
        else:
            return CartService._resolve_anonymous_cart(
                cart_token=cart_token,
                create_if_missing=create_if_missing,
                ip_address=ip_address,
                user_agent=user_agent,
            )
    
    @staticmethod
    def _resolve_authenticated_cart(
        user,
        cart_token: Optional[uuid.UUID] = None,
        create_if_missing: bool = True,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Optional[Cart]:
        """Resolve cart for authenticated user."""
        # Get or create user's open cart
        user_cart = Cart.objects.filter(
            user=user,
            status=Cart.Status.OPEN,
        ).select_for_update().first()
        
        if not user_cart and create_if_missing:
            user_cart = Cart.objects.create(
                user=user,
                status=Cart.Status.OPEN,
                ip_address=ip_address,
                user_agent=user_agent or "",
            )
            logger.info(f"Created new cart for user {user.email}: {user_cart.token.hex[:8]}")
        
        # If cart_token provided, check for anonymous cart to merge
        if cart_token and user_cart:
            anonymous_cart = Cart.objects.filter(
                token=cart_token,
                user__isnull=True,
                status=Cart.Status.OPEN,
            ).select_for_update().first()
            
            if anonymous_cart and anonymous_cart.items.exists():
                logger.info(
                    f"Merging anonymous cart {cart_token.hex[:8]} "
                    f"into user cart {user_cart.token.hex[:8]}"
                )
                CartService.merge_carts(
                    source_cart=anonymous_cart,
                    target_cart=user_cart,
                )
        
        return user_cart
    
    @staticmethod
    def _resolve_anonymous_cart(
        cart_token: Optional[uuid.UUID] = None,
        create_if_missing: bool = True,
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Optional[Cart]:
        """Resolve cart for anonymous user."""
        if cart_token:
            # First check if any cart with this token exists
            cart = Cart.objects.filter(
                token=cart_token,
                status=Cart.Status.OPEN,
            ).select_for_update().first()
            
            if cart:
                # If cart belongs to a user, anonymous access is denied
                if cart.user is not None:
                    logger.warning(
                        f"Anonymous access denied for user cart: {cart_token.hex[:8]}"
                    )
                    return None
                # Return anonymous cart
                return cart
            
            if create_if_missing:
                # Token provided but no cart found - create with that token
                cart = Cart.objects.create(
                    token=cart_token,
                    status=Cart.Status.OPEN,
                    ip_address=ip_address,
                    user_agent=user_agent or "",
                )
                logger.info(f"Created anonymous cart with provided token: {cart_token.hex[:8]}")
                return cart
            
            return None
        
        if create_if_missing:
            # No token, create new anonymous cart
            cart = Cart.objects.create(
                status=Cart.Status.OPEN,
                ip_address=ip_address,
                user_agent=user_agent or "",
            )
            logger.info(f"Created new anonymous cart: {cart.token.hex[:8]}")
            return cart
        
        return None
    
    @staticmethod
    @transaction.atomic
    def create_anonymous_cart(
        ip_address: Optional[str] = None,
        user_agent: str = "",
    ) -> Cart:
        """
        Create a new anonymous cart with a fresh token.
        
        Returns:
            New Cart instance
        """
        cart = Cart.objects.create(
            status=Cart.Status.OPEN,
            ip_address=ip_address,
            user_agent=user_agent or "",
        )
        logger.info(f"Created new anonymous cart: {cart.token.hex[:8]}")
        return cart
    
    @staticmethod
    def merge_carts(
        source_cart: Cart,
        target_cart: Cart,
        dry_run: bool = False,
    ) -> dict:
        """
        Merge items from source cart into target cart.
        
        For each item in source:
        - If same variant exists in target: add quantities (up to stock limit)
        - If not exists: move item to target
        - Enforce stock policy strictly
        
        After merge (if not dry_run):
        - Mark source cart as abandoned to prevent reuse
        - Items are moved/merged
        
        Args:
            source_cart: Cart to merge from (will be abandoned)
            target_cart: Cart to merge into
            dry_run: If True, preview merge without committing
            
        Returns:
            dict with merge summary and warnings
        """
        if source_cart.id == target_cart.id:
            raise CartServiceError("Cannot merge cart into itself")
        
        if not source_cart.is_open:
            raise CartNotOpenError("Source cart is not open")
        
        if not target_cart.is_open:
            raise CartNotOpenError("Target cart is not open")
        
        if dry_run:
            return CartService._merge_carts_dry_run(source_cart, target_cart)
        else:
            return CartService._merge_carts_commit(source_cart, target_cart)
    
    @staticmethod
    def _merge_carts_dry_run(source_cart: Cart, target_cart: Cart) -> dict:
        """
        Preview merge without committing changes.
        
        Returns predicted result with warnings.
        """
        source_items = list(source_cart.items.select_related("variant__product"))
        target_items_map = {
            item.variant_id: item
            for item in target_cart.items.select_related("variant__product")
        }
        
        merged_count = 0
        skipped_count = 0
        warnings = []
        predicted_items = []
        
        # Copy existing target items
        for item in target_cart.items.select_related("variant__product"):
            predicted_items.append({
                "variant_id": str(item.variant_id),
                "model_code": item.variant.model_code,
                "quantity": item.quantity,
                "from_source": False,
            })
        
        for source_item in source_items:
            variant = source_item.variant
            target_item = target_items_map.get(variant.id)
            
            # Check stock availability
            available = variant.stock_qty
            if available is not None and available <= 0:
                # Out of stock - skip and warn
                warnings.append({
                    "variant_id": str(variant.id),
                    "requested": source_item.quantity,
                    "available": 0,
                    "reason": "insufficient_stock",
                })
                skipped_count += 1
                continue
            
            if target_item:
                # Would merge quantities
                new_quantity = target_item.quantity + source_item.quantity
                
                if available is not None and new_quantity > available:
                    # Would cap to stock limit
                    warnings.append({
                        "variant_id": str(variant.id),
                        "requested": new_quantity,
                        "available": available,
                        "reason": "insufficient_stock",
                    })
                    new_quantity = available
                
                # Update predicted item
                for pred in predicted_items:
                    if pred["variant_id"] == str(variant.id):
                        pred["quantity"] = new_quantity
                        pred["from_source"] = True
                        break
                merged_count += 1
            else:
                # Would move item
                new_quantity = source_item.quantity
                
                if available is not None and new_quantity > available:
                    warnings.append({
                        "variant_id": str(variant.id),
                        "requested": new_quantity,
                        "available": available,
                        "reason": "insufficient_stock",
                    })
                    new_quantity = available
                
                predicted_items.append({
                    "variant_id": str(variant.id),
                    "model_code": variant.model_code,
                    "quantity": new_quantity,
                    "from_source": True,
                })
                merged_count += 1
        
        return {
            "dry_run": True,
            "merged_count": merged_count,
            "skipped_count": skipped_count,
            "warnings": warnings,
            "predicted_items": predicted_items,
        }
    
    @staticmethod
    @transaction.atomic
    def _merge_carts_commit(source_cart: Cart, target_cart: Cart) -> dict:
        """
        Actually commit the merge with proper locking.
        """
        # Lock both carts for update
        locked_carts = list(
            Cart.objects.filter(id__in=[source_cart.id, target_cart.id])
            .select_for_update()
            .order_by("id")
        )
        
        merged_count = 0
        skipped_count = 0
        warnings = []
        
        source_items = list(source_cart.items.select_related("variant__product").select_for_update())
        
        for source_item in source_items:
            variant = source_item.variant
            
            # Check stock availability (strict 409 policy)
            available = variant.stock_qty
            if available is not None and available <= 0:
                # Out of stock - skip and warn
                warnings.append({
                    "variant_id": str(variant.id),
                    "requested": source_item.quantity,
                    "available": 0,
                    "reason": "insufficient_stock",
                })
                source_item.delete()
                skipped_count += 1
                continue
            
            # Check if variant exists in target cart
            target_item = target_cart.items.filter(variant=variant).select_for_update().first()
            
            if target_item:
                # Merge quantities
                new_quantity = target_item.quantity + source_item.quantity
                
                # Enforce stock limit strictly
                if available is not None and new_quantity > available:
                    warnings.append({
                        "variant_id": str(variant.id),
                        "requested": new_quantity,
                        "available": available,
                        "reason": "insufficient_stock",
                    })
                    new_quantity = available
                
                target_item.quantity = new_quantity
                target_item.save(update_fields=["quantity", "updated_at"])
                source_item.delete()
                merged_count += 1
            else:
                # Move item to target cart
                new_quantity = source_item.quantity
                
                if available is not None and new_quantity > available:
                    warnings.append({
                        "variant_id": str(variant.id),
                        "requested": new_quantity,
                        "available": available,
                        "reason": "insufficient_stock",
                    })
                    source_item.quantity = available
                
                source_item.cart = target_cart
                source_item.save(update_fields=["cart", "quantity", "updated_at"])
                merged_count += 1
        
        # Mark source cart as abandoned to prevent reuse
        source_cart.status = Cart.Status.ABANDONED
        source_cart.save(update_fields=["status", "updated_at"])
        
        logger.info(
            f"Merged cart {source_cart.token.hex[:8]} into {target_cart.token.hex[:8]}: "
            f"{merged_count} merged, {skipped_count} skipped"
        )
        
        return {
            "dry_run": False,
            "merged_count": merged_count,
            "skipped_count": skipped_count,
            "warnings": warnings,
        }
    
    @staticmethod
    @transaction.atomic
    def add_item(
        cart: Cart,
        variant_id: uuid.UUID,
        quantity: int = 1,
    ) -> CartItem:
        """
        Add item to cart or increment quantity if already exists.
        
        Validates:
        - Variant exists and is active (product.status = active)
        - Quantity is positive
        - Stock is sufficient (returns 409-compatible error)
        - Currency matches cart (single-currency enforcement)
        
        Args:
            cart: Cart to add item to
            variant_id: UUID of the variant
            quantity: Quantity to add (default 1)
            
        Returns:
            CartItem instance (created or updated)
            
        Raises:
            CartNotOpenError: Cart is not in open state
            VariantNotFoundError: Variant does not exist
            VariantNotActiveError: Variant's product is not active
            InvalidQuantityError: Quantity is <= 0
            InsufficientStockError: Requested quantity exceeds stock (409)
            MixedCurrencyError: Variant currency doesn't match cart (409)
        """
        if not cart.is_open:
            raise CartNotOpenError("Cannot add items to a non-open cart")
        
        if quantity <= 0:
            raise InvalidQuantityError("Quantity must be positive")
        
        # Lock cart
        Cart.objects.filter(id=cart.id).select_for_update()
        
        # Get variant with related product
        try:
            variant = Variant.objects.select_related("product").get(id=variant_id)
        except Variant.DoesNotExist:
            raise VariantNotFoundError(f"Variant {variant_id} not found")
        
        # Check if product is active
        from apps.catalog.models import Product
        if variant.product.status != Product.Status.ACTIVE:
            raise VariantNotActiveError(
                f"Variant {variant.model_code} is not available (product not active)"
            )
        
        # Currency validation (single-currency cart)
        # For now, all variants use TRY. If variant had currency field:
        variant_currency = "TRY"  # Could be variant.currency in future
        if cart.items.exists() and cart.currency != variant_currency:
            raise MixedCurrencyError(
                f"Cannot add variant with currency {variant_currency} to cart with currency {cart.currency}",
                cart_currency=cart.currency,
                variant_currency=variant_currency,
            )
        
        # Check existing item in cart
        existing_item = cart.items.filter(variant=variant).select_for_update().first()
        
        new_quantity = quantity
        if existing_item:
            new_quantity = existing_item.quantity + quantity
        
        # Stock validation (strict 409 policy)
        # stock_qty == 0 means out of stock
        # stock_qty > 0 means limited stock
        # stock_qty is None means unlimited (no tracking)
        if variant.stock_qty is not None:
            if variant.stock_qty <= 0:
                raise InsufficientStockError(
                    f"Variant {variant.model_code} is out of stock",
                    variant_id=variant.id,
                    requested=new_quantity,
                    available=0,
                )
            if new_quantity > variant.stock_qty:
                raise InsufficientStockError(
                    f"Only {variant.stock_qty} units available for {variant.model_code}",
                    variant_id=variant.id,
                    requested=new_quantity,
                    available=variant.stock_qty,
                )
        
        if existing_item:
            existing_item.quantity = new_quantity
            existing_item.save(update_fields=["quantity", "updated_at"])
            logger.info(f"Updated cart item quantity: {variant.model_code} x {new_quantity}")
            return existing_item
        else:
            # Create new cart item with full snapshots
            product_name = variant.product.title_tr or variant.product.name or ""
            variant_label = f"{variant.model_code}"
            if variant.name_tr:
                variant_label = f"{variant.model_code} - {variant.name_tr}"
            
            item = CartItem.objects.create(
                cart=cart,
                variant=variant,
                quantity=quantity,
                unit_price_snapshot=variant.get_display_price(),
                currency_snapshot=cart.currency,
                product_name_snapshot=product_name[:255],
                variant_label_snapshot=variant_label[:255],
            )
            logger.info(f"Added to cart: {variant.model_code} x {quantity}")
            return item
    
    @staticmethod
    @transaction.atomic
    def set_item_quantity(
        cart: Cart,
        item_id: uuid.UUID,
        quantity: int,
    ) -> Optional[CartItem]:
        """
        Set cart item quantity. Removes item if quantity is 0.
        
        Args:
            cart: Cart containing the item
            item_id: UUID of the CartItem
            quantity: New quantity (0 = remove)
            
        Returns:
            Updated CartItem or None if removed
            
        Raises:
            CartNotOpenError: Cart is not open
            CartItemNotFoundError: Item not in cart
            InvalidQuantityError: Quantity is negative
            InsufficientStockError: Quantity exceeds stock (409)
        """
        if not cart.is_open:
            raise CartNotOpenError("Cannot modify items in a non-open cart")
        
        if quantity < 0:
            raise InvalidQuantityError("Quantity cannot be negative")
        
        # Lock cart
        Cart.objects.filter(id=cart.id).select_for_update()
        
        try:
            item = cart.items.select_related("variant__product").select_for_update().get(id=item_id)
        except CartItem.DoesNotExist:
            raise CartItemNotFoundError(f"Cart item {item_id} not found")
        
        if quantity == 0:
            item.delete()
            logger.info(f"Removed from cart: {item.variant.model_code}")
            return None
        
        # Stock validation (strict 409 policy)
        variant = item.variant
        if variant.stock_qty is not None:
            if variant.stock_qty <= 0:
                raise InsufficientStockError(
                    f"Variant {variant.model_code} is out of stock",
                    variant_id=variant.id,
                    requested=quantity,
                    available=0,
                )
            if quantity > variant.stock_qty:
                raise InsufficientStockError(
                    f"Only {variant.stock_qty} units available for {variant.model_code}",
                    variant_id=variant.id,
                    requested=quantity,
                    available=variant.stock_qty,
                )
        
        item.quantity = quantity
        item.save(update_fields=["quantity", "updated_at"])
        logger.info(f"Set cart item quantity: {variant.model_code} x {quantity}")
        return item
    
    @staticmethod
    @transaction.atomic
    def remove_item(cart: Cart, item_id: uuid.UUID) -> bool:
        """
        Remove item from cart.
        
        Args:
            cart: Cart containing the item
            item_id: UUID of the CartItem
            
        Returns:
            True if removed, False if not found
            
        Raises:
            CartNotOpenError: Cart is not open
        """
        if not cart.is_open:
            raise CartNotOpenError("Cannot remove items from a non-open cart")
        
        Cart.objects.filter(id=cart.id).select_for_update()
        
        deleted_count, _ = cart.items.filter(id=item_id).delete()
        
        if deleted_count > 0:
            logger.info(f"Removed cart item: {item_id}")
            return True
        
        logger.warning(f"Cart item not found for removal: {item_id}")
        return False
    
    @staticmethod
    @transaction.atomic
    def clear_cart(cart: Cart) -> int:
        """
        Remove all items from cart.
        
        Args:
            cart: Cart to clear
            
        Returns:
            Number of items removed
            
        Raises:
            CartNotOpenError: Cart is not open
        """
        if not cart.is_open:
            raise CartNotOpenError("Cannot clear a non-open cart")
        
        Cart.objects.filter(id=cart.id).select_for_update()
        
        deleted_count, _ = cart.items.all().delete()
        logger.info(f"Cleared cart {cart.token.hex[:8]}: {deleted_count} items removed")
        return deleted_count
    
    @staticmethod
    def compute_cart_totals(cart: Cart) -> dict:
        """
        Compute cart totals.
        
        Args:
            cart: Cart to compute totals for
            
        Returns:
            dict with subtotal, item_count, line_count, currency
        """
        return cart.compute_totals()
    
    @staticmethod
    def get_cart_by_token(
        token: uuid.UUID,
        user=None,
    ) -> Optional[Cart]:
        """
        Get cart by token with ownership validation.
        
        For security:
        - Anonymous tokens only return anonymous carts
        - User tokens are validated against user ownership
        
        Args:
            token: Cart token UUID
            user: Optional user for ownership check
            
        Returns:
            Cart if found and accessible, None otherwise
        """
        cart = Cart.objects.filter(
            token=token,
            status=Cart.Status.OPEN,
        ).first()
        
        if not cart:
            return None
        
        # Security check: prevent accessing other users' carts
        if cart.user is not None and user is not None:
            if cart.user.id != user.id:
                logger.warning(
                    f"User {user.id} attempted to access cart belonging to {cart.user.id}"
                )
                return None
        
        # Anonymous token can only access anonymous cart
        if cart.user is not None and user is None:
            logger.warning(f"Anonymous access attempted for user cart {token.hex[:8]}")
            return None
        
        return cart
    
    # -------------------------------------------------------------------------
    # Idempotency Support
    # -------------------------------------------------------------------------
    
    @staticmethod
    def compute_request_hash(data: dict) -> str:
        """Compute SHA256 hash of request data for idempotency validation."""
        serialized = json.dumps(data, sort_keys=True, default=str)
        return hashlib.sha256(serialized.encode()).hexdigest()
    
    @staticmethod
    def _serialize_for_json(obj):
        """Convert non-JSON-serializable objects to JSON-compatible types."""
        if isinstance(obj, dict):
            return {k: CartService._serialize_for_json(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [CartService._serialize_for_json(i) for i in obj]
        elif isinstance(obj, Decimal):
            return str(obj)
        elif isinstance(obj, uuid.UUID):
            return str(obj)
        elif hasattr(obj, 'isoformat'):
            return obj.isoformat()
        return obj
    
    @staticmethod
    def check_idempotency(
        key: str,
        scope: str,
        cart: Cart,
    ) -> Optional[IdempotencyRecord]:
        """
        Check for existing idempotency record.
        
        Returns record if found and not expired, None otherwise.
        """
        try:
            record = IdempotencyRecord.objects.get(
                key=key,
                scope=scope,
                cart=cart,
            )
            if record.is_expired:
                # Clean up expired record
                record.delete()
                return None
            return record
        except IdempotencyRecord.DoesNotExist:
            return None
    
    @staticmethod
    @transaction.atomic
    def store_idempotency(
        key: str,
        scope: str,
        cart: Cart,
        request_hash: str,
        response_body: dict,
        status_code: int,
    ) -> IdempotencyRecord:
        """
        Store idempotency record for future replay.
        
        Uses get_or_create with atomic to handle race conditions.
        Serializes response_body to ensure JSON compatibility (Decimals -> str).
        """
        # Serialize response to ensure JSON compatibility
        serialized_body = CartService._serialize_for_json(response_body)
        
        record, created = IdempotencyRecord.objects.get_or_create(
            key=key,
            scope=scope,
            cart=cart,
            defaults={
                "request_hash": request_hash,
                "response_body": serialized_body,
                "status_code": status_code,
            },
        )
        if not created:
            # Record already exists, don't overwrite
            pass
        return record
