"""
Turkish-safe slugify utility.

Handles Turkish characters properly before applying Django's slugify.
"""

import re
import unicodedata

from django.utils.text import slugify as django_slugify


# Turkish character mapping
TURKISH_CHAR_MAP = {
    "ı": "i",
    "İ": "i",
    "ş": "s",
    "Ş": "s",
    "ğ": "g",
    "Ğ": "g",
    "ü": "u",
    "Ü": "u",
    "ö": "o",
    "Ö": "o",
    "ç": "c",
    "Ç": "c",
}


def slugify_tr(text: str) -> str:
    """
    Create a URL-friendly slug from Turkish text.
    
    Replaces Turkish-specific characters before applying Django's slugify.
    Normalizes multiple dashes to single dash.
    
    Args:
        text: The text to slugify
        
    Returns:
        A URL-safe slug string
        
    Examples:
        >>> slugify_tr("Gazlı Ocaklar")
        'gazli-ocaklar'
        >>> slugify_tr("Pişirme Üniteleri")
        'pisirme-uniteleri'
        >>> slugify_tr("Çorba Kazanları")
        'corba-kazanlari'
    """
    if not text:
        return ""
    
    # Replace Turkish characters
    result = text
    for turkish_char, ascii_char in TURKISH_CHAR_MAP.items():
        result = result.replace(turkish_char, ascii_char)
    
    # Apply Django's slugify (handles lowercase, spaces, etc.)
    slug = django_slugify(result)
    
    # Normalize multiple dashes to single dash
    slug = re.sub(r"-+", "-", slug)
    
    # Strip leading/trailing dashes
    slug = slug.strip("-")
    
    return slug
