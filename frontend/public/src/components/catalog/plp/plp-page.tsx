"use client";

import { Suspense } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ChevronRight, Package, LayoutGrid } from "lucide-react";
import { usePLPQuery } from "@/hooks/use-plp-query";
import {
    TopBrandBar,
    FilterSidebar,
    SortingDropdown,
    PLPProductGrid,
    Pagination,
    MobileFilterDrawer,
} from "@/components/catalog/plp";
import { cn } from "@/lib/utils";

interface PLPPageContentProps {
    categorySlug: string;
}

function PLPPageContent({ categorySlug }: PLPPageContentProps) {
    const {
        // Data
        products,
        facets,
        pagination,
        sortOptions,
        categoryInfo,

        // State
        filters,
        isLoading,

        // Actions
        toggleBrand,
        setPriceRange,
        toggleInStock,
        setSort,
        clearAllFilters,
        clearBrands,
        hasNextPage,
        fetchNextPage,
        isFetchingNextPage,
    } = usePLPQuery({ categorySlug });

    const hasActiveFilters =
        filters.brands.length > 0 ||
        filters.priceMin !== null ||
        filters.priceMax !== null ||
        filters.inStock;

    return (
        <div className="min-h-screen py-6 lg:py-8">
            {/* Breadcrumbs */}
            <nav className="mb-4 sm:mb-6 px-4 lg:px-8 overflow-hidden">
                <ol className="flex items-center gap-1 sm:gap-1.5 text-[11px] sm:text-sm text-muted-foreground overflow-x-auto whitespace-nowrap scrollbar-hide pb-1">
                    <li>
                        <Link href="/" className="hover:text-primary transition-colors">
                            Ana Sayfa
                        </Link>
                    </li>
                    <ChevronRight className="h-3.5 w-3.5" />
                    <li>
                        <Link href="/kategori" className="hover:text-primary transition-colors">
                            Kategoriler
                        </Link>
                    </li>
                    {categoryInfo?.breadcrumbs?.map((crumb, index) => (
                        <li key={crumb.slug} className="flex items-center gap-1.5">
                            <ChevronRight className="h-3.5 w-3.5" />
                            {index === (categoryInfo.breadcrumbs?.length || 0) - 1 ? (
                                <span className="font-medium text-foreground">{crumb.name}</span>
                            ) : (
                                <Link
                                    href={`/kategori/${crumb.slug}`}
                                    className="hover:text-primary transition-colors"
                                >
                                    {crumb.name}
                                </Link>
                            )}
                        </li>
                    ))}
                </ol>
            </nav>

            {/* Category Header */}
            <header className="mb-6 sm:mb-8 px-4 lg:px-8">
                <h1 className="text-xl sm:text-2xl font-bold tracking-tight lg:text-3xl text-foreground">
                    {categoryInfo?.name || categorySlug}
                </h1>
                {categoryInfo?.description_short && (
                    <p className="mt-1.5 sm:mt-2 text-sm sm:text-base text-muted-foreground max-w-3xl">
                        {categoryInfo.description_short}
                    </p>
                )}
            </header>

            {/* Top Brand Bar */}
            <div className="px-4 lg:px-8 mb-6">
                <TopBrandBar
                    brands={facets.brands}
                    selectedBrands={filters.brands}
                    onToggleBrand={toggleBrand}
                    onClearAll={clearBrands}
                    isLoading={isLoading}
                />
            </div>

            {/* Main Content Area */}
            <div className="flex gap-4 sm:gap-6 lg:gap-8 px-4 lg:px-8 overflow-hidden">
                {/* Left Sidebar - Desktop Only */}
                <aside className="hidden lg:block w-64 flex-shrink-0">
                    <div className="sticky top-24">
                        <FilterSidebar
                            brandFacets={facets.brands}
                            categoryFacets={facets.categories}
                            priceFacet={facets.price}
                            selectedBrands={filters.brands}
                            selectedPriceMin={filters.priceMin}
                            selectedPriceMax={filters.priceMax}
                            inStockOnly={filters.inStock}
                            onToggleBrand={toggleBrand}
                            onPriceChange={setPriceRange}
                            onStockToggle={toggleInStock}
                            onClearAll={clearAllFilters}
                            isLoading={isLoading}
                        />
                    </div>
                </aside>

                {/* Products Area */}
                <main className="flex-1 min-w-0">
                    {/* Toolbar */}
                    <div className="flex flex-wrap items-center justify-between mb-6 gap-2 sm:gap-4">
                        {/* Results count */}
                        <div className="flex items-center gap-1.5 sm:gap-2 text-xs sm:text-sm text-muted-foreground min-w-0">
                            <LayoutGrid className="h-3.5 w-3.5 sm:h-4 sm:w-4 flex-shrink-0" />
                            <span className="truncate">
                                <strong className="text-foreground">
                                    {pagination?.total.toLocaleString("tr-TR") || 0}
                                </strong>{" "}
                                ürün
                            </span>
                            {hasActiveFilters && (
                                <button
                                    onClick={clearAllFilters}
                                    className="ml-1 sm:ml-2 text-primary hover:text-primary/80 font-medium transition-colors text-xs whitespace-nowrap"
                                >
                                    Temizle
                                </button>
                            )}
                        </div>

                        {/* Right controls */}
                        <div className="flex items-center gap-3">
                            {/* Mobile filter trigger */}
                            <MobileFilterDrawer
                                brandFacets={facets.brands}
                                categoryFacets={facets.categories}
                                priceFacet={facets.price}
                                selectedBrands={filters.brands}
                                selectedPriceMin={filters.priceMin}
                                selectedPriceMax={filters.priceMax}
                                inStockOnly={filters.inStock}
                                onToggleBrand={toggleBrand}
                                onPriceChange={setPriceRange}
                                onStockToggle={toggleInStock}
                                onClearAll={clearAllFilters}
                                totalProducts={pagination?.total || 0}
                                isLoading={isLoading}
                            />

                            {/* Sorting dropdown */}
                            <SortingDropdown
                                sortOptions={sortOptions}
                                currentSort={filters.sort}
                                onSortChange={setSort}
                            />
                        </div>
                    </div>

                    {/* Product Grid */}
                    <PLPProductGrid products={products} isLoading={isLoading} />

                    {/* Pagination */}
                    {/* Load More */}
                    {hasNextPage && (
                        <div className="mt-8 sm:mt-10 flex justify-center pb-4">
                            <button
                                onClick={() => fetchNextPage()}
                                disabled={isFetchingNextPage}
                                className="inline-flex items-center justify-center rounded-sm text-sm font-semibold ring-offset-background transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 border-2 border-primary/20 bg-background hover:bg-primary/5 hover:border-primary/40 text-foreground h-11 px-8 w-full sm:w-auto"
                            >
                                {isFetchingNextPage ? (
                                  <span className="flex items-center gap-2">
                                    <span className="h-4 w-4 border-2 border-primary/30 border-t-primary rounded-full animate-spin" />
                                    Yükleniyor...
                                  </span>
                                ) : "Daha Fazla Göster"}
                            </button>
                        </div>
                    )}
                </main>
            </div>
        </div>
    );
}

