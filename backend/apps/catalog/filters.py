"""
Django-filter FilterSets for Gastrotech catalog APIs.

Provides filtering for:
- Products: by series, taxonomy node, status, search, sort
"""

from django.db.models import Q

import django_filters

from .models import Product, TaxonomyNode, Series
from .query_utils import parse_bool_param, resolve_category_ids


class ProductFilter(django_filters.FilterSet):
    """
    FilterSet for Product list endpoint.
    
    Filters:
    - series: by series slug
    - node: by taxonomy node slug (primary_node OR in product.nodes)
    - status: publication status (default: active)
    - search: search in title_tr, title_en, variant model_code
    - sort: ordering (newest, featured, title_asc)
    """
    
    series = django_filters.CharFilter(
        field_name="series__slug",
        lookup_expr="exact",
        help_text="Filter by series slug",
    )
    
    node = django_filters.CharFilter(
        method="filter_by_node",
        help_text="Filter by taxonomy node slug (includes primary_node and associated nodes)",
    )
    
    status = django_filters.ChoiceFilter(
        choices=Product.Status.choices,
        help_text="Filter by status (default: active for public views)",
    )
    
    search = django_filters.CharFilter(
        method="filter_by_search",
        help_text="Search in title_tr, title_en, and variant model_code",
    )
    
    sort = django_filters.ChoiceFilter(
        method="apply_sort",
        choices=[
            ("newest", "Newest first"),
            ("featured", "Featured first"),
            ("title_asc", "Title A-Z"),
        ],
        help_text="Sort order",
    )
    
    category = django_filters.CharFilter(
        method="filter_by_category",
        help_text="Filter by category slug (comma-separated for multiple)",
    )
    
    is_featured = django_filters.BooleanFilter(
        field_name="is_featured",
        help_text="Filter by featured status",
    )
    
    brand = django_filters.CharFilter(
        field_name="brand__slug",
        lookup_expr="exact",
        help_text="Filter by brand slug",
    )
    
    class Meta:
        model = Product
        fields = ["series", "node", "status", "search", "sort", "category", "is_featured", "brand"]

    def filter_by_category(self, queryset, name, value):
        """
        Filter by category slug. Supports comma-separated values.
        Includes all descendant categories (recursive) by default.
        Set include_descendants=false to limit to direct categories only.
        """
        if not value:
            return queryset
            
        slugs = [s.strip() for s in value.split(",") if s.strip()]
        if not slugs:
            return queryset

        include_descendants = parse_bool_param(
            getattr(self.request, "query_params", {}).get("include_descendants")
            if self.request
            else None
        )
        # Preserve existing behavior unless explicitly disabled
        include_descendants = True if include_descendants is None else include_descendants

        category_ids = resolve_category_ids(slugs, include_descendants=include_descendants)
        if not category_ids:
            return queryset.none()

        return queryset.filter(series__category__id__in=category_ids).distinct()

    def filter_by_node(self, queryset, name, value):
        """
        Filter products by taxonomy node slug.
        
        Includes products where:
        - primary_node matches the slug, OR
        - product.nodes includes a node with this slug
        """
        if not value:
            return queryset
        
        # Get nodes by slug (slugs are not unique globally, only per series/parent)
        nodes = TaxonomyNode.objects.filter(slug=value)
        
        if not nodes.exists():
            return queryset.none()
        
        return queryset.filter(
            Q(primary_node__in=nodes) | Q(nodes__in=nodes)
        ).distinct()
    
    def filter_by_search(self, queryset, name, value):
        """
        Search across title, variants (code, name, sku) and hierarchy (series, category).
        """
        if not value:
            return queryset
        
        search_term = value.strip()[:200]
        if not search_term:
            return queryset
        
        # Search in product fields, variant fields and hierarchy
        return queryset.filter(
            Q(title_tr__icontains=search_term) |
            Q(title_en__icontains=search_term) |
            Q(name__icontains=search_term) |
            # Variants
            Q(variants__model_code__icontains=search_term) |
            Q(variants__sku__icontains=search_term) |
            Q(variants__name_tr__icontains=search_term) |
            Q(variants__name_en__icontains=search_term) |
            # Hierarchy
            Q(series__name__icontains=search_term) |
            Q(series__category__name__icontains=search_term)
        ).distinct()
    
    def apply_sort(self, queryset, name, value):
        """Apply sorting based on sort parameter."""
        if value == "newest":
            return queryset.order_by("-created_at")
        elif value == "featured":
            return queryset.order_by("-is_featured", "-created_at")
        elif value == "title_asc":
            return queryset.order_by("title_tr")
        return queryset


class SeriesFilter(django_filters.FilterSet):
    """
    FilterSet for Series list endpoint.
    
    Filters:
    - category: by category slug
    """
    
    category = django_filters.CharFilter(
        field_name="category__slug",
        lookup_expr="exact",
        help_text="Filter by category slug",
    )
    
    class Meta:
        model = Series
        fields = ["category"]


class TaxonomyNodeFilter(django_filters.FilterSet):
    """
    FilterSet for TaxonomyNode list endpoint.
    
    Filters:
    - series: by series slug
    """
    
    series = django_filters.CharFilter(
        field_name="series__slug",
        lookup_expr="exact",
        help_text="Filter by series slug",
    )
    
    class Meta:
        model = TaxonomyNode
        fields = ["series"]
