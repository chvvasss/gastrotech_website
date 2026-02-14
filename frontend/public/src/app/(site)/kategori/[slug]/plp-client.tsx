"use client";

/**
 * PLP Client Component
 * 
 * This is the client-side PLP content with URL-synced filtering.
 * Rendered by the server page.tsx which handles metadata.
 */

import { Suspense } from "react";
import Link from "next/link";
import { ChevronRight, Filter, LayoutGrid, Package, SlidersHorizontal, ChevronDown, Check, X } from "lucide-react";
import { usePLPQuery } from "@/hooks/use-plp-query";
import {
    TopBrandBar,
    FilterSidebar,
    SortingDropdown,
    PLPProductGrid,
    // Pagination, // Removed
    MobileFilterDrawer,
} from "@/components/catalog/plp";
import { CategoryCatalogViewer } from "@/components/catalog/category-catalog-viewer";

// =============================================================================
// Loading Skeleton
// =============================================================================

export function PLPLoadingSkeleton() {
    return (
        <div className="min-h-screen py-4 lg:py-6 px-4 lg:px-6">
            {/* Breadcrumb skeleton */}
            <div className="mb-4 flex gap-2">
                {[1, 2, 3].map((i) => (
                    <div key={i} className="h-4 w-16 animate-pulse rounded-sm bg-muted" />
                ))}
            </div>

            {/* Header skeleton */}
            <div className="mb-4">
                <div className="h-6 w-48 animate-pulse rounded-sm bg-muted mb-1" />
                <div className="h-4 w-80 max-w-full animate-pulse rounded-sm bg-muted" />
            </div>

            {/* Brand bar skeleton */}
            <div className="mb-4 flex gap-2 overflow-hidden">
                {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                    <div key={i} className="h-10 w-28 flex-shrink-0 animate-pulse rounded-sm bg-muted" />
                ))}
            </div>

            {/* Content skeleton */}
            <div className="flex gap-6">
                <aside className="hidden lg:block w-56 flex-shrink-0">
                    <div className="space-y-3">
                        {[1, 2, 3, 4, 5, 6].map((i) => (
                            <div key={i} className="h-6 animate-pulse rounded-sm bg-muted" />
                        ))}
                    </div>
                </aside>
                <main className="flex-1">
                    <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4">
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

// =============================================================================
// PLP Content Component
// =============================================================================

// =============================================================================
// PLP Content Component
// =============================================================================

interface PLPClientProps {
    categorySlug: string;
    categoryName?: string;
    categoryDescription?: string;
}

