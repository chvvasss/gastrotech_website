"""
Canonical text processing utilities for Gastrotech.

This module provides standardized text canonicalization functions
used throughout the codebase for:
- Import processing
- Admin create/update operations
- Search and matching
- URL slug generation

IMPORTANT: Use these functions consistently across the codebase to
ensure deterministic behavior in imports and lookups.
"""

import re
import unicodedata
from typing import Optional

from django.utils.text import slugify as django_slugify


# Turkish character mapping (comprehensive)
TURKISH_CHAR_MAP = {
    # Lowercase
    "ı": "i",  # dotless i -> i
    "ş": "s",  # s with cedilla -> s
    "ğ": "g",  # g with breve -> g
    "ü": "u",  # u with umlaut -> u
    "ö": "o",  # o with umlaut -> o
    "ç": "c",  # c with cedilla -> c
    # Uppercase
    "İ": "i",  # I with dot -> i
    "Ş": "s",  # S with cedilla -> s
    "Ğ": "g",  # G with breve -> g
    "Ü": "u",  # U with umlaut -> u
    "Ö": "o",  # O with umlaut -> o
    "Ç": "c",  # C with cedilla -> c
}

# Reverse mapping for reconstruction (if needed)
ASCII_TO_TURKISH_MAP = {
    "i": "i",  # ambiguous - could be i or ı
    "s": "s",  # ambiguous - could be s or ş
    "g": "g",  # ambiguous - could be g or ğ
    "u": "u",  # ambiguous - could be u or ü
    "o": "o",  # ambiguous - could be o or ö
    "c": "c",  # ambiguous - could be c or ç
}


def canonical_tr(text: str) -> str:
    """
    Canonicalize Turkish text by replacing Turkish-specific characters
    with their ASCII equivalents.

    This is the base canonicalization function used for:
    - Text comparison
    - Search matching
    - Before slug generation

    Args:
        text: Input text (may contain Turkish characters)

    Returns:
        Text with Turkish characters replaced by ASCII equivalents

    Examples:
        >>> canonical_tr("Gazlı Ocaklar")
        'Gazli Ocaklar'
        >>> canonical_tr("Pişirme Üniteleri")
        'Pisirme Uniteleri'
        >>> canonical_tr("Çorba Kazanları")
        'Corba Kazanlari'
    """
    if not text:
        return ""

    result = text
    for turkish_char, ascii_char in TURKISH_CHAR_MAP.items():
        result = result.replace(turkish_char, ascii_char)

    return result


def canonical_text(text: str) -> str:
    """
    Full text canonicalization: lowercase, strip whitespace,
    normalize Turkish characters.

    Use this for text comparison and matching.

    Args:
        text: Input text

    Returns:
        Canonicalized lowercase text

    Examples:
        >>> canonical_text("  Gazlı OCAKLAR  ")
        'gazli ocaklar'
        >>> canonical_text("PİŞİRME ÜNİTELERİ")
        'pisirme uniteleri'
    """
    if not text:
        return ""

    # Apply Turkish canonicalization
    result = canonical_tr(text)

    # Lowercase
    result = result.lower()

    # Normalize whitespace (multiple spaces -> single space)
    result = re.sub(r"\s+", " ", result)

    # Strip leading/trailing whitespace
    result = result.strip()

    return result


