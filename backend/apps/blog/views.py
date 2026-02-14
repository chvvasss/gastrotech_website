"""
Blog views for public and admin endpoints.

Public views are read-only and filter by published status.
Admin views require IsAdminOrEditor permission for CRUD operations.
"""

from django.db.models import Q
from django.utils import timezone
from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.api.permissions import IsAdminOrEditor

from .models import BlogCategory, BlogPost, BlogTag
from .serializers import (
    BlogCategorySerializer,
    BlogPostAdminSerializer,
    BlogPostDetailSerializer,
    BlogPostListSerializer,
    BlogTagSerializer,
)


# ==============================================================================
# Public Views
# ==============================================================================


class BlogPostListView(generics.ListAPIView):
    """
    GET /api/v1/blog/
    
    List published blog posts with pagination.
    Supports filtering by category and search.
    """
    
    permission_classes = [AllowAny]
    serializer_class = BlogPostListSerializer
    
    def get_queryset(self):
        queryset = BlogPost.objects.filter(
            status=BlogPost.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        ).select_related("category", "author", "cover_media").prefetch_related("tags")
        
        # Filter by category slug
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Filter by tag slug
        tag = self.request.query_params.get("tag")
        if tag:
            queryset = queryset.filter(tags__slug=tag)
        
        # Search in title and excerpt
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(excerpt__icontains=search)
            )
        
        return queryset


class BlogPostDetailView(generics.RetrieveAPIView):
    """
    GET /api/v1/blog/{slug}/
    
    Get a single published blog post by slug.
    Increments view count.
    """
    
    permission_classes = [AllowAny]
    serializer_class = BlogPostDetailSerializer
    lookup_field = "slug"
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            status=BlogPost.Status.PUBLISHED,
            published_at__lte=timezone.now(),
        ).select_related("category", "author", "cover_media").prefetch_related("tags")
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Increment view count
        instance.increment_view_count()
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)


class BlogCategoryListView(generics.ListAPIView):
    """
    GET /api/v1/blog/categories/
    
    List all active blog categories.
    """
    
    permission_classes = [AllowAny]
    serializer_class = BlogCategorySerializer
    queryset = BlogCategory.objects.filter(is_active=True)


class BlogFeaturedView(generics.ListAPIView):
    """
    GET /api/v1/blog/featured/
    
    List featured blog posts (max 5).
    """
    
    permission_classes = [AllowAny]
    serializer_class = BlogPostListSerializer
    
    def get_queryset(self):
        return BlogPost.objects.filter(
            status=BlogPost.Status.PUBLISHED,
            published_at__lte=timezone.now(),
            is_featured=True,
        ).select_related("category", "author", "cover_media").prefetch_related("tags")[:5]


class BlogTagListView(generics.ListAPIView):
    """
    GET /api/v1/blog/tags/
    
    List all blog tags.
    """
    
    permission_classes = [AllowAny]
    serializer_class = BlogTagSerializer
    queryset = BlogTag.objects.all()


# ==============================================================================
# Admin Views
# ==============================================================================


class BlogPostAdminListView(generics.ListAPIView):
    """
    GET /api/v1/admin/blog/
    
    List all blog posts (all statuses) for admin.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    serializer_class = BlogPostAdminSerializer
    
    def get_queryset(self):
        queryset = BlogPost.objects.select_related(
            "category", "author", "cover_media"
        ).prefetch_related("tags")
        
        # Filter by status
        post_status = self.request.query_params.get("status")
        if post_status:
            queryset = queryset.filter(status=post_status)
        
        # Filter by category
        category = self.request.query_params.get("category")
        if category:
            queryset = queryset.filter(category__slug=category)
        
        # Search
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) | Q(excerpt__icontains=search)
            )
        
        return queryset


class BlogPostAdminCreateView(generics.CreateAPIView):
    """
    POST /api/v1/admin/blog/
    
    Create a new blog post.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    serializer_class = BlogPostAdminSerializer


class BlogPostAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/v1/admin/blog/{id}/
    
    Get, update, or delete a blog post.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    serializer_class = BlogPostAdminSerializer
    queryset = BlogPost.objects.select_related(
        "category", "author", "cover_media"
    ).prefetch_related("tags")


class BlogCategoryAdminListCreateView(generics.ListCreateAPIView):
    """
    GET/POST /api/v1/admin/blog/categories/
    
    List all categories or create new one.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    serializer_class = BlogCategorySerializer
    queryset = BlogCategory.objects.all()


class BlogCategoryAdminDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET/PUT/DELETE /api/v1/admin/blog/categories/{id}/
    
    Get, update, or delete a category.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    serializer_class = BlogCategorySerializer
    queryset = BlogCategory.objects.all()


class BlogTagAdminListCreateView(generics.ListCreateAPIView):
    """
    GET/POST /api/v1/admin/blog/tags/
    
    List all tags or create new one.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    serializer_class = BlogTagSerializer
    queryset = BlogTag.objects.all()


class BlogTagAdminDeleteView(generics.DestroyAPIView):
    """
    DELETE /api/v1/admin/blog/tags/{id}/
    
    Delete a tag.
    """
    
    permission_classes = [IsAuthenticated, IsAdminOrEditor]
    queryset = BlogTag.objects.all()