// Loading state wrapper
function PLPPageLoading() {
    return (
        <div className="min-h-screen py-6 lg:py-8 px-4 lg:px-8">
            {/* Breadcrumb skeleton */}
            <div className="mb-6 flex gap-2">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="h-4 w-20 animate-pulse rounded bg-muted" />
                ))}
            </div>

            {/* Header skeleton */}
            <div className="mb-8">
                <div className="h-8 w-64 animate-pulse rounded bg-muted mb-2" />
                <div className="h-4 w-96 animate-pulse rounded bg-muted" />
            </div>

            {/* Brand bar skeleton */}
            <div className="mb-6 flex gap-3">
                {[1, 2, 3, 4, 5].map((i) => (
                    <div key={i} className="h-10 w-24 animate-pulse rounded-full bg-muted" />
                ))}
            </div>

            {/* Content skeleton */}
            <div className="flex gap-8">
                <aside className="hidden lg:block w-64">
                    <div className="space-y-4">
                        {[1, 2, 3, 4, 5].map((i) => (
                            <div key={i} className="h-8 animate-pulse rounded bg-muted" />
                        ))}
                    </div>
                </aside>
                <main className="flex-1">
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                            <div
                                key={i}
                                className="aspect-[3/4] animate-pulse rounded-sm border bg-muted"
                            />
                        ))}
                    </div>
                </main>
            </div>
        </div>
    );
}

export function PLPPage() {
    const params = useParams();
    const categorySlug = params.slug as string;

    return (
        <Suspense fallback={<PLPPageLoading />}>
            <PLPPageContent categorySlug={categorySlug} />
        </Suspense>
    );
}
