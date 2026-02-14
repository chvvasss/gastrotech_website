"""
Hierarchical Taxonomy Path Parser for Import System.

Parses taxonomy strings like:
- "Fırınlar > Pizza Fırını" (2 levels)
- "Pişirme Üniteleri / Gazlı Ocaklar / 700 Serisi" (3 levels)

Supports:
- Both "/" and ">" delimiters
- Up to 3 levels of hierarchy
- Smart mode creation of missing categories
- Idempotent get_or_create operations
"""

import re
import logging
from typing import List, Optional, Dict, Any, Tuple
from dataclasses import dataclass, field
from django.db import transaction
from django.db.models import Q

from apps.catalog.models import Category
from apps.common.slugify_tr import slugify_tr

logger = logging.getLogger(__name__)

# Maximum allowed depth for category hierarchy
MAX_CATEGORY_DEPTH = 3


@dataclass
class CategorySegment:
    """Represents a single segment in a category path."""
    name: str  # Original name with Turkish chars (for display)
    slug: str  # URL-safe slug
    level: int  # 0 = root, 1 = subcategory, 2 = sub-subcategory


@dataclass
class CategoryResolution:
    """Result of resolving a category path."""
    segments: List[CategorySegment] = field(default_factory=list)
    leaf_category: Optional[Category] = None
    matched_categories: List[Dict[str, Any]] = field(default_factory=list)
    missing_categories: List[Dict[str, Any]] = field(default_factory=list)
    created_categories: List[Dict[str, Any]] = field(default_factory=list)
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to serializable dict."""
        return {
            'segments': [
                {'name': s.name, 'slug': s.slug, 'level': s.level}
                for s in self.segments
            ],
            'leaf_category_id': str(self.leaf_category.id) if self.leaf_category else None,
            'leaf_category_slug': self.leaf_category.slug if self.leaf_category else None,
            'matched_categories': self.matched_categories,
            'missing_categories': self.missing_categories,
            'created_categories': self.created_categories,
            'error': self.error,
        }


def parse_category_path(
    raw_path: str,
    treat_slash_as_hierarchy: bool = True
) -> List[CategorySegment]:
    """
    Parse a category path string into segments.

    Supports both "/" and ">" as delimiters.

    Args:
        raw_path: Raw category path string (e.g., "Fırınlar / Pizza Fırını")
        treat_slash_as_hierarchy: If True, "/" is treated as hierarchy delimiter
                                  If False, "/" is kept as literal character

    Returns:
        List of CategorySegment objects

    Examples:
        >>> parse_category_path("Fırınlar > Pizza Fırını")
        [CategorySegment(name='Fırınlar', slug='firinlar', level=0),
         CategorySegment(name='Pizza Fırını', slug='pizza-firini', level=1)]

        >>> parse_category_path("Pişirme Üniteleri / Gazlı Ocaklar / 700 Serisi")
        [CategorySegment(...), CategorySegment(...), CategorySegment(...)]
    """
    if not raw_path or not raw_path.strip():
        return []

    # Determine delimiter pattern
    if treat_slash_as_hierarchy:
        # Split by both "/" and ">" (trim whitespace around delimiters)
        delimiter_pattern = r'\s*[/>]\s*'
    else:
        # Split by ">" only
        delimiter_pattern = r'\s*>\s*'

    parts = re.split(delimiter_pattern, raw_path.strip())

    # Filter out empty segments and create CategorySegment objects
    segments = []
    for i, part in enumerate(parts):
        part = part.strip()
        if part:
            segments.append(CategorySegment(
                name=part,
                slug=slugify_tr(part),
                level=i,
            ))

    return segments


def resolve_category_chain(
    segments: List[CategorySegment],
    mode: str = 'strict',
    allow_create_missing: bool = False,
) -> CategoryResolution:
    """
    Resolve a list of category segments to actual Category instances.

    Args:
        segments: List of CategorySegment objects from parse_category_path
        mode: Import mode ('strict' or 'smart')
        allow_create_missing: If True (and mode='smart'), create missing categories

    Returns:
        CategoryResolution with matched/missing/created categories
    """
    result = CategoryResolution(segments=segments)

    if not segments:
        result.error = "Empty category path"
        return result

    if len(segments) > MAX_CATEGORY_DEPTH:
        result.error = (
            f"Category path too deep: {len(segments)} levels. "
            f"Maximum allowed is {MAX_CATEGORY_DEPTH} levels."
        )
        return result

    # Walk the hierarchy chain
    parent_category: Optional[Category] = None

    for segment in segments:
        # Look up category with this slug under this parent
        category = Category.objects.filter(
            slug=segment.slug,
            parent=parent_category,
        ).first()

        if category:
            # Found existing category
            result.matched_categories.append({
                'slug': category.slug,
                'name': category.name,
                'level': segment.level,
                'id': str(category.id),
                'parent_id': str(category.parent_id) if category.parent_id else None,
            })
            parent_category = category
        else:
            # Category not found
            missing_info = {
                'slug': segment.slug,
                'name': segment.name,
                'level': segment.level,
                'parent_slug': parent_category.slug if parent_category else None,
                'parent_id': str(parent_category.id) if parent_category else None,
            }
            result.missing_categories.append(missing_info)

            if mode == 'strict' or not allow_create_missing:
                # In strict mode, report error
                result.error = (
                    f"Category '{segment.name}' (slug: {segment.slug}) not found "
                    f"at level {segment.level}"
                    + (f" under parent '{parent_category.name}'" if parent_category else " as root category")
                )
                return result

            # In smart mode with allow_create_missing, we'll create later
            # For now, just mark as missing and continue with None as parent
            # (We can't resolve further without creating)
            break

    # Set leaf category if we resolved all segments
    if len(result.matched_categories) == len(segments):
        result.leaf_category = parent_category

    return result


def get_or_create_category_chain(
    segments: List[CategorySegment],
    series_mode: str = 'disabled',
) -> CategoryResolution:
    """
    Get or create the full category chain atomically.

    This is the main entry point for smart mode category creation.
    Uses get_or_create with proper parent scoping to be idempotent.

    Args:
        segments: List of CategorySegment objects
        series_mode: Value for series_mode field ('disabled', 'optional', 'required')

    Returns:
        CategoryResolution with created/matched categories
    """
    result = CategoryResolution(segments=segments)

    if not segments:
        result.error = "Empty category path"
        return result

    if len(segments) > MAX_CATEGORY_DEPTH:
        result.error = (
            f"Category path too deep: {len(segments)} levels. "
            f"Maximum allowed is {MAX_CATEGORY_DEPTH} levels."
        )
        return result

    # Validate series_mode
    valid_series_modes = ['disabled', 'optional', 'required']
    if series_mode not in valid_series_modes:
        series_mode = 'disabled'  # Safe default

    parent_category: Optional[Category] = None

    try:
        with transaction.atomic():
            for segment in segments:
                # Use get_or_create with parent scoping
                # select_for_update() to prevent race conditions
                existing = Category.objects.select_for_update().filter(
                    slug=segment.slug,
                    parent=parent_category,
                ).first()

                if existing:
                    result.matched_categories.append({
                        'slug': existing.slug,
                        'name': existing.name,
                        'level': segment.level,
                        'id': str(existing.id),
                        'parent_id': str(existing.parent_id) if existing.parent_id else None,
                        'created': False,
                    })
                    parent_category = existing
                else:
                    # Create new category
                    # CRITICAL: Always set series_mode to avoid NULL violation
                    new_category = Category.objects.create(
                        slug=segment.slug,
                        name=segment.name,
                        parent=parent_category,
                        series_mode=series_mode,
                        order=999,  # Place at end of ordering
                    )

                    created_info = {
                        'slug': new_category.slug,
                        'name': new_category.name,
                        'level': segment.level,
                        'id': str(new_category.id),
                        'parent_id': str(new_category.parent_id) if new_category.parent_id else None,
                        'created': True,
                    }
                    result.created_categories.append(created_info)
                    result.matched_categories.append(created_info)

                    logger.info(
                        f"[TAXONOMY] Created category: {new_category.slug} "
                        f"(parent={parent_category.slug if parent_category else 'ROOT'}, "
                        f"series_mode={series_mode})"
                    )

                    parent_category = new_category

            # Set leaf category
            result.leaf_category = parent_category

    except Exception as e:
        logger.exception(f"[TAXONOMY] Error creating category chain: {e}")
        result.error = f"Failed to create category chain: {str(e)}"

    return result


def resolve_taxonomy_for_import(
    raw_path: str,
    mode: str = 'strict',
    treat_slash_as_hierarchy: bool = True,
    allow_create_missing: bool = False,
    series_mode: str = 'disabled',
    dry_run: bool = True,
) -> CategoryResolution:
    """
    Main entry point for resolving taxonomy during import.

    Args:
        raw_path: Raw category path string (e.g., "Fırınlar / Pizza Fırını")
        mode: Import mode ('strict' or 'smart')
        treat_slash_as_hierarchy: If True, "/" is treated as hierarchy delimiter
        allow_create_missing: If True (and mode='smart'), create missing categories
        series_mode: Value for series_mode when creating new categories
        dry_run: If True, don't actually create categories (preview only)

    Returns:
        CategoryResolution with full resolution info

    Examples:
        # Strict mode - just validate
        >>> resolve_taxonomy_for_import("Fırınlar > Pizza", mode='strict')

        # Smart mode preview - show what would be created
        >>> resolve_taxonomy_for_import("New / Category", mode='smart', dry_run=True)

        # Smart mode commit - actually create
        >>> resolve_taxonomy_for_import("New / Category", mode='smart', dry_run=False)
    """
    # Parse the path into segments
    segments = parse_category_path(raw_path, treat_slash_as_hierarchy)

    if not segments:
        return CategoryResolution(error="Empty or invalid category path")

    if dry_run or mode == 'strict' or not allow_create_missing:
        # Just resolve and report what exists/is missing
        return resolve_category_chain(
            segments,
            mode=mode,
            allow_create_missing=False,  # Don't create during dry_run
        )
    else:
        # Actually create missing categories
        return get_or_create_category_chain(
            segments,
            series_mode=series_mode,
        )


# ============================================================================
# Legacy compatibility functions (for existing code)
# ============================================================================

def parse_taxonomy_path(taxonomy_str: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Legacy function: Parse taxonomy path into (root_slug, subcategory_slug).

    DEPRECATED: Use parse_category_path() instead for full hierarchy support.

    This function is kept for backward compatibility with existing code.
    """
    segments = parse_category_path(taxonomy_str, treat_slash_as_hierarchy=True)

    if len(segments) == 0:
        return (None, None)
    elif len(segments) == 1:
        return (segments[0].slug, None)
    elif len(segments) >= 2:
        # Return root and last segment (leaf)
        return (segments[0].slug, segments[-1].slug)


