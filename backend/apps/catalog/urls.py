"""
URL configuration for Gastrotech catalog public APIs.

All endpoints are public (AllowAny).
All URLs use trailing slashes for DRF consistency.
"""

from django.urls import path

from .views import (
    BrandCategoriesUpdateView,
    BrandDetailView,
    BrandListView,
    BrowseCategoryView,
    CatalogAssetListView,
    CategoryCatalogListView,
    CategoryChildrenView,
    CategoryDetailView,
    CategoryListView,
    CategoryTreeView,
    MediaFileView,
    MediaMetadataView,
    NavView,
    ProductDetailView,
    ProductListView,
    SeriesListView,
    SpecKeyListView,
    TaxonomyTreeView,
    VariantByCodesView,
)
from .plp import PLPView

app_name = "catalog"

urlpatterns = [
    # Navigation
    path("nav/", NavView.as_view(), name="nav"),
    path("browse/", BrowseCategoryView.as_view(), name="browse"),
    
    # PLP (Product Listing Page with faceted filters)
    path("plp/", PLPView.as_view(), name="plp"),

    # Categories
    path("categories/", CategoryListView.as_view(), name="category-list"),
    path("categories/tree/", CategoryTreeView.as_view(), name="category-tree"),
    path("categories/<slug:slug>/", CategoryDetailView.as_view(), name="category-detail"),
    path("categories/<slug:slug>/children/", CategoryChildrenView.as_view(), name="category-children"),

    # Series
    path("series/", SeriesListView.as_view(), name="series-list"),
    
    # Brands
    path("brands/", BrandListView.as_view(), name="brand-list"),
    path("brands/<slug:slug>/", BrandDetailView.as_view(), name="brand-detail"),
    path("brands/<slug:slug>/categories/", BrandCategoriesUpdateView.as_view(), name="brand-categories-update"),

    # Taxonomy
    path("taxonomy/tree/", TaxonomyTreeView.as_view(), name="taxonomy-tree"),
    
    # Spec Keys
    path("spec-keys/", SpecKeyListView.as_view(), name="spec-key-list"),
    
    # Products
    path("products/", ProductListView.as_view(), name="product-list"),
    path("products/<slug:slug>/", ProductDetailView.as_view(), name="product-detail"),
    
    # Media
    path("media/<uuid:id>/", MediaMetadataView.as_view(), name="media-metadata"),
    path("media/<uuid:id>/file/", MediaFileView.as_view(), name="media-file"),
    
    # Catalog Assets (PDF downloads)
    path("catalog-assets/", CatalogAssetListView.as_view(), name="catalog-asset-list"),

    # Category Catalogs (catalog mode PDFs)
    path("category-catalogs/", CategoryCatalogListView.as_view(), name="category-catalog-list"),
    
    # Variant Lookup
    path("variants/by-codes/", VariantByCodesView.as_view(), name="variants-by-codes"),
]
