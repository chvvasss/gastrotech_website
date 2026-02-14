"""
Admin URL configuration for Blog API.

These endpoints require IsAdminOrEditor permission.
"""

from django.urls import path

from .views import (
    BlogCategoryAdminDetailView,
    BlogCategoryAdminListCreateView,
    BlogPostAdminCreateView,
    BlogPostAdminDetailView,
    BlogPostAdminListView,
    BlogTagAdminDeleteView,
    BlogTagAdminListCreateView,
)

urlpatterns = [
    # Blog posts
    path("blog/", BlogPostAdminListView.as_view(), name="admin_blog_list"),
    path("blog/create/", BlogPostAdminCreateView.as_view(), name="admin_blog_create"),
    path("blog/<uuid:pk>/", BlogPostAdminDetailView.as_view(), name="admin_blog_detail"),
    
    # Categories
    path("blog/categories/", BlogCategoryAdminListCreateView.as_view(), name="admin_blog_categories"),
    path("blog/categories/<uuid:pk>/", BlogCategoryAdminDetailView.as_view(), name="admin_blog_category_detail"),
    
    # Tags
    path("blog/tags/", BlogTagAdminListCreateView.as_view(), name="admin_blog_tags"),
    path("blog/tags/<uuid:pk>/", BlogTagAdminDeleteView.as_view(), name="admin_blog_tag_delete"),
]