function PLPContent({ categorySlug, categoryName, categoryDescription }: PLPClientProps) {
    const {
        // Data
        products,
        facets,
        pagination,
        sortOptions,
        categoryInfo,
        catalogMode,
        catalogs,

        // State
        filters,
        isLoading,

        // Actions
        toggleBrand,
        toggleCategory,
        setPriceRange,
        toggleInStock,
        setSort,
        // setPage, // Removed
        clearAllFilters,
        clearBrands,
        toggleSeries,
        toggleAttribute,

        // Infinite Scroll
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage
    } = usePLPQuery({ categorySlug });

    const hasActiveFilters =
        filters.brands.length > 0 ||
        filters.priceMin !== null ||
        filters.priceMax !== null ||
        filters.inStock;

    // Use server-provided category info as fallback during loading
    const displayName = categoryInfo?.name || categoryName || categorySlug.replace(/-/g, " ");
    const displayDescription = categoryInfo?.description_short || categoryDescription;

    // Catalog mode: show embedded PDF catalogs instead of products
    if (catalogMode) {
        return (
            <div className="min-h-screen bg-white py-4 lg:py-6">
                {/* Breadcrumbs */}
                <nav className="mb-4 px-4 lg:px-6" aria-label="Breadcrumb">
                    <ol className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
                        <li>
                            <Link href="/" className="hover:text-destructive transition-colors">
                                Ana Sayfa
                            </Link>
                        </li>
                        <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" />
                        <li>
                            <Link href="/kategori" className="hover:text-destructive transition-colors">
                                Kategoriler
                            </Link>
                        </li>
                        {categoryInfo?.breadcrumbs?.map((crumb, index) => (
                            <li key={crumb.slug} className="flex items-center gap-1.5">
                                <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" />
                                {index === (categoryInfo.breadcrumbs?.length || 0) - 1 ? (
                                    <span className="font-medium text-foreground">{crumb.name}</span>
                                ) : (
                                    <Link
                                        href={`/kategori/${crumb.slug}`}
                                        className="hover:text-destructive transition-colors"
                                    >
                                        {crumb.name}
                                    </Link>
                                )}
                            </li>
                        ))}
                    </ol>
                </nav>

                <div className="mx-auto max-w-[1400px] px-4 md:px-6 lg:px-8">
                    <div className="mb-6">
                        <div className="flex items-center gap-3 mb-2">
                            <div className="h-8 w-1.5 rounded-sm bg-primary" />
                            <h1 className="text-3xl font-bold tracking-tight text-foreground">
                                {displayName} - Katalog
                            </h1>
                        </div>
                        {displayDescription && (
                            <p className="mt-2 text-sm text-muted-foreground max-w-2xl pl-[18px]">
                                {displayDescription}
                            </p>
                        )}
                    </div>
                    <CategoryCatalogViewer categorySlug={categorySlug} catalogs={catalogs} />
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-muted/5 py-4 lg:py-6">
            {/* Breadcrumbs */}
            <nav className="mb-4 px-4 lg:px-6" aria-label="Breadcrumb">
                <ol className="flex flex-wrap items-center gap-1.5 text-sm text-muted-foreground">
                    <li>
                        <Link href="/" className="hover:text-destructive transition-colors">
                            Ana Sayfa
                        </Link>
                    </li>
                    <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" />
                    <li>
                        <Link href="/kategori" className="hover:text-destructive transition-colors">
                            Kategoriler
                        </Link>
                    </li>
                    {categoryInfo?.breadcrumbs?.map((crumb, index) => (
                        <li key={crumb.slug} className="flex items-center gap-1.5">
                            <ChevronRight className="h-3.5 w-3.5 flex-shrink-0" />
                            {index === (categoryInfo.breadcrumbs?.length || 0) - 1 ? (
                                <span className="font-medium text-foreground">{crumb.name}</span>
                            ) : (
                                <Link
                                    href={`/kategori/${crumb.slug}`}
                                    className="hover:text-destructive transition-colors"
                                >
                                    {crumb.name}
                                </Link>
                            )}
                        </li>
                    ))}
                </ol>
            </nav>

            {/* Main Content Area - Layout with Gaps and Sidebar */}
            <div className="mx-auto max-w-[1920px] px-4 md:px-6 lg:px-8">
                {/* 12 Column Grid for precise control */}
                <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">



                    {/* Main Sidebar - Wider */}
                    <aside className="hidden lg:block lg:col-span-3 xl:col-span-3 2xl:col-span-3">
                        <div className="sticky top-24 pr-4 border-r border-border/40">
                            <FilterSidebar
                                brandFacets={facets.brands}
                                categoryFacets={facets.categories}
                                priceFacet={facets.price}
                                seriesFacets={facets.series}
                                attributeFacets={facets.attributes}
                                selectedBrands={filters.brands}
                                selectedCategories={filters.categories}
                                selectedSeries={filters.series}
                                selectedAttributes={filters.attrs}
                                selectedPriceMin={filters.priceMin}
                                selectedPriceMax={filters.priceMax}
                                inStockOnly={filters.inStock}
                                onToggleBrand={toggleBrand}
                                onToggleCategory={toggleCategory}
                                onToggleSeries={toggleSeries}
                                onToggleAttribute={toggleAttribute}
                                onPriceChange={setPriceRange}
                                onStockToggle={toggleInStock}
                                onClearAll={clearAllFilters}
                                isLoading={isLoading}
                            />
                        </div>
                    </aside>

                    {/* Main Content - 8 Cols (leaves 1 col gap) */}
                    <main className="lg:col-span-9 xl:col-span-8 2xl:col-span-8">
                        {/* Header Area */}
                        <div className="mb-6 border-b border-border/50 pb-6">
                            <div className="flex flex-wrap items-baseline justify-between gap-4 mb-4">
                                <div>
                                    <h1 className="text-3xl font-bold tracking-tight text-foreground">
                                        {displayName}
                                    </h1>
                                    {displayDescription && (
                                        <p className="mt-2 text-sm text-muted-foreground line-clamp-2 max-w-2xl">
                                            {displayDescription}
                                        </p>
                                    )}
                                </div>
                                {/* Removed Count Display */}
                            </div>

                            {/* Brand Selection - ON TOP OF GRID */}
                            {facets.brands.length > 0 && (
                                <div className="mb-8">
                                    <TopBrandBar
                                        brands={facets.brands}
                                        selectedBrands={filters.brands}
                                        onToggleBrand={toggleBrand}
                                        onClearAll={clearBrands}
                                        isLoading={isLoading}
                                    />
                                </div>
                            )}

                            {/* Controls */}
                            <div className="flex items-center justify-between gap-4">
                                {/* Sort */}
                                <div className="flex items-center gap-2">
                                    <span className="text-sm font-medium text-muted-foreground">Sıralama:</span>
                                    <SortingDropdown
                                        sortOptions={sortOptions}
                                        currentSort={filters.sort}
                                        onSortChange={setSort}
                                    />
                                </div>

                                {/* Active Filters Chips */}
                                {hasActiveFilters && (
                                    <div className="flex flex-wrap gap-2">
                                        <button
                                            onClick={clearAllFilters}
                                            className="text-xs font-bold text-destructive hover:underline uppercase"
                                        >
                                            Temizle
                                        </button>
                                    </div>
                                )}
                            </div>
                        </div>

                        {/* Product Grid */}
                        <PLPProductGrid products={products} isLoading={isLoading && !isFetchingNextPage} />

                        {/* Interactive Loading Trigger */}
                        {(hasNextPage || isFetchingNextPage) && (
                            <div className="mt-8 flex justify-center py-8">
                                <InfiniteScrollTrigger
                                    onIntersect={() => hasNextPage && !isFetchingNextPage && fetchNextPage()}
                                    isLoading={isFetchingNextPage}
                                />
                            </div>
                        )}
                    </main>

                    {/* Visual Gap - Right (1 col) */}
                    <div className="hidden xl:block xl:col-span-1 pointer-events-none" />
                </div>
            </div>
        </div>
    );
}

// Simple Intersection Observer Component
function InfiniteScrollTrigger({ onIntersect, isLoading }: { onIntersect: () => void, isLoading: boolean }) {
    const observerRef = (node: HTMLDivElement | null) => {
        if (!node) return;

        const observer = new IntersectionObserver(
            (entries) => {
                if (entries[0].isIntersecting) {
                    onIntersect();
                }
            },
            { rootMargin: "200px" } // Trigger 200px before end
        );

        observer.observe(node);
        return () => observer.disconnect();
    };

    return (
        <div
            // @ts-ignore
            ref={observerRef}
            className="flex flex-col items-center gap-2 text-muted-foreground w-full"
        >
            {isLoading ? (
                <>
                    <div className="h-6 w-6 animate-spin rounded-full border-2 border-primary border-t-transparent" />
                    <span className="text-sm">Yükleniyor...</span>
                </>
            ) : (
                <div className="h-4 w-full" /> // Invisible trigger target
            )}
        </div>
    );
}

// =============================================================================
// Exported Client Wrapper
// =============================================================================

export function PLPClient({ categorySlug, categoryName, categoryDescription }: PLPClientProps) {
    return (
        <Suspense fallback={<PLPLoadingSkeleton />}>
            <PLPContent
                categorySlug={categorySlug}
                categoryName={categoryName}
                categoryDescription={categoryDescription}
            />
        </Suspense>
    );
}
