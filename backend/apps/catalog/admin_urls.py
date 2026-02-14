"""
Admin API URL patterns for catalog management.

Uses DRF routers for ViewSets and explicit paths for APIViews.
All endpoints use trailing slashes for DRF consistency.
"""

from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .admin_api import (
    MediaUploadView,
    ProductMediaDeleteView,
    ProductMediaReorderView,
    ProductMediaUploadView,
    JsonImportPreviewView,
    JsonImportCommitView,
    JsonImportUndoView,
)
from .admin_search import AdminSearchView
from .admin_viewsets import (
    AdminBrandViewSet,
    AdminCatalogAssetViewSet,
    AdminCategoryCatalogViewSet,
    AdminCategoryViewSet,
    AdminProductViewSet,
    AdminSeriesViewSet,
    AdminSpecKeyViewSet,
    AdminSpecTemplateViewSet,
    AdminTaxonomyNodeViewSet,
    AdminVariantViewSet,
    TaxonomyGenerateProductsView,
    BulkUploadViewSet,
)
from .stats_api import StatsView

app_name = "catalog_admin"

# Create router for ViewSets (with trailing slash for DRF consistency)
router = DefaultRouter(trailing_slash=True)
router.register(r"brands", AdminBrandViewSet, basename="admin-brands")
router.register(r"categories", AdminCategoryViewSet, basename="admin-categories")
router.register(r"series", AdminSeriesViewSet, basename="admin-series")
router.register(r"taxonomy-nodes", AdminTaxonomyNodeViewSet, basename="admin-taxonomy-nodes")
router.register(r"products", AdminProductViewSet, basename="admin-products")
router.register(r"variants", AdminVariantViewSet, basename="admin-variants")
router.register(r"spec-templates", AdminSpecTemplateViewSet, basename="admin-spec-templates")
router.register(r"spec-keys", AdminSpecKeyViewSet, basename="admin-spec-keys")
router.register(r"bulk-upload", BulkUploadViewSet, basename="admin-bulk-upload")
router.register(r"catalog-assets", AdminCatalogAssetViewSet, basename="admin-catalog-assets")
router.register(r"category-catalogs", AdminCategoryCatalogViewSet, basename="admin-category-catalogs")


urlpatterns = [
    # Global search
    path(
        "search/",
        AdminSearchView.as_view(),
        name="search",
    ),
    
    # Dashboard stats
    path(
        "stats/",
        StatsView.as_view(),
        name="stats",
    ),
    
    # Taxonomy generate products
    path(
        "taxonomy/generate-products/",
        TaxonomyGenerateProductsView.as_view(),
        name="taxonomy-generate-products",
    ),
    
    # Media upload (standalone)
    path(
        "media/upload/",
        MediaUploadView.as_view(),
        name="media-upload",
    ),
    
    # Product media management (nested under products but outside router)
    path(
        "products/<uuid:product_id>/media/upload/",
        ProductMediaUploadView.as_view(),
        name="product-media-upload",
    ),
    path(
        "products/<uuid:product_id>/media/reorder/",
        ProductMediaReorderView.as_view(),
        name="product-media-reorder",
    ),
    path(
        "products/<uuid:product_id>/media/<int:product_media_id>/",
        ProductMediaDeleteView.as_view(),
        name="product-media-delete",
    ),

    # JSON Import
    path(
        "import/json/preview/",
        JsonImportPreviewView.as_view(),
        name="json-import-preview",
    ),
    path(
        "import/json/commit/",
        JsonImportCommitView.as_view(),
        name="json-import-commit",
    ),
    path(
        "import/json/undo/<uuid:job_id>/",
        JsonImportUndoView.as_view(),
        name="json-import-undo",
    ),
    
    # Include router URLs
    path("", include(router.urls)),
]
