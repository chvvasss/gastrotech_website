"""
End-to-End Test: Subcategory Navigation Flow

Tests the complete user journey:
1. Category Tree → Shows Fırınlar with is_leaf=false
2. Category Children → Shows Pizza Fırını and Elektrikli Fırın
3. Brands by Subcategory → Shows Gastrotech for pizza-firini
4. Series by Subcategory + Brand → Shows 600 Series
5. Products by Subcategory + Brand + Series → Shows Pizza Oven 600
"""

import requests
import sys

BASE_URL = "http://localhost:8000/api/v1"

def test_step(step_num, description, url, expected_checks):
    """Test a single navigation step."""
    print(f"\n[STEP {step_num}] {description}")
    print(f"URL: {url}")

    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()

        # Run expected checks
        all_passed = True
        for check_name, check_fn in expected_checks.items():
            try:
                check_fn(data)
                print(f"  [+] {check_name}: PASS")
            except AssertionError as e:
                print(f"  [X] {check_name}: FAIL - {e}")
                all_passed = False

        if all_passed:
            print(f"  [OK] Step {step_num} complete")
            return True
        else:
            print(f"  [ERROR] Step {step_num} failed")
            return False

    except requests.exceptions.ConnectionError:
        print(f"  [ERROR] Cannot connect to {BASE_URL}")
        print(f"  [HINT] Is the Django server running? (python manage.py runserver)")
        return False
    except Exception as e:
        print(f"  [ERROR] {type(e).__name__}: {e}")
        return False


def main():
    """Run complete navigation flow test."""
    print("=" * 70)
    print("SUBCATEGORY NAVIGATION - END-TO-END TEST")
    print("=" * 70)

    steps_passed = 0
    total_steps = 5

    # STEP 1: Get category tree and verify Fırınlar exists with subcategories
    if test_step(
        1,
        "Get Category Tree - Verify Fırınlar has subcategories",
        f"{BASE_URL}/categories/tree/",
        {
            "Is list": lambda data: isinstance(data, list) or None,
            "Has Fırınlar": lambda data: any(
                cat['slug'] == 'firinlar' for cat in data
            ) or None,
            "Fırınlar is not leaf": lambda data: next(
                cat for cat in data if cat['slug'] == 'firinlar'
            )['is_leaf'] == False or None,
            "Fırınlar has 2 subcategories": lambda data: next(
                cat for cat in data if cat['slug'] == 'firinlar'
            )['subcategory_count'] == 2 or None,
        }
    ):
        steps_passed += 1

    # STEP 2: Get children of Fırınlar
    if test_step(
        2,
        "Get Subcategories of Fırınlar",
        f"{BASE_URL}/categories/firinlar/children/",
        {
            "Has results": lambda data: 'results' in data or None,
            "Has 2 subcategories": lambda data: len(data['results']) == 2 or None,
            "Has Pizza Fırını": lambda data: any(
                cat['slug'] == 'pizza-firini' for cat in data['results']
            ) or None,
            "Has Elektrikli Fırın": lambda data: any(
                cat['slug'] == 'elektrikli-firin' for cat in data['results']
            ) or None,
            "Pizza Fırını has products": lambda data: next(
                cat for cat in data['results'] if cat['slug'] == 'pizza-firini'
            )['products_count'] > 0 or None,
        }
    ):
        steps_passed += 1

    # STEP 3: Get brands for Pizza Fırını subcategory
    if test_step(
        3,
        "Get Brands for Pizza Fırını subcategory",
        f"{BASE_URL}/brands/?category=pizza-firini",
        {
            "Is list": lambda data: isinstance(data, list) or None,
            "Has Gastrotech": lambda data: any(
                brand['slug'] == 'gastrotech' for brand in data
            ) or None,
            "Gastrotech is active": lambda data: next(
                brand for brand in data if brand['slug'] == 'gastrotech'
            )['is_active'] == True or None,
        }
    ):
        steps_passed += 1

    # STEP 4: Get series for Pizza Fırını + Gastrotech
    if test_step(
        4,
        "Get Series for Pizza Fırını + Gastrotech",
        f"{BASE_URL}/series/?category=pizza-firini&brand=gastrotech",
        {
            "Has results": lambda data: 'results' in data or None,
            "Has series": lambda data: len(data['results']) > 0 or None,
            "Has 600 Series": lambda data: any(
                series['slug'] == 'pizza-600' for series in data['results']
            ) or None,
            "Series has products": lambda data: next(
                series for series in data['results'] if series['slug'] == 'pizza-600'
            )['products_count'] > 0 or None,
        }
    ):
        steps_passed += 1

    # STEP 5: Get products for Pizza Fırını + Gastrotech + 600 Series
    if test_step(
        5,
        "Get Products for Pizza Fırını + Gastrotech + 600 Series",
        f"{BASE_URL}/products/?category=pizza-firini&brand=gastrotech&series=pizza-600",
        {
            "Has results": lambda data: 'results' in data or None,
            "Has products": lambda data: len(data['results']) > 0 or None,
            "Product has correct category": lambda data:
                data['results'][0]['category_slug'] == 'pizza-firini' or None,
            "Product has correct brand": lambda data:
                data['results'][0]['brand_slug'] == 'gastrotech' or None,
            "Product has correct series": lambda data:
                data['results'][0]['series_slug'] == 'pizza-600' or None,
        }
    ):
        steps_passed += 1

    # Summary
    print("\n" + "=" * 70)
    print(f"TEST SUMMARY: {steps_passed}/{total_steps} steps passed")
    print("=" * 70)

    if steps_passed == total_steps:
        print("\n[SUCCESS] All navigation steps completed successfully!")
        print("\nComplete flow verified:")
        print("  Firinlar (root) -> Pizza Firini (subcategory) -> Gastrotech (brand)")
        print("  -> 600 Series -> Pizza Oven 600 (product)")
        print("\nFrontend URLs to test:")
        print("  1. http://localhost:3000/kategori/firinlar")
        print("     (Should show subcategory selection grid)")
        print("  2. http://localhost:3000/kategori/firinlar?subcategory=pizza-firini")
        print("     (Should show brand selection)")
        print("  3. http://localhost:3000/kategori/firinlar?subcategory=pizza-firini&brand=gastrotech")
        print("     (Should show series selection)")
        print("  4. http://localhost:3000/kategori/firinlar?subcategory=pizza-firini&brand=gastrotech&series=pizza-600")
        print("     (Should show product listing)")
        return 0
    else:
        print(f"\n[FAILED] {total_steps - steps_passed} step(s) failed")
        print("Please check the errors above and verify:")
        print("  1. Django server is running (python manage.py runserver)")
        print("  2. Test data was created (python scripts/create_test_subcategories.py)")
        print("  3. All migrations are applied (python manage.py migrate)")
        return 1


if __name__ == "__main__":
    sys.exit(main())
