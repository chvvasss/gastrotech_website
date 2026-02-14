"""
Tests for Turkish slugify utility.
"""

from django.test import TestCase

from apps.common.slugify_tr import slugify_tr


class SlugifyTrTest(TestCase):
    """Test Turkish-safe slugify function."""
    
    def test_turkish_i_dotless(self):
        """Test Turkish dotless i (ı) conversion."""
        self.assertEqual(slugify_tr("ışık"), "isik")
        self.assertEqual(slugify_tr("kırmızı"), "kirmizi")
    
    def test_turkish_i_dotted(self):
        """Test Turkish dotted I (İ) conversion."""
        self.assertEqual(slugify_tr("İstanbul"), "istanbul")
        self.assertEqual(slugify_tr("İZGARA"), "izgara")
    
    def test_turkish_s_cedilla(self):
        """Test Turkish ş/Ş conversion."""
        self.assertEqual(slugify_tr("şeker"), "seker")
        self.assertEqual(slugify_tr("Şehir"), "sehir")
        self.assertEqual(slugify_tr("Pişirme"), "pisirme")
    
    def test_turkish_g_breve(self):
        """Test Turkish ğ/Ğ conversion."""
        self.assertEqual(slugify_tr("dağ"), "dag")
        self.assertEqual(slugify_tr("soğuk"), "soguk")
        self.assertEqual(slugify_tr("Ağır"), "agir")
    
    def test_turkish_u_umlaut(self):
        """Test Turkish ü/Ü conversion."""
        self.assertEqual(slugify_tr("ünite"), "unite")
        self.assertEqual(slugify_tr("Ünite"), "unite")
        self.assertEqual(slugify_tr("Fritözler"), "fritozler")
    
    def test_turkish_o_umlaut(self):
        """Test Turkish ö/Ö conversion."""
        self.assertEqual(slugify_tr("ölçü"), "olcu")
        self.assertEqual(slugify_tr("Ölçü"), "olcu")
    
    def test_turkish_c_cedilla(self):
        """Test Turkish ç/Ç conversion."""
        self.assertEqual(slugify_tr("çorba"), "corba")
        self.assertEqual(slugify_tr("Çorba"), "corba")
    
    def test_combined_turkish_chars(self):
        """Test multiple Turkish characters in one string."""
        self.assertEqual(slugify_tr("Gazlı Ocaklar"), "gazli-ocaklar")
        self.assertEqual(slugify_tr("Pişirme Üniteleri"), "pisirme-uniteleri")
        self.assertEqual(slugify_tr("Çorba Kazanları"), "corba-kazanlari")
        self.assertEqual(slugify_tr("Izgaralar"), "izgaralar")
    
    def test_spaces_become_dashes(self):
        """Test that spaces are converted to dashes."""
        self.assertEqual(slugify_tr("Hello World"), "hello-world")
        self.assertEqual(slugify_tr("Ara Tezgahlar"), "ara-tezgahlar")
    
    def test_multiple_spaces_normalized(self):
        """Test that multiple spaces become single dash."""
        self.assertEqual(slugify_tr("hello   world"), "hello-world")
    
    def test_empty_string(self):
        """Test empty string returns empty."""
        self.assertEqual(slugify_tr(""), "")
    
    def test_none_handling(self):
        """Test None input returns empty string."""
        self.assertEqual(slugify_tr(None), "")
    
    def test_numbers_preserved(self):
        """Test that numbers are preserved."""
        self.assertEqual(slugify_tr("600 Serisi"), "600-serisi")
        self.assertEqual(slugify_tr("Model GKO6010"), "model-gko6010")
    
    def test_special_chars_removed(self):
        """Test that special characters are removed."""
        self.assertEqual(slugify_tr("Hello! World?"), "hello-world")
        self.assertEqual(slugify_tr("(Test)"), "test")
    
    def test_lowercase_output(self):
        """Test output is lowercase."""
        self.assertEqual(slugify_tr("BÜYÜK HARFLER"), "buyuk-harfler")
    
    def test_leading_trailing_dashes_stripped(self):
        """Test leading/trailing dashes are stripped."""
        self.assertEqual(slugify_tr("---hello---"), "hello")
        self.assertEqual(slugify_tr("  hello  "), "hello")
    
    def test_realistic_product_names(self):
        """Test realistic product names from Gastrotech catalog."""
        self.assertEqual(
            slugify_tr("600 Serisi Gazlı Wok Ocaklar"),
            "600-serisi-gazli-wok-ocaklar"
        )
        self.assertEqual(
            slugify_tr("Elektrikli Fritözler"),
            "elektrikli-fritozler"
        )
        self.assertEqual(
            slugify_tr("Makarna Pişiriciler"),
            "makarna-pisiriciler"
        )
        self.assertEqual(
            slugify_tr("İndüksiyon Ocaklar"),
            "induksiyon-ocaklar"
        )