def canonical_slug(text: str, max_length: int = 255) -> str:
    """
    Generate a URL-safe slug from text.

    This is the single source of truth for slug generation.
    Use this function everywhere instead of direct slugify calls.

    Args:
        text: Input text
        max_length: Maximum length of the slug (default: 255)

    Returns:
        URL-safe slug string

    Examples:
        >>> canonical_slug("Gazlı Ocaklar")
        'gazli-ocaklar'
        >>> canonical_slug("Pişirme Üniteleri")
        'pisirme-uniteleri'
        >>> canonical_slug("600 Series - Premium")
        '600-series-premium'
        >>> canonical_slug("Foo / Bar / Baz")
        'foo-bar-baz'
    """
    if not text:
        return ""

    # Apply Turkish canonicalization first
    result = canonical_tr(text)

    # Apply Django's slugify (handles lowercase, removes special chars)
    slug = django_slugify(result)

    # Normalize multiple dashes to single dash
    slug = re.sub(r"-+", "-", slug)

    # Strip leading/trailing dashes
    slug = slug.strip("-")

    # Enforce max length (truncate at word boundary if possible)
    if len(slug) > max_length:
        slug = slug[:max_length]
        # Try to cut at last dash
        last_dash = slug.rfind("-")
        if last_dash > max_length // 2:
            slug = slug[:last_dash]
        slug = slug.strip("-")

    return slug


def canonical_model_code(code: str) -> str:
    """
    Canonicalize model code for matching.

    Model codes should be:
    - Uppercase
    - No leading/trailing whitespace
    - Dashes preserved

    Args:
        code: Raw model code

    Returns:
        Canonicalized model code

    Examples:
        >>> canonical_model_code("gko-6010")
        'GKO-6010'
        >>> canonical_model_code("  ABC 123  ")
        'ABC 123'
    """
    if not code:
        return ""

    # Strip whitespace
    result = code.strip()

    # Uppercase
    result = result.upper()

    return result


def normalize_empty_value(value: Optional[str]) -> Optional[str]:
    """
    Normalize empty-like values to None.

    Import files often contain various representations of "empty":
    - Empty string
    - "-" or "—"
    - "N/A", "n/a", "#N/A"
    - "null", "NULL", "None"
    - "nan", "NaN"

    Args:
        value: Input value (may be None or empty-like)

    Returns:
        None if value is empty-like, otherwise the stripped value

    Examples:
        >>> normalize_empty_value("")
        None
        >>> normalize_empty_value("-")
        None
        >>> normalize_empty_value("  hello  ")
        'hello'
    """
    if value is None:
        return None

    stripped = str(value).strip()

    # Check against empty-like values
    empty_values = {
        "",
        "-",
        "—",
        "–",  # various dashes
        "n/a",
        "N/A",
        "#N/A",
        "null",
        "NULL",
        "none",
        "None",
        "nan",
        "NaN",
        "undefined",
    }

    if stripped.lower() in {v.lower() for v in empty_values}:
        return None

    return stripped


def extract_hierarchy_segments(path: str, separators: tuple = ("/", ">", ">>")) -> list:
    """
    Extract hierarchy segments from a path string.

    Args:
        path: Path like "Root / Sub / Leaf" or "Root > Sub > Leaf"
        separators: Tuple of separator characters to consider

    Returns:
        List of segment names

    Examples:
        >>> extract_hierarchy_segments("Fırınlar / Pizza / Elektrikli")
        ['Fırınlar', 'Pizza', 'Elektrikli']
        >>> extract_hierarchy_segments("A > B > C")
        ['A', 'B', 'C']
    """
    if not path:
        return []

    # Find which separator is used
    for sep in separators:
        if sep in path:
            segments = [s.strip() for s in path.split(sep) if s.strip()]
            return segments

    # No separator found - treat as single segment
    return [path.strip()] if path.strip() else []


def compare_canonical(text1: Optional[str], text2: Optional[str]) -> bool:
    """
    Compare two texts after canonicalization.

    Useful for matching imports against existing data.

    Args:
        text1: First text
        text2: Second text

    Returns:
        True if texts are equivalent after canonicalization

    Examples:
        >>> compare_canonical("Gazlı Ocak", "gazli ocak")
        True
        >>> compare_canonical("PİŞİRME", "pisirme")
        True
    """
    return canonical_text(text1 or "") == canonical_text(text2 or "")


# Backwards compatibility aliases
slugify_tr = canonical_slug
