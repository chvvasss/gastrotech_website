"""
Admin API URL patterns for inquiries management.
All endpoints use trailing slashes for DRF consistency.
"""

from django.urls import path

from .admin_api import InquiryListView, InquiryDetailView

app_name = "inquiries_admin"

urlpatterns = [
    path(
        "inquiries/",
        InquiryListView.as_view(),
        name="inquiry-list",
    ),
    path(
        "inquiries/<uuid:inquiry_id>/",
        InquiryDetailView.as_view(),
        name="inquiry-detail",
    ),
]
