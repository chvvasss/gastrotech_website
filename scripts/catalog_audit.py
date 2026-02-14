import argparse
import os
import sys

import django

import logging

def setup_django():
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    sys.path.insert(0, os.path.join(repo_root, "backend"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")
    django.setup()


def collect_descendant_ids(category):
    descendants = category.get_descendants(include_self=True)
    return [c.id for c in descendants]


def main():
    parser = argparse.ArgumentParser(description="Audit catalog taxonomy and intersections.")
    parser.add_argument("--root-slug", default="firinlar", help="Root category slug to audit")
    parser.add_argument(
        "--legacy-parent-slug",
        default="pisirme-ekipmanlari",
        help="Legacy parent slug expected to be incorrect",
    )
    args = parser.parse_args()

    logging.getLogger("django.db.backends").setLevel(logging.WARNING)

    from django.db.models import F
    from apps.catalog.models import BrandCategory, Category, Product, Series

    root_slug = args.root_slug
    legacy_slug = args.legacy_parent_slug

    print("== Catalog Taxonomy Audit ==")
    print(f"Root slug: {root_slug}")
    print(f"Legacy parent slug: {legacy_slug}")
    print()

    firinlar_candidates = list(Category.objects.filter(slug=root_slug))
    print(f"Root candidates with slug '{root_slug}': {len(firinlar_candidates)}")
    for cat in firinlar_candidates:
        print(
            f"  - id={cat.id} name='{cat.name}' parent='{cat.parent.slug if cat.parent else None}' depth={cat.depth}"
        )

    root = Category.objects.filter(slug=root_slug, parent__isnull=True).first()
    if not root and firinlar_candidates:
        root = firinlar_candidates[0]

    if not root:
        print("Root category not found. Exiting.")
        return

    print("\n-- Root category --")
    print(f"id={root.id}")
    print(f"name={root.name}")
    print(f"slug={root.slug}")
    print(f"parent={root.parent.slug if root.parent else None}")
    print(f"depth={root.depth}")

    children = list(Category.objects.filter(parent=root).order_by("order", "name"))
    print(f"\nImmediate children: {len(children)}")
    for child in children:
        series_count = Series.objects.filter(category=child).count()
        product_count = Product.objects.filter(series__category=child, status="active").count()
        print(
            f"  - {child.slug} ({child.name}) | series={series_count} | products={product_count}"
        )

    scope_ids = collect_descendant_ids(root)
    total_series = Series.objects.filter(category_id__in=scope_ids).count()
    total_products = Product.objects.filter(
        series__category_id__in=scope_ids, status="active"
    ).count()
    print(f"\nDescendant scope: {len(scope_ids)} categories")
    print(f"Series in scope: {total_series}")
    print(f"Active products in scope: {total_products}")

    brand_ids_from_products = (
        Product.objects.filter(
            series__category_id__in=scope_ids,
            status="active",
            brand__isnull=False,
        )
        .values_list("brand_id", flat=True)
        .distinct()
    )
    brand_ids_from_links = (
        BrandCategory.objects.filter(category_id__in=scope_ids, is_active=True)
        .values_list("brand_id", flat=True)
        .distinct()
    )
    print(f"Brands with active products in scope: {len(list(brand_ids_from_products))}")
    print(f"Brands linked via BrandCategory in scope: {len(list(brand_ids_from_links))}")

    # Integrity checks
    mismatch_products = (
        Product.objects.filter(series__category__isnull=False)
        .exclude(category_id=F("series__category_id"))
        .count()
    )
    null_category_products = Product.objects.filter(
        series__category__isnull=False, category__isnull=True
    ).count()
    print("\n-- Integrity --")
    print(f"Products with category != series.category: {mismatch_products}")
    print(f"Products with NULL category but series.category set: {null_category_products}")

    legacy_parent = Category.objects.filter(slug=legacy_slug).first()
    if legacy_parent:
        legacy_children = Category.objects.filter(parent=legacy_parent).count()
        print(
            f"\nLegacy parent '{legacy_slug}' children count: {legacy_children}"
        )


if __name__ == "__main__":
    setup_django()
    main()
