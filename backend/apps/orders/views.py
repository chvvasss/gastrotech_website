"""
Cart API views for orders app.

This module provides REST API endpoints for cart operations:
- Create anonymous cart token
- Get current cart
- Add items to cart (with idempotency support)
- Update item quantity
- Remove items
- Clear cart
- Merge anonymous cart into user cart (with idempotency + dry_run)

Stock Policy:
- 409 Conflict for insufficient stock or mixed currency
- Consistent error format: { detail, variant_id, requested, available }

Idempotency:
- Idempotency-Key header for POST /items/ and POST /merge/
- Records stored for 24h, replayed on duplicate keys
"""

import logging
import uuid
from typing import Optional

from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from drf_spectacular.utils import (
    OpenApiExample,
    OpenApiParameter,
    OpenApiResponse,
    extend_schema,
    extend_schema_view,
)
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.orders.models import Cart, CartItem, IdempotencyRecord
from apps.orders.serializers import (
    AddItemSerializer,
    CartItemSerializer,
    CartMergeResultSerializer,
    CartSerializer,
    CartTokenSerializer,
    MergeCartSerializer,
    UpdateItemSerializer,
)
from apps.orders.services.cart_service import (
    CartItemNotFoundError,
    CartNotOpenError,
    CartService,
    CartServiceError,
    IdempotencyConflictError,
    InsufficientStockError,
    InvalidQuantityError,
    MixedCurrencyError,
    VariantNotActiveError,
    VariantNotFoundError,
)

logger = logging.getLogger(__name__)


# Header names
CART_TOKEN_HEADER = "HTTP_X_CART_TOKEN"
IDEMPOTENCY_KEY_HEADER = "HTTP_IDEMPOTENCY_KEY"


class CartTokenMixin:
    """
    Mixin for extracting cart token and idempotency key from headers.
    """
    
    def get_cart_token(self) -> Optional[uuid.UUID]:
        """Extract cart token from request header."""
        token_str = self.request.META.get(CART_TOKEN_HEADER)
        if token_str:
            try:
                return uuid.UUID(token_str)
            except (ValueError, AttributeError):
                logger.warning(f"Invalid cart token format: {token_str}")
        return None
    
    def get_idempotency_key(self) -> Optional[str]:
        """Extract idempotency key from request header."""
        return self.request.META.get(IDEMPOTENCY_KEY_HEADER)
    
    def get_client_ip(self) -> Optional[str]:
        """Extract client IP from request."""
        x_forwarded_for = self.request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return self.request.META.get("REMOTE_ADDR")
    
    def get_user_agent(self) -> str:
        """Extract user agent from request."""
        return self.request.META.get("HTTP_USER_AGENT", "")[:500]


class CartPermission:
    """
    Custom permission for cart endpoints.
    
    - Authenticated users: always allowed
    - Anonymous users: only with valid X-Cart-Token
    """
    
    def has_permission(self, request, view) -> bool:
        # Authenticated users always allowed
        if request.user and request.user.is_authenticated:
            return True
        
        # Anonymous users need cart token for most operations
        # Create token endpoint is always allowed
        if hasattr(view, "allow_anonymous_without_token"):
            return view.allow_anonymous_without_token
        
        # Check for cart token
        token_str = request.META.get(CART_TOKEN_HEADER)
        if token_str:
            try:
                uuid.UUID(token_str)
                return True
            except (ValueError, AttributeError):
                pass
        
        return False


# Error response schemas for OpenAPI
INSUFFICIENT_STOCK_EXAMPLE = {
    "detail": "insufficient_stock",
    "variant_id": "550e8400-e29b-41d4-a716-446655440000",
    "requested": 5,
    "available": 3,
}

MIXED_CURRENCY_EXAMPLE = {
    "detail": "mixed_currency",
    "cart_currency": "TRY",
    "variant_currency": "USD",
}


