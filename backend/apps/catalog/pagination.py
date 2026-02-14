"""
Custom pagination classes for Gastrotech catalog APIs.
"""

from rest_framework.pagination import CursorPagination


class ProductCursorPagination(CursorPagination):
    """
    Cursor-based pagination for product lists.
    
    Uses created_at for efficient cursor pagination.
    Default page size: 24, max: 100.
    """
    
    page_size = 24
    page_size_query_param = "page_size"
    max_page_size = 100
    ordering = "-created_at"
    cursor_query_param = "cursor"
    
    def get_page_size(self, request):
        """Get page size with validation."""
        if self.page_size_query_param:
            try:
                page_size = int(
                    request.query_params.get(self.page_size_query_param, self.page_size)
                )
                if page_size > 0:
                    return min(page_size, self.max_page_size)
            except (ValueError, TypeError):
                pass
        return self.page_size
