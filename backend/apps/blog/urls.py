"""
Public URL configuration for Blog API.

These endpoints are accessible without authentication.
"""

from django.urls import path

from .views import (
    BlogCategoryListView,
    BlogFeaturedView,
    BlogPostDetailView,
    BlogPostListView,
    BlogTagListView,
)

urlpatterns = [
    # Blog posts
    path("blog/", BlogPostListView.as_view(), name="blog_list"),
    path("blog/featured/", BlogFeaturedView.as_view(), name="blog_featured"),
    path("blog/categories/", BlogCategoryListView.as_view(), name="blog_categories"),
    path("blog/tags/", BlogTagListView.as_view(), name="blog_tags"),
    path("blog/<slug:slug>/", BlogPostDetailView.as_view(), name="blog_detail"),
]
