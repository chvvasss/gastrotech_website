"""
Tests for the canonical text processing module.

Tests cover:
- Turkish character canonicalization
- Slug generation
- Text comparison
- Empty value normalization
- Hierarchy extraction
"""

from django.test import TestCase

from apps.common.canonical import (
    canonical_tr,
    canonical_text,
    canonical_slug,
    canonical_model_code,
    normalize_empty_value,
    extract_hierarchy_segments,
    compare_canonical,
)


class CanonicalTRTests(TestCase):
    """Tests for Turkish character canonicalization."""

    def test_lowercase_turkish_chars(self):
        """Test lowercase Turkish characters are converted."""
        self.assertEqual(canonical_tr("ı"), "i")  # dotless i
        self.assertEqual(canonical_tr("ş"), "s")  # s cedilla
        self.assertEqual(canonical_tr("ğ"), "g")  # g breve
        self.assertEqual(canonical_tr("ü"), "u")  # u umlaut
        self.assertEqual(canonical_tr("ö"), "o")  # o umlaut
        self.assertEqual(canonical_tr("ç"), "c")  # c cedilla

    def test_uppercase_turkish_chars(self):
        """Test uppercase Turkish characters are converted."""
        self.assertEqual(canonical_tr("İ"), "i")  # I with dot
        self.assertEqual(canonical_tr("Ş"), "s")  # S cedilla
        self.assertEqual(canonical_tr("Ğ"), "g")  # G breve
        self.assertEqual(canonical_tr("Ü"), "u")  # U umlaut
        self.assertEqual(canonical_tr("Ö"), "o")  # O umlaut
        self.assertEqual(canonical_tr("Ç"), "c")  # C cedilla

    def test_mixed_text(self):
        """Test text with mixed Turkish and ASCII characters."""
        self.assertEqual(canonical_tr("Gazlı Ocaklar"), "Gazli Ocaklar")
        self.assertEqual(canonical_tr("Pişirme Üniteleri"), "Pisirme Uniteleri")
        self.assertEqual(canonical_tr("Çorba Kazanları"), "Corba Kazanlari")
        self.assertEqual(canonical_tr("FIRINLAR"), "FIRINLAR")  # No Turkish chars

    def test_empty_string(self):
        """Test empty string handling."""
        self.assertEqual(canonical_tr(""), "")
        self.assertEqual(canonical_tr(None), "")


class CanonicalTextTests(TestCase):
    """Tests for full text canonicalization."""

    def test_lowercase_and_strip(self):
        """Test text is lowercased and stripped."""
        self.assertEqual(canonical_text("  HELLO WORLD  "), "hello world")
        self.assertEqual(canonical_text("Test"), "test")

    def test_turkish_and_lowercase(self):
        """Test Turkish chars and lowercase combined."""
        self.assertEqual(canonical_text("  Gazlı OCAKLAR  "), "gazli ocaklar")
        self.assertEqual(canonical_text("PİŞİRME ÜNİTELERİ"), "pisirme uniteleri")

    def test_whitespace_normalization(self):
        """Test multiple whitespace is normalized."""
        self.assertEqual(canonical_text("hello    world"), "hello world")
        self.assertEqual(canonical_text("a\t\nb"), "a b")


class CanonicalSlugTests(TestCase):
    """Tests for URL-safe slug generation."""

    def test_basic_slugs(self):
        """Test basic slug generation."""
        self.assertEqual(canonical_slug("Hello World"), "hello-world")
        self.assertEqual(canonical_slug("Test Product"), "test-product")

    def test_turkish_slugs(self):
        """Test Turkish text is properly slugified."""
        self.assertEqual(canonical_slug("Gazlı Ocaklar"), "gazli-ocaklar")
        self.assertEqual(canonical_slug("Pişirme Üniteleri"), "pisirme-uniteleri")
        self.assertEqual(canonical_slug("600 Series - Premium"), "600-series-premium")

    def test_special_chars_removed(self):
        """Test special characters are removed."""
        self.assertEqual(canonical_slug("Foo / Bar / Baz"), "foo-bar-baz")
        self.assertEqual(canonical_slug("A & B"), "a-b")
        self.assertEqual(canonical_slug("Test@#$%"), "test")

    def test_multiple_dashes_normalized(self):
        """Test multiple dashes are normalized to single dash."""
        self.assertEqual(canonical_slug("a---b"), "a-b")
        self.assertEqual(canonical_slug("hello   world"), "hello-world")

    def test_max_length(self):
        """Test slug is truncated to max length."""
        long_text = "a" * 300
        slug = canonical_slug(long_text, max_length=50)
        self.assertLessEqual(len(slug), 50)

    def test_empty_string(self):
        """Test empty string handling."""
        self.assertEqual(canonical_slug(""), "")
        self.assertEqual(canonical_slug("   "), "")


