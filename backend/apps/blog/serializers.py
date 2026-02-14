"""
Blog serializers for API endpoints.

Provides serializers for:
- Public views (list, detail)
- Admin CRUD operations
"""

from rest_framework import serializers

from apps.catalog.serializers import MediaMetadataSerializer

from .models import BlogCategory, BlogPost, BlogTag


class BlogCategorySerializer(serializers.ModelSerializer):
    """Serializer for blog categories."""
    
    posts_count = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogCategory
        fields = [
            "id",
            "name_tr",
            "name_en",
            "slug",
            "description",
            "order",
            "is_active",
            "posts_count",
        ]
        read_only_fields = ["id", "posts_count", "slug"]
    
    def get_posts_count(self, obj):
        """Get count of published posts in this category."""
        return obj.posts.filter(status="published").count()


class BlogTagSerializer(serializers.ModelSerializer):
    """Serializer for blog tags."""
    
    class Meta:
        model = BlogTag
        fields = ["id", "name", "slug"]
        read_only_fields = ["id", "slug"]


class BlogPostListSerializer(serializers.ModelSerializer):
    """
    Serializer for blog post list view.
    
    Minimal data for list performance.
    """
    
    category = BlogCategorySerializer(read_only=True)
    tags = BlogTagSerializer(many=True, read_only=True)
    author_name = serializers.SerializerMethodField()
    cover_url = serializers.SerializerMethodField()
    
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "cover_url",
            "category",
            "tags",
            "author_name",
            "published_at",
            "is_featured",
            "reading_time_min",
            "view_count",
        ]
    
    def get_author_name(self, obj):
        """Get author display name."""
        if obj.author:
            return obj.author.get_full_name() or obj.author.email
        return None
    
    def get_cover_url(self, obj):
        """Get cover image URL."""
        if obj.cover_media:
            request = self.context.get("request")
            if request:
                return request.build_absolute_uri(
                    f"/api/v1/media/{obj.cover_media.id}/file/"
                )
            return f"/api/v1/media/{obj.cover_media.id}/file/"
        return None


class BlogPostDetailSerializer(BlogPostListSerializer):
    """
    Serializer for blog post detail view.
    
    Full content included.
    """
    
    class Meta(BlogPostListSerializer.Meta):
        fields = BlogPostListSerializer.Meta.fields + [
            "content",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]


class BlogPostAdminSerializer(serializers.ModelSerializer):
    """
    Serializer for admin CRUD operations.
    
    Includes all fields and supports write operations.
    """
    
    category_detail = BlogCategorySerializer(source="category", read_only=True)
    tags_detail = BlogTagSerializer(source="tags", many=True, read_only=True)
    author_name = serializers.SerializerMethodField()
    cover = MediaMetadataSerializer(source="cover_media", read_only=True)
    
    # Write fields
    category_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    tag_ids = serializers.ListField(
        child=serializers.UUIDField(),
        write_only=True,
        required=False,
    )
    cover_media_id = serializers.UUIDField(write_only=True, required=False, allow_null=True)
    
    class Meta:
        model = BlogPost
        fields = [
            "id",
            "title",
            "slug",
            "excerpt",
            "content",
            "cover",
            "cover_media_id",
            "category_detail",
            "category_id",
            "tags_detail",
            "tag_ids",
            "author",
            "author_name",
            "status",
            "published_at",
            "is_featured",
            "view_count",
            "reading_time_min",
            "meta_title",
            "meta_description",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "slug",
            "author",
            "view_count",
            "reading_time_min",
            "created_at",
            "updated_at",
        ]
    
    def get_author_name(self, obj):
        """Get author display name."""
        if obj.author:
            return obj.author.get_full_name() or obj.author.email
        return None
    
    def create(self, validated_data):
        """Create blog post with category and tags."""
        category_id = validated_data.pop("category_id", None)
        tag_ids = validated_data.pop("tag_ids", [])
        cover_media_id = validated_data.pop("cover_media_id", None)
        
        # Set author from request
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            validated_data["author"] = request.user
        
        # Set category
        if category_id:
            validated_data["category_id"] = category_id
        
        # Set cover media
        if cover_media_id:
            validated_data["cover_media_id"] = cover_media_id
        
        post = BlogPost.objects.create(**validated_data)
        
        # Set tags
        if tag_ids:
            post.tags.set(tag_ids)
        
        return post
    
    def update(self, instance, validated_data):
        """Update blog post with category and tags."""
        # Handle fields that might be cleared (None) or not provided
        if "category_id" in validated_data:
            instance.category_id = validated_data.pop("category_id")
            
        if "cover_media_id" in validated_data:
            instance.cover_media_id = validated_data.pop("cover_media_id")
            
        if "tag_ids" in validated_data:
            tag_ids = validated_data.pop("tag_ids")
            instance.tags.set(tag_ids)

        # Update basic fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        instance.save()
        
        return instance
