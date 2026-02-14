"""
Orders app for B2B order management.

This app will contain models for:
- Order: Customer orders
- OrderItem: Individual items in an order
- Quote: Price quotes for B2B customers

This app is payment-ready but payments are not currently enabled.
Payment integration (Stripe, etc.) can be added when needed.

Models will be added in a future iteration.
"""

default_app_config = "apps.orders.apps.OrdersConfig"
