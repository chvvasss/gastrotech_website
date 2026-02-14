"""
Query helpers for catalog filtering and taxonomy lookups.

Keeps common logic (boolean parsing, category scope resolution) in one place
to ensure filters and views behave consistently.
"""

from __future__ import annotations

from typing import Iterable, Optional, Set

from .models import Category


TRUE_VALUES = {"1", "true", "yes", "y", "t"}
FALSE_VALUES = {"0", "false", "no", "n", "f"}


def parse_bool_param(value: Optional[str]) -> Optional[bool]:
    """Parse a boolean-ish query param into True/False/None."""
    if value is None:
        return None
    normalized = value.strip().lower()
    if normalized in TRUE_VALUES:
        return True
    if normalized in FALSE_VALUES:
        return False
    return None


def resolve_category_ids(
    slugs: Iterable[str],
    include_descendants: bool,
) -> Set[str]:
    """
    Resolve category IDs for the given slugs.

    If include_descendants is True, all descendant categories are included.
    """
    clean_slugs = [s.strip() for s in slugs if s and str(s).strip()]
    if not clean_slugs:
        return set()

    category_ids = set(
        Category.objects.filter(slug__in=clean_slugs).values_list("id", flat=True)
    )

    if not include_descendants or not category_ids:
        return category_ids

    pending = set(category_ids)
    while pending:
        child_ids = set(
            Category.objects.filter(parent_id__in=pending).values_list("id", flat=True)
        )
        new_children = child_ids - category_ids
        if not new_children:
            break
        category_ids.update(new_children)
        pending = new_children

    return category_ids
