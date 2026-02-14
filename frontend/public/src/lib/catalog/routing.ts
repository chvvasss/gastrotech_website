import type { Category } from "@/lib/api/schemas";

export function findCategoryBySlug(
  categories: Category[],
  targetSlug: string
): Category | null {
  for (const cat of categories) {
    if (cat.slug === targetSlug) return cat;
    if (cat.children) {
      const found = findCategoryBySlug(cat.children, targetSlug);
      if (found) return found;
    }
  }
  return null;
}

export function buildLegacyCategoryRedirect(options: {
  currentSlug: string;
  subcategorySlug?: string | null;
  categories: Category[];
  searchParams: URLSearchParams;
}): string | null {
  const { currentSlug, subcategorySlug, categories, searchParams } = options;

  if (!subcategorySlug) return null;

  const subcategory = findCategoryBySlug(categories, subcategorySlug);
  if (!subcategory) return null;

  const isRoot = !subcategory.parent_slug;
  if (!isRoot) return null;

  const nextParams = new URLSearchParams(searchParams.toString());
  nextParams.delete("subcategory");
  const query = nextParams.toString();

  if (subcategory.slug !== currentSlug) {
    return `/kategori/${subcategory.slug}${query ? `?${query}` : ""}`;
  }

  // Same slug but subcategory param present -> clean URL
  return `/kategori/${currentSlug}${query ? `?${query}` : ""}`;
}