def resolve_taxonomy_category(
    taxonomy_str: str,
    mode: str = 'strict'
) -> Dict[str, Any]:
    """
    Legacy function: Resolve taxonomy path to a Category instance or candidate.

    DEPRECATED: Use resolve_taxonomy_for_import() instead.
    """
    result = resolve_taxonomy_for_import(
        taxonomy_str,
        mode=mode,
        treat_slash_as_hierarchy=True,
        allow_create_missing=(mode == 'smart'),
        dry_run=True,  # Legacy function doesn't create
    )

    if result.error:
        return {'error': result.error}

    if result.leaf_category:
        return {'category': result.leaf_category}

    if result.missing_categories:
        # Return first missing as candidate
        missing = result.missing_categories[0]
        return {
            'candidate': {
                'type': 'category',
                'entity': 'root' if missing['level'] == 0 else 'subcategory',
                'slug': missing['slug'],
                'name': missing['name'],
                'parent': missing.get('parent_id'),
                'parent_slug': missing.get('parent_slug'),
            }
        }

    return {'error': 'Unable to resolve taxonomy'}


def get_or_create_taxonomy_category(
    taxonomy_str: str,
    mode: str = 'smart'
) -> Tuple[Optional[Category], Optional[Dict]]:
    """
    Legacy function: Get or create category from taxonomy path.

    DEPRECATED: Use resolve_taxonomy_for_import() with dry_run=False instead.
    """
    result = resolve_taxonomy_for_import(
        taxonomy_str,
        mode=mode,
        treat_slash_as_hierarchy=True,
        allow_create_missing=True,
        series_mode='disabled',  # Safe default
        dry_run=False,  # Actually create
    )

    if result.error:
        return (None, {'error': result.error})

    return (result.leaf_category, None)


def validate_series_category_match(series, target_category) -> Tuple[Optional[str], str]:
    """
    Validate that a series belongs to the target category or one of its ancestors.

    Supports hierarchical categories where a series can belong to a parent
    category while products are assigned to child categories.

    Args:
        series: Series instance
        target_category: Category instance (should be leaf or any descendant)

    Returns:
        Tuple of (error_message, match_type) where:
        - error_message: None if valid, error string if mismatch
        - match_type: 'exact', 'ancestor', or 'mismatch'
    """
    if not series or not target_category:
        return None, 'exact'

    # Exact match - series category matches target category directly
    if series.category_id == target_category.id:
        return None, 'exact'

    # Check if series.category is an ancestor of target_category
    # by walking up the parent chain from target_category
    current = target_category.parent
    while current:
        if current.id == series.category_id:
            return None, 'ancestor'
        current = current.parent

    # Mismatch - categories are unrelated
    return (
        f'Series "{series.slug}" belongs to category "{series.category.name}", '
        f'but file specifies "{target_category.name}" which is not a descendant. '
        f'Series must be assigned to an ancestor category of the product category.',
        'mismatch'
    )

