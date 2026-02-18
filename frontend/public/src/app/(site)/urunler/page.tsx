"use client";

import { Suspense, useState, useCallback } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useSearchParams } from "next/navigation";
import { Filter, X } from "lucide-react";
import { ENDPOINTS, fetchProducts, fetchNav, fetchBrands } from "@/lib/api";
import { Container } from "@/components/layout";
import { ProductGrid } from "@/components/catalog";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@/components/ui/sheet";
const getCursorFromUrl = (url?: string | null) => {
  if (!url) return undefined;
  try {
    return new URL(url, ENDPOINTS.PRODUCTS).searchParams.get("cursor") || undefined;
  } catch {
    return undefined;
  }
};


import { ProductFilters } from "@/components/catalog/product-filters";

function ProductsContent() {
  const searchParams = useSearchParams();
  const initialSearch = searchParams.get("search") || "";
  const initialCategory = searchParams.get("category") || "";
  const initialSeries = searchParams.get("series") || "";
  const initialBrand = searchParams.get("brand") || "";
  const initialSort = (searchParams.get("sort") as "newest" | "featured" | "title_asc") || "featured";

  const [search, setSearch] = useState(initialSearch);
  const [selectedCategory, setSelectedCategory] = useState(initialCategory);
  const [selectedSeries, setSelectedSeries] = useState(initialSeries);
  const [selectedBrand, setSelectedBrand] = useState(initialBrand);
  const [sort, setSort] = useState(initialSort);

  const { data: categories = [] } = useQuery({
    queryKey: ["nav"],
    queryFn: fetchNav,
  });

  const { data: brands = [] } = useQuery({
    queryKey: ["brands"],
    queryFn: () => fetchBrands(),
  });

  const {
    data,
    isLoading,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: ["products", search, selectedCategory, selectedSeries, selectedBrand, sort],
    queryFn: ({ pageParam }) =>
      fetchProducts({
        search: search || undefined,
        category: selectedCategory || undefined,
        series: selectedSeries || undefined,
        brand: selectedBrand || undefined,
        sort,
        cursor: pageParam,
        page_size: 12,
      }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => getCursorFromUrl(lastPage.next),
  });

  const products = data?.pages.flatMap((page) => page.results) || [];

  const clearFilters = useCallback(() => {
    setSearch("");
    setSelectedCategory("");
    setSelectedSeries("");
    setSelectedBrand("");
  }, []);

  const handleSearchChange = useCallback((value: string) => {
    setSearch(value);
  }, []);

  const handleCategorySelect = useCallback((categorySlug: string, seriesSlug?: string) => {
    setSelectedCategory(categorySlug);
    setSelectedSeries(seriesSlug || "");
  }, []);

  const handleSeriesSelect = useCallback((seriesSlug: string) => {
    setSelectedSeries(seriesSlug);
  }, []);

  const handleBrandSelect = useCallback((brandSlug: string) => {
    setSelectedBrand(brandSlug);
  }, []);

  const hasActiveFilters = Boolean(search || selectedCategory || selectedSeries || selectedBrand);

  const filtersProps = {
    search,
    onSearchChange: handleSearchChange,
    selectedCategory,
    onCategorySelect: handleCategorySelect,
    selectedSeries,
    onSeriesSelect: handleSeriesSelect,
    brands,
    selectedBrand,
    onBrandSelect: handleBrandSelect,
    categories,
    hasActiveFilters,
    clearFilters,
  };

  return (
    <Container className="py-8 lg:py-12">
      {/* Page Header */}
      <div className="mb-8 flex items-center gap-4">
        <div className="h-16 w-2 rounded-sm bg-gradient-to-b from-primary via-primary to-primary/70 shadow-primary-soft" />
        <div>
          <h1 className="text-3xl font-bold lg:text-4xl">Ürünler</h1>
          <p className="mt-1 text-muted-foreground">
            Tüm endüstriyel mutfak ekipmanlarımızı keşfedin
          </p>
        </div>
      </div>

      {/* FIXED: Use explicit sidebar width for centered product grid */}
      <div className="lg:grid lg:grid-cols-[280px_1fr] lg:gap-8">
        {/* Desktop Filters - narrower fixed width sidebar */}
        <aside className="hidden lg:block">
          <div className="sticky top-24 w-full rounded-sm border bg-card p-5">
            <div className="mb-4 flex items-center gap-3">
              <div className="h-8 w-1 rounded-sm bg-gradient-to-b from-primary to-primary/70" />
              <h2 className="font-semibold">Filtreler</h2>
            </div>
            <ProductFilters {...filtersProps} />
          </div>
        </aside>

        {/* Products - flexible content area */}
        <div>
          {/* Mobile Filter + Sort Bar */}
          <div className="mb-6 flex items-center justify-between gap-4">
            {/* Mobile Filter Trigger */}
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="outline" className="lg:hidden">
                  <Filter className="mr-2 h-4 w-4" />
                  Filtreler
                  {hasActiveFilters && (
                    <span className="ml-2 rounded-sm bg-primary px-2 py-0.5 text-xs text-primary-foreground">
                      !
                    </span>
                  )}
                </Button>
              </SheetTrigger>
              <SheetContent side="left">
                <SheetHeader>
                  <SheetTitle>Filtreler</SheetTitle>
                </SheetHeader>
                <div className="mt-6">
                  <ProductFilters {...filtersProps} />
                </div>
              </SheetContent>
            </Sheet>

            {/* Sort */}
            <div className="flex items-center gap-2">
              <span className="hidden text-sm text-muted-foreground sm:inline">
                Sırala:
              </span>
              <select
                value={sort}
                onChange={(e) => {
                  setSort(e.target.value as typeof sort);
                }}
                className="rounded-sm border bg-background px-3 py-2 text-sm"
              >
                <option value="featured">Öne Çıkan</option>
                <option value="newest">En Yeni</option>
                <option value="title_asc">A-Z</option>
              </select>
            </div>
          </div>

          {/* Active Filters Display */}
          {hasActiveFilters && (
            <div className="mb-4 flex flex-wrap items-center gap-2">
              <span className="text-sm text-muted-foreground">Aktif filtreler:</span>
              {search && (
                <span className="inline-flex items-center gap-1 rounded-sm bg-muted px-3 py-1 text-sm">
                  Arama: {search}
                  <button onClick={() => handleSearchChange("")}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )}
              {selectedCategory && (
                <span className="inline-flex items-center gap-1 rounded-sm bg-muted px-3 py-1 text-sm">
                  {categories.find((c) => c.slug === selectedCategory)?.name}
                  <button onClick={() => handleCategorySelect("")}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )}
              {selectedSeries && (
                <span className="inline-flex items-center gap-1 rounded-sm bg-muted px-3 py-1 text-sm">
                  {categories
                    .find((c) => c.slug === selectedCategory)
                    ?.series.find((s) => s.slug === selectedSeries)?.name}
                  <button onClick={() => handleSeriesSelect("")}>
                    <X className="h-3 w-3" />
                  </button>
                </span>
              )}
            </div>
          )}

          {/* Products Grid - responsive columns */}
          <ProductGrid products={products} isLoading={isLoading} columns={4} />

          {/* Load More */}
          {hasNextPage && (
            <div className="mt-8 text-center">
              <Button
                variant="outline"
                size="lg"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? "Yükleniyor..." : "Daha Fazla Göster"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </Container>
  );
}

function ProductsLoadingFallback() {
  return (
    <Container className="py-8 lg:py-12">
      <div className="mb-8">
        <Skeleton className="h-10 w-48" />
        <Skeleton className="mt-2 h-5 w-72" />
      </div>
      <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
        {Array.from({ length: 6 }).map((_, i) => (
          <div key={i} className="space-y-3">
            <Skeleton className="aspect-square w-full rounded-sm" />
            <Skeleton className="h-4 w-3/4" />
            <Skeleton className="h-4 w-1/2" />
          </div>
        ))}
      </div>
    </Container>
  );
}

export default function ProductsPage() {
  return (
    <Suspense fallback={<ProductsLoadingFallback />}>
      <ProductsContent />
    </Suspense>
  );
}
