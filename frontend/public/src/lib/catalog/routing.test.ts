import { buildLegacyCategoryRedirect } from "@/lib/catalog/routing";
import type { Category } from "@/lib/api/schemas";

const categories: Category[] = [
  {
    id: "1",
    name: "Firinlar",
    slug: "firinlar",
    menu_label: null,
    description_short: null,
    order: 1,
    cover_media_url: null,
    parent_slug: null,
    children: [
      {
        id: "2",
        name: "Pizza Firini",
        slug: "pizza-firini",
        menu_label: null,
        description_short: null,
        order: 1,
        cover_media_url: null,
        parent_slug: "firinlar",
        children: [],
      },
    ],
  },
];

describe("buildLegacyCategoryRedirect", () => {
  it("redirects legacy subcategory root to canonical category URL", () => {
    const redirectTo = buildLegacyCategoryRedirect({
      currentSlug: "pisirme-ekipmanlari",
      subcategorySlug: "firinlar",
      categories,
      searchParams: new URLSearchParams("subcategory=firinlar&brand=gastrotech"),
    });

    expect(redirectTo).toBe("/kategori/firinlar?brand=gastrotech");
  });

  it("cleans subcategory param when it matches root slug", () => {
    const redirectTo = buildLegacyCategoryRedirect({
      currentSlug: "firinlar",
      subcategorySlug: "firinlar",
      categories,
      searchParams: new URLSearchParams("subcategory=firinlar&series=test-series"),
    });

    expect(redirectTo).toBe("/kategori/firinlar?series=test-series");
  });

  it("does not redirect for real subcategories", () => {
    const redirectTo = buildLegacyCategoryRedirect({
      currentSlug: "firinlar",
      subcategorySlug: "pizza-firini",
      categories,
      searchParams: new URLSearchParams("subcategory=pizza-firini"),
    });

    expect(redirectTo).toBeNull();
  });
});
