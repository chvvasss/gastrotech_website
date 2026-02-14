"""
URL patterns for inquiries API.
All URLs use trailing slashes for DRF consistency.
"""

from django.urls import path

from .views import InquiryCreateView, QuoteComposeView, QuoteValidateView

app_name = "inquiries"

urlpatterns = [
    path("inquiries/", InquiryCreateView.as_view(), name="inquiry-create"),
    path("quote/validate/", QuoteValidateView.as_view(), name="quote-validate"),
    path("quote/compose/", QuoteComposeView.as_view(), name="quote-compose"),
]