@extend_schema(tags=["Cart"])
@method_decorator(never_cache, name="dispatch")
class CreateCartTokenView(CartTokenMixin, APIView):
    """
    Create a new anonymous cart and return its token.
    
    Use this endpoint to get a cart token for anonymous shopping.
    Include the token in subsequent requests as X-Cart-Token header.
    """
    
    permission_classes = [AllowAny]
    allow_anonymous_without_token = True
    
    @extend_schema(
        summary="Create anonymous cart token",
        description=(
            "Create a new anonymous shopping cart and get its token. "
            "Use the returned cart_token in the X-Cart-Token header for subsequent cart operations."
        ),
        responses={
            201: CartTokenSerializer,
        },
        examples=[
            OpenApiExample(
                "Success",
                value={
                    "cart_token": "550e8400-e29b-41d4-a716-446655440000",
                    "cart": {
                        "id": "550e8400-e29b-41d4-a716-446655440001",
                        "token": "550e8400-e29b-41d4-a716-446655440000",
                        "status": "open",
                        "currency": "TRY",
                        "is_anonymous": True,
                        "items": [],
                        "totals": {
                            "subtotal": "0.00",
                            "item_count": 0,
                            "line_count": 0,
                            "currency": "TRY",
                            "has_pricing_gaps": False,
                        },
                        "warnings": [],
                    },
                },
                response_only=True,
            ),
        ],
        auth=[],  # Public endpoint - no authentication required
    )
    def post(self, request):
        """Create a new anonymous cart."""
        cart = CartService.create_anonymous_cart(
            ip_address=self.get_client_ip(),
            user_agent=self.get_user_agent(),
        )
        
        return Response(
            {
                "cart_token": cart.token,
                "cart": CartSerializer(cart).data,
            },
            status=status.HTTP_201_CREATED,
        )


