"""
URL configuration for the orders app (Cart API).

All cart endpoints are under /api/v1/cart/
"""

from django.urls import path

from apps.orders.views import (
    CartClearView,
    CartItemDetailView,
    CartItemsView,
    CartMergeView,
    CartView,
    CreateCartTokenView,
)

app_name = "orders"

urlpatterns = [
    # Create anonymous cart token
    path("token/", CreateCartTokenView.as_view(), name="cart_create_token"),
    
    # Get current cart
    path("", CartView.as_view(), name="cart_detail"),
    
    # Add items to cart
    path("items/", CartItemsView.as_view(), name="cart_add_item"),
    
    # Update/remove specific item
    path("items/<uuid:item_id>/", CartItemDetailView.as_view(), name="cart_item_detail"),
    
    # Clear cart
    path("clear/", CartClearView.as_view(), name="cart_clear"),
    
    # Merge anonymous cart into user cart
    path("merge/", CartMergeView.as_view(), name="cart_merge"),
]
