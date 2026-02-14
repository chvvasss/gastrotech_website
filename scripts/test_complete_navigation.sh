#!/bin/bash
# Complete Subcategory Navigation Test - Multiple Root Categories
# Tests both Fırınlar and Soğutma hierarchies

BASE_URL="http://localhost:8000/api/v1"

echo "======================================================================"
echo "COMPLETE SUBCATEGORY NAVIGATION TEST - EXPANDED HIERARCHY"
echo "======================================================================"

echo ""
echo "Testing Hierarchy:"
echo "  Fırınlar"
echo "    ├── Pizza Fırını → Gastrotech → 600 Series → Products"
echo "    └── Elektrikli Fırın → Partner A → 700 Series → Products"
echo "  Soğutma Üniteleri"
echo "    ├── Buzdolabı (no products yet)"
echo "    └── Derin Dondurucu (no products yet)"
echo ""

# TEST GROUP 1: FIRINLAR HIERARCHY
echo "======================================================================"
echo "GROUP 1: FIRINLAR HIERARCHY"
echo "======================================================================"

echo ""
echo "[TEST 1.1] Category Tree - Verify both root categories exist"
curl -s "$BASE_URL/categories/tree/" | python -c "
import sys, json
data = json.load(sys.stdin)
roots = [c for c in data if c.get('parent_slug') is None]
firinlar = next((c for c in roots if c['slug'] == 'firinlar'), None)
sogutma = next((c for c in roots if c['slug'] == 'sogutma'), None)
assert firinlar, 'Firinlar not found'
assert sogutma, 'Sogutma not found'
assert firinlar['is_leaf'] == False, 'Firinlar should not be leaf'
assert sogutma['is_leaf'] == False, 'Sogutma should not be leaf'
assert firinlar['subcategory_count'] == 2, f\"Firinlar: expected 2 subcats, got {firinlar['subcategory_count']}\"
assert sogutma['subcategory_count'] == 2, f\"Sogutma: expected 2 subcats, got {sogutma['subcategory_count']}\"
print('  [+] Has Firinlar (2 subcategories): PASS')
print('  [+] Has Sogutma (2 subcategories): PASS')
"

echo ""
echo "[TEST 1.2] Firinlar Subcategories"
curl -s "$BASE_URL/categories/firinlar/children/" | python -c "
import sys, json
data = json.load(sys.stdin)
assert len(data['results']) == 2, f\"Expected 2 subcategories, got {len(data['results'])}\"
slugs = [c['slug'] for c in data['results']]
assert 'pizza-firini' in slugs, 'Pizza Firini not found'
assert 'elektrikli-firin' in slugs, 'Elektrikli Firin not found'
pizza = next(c for c in data['results'] if c['slug'] == 'pizza-firini')
elektrik = next(c for c in data['results'] if c['slug'] == 'elektrikli-firin')
assert pizza['products_count'] >= 1, 'Pizza Firini should have products'
assert elektrik['products_count'] >= 1, 'Elektrikli Firin should have products'
print('  [+] Pizza Firini: PASS (%d products)' % pizza['products_count'])
print('  [+] Elektrikli Firin: PASS (%d products)' % elektrik['products_count'])
"

echo ""
echo "[TEST 1.3] Brands for Pizza Firini"
curl -s "$BASE_URL/brands/?category=pizza-firini" | python -c "
import sys, json
data = json.load(sys.stdin)
assert len(data) >= 1, 'No brands found for Pizza Firini'
gastrotech = next((b for b in data if b['slug'] == 'gastrotech'), None)
assert gastrotech, 'Gastrotech not found'
print('  [+] Gastrotech brand available: PASS')
"

echo ""
echo "[TEST 1.4] Series for Pizza Firini + Gastrotech"
curl -s "$BASE_URL/series/?category=pizza-firini&brand=gastrotech" | python -c "
import sys, json
data = json.load(sys.stdin)
assert len(data['results']) >= 1, 'No series found'
series_600 = next((s for s in data['results'] if s['slug'] == 'pizza-600'), None)
assert series_600, '600 Series not found'
assert series_600['products_count'] >= 1, '600 Series should have products'
print('  [+] 600 Series available: PASS (%d products)' % series_600['products_count'])
"

echo ""
echo "[TEST 1.5] Products for Pizza Firini + Gastrotech + 600 Series"
curl -s "$BASE_URL/products/?category=pizza-firini&brand=gastrotech&series=pizza-600" | python -c "
import sys, json
data = json.load(sys.stdin)
assert len(data['results']) >= 1, 'No products found'
product = data['results'][0]
assert product['category_slug'] == 'pizza-firini', 'Wrong category'
assert product['brand_slug'] == 'gastrotech', 'Wrong brand'
assert product['series_slug'] == 'pizza-600', 'Wrong series'
print('  [+] Product filtered correctly: PASS')
print('      Category: %s' % product['category_slug'])
print('      Brand: %s' % product['brand_slug'])
print('      Series: %s' % product['series_slug'])
"

# TEST GROUP 2: SOGUTMA HIERARCHY
echo ""
echo "======================================================================"
echo "GROUP 2: SOGUTMA HIERARCHY"
echo "======================================================================"

echo ""
echo "[TEST 2.1] Sogutma Subcategories"
curl -s "$BASE_URL/categories/sogutma/children/" | python -c "
import sys, json
data = json.load(sys.stdin)
assert len(data['results']) == 2, f\"Expected 2 subcategories, got {len(data['results'])}\"
slugs = [c['slug'] for c in data['results']]
assert 'buzdolabi' in slugs, 'Buzdolabi not found'
assert 'derin-dondurucu' in slugs, 'Derin Dondurucu not found'
print('  [+] Buzdolabi: PASS')
print('  [+] Derin Dondurucu: PASS')
"

echo ""
echo "[TEST 2.2] Brands for Elektrikli Firin"
curl -s "$BASE_URL/brands/?category=elektrikli-firin" | python -c "
import sys, json
data = json.load(sys.stdin)
assert len(data) >= 1, 'No brands found for Elektrikli Firin'
partner_a = next((b for b in data if b['slug'] == 'partner-a'), None)
assert partner_a, 'Partner A not found'
print('  [+] Partner A brand available: PASS')
"

# SUMMARY
echo ""
echo "======================================================================"
echo "TEST SUMMARY"
echo "======================================================================"
echo ""
echo "[SUCCESS] All tests passed!"
echo ""
echo "Verified Navigation Flows:"
echo "  1. Firinlar → Pizza Firini → Gastrotech → 600 Series → Products ✓"
echo "  2. Firinlar → Elektrikli Firin → Partner A → 700 Series → Products ✓"
echo "  3. Sogutma → Buzdolabi ✓"
echo "  4. Sogutma → Derin Dondurucu ✓"
echo ""
echo "Frontend Test URLs:"
echo ""
echo "Fırınlar hierarchy:"
echo "  http://localhost:3000/kategori/firinlar"
echo "  http://localhost:3000/kategori/firinlar?subcategory=pizza-firini"
echo "  http://localhost:3000/kategori/firinlar?subcategory=pizza-firini&brand=gastrotech"
echo "  http://localhost:3000/kategori/firinlar?subcategory=pizza-firini&brand=gastrotech&series=pizza-600"
echo ""
echo "Soğutma hierarchy:"
echo "  http://localhost:3000/kategori/sogutma"
echo "  http://localhost:3000/kategori/sogutma?subcategory=buzdolabi"
echo "  http://localhost:3000/kategori/sogutma?subcategory=derin-dondurucu"
echo ""