@extend_schema(tags=["Cart"])
@method_decorator(never_cache, name="dispatch")
class CartView(CartTokenMixin, APIView):
    """
    Get current cart for authenticated user or anonymous token.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Get current cart",
        description=(
            "Retrieve the current cart for the authenticated user or anonymous token. "
            "For authenticated users, the cart is resolved by user. "
            "For anonymous users, include X-Cart-Token header."
        ),
        parameters=[
            OpenApiParameter(
                name="X-Cart-Token",
                location=OpenApiParameter.HEADER,
                description="Cart token for anonymous users",
                required=False,
                type=str,
            ),
        ],
        responses={
            200: CartSerializer,
            404: OpenApiResponse(description="Cart not found"),
        },
    )
    def get(self, request):
        """Get current cart."""
        user = request.user if request.user.is_authenticated else None
        cart_token = self.get_cart_token()
        
        # For anonymous users, require token
        if not user and not cart_token:
            return Response(
                {"detail": "Cart token required for anonymous access"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        cart = CartService.resolve_cart(
            user=user,
            cart_token=cart_token,
            create_if_missing=True,
            ip_address=self.get_client_ip(),
            user_agent=self.get_user_agent(),
        )
        
        if not cart:
            return Response(
                {"detail": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Prefetch items for serialization
        cart = Cart.objects.prefetch_related(
            "items__variant__product"
        ).get(id=cart.id)
        
        return Response(CartSerializer(cart).data)


@extend_schema(tags=["Cart"])
@method_decorator(never_cache, name="dispatch")
class CartItemsView(CartTokenMixin, APIView):
    """
    Add items to cart with idempotency support.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Add item to cart",
        description=(
            "Add a product variant to the cart. If the variant is already in the cart, "
            "the quantity will be incremented. Stock limits are enforced.\n\n"
            "**Idempotency:** Include `Idempotency-Key` header to prevent duplicate adds. "
            "If the same key is sent again within 24h, the original response is replayed.\n\n"
            "**Stock Policy:** Returns 409 Conflict if:\n"
            "- Requested quantity exceeds available stock\n"
            "- Variant currency doesn't match cart currency"
        ),
        parameters=[
            OpenApiParameter(
                name="X-Cart-Token",
                location=OpenApiParameter.HEADER,
                description="Cart token for anonymous users",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="Idempotency-Key",
                location=OpenApiParameter.HEADER,
                description="Unique key to prevent duplicate operations (24h validity)",
                required=False,
                type=str,
            ),
        ],
        request=AddItemSerializer,
        responses={
            201: CartSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Variant not found"),
            409: OpenApiResponse(
                description="Insufficient stock or mixed currency",
                examples=[
                    OpenApiExample(
                        "Insufficient Stock",
                        value=INSUFFICIENT_STOCK_EXAMPLE,
                    ),
                    OpenApiExample(
                        "Mixed Currency",
                        value=MIXED_CURRENCY_EXAMPLE,
                    ),
                ],
            ),
        },
        examples=[
            OpenApiExample(
                "Add item",
                value={
                    "variant_id": "550e8400-e29b-41d4-a716-446655440000",
                    "quantity": 2,
                },
                request_only=True,
            ),
        ],
    )
    def post(self, request):
        """Add item to cart."""
        user = request.user if request.user.is_authenticated else None
        cart_token = self.get_cart_token()
        idempotency_key = self.get_idempotency_key()
        
        # For anonymous users, require token
        if not user and not cart_token:
            return Response(
                {"detail": "Cart token required for anonymous access"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = AddItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        cart = CartService.resolve_cart(
            user=user,
            cart_token=cart_token,
            create_if_missing=True,
            ip_address=self.get_client_ip(),
            user_agent=self.get_user_agent(),
        )
        
        if not cart:
            return Response(
                {"detail": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Check idempotency
        if idempotency_key:
            existing_record = CartService.check_idempotency(
                key=idempotency_key,
                scope=IdempotencyRecord.Scope.CART_ADD_ITEM,
                cart=cart,
            )
            if existing_record:
                logger.info(f"Replaying idempotent response for key: {idempotency_key[:16]}...")
                return Response(
                    existing_record.response_body,
                    status=existing_record.status_code,
                )
        
        try:
            CartService.add_item(
                cart=cart,
                variant_id=serializer.validated_data["variant_id"],
                quantity=serializer.validated_data["quantity"],
            )
        except VariantNotFoundError:
            return Response(
                {"detail": "Variant not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except VariantNotActiveError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except InsufficientStockError as e:
            return Response(
                e.to_dict(),
                status=status.HTTP_409_CONFLICT,
            )
        except MixedCurrencyError as e:
            return Response(
                e.to_dict(),
                status=status.HTTP_409_CONFLICT,
            )
        except InvalidQuantityError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except CartNotOpenError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Refresh cart for response
        cart = Cart.objects.prefetch_related(
            "items__variant__product"
        ).get(id=cart.id)
        
        response_data = CartSerializer(cart).data
        response_status = status.HTTP_201_CREATED
        
        # Store idempotency record
        if idempotency_key:
            request_hash = CartService.compute_request_hash(serializer.validated_data)
            CartService.store_idempotency(
                key=idempotency_key,
                scope=IdempotencyRecord.Scope.CART_ADD_ITEM,
                cart=cart,
                request_hash=request_hash,
                response_body=response_data,
                status_code=response_status,
            )
        
        return Response(response_data, status=response_status)


@extend_schema(tags=["Cart"])
@method_decorator(never_cache, name="dispatch")
class CartItemDetailView(CartTokenMixin, APIView):
    """
    Update or remove specific cart item.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Update cart item quantity",
        description=(
            "Set quantity for a cart item. Set quantity to 0 to remove the item.\n\n"
            "**Stock Policy:** Returns 409 Conflict if requested quantity exceeds stock."
        ),
        parameters=[
            OpenApiParameter(
                name="X-Cart-Token",
                location=OpenApiParameter.HEADER,
                description="Cart token for anonymous users",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="item_id",
                location=OpenApiParameter.PATH,
                description="Cart item UUID",
                required=True,
                type=str,
            ),
        ],
        request=UpdateItemSerializer,
        responses={
            200: CartSerializer,
            400: OpenApiResponse(description="Validation error"),
            404: OpenApiResponse(description="Item not found"),
            409: OpenApiResponse(
                description="Insufficient stock",
                examples=[
                    OpenApiExample(
                        "Insufficient Stock",
                        value=INSUFFICIENT_STOCK_EXAMPLE,
                    ),
                ],
            ),
        },
    )
    def patch(self, request, item_id):
        """Update item quantity."""
        user = request.user if request.user.is_authenticated else None
        cart_token = self.get_cart_token()
        
        if not user and not cart_token:
            return Response(
                {"detail": "Cart token required for anonymous access"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        serializer = UpdateItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        cart = CartService.resolve_cart(
            user=user,
            cart_token=cart_token,
            create_if_missing=False,
        )
        
        if not cart:
            return Response(
                {"detail": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            item_uuid = uuid.UUID(str(item_id))
        except ValueError:
            return Response(
                {"detail": "Invalid item ID format"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            CartService.set_item_quantity(
                cart=cart,
                item_id=item_uuid,
                quantity=serializer.validated_data["quantity"],
            )
        except CartItemNotFoundError:
            return Response(
                {"detail": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        except InsufficientStockError as e:
            return Response(
                e.to_dict(),
                status=status.HTTP_409_CONFLICT,
            )
        except (InvalidQuantityError, CartNotOpenError) as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Refresh cart
        cart = Cart.objects.prefetch_related(
            "items__variant__product"
        ).get(id=cart.id)
        
        return Response(CartSerializer(cart).data)
    
    @extend_schema(
        summary="Remove cart item",
        description="Remove an item from the cart.",
        parameters=[
            OpenApiParameter(
                name="X-Cart-Token",
                location=OpenApiParameter.HEADER,
                description="Cart token for anonymous users",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="item_id",
                location=OpenApiParameter.PATH,
                description="Cart item UUID",
                required=True,
                type=str,
            ),
        ],
        responses={
            200: CartSerializer,
            404: OpenApiResponse(description="Item not found"),
        },
    )
    def delete(self, request, item_id):
        """Remove item from cart."""
        user = request.user if request.user.is_authenticated else None
        cart_token = self.get_cart_token()
        
        if not user and not cart_token:
            return Response(
                {"detail": "Cart token required for anonymous access"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        cart = CartService.resolve_cart(
            user=user,
            cart_token=cart_token,
            create_if_missing=False,
        )
        
        if not cart:
            return Response(
                {"detail": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            item_uuid = uuid.UUID(str(item_id))
        except ValueError:
            return Response(
                {"detail": "Invalid item ID format"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        try:
            removed = CartService.remove_item(cart=cart, item_id=item_uuid)
        except CartNotOpenError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        if not removed:
            return Response(
                {"detail": "Cart item not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Refresh cart
        cart = Cart.objects.prefetch_related(
            "items__variant__product"
        ).get(id=cart.id)
        
        return Response(CartSerializer(cart).data)


@extend_schema(tags=["Cart"])
@method_decorator(never_cache, name="dispatch")
class CartClearView(CartTokenMixin, APIView):
    """
    Clear all items from cart.
    """
    
    permission_classes = [AllowAny]
    
    @extend_schema(
        summary="Clear cart",
        description="Remove all items from the cart.",
        parameters=[
            OpenApiParameter(
                name="X-Cart-Token",
                location=OpenApiParameter.HEADER,
                description="Cart token for anonymous users",
                required=False,
                type=str,
            ),
        ],
        responses={
            200: CartSerializer,
            404: OpenApiResponse(description="Cart not found"),
        },
    )
    def delete(self, request):
        """Clear cart."""
        user = request.user if request.user.is_authenticated else None
        cart_token = self.get_cart_token()
        
        if not user and not cart_token:
            return Response(
                {"detail": "Cart token required for anonymous access"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        cart = CartService.resolve_cart(
            user=user,
            cart_token=cart_token,
            create_if_missing=False,
        )
        
        if not cart:
            return Response(
                {"detail": "Cart not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        try:
            CartService.clear_cart(cart)
        except CartNotOpenError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Refresh cart
        cart = Cart.objects.prefetch_related(
            "items__variant__product"
        ).get(id=cart.id)
        
        return Response(CartSerializer(cart).data)


@extend_schema(tags=["Cart"])
@method_decorator(never_cache, name="dispatch")
class CartMergeView(CartTokenMixin, APIView):
    """
    Merge anonymous cart into authenticated user's cart.
    
    Supports dry_run mode for previewing merge without committing.
    
    Only available for authenticated users.
    """
    
    # This endpoint requires authentication
    # permission_classes will default to IsAuthenticated
    
    @extend_schema(
        summary="Merge anonymous cart",
        description=(
            "Merge an anonymous cart (identified by X-Cart-Token) into the "
            "authenticated user's cart. After merge, the anonymous cart is abandoned.\n\n"
            "**Idempotency:** Include `Idempotency-Key` header to prevent duplicate merges.\n\n"
            "**Dry Run:** Add `?dry_run=1` query param to preview merge without committing. "
            "Returns predicted result with warnings but does not modify the database.\n\n"
            "**Stock Policy:** Items exceeding stock are capped or skipped with warnings."
        ),
        parameters=[
            OpenApiParameter(
                name="X-Cart-Token",
                location=OpenApiParameter.HEADER,
                description="Anonymous cart token to merge",
                required=True,
                type=str,
            ),
            OpenApiParameter(
                name="Idempotency-Key",
                location=OpenApiParameter.HEADER,
                description="Unique key to prevent duplicate merges (24h validity)",
                required=False,
                type=str,
            ),
            OpenApiParameter(
                name="dry_run",
                location=OpenApiParameter.QUERY,
                description="Preview merge without committing (1 = dry run)",
                required=False,
                type=str,
            ),
        ],
        request=MergeCartSerializer,
        responses={
            200: CartMergeResultSerializer,
            400: OpenApiResponse(description="No token provided or invalid"),
            401: OpenApiResponse(description="Authentication required"),
            404: OpenApiResponse(description="Anonymous cart not found"),
        },
        examples=[
            OpenApiExample(
                "Merge Result",
                value={
                    "merged_count": 2,
                    "skipped_count": 1,
                    "warnings": [
                        {
                            "variant_id": "550e8400-e29b-41d4-a716-446655440000",
                            "requested": 5,
                            "available": 3,
                            "reason": "insufficient_stock",
                        }
                    ],
                    "cart": {
                        "id": "...",
                        "items": [],
                        "totals": {},
                    },
                },
                response_only=True,
            ),
        ],
    )
    def post(self, request):
        """Merge anonymous cart into user cart."""
        if not request.user or not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )
        
        cart_token = self.get_cart_token()
        idempotency_key = self.get_idempotency_key()
        dry_run = request.query_params.get("dry_run") == "1"
        
        if not cart_token:
            return Response(
                {"detail": "X-Cart-Token header required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Get anonymous cart
        anonymous_cart = CartService.get_cart_by_token(token=cart_token, user=None)
        if not anonymous_cart:
            return Response(
                {"detail": "Anonymous cart not found"},
                status=status.HTTP_404_NOT_FOUND,
            )
        
        # Get or create user cart
        user_cart = CartService.resolve_cart(
            user=request.user,
            cart_token=None,
            create_if_missing=True,
            ip_address=self.get_client_ip(),
            user_agent=self.get_user_agent(),
        )
        
        # Check idempotency (skip for dry_run)
        if idempotency_key and not dry_run:
            existing_record = CartService.check_idempotency(
                key=idempotency_key,
                scope=IdempotencyRecord.Scope.CART_MERGE,
                cart=user_cart,
            )
            if existing_record:
                logger.info(f"Replaying idempotent merge response for key: {idempotency_key[:16]}...")
                return Response(
                    existing_record.response_body,
                    status=existing_record.status_code,
                )
        
        try:
            result = CartService.merge_carts(
                source_cart=anonymous_cart,
                target_cart=user_cart,
                dry_run=dry_run,
            )
        except CartServiceError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
        
        # Refresh user cart for response
        user_cart = Cart.objects.prefetch_related(
            "items__variant__product"
        ).get(id=user_cart.id)
        
        response_data = {
            "merged_count": result["merged_count"],
            "skipped_count": result["skipped_count"],
            "warnings": result.get("warnings", []),
            "dry_run": result.get("dry_run", False),
            "cart": CartSerializer(user_cart).data,
        }
        
        # Add predicted_items for dry_run
        if dry_run:
            response_data["predicted_items"] = result.get("predicted_items", [])
        
        response_status = status.HTTP_200_OK
        
        # Store idempotency record (skip for dry_run)
        if idempotency_key and not dry_run:
            request_hash = CartService.compute_request_hash({"cart_token": str(cart_token)})
            CartService.store_idempotency(
                key=idempotency_key,
                scope=IdempotencyRecord.Scope.CART_MERGE,
                cart=user_cart,
                request_hash=request_hash,
                response_body=response_data,
                status_code=response_status,
            )
        
        return Response(response_data, status=response_status)