class CanonicalModelCodeTests(TestCase):
    """Tests for model code canonicalization."""

    def test_uppercase(self):
        """Test model codes are uppercased."""
        self.assertEqual(canonical_model_code("gko-6010"), "GKO-6010")
        self.assertEqual(canonical_model_code("abc123"), "ABC123")

    def test_strip_whitespace(self):
        """Test whitespace is stripped."""
        self.assertEqual(canonical_model_code("  ABC 123  "), "ABC 123")

    def test_preserve_dashes(self):
        """Test dashes are preserved."""
        self.assertEqual(canonical_model_code("gko-601-a"), "GKO-601-A")


class NormalizeEmptyValueTests(TestCase):
    """Tests for empty value normalization."""

    def test_empty_string(self):
        """Test empty string returns None."""
        self.assertIsNone(normalize_empty_value(""))
        self.assertIsNone(normalize_empty_value("   "))

    def test_dash_values(self):
        """Test dash values return None."""
        self.assertIsNone(normalize_empty_value("-"))
        self.assertIsNone(normalize_empty_value("—"))  # em dash
        self.assertIsNone(normalize_empty_value("–"))  # en dash

    def test_na_values(self):
        """Test N/A values return None."""
        self.assertIsNone(normalize_empty_value("N/A"))
        self.assertIsNone(normalize_empty_value("n/a"))
        self.assertIsNone(normalize_empty_value("#N/A"))

    def test_null_values(self):
        """Test null-like values return None."""
        self.assertIsNone(normalize_empty_value("null"))
        self.assertIsNone(normalize_empty_value("NULL"))
        self.assertIsNone(normalize_empty_value("None"))
        self.assertIsNone(normalize_empty_value("none"))

    def test_nan_values(self):
        """Test NaN values return None."""
        self.assertIsNone(normalize_empty_value("nan"))
        self.assertIsNone(normalize_empty_value("NaN"))

    def test_valid_values(self):
        """Test valid values are returned stripped."""
        self.assertEqual(normalize_empty_value("  hello  "), "hello")
        self.assertEqual(normalize_empty_value("test"), "test")
        self.assertEqual(normalize_empty_value("0"), "0")  # Zero is valid


class ExtractHierarchySegmentsTests(TestCase):
    """Tests for hierarchy segment extraction."""

    def test_slash_separator(self):
        """Test slash separator."""
        result = extract_hierarchy_segments("Fırınlar / Pizza / Elektrikli")
        self.assertEqual(result, ["Fırınlar", "Pizza", "Elektrikli"])

    def test_arrow_separator(self):
        """Test arrow separator."""
        result = extract_hierarchy_segments("A > B > C")
        self.assertEqual(result, ["A", "B", "C"])

    def test_double_arrow_separator(self):
        """Test double arrow separator."""
        result = extract_hierarchy_segments("Root >> Child >> Leaf")
        self.assertEqual(result, ["Root", "Child", "Leaf"])

    def test_no_separator(self):
        """Test single segment without separator."""
        result = extract_hierarchy_segments("SingleCategory")
        self.assertEqual(result, ["SingleCategory"])

    def test_empty_string(self):
        """Test empty string returns empty list."""
        self.assertEqual(extract_hierarchy_segments(""), [])
        self.assertEqual(extract_hierarchy_segments("   "), [])

    def test_strips_whitespace(self):
        """Test segments are stripped of whitespace."""
        result = extract_hierarchy_segments("  A  /  B  /  C  ")
        self.assertEqual(result, ["A", "B", "C"])


class CompareCanonicalTests(TestCase):
    """Tests for canonical text comparison."""

    def test_identical_texts(self):
        """Test identical texts compare equal."""
        self.assertTrue(compare_canonical("hello", "hello"))
        self.assertTrue(compare_canonical("Test", "Test"))

    def test_case_insensitive(self):
        """Test comparison is case insensitive."""
        self.assertTrue(compare_canonical("HELLO", "hello"))
        self.assertTrue(compare_canonical("Test", "TEST"))

    def test_turkish_equivalence(self):
        """Test Turkish equivalence."""
        self.assertTrue(compare_canonical("Gazlı Ocak", "gazli ocak"))
        self.assertTrue(compare_canonical("PİŞİRME", "pisirme"))
        self.assertTrue(compare_canonical("ÇORBA", "corba"))

    def test_whitespace_equivalence(self):
        """Test whitespace normalization in comparison."""
        self.assertTrue(compare_canonical("hello  world", "hello world"))
        self.assertTrue(compare_canonical("  test  ", "test"))

    def test_different_texts(self):
        """Test different texts compare not equal."""
        self.assertFalse(compare_canonical("hello", "world"))
        self.assertFalse(compare_canonical("test", "testing"))

    def test_none_handling(self):
        """Test None handling in comparison."""
        self.assertTrue(compare_canonical(None, None))
        self.assertTrue(compare_canonical(None, ""))
        self.assertFalse(compare_canonical(None, "text"))
