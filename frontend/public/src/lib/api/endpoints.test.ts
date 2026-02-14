import { ENDPOINTS } from "@/lib/api/endpoints";

describe("ENDPOINTS helpers", () => {
  it("builds series URL with category and brand", () => {
    const url = ENDPOINTS.seriesByCategory("firinlar", "gastrotech");
    expect(url).toBe("/api/v1/series/?category=firinlar&brand=gastrotech");
  });

  it("builds product search URL with category and brand", () => {
    const url = ENDPOINTS.productsSearch({
      category: "firinlar",
      brand: "gastrotech",
      page_size: 24,
    });
    expect(url).toBe("/api/v1/products/?category=firinlar&brand=gastrotech&page_size=24");
  });
});
