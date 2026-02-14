"use client";

import { useState } from "react";
import { PLPBrandFacet, PLPCategoryFacet, PLPPriceFacet } from "@/lib/api/schemas";
import { FilterSidebar } from "./filter-sidebar";
import { cn } from "@/lib/utils";
import { SlidersHorizontal, X } from "lucide-react";

interface MobileFilterDrawerProps {
    // Facet data
    brandFacets: PLPBrandFacet[];
    categoryFacets: PLPCategoryFacet[];
    priceFacet: PLPPriceFacet;

    // Selected values
    selectedBrands: string[];
    selectedPriceMin: number | null;
    selectedPriceMax: number | null;
    inStockOnly: boolean;

    // Handlers
    onToggleBrand: (brandSlug: string) => void;
    onPriceChange: (min: number | null, max: number | null) => void;
    onStockToggle: () => void;
    onClearAll: () => void;

    // Counts
    totalProducts: number;

    // Loading state
    isLoading?: boolean;
}

export function MobileFilterDrawer({
    brandFacets,
    categoryFacets,
    priceFacet,
    selectedBrands,
    selectedPriceMin,
    selectedPriceMax,
    inStockOnly,
    onToggleBrand,
    onPriceChange,
    onStockToggle,
    onClearAll,
    totalProducts,
    isLoading = false,
}: MobileFilterDrawerProps) {
    const [isOpen, setIsOpen] = useState(false);

    const hasActiveFilters =
        selectedBrands.length > 0 ||
        selectedPriceMin !== null ||
        selectedPriceMax !== null ||
        inStockOnly;

    const activeFilterCount =
        selectedBrands.length +
        (selectedPriceMin !== null || selectedPriceMax !== null ? 1 : 0) +
        (inStockOnly ? 1 : 0);

    return (
        <>
            {/* Trigger Button */}
            <button
                onClick={() => setIsOpen(true)}
                className="flex items-center gap-2 rounded-lg border border-border bg-card px-4 py-2.5 text-sm font-medium text-foreground shadow-sm transition-all hover:border-destructive/50 hover:shadow-md lg:hidden"
            >
                <SlidersHorizontal className="h-4 w-4" />
                Filtrele
                {activeFilterCount > 0 && (
                    <span className="flex h-5 min-w-[20px] items-center justify-center rounded-full bg-destructive px-1.5 text-xs font-semibold text-white">
                        {activeFilterCount}
                    </span>
                )}
            </button>

            {/* Backdrop */}
            {isOpen && (
                <div
                    className="fixed inset-0 z-40 bg-black/50 backdrop-blur-sm transition-opacity lg:hidden"
                    onClick={() => setIsOpen(false)}
                />
            )}

            {/* Drawer */}
            <div
                className={cn(
                    "fixed inset-y-0 right-0 z-50 w-full max-w-sm transform bg-background shadow-2xl transition-transform duration-300 ease-out lg:hidden",
                    isOpen ? "translate-x-0" : "translate-x-full"
                )}
            >
                {/* Header */}
                <div className="flex items-center justify-between border-b border-border px-4 py-4">
                    <div className="flex items-center gap-2">
                        <SlidersHorizontal className="h-5 w-5 text-destructive" />
                        <span className="text-lg font-bold text-foreground">Filtreler</span>
                        {activeFilterCount > 0 && (
                            <span className="rounded-full bg-destructive px-2 py-0.5 text-xs font-semibold text-white">
                                {activeFilterCount}
                            </span>
                        )}
                    </div>
                    <button
                        onClick={() => setIsOpen(false)}
                        className="flex h-8 w-8 items-center justify-center rounded-full bg-muted text-muted-foreground transition-colors hover:bg-destructive hover:text-white"
                    >
                        <X className="h-4 w-4" />
                    </button>
                </div>

                {/* Content - Scrollable */}
                <div className="flex-1 overflow-y-auto p-4">
                    <FilterSidebar
                        brandFacets={brandFacets}
                        categoryFacets={categoryFacets}
                        priceFacet={priceFacet}
                        selectedBrands={selectedBrands}
                        selectedPriceMin={selectedPriceMin}
                        selectedPriceMax={selectedPriceMax}
                        inStockOnly={inStockOnly}
                        onToggleBrand={onToggleBrand}
                        onPriceChange={onPriceChange}
                        onStockToggle={onStockToggle}
                        onClearAll={onClearAll}
                        isLoading={isLoading}
                    />
                </div>

                {/* Footer */}
                <div className="border-t border-border p-4 space-y-3">
                    {hasActiveFilters && (
                        <button
                            onClick={() => {
                                onClearAll();
                            }}
                            className="w-full rounded-lg border border-destructive/30 bg-destructive/10 py-2.5 text-sm font-medium text-destructive transition-colors hover:bg-destructive/20"
                        >
                            Tüm Filtreleri Temizle
                        </button>
                    )}
                    <button
                        onClick={() => setIsOpen(false)}
                        className="w-full rounded-lg bg-destructive py-3 text-sm font-semibold text-white transition-colors hover:bg-destructive/90"
                    >
                        {totalProducts.toLocaleString("tr-TR")} Ürün Göster
                    </button>
                </div>
            </div>
        </>
    );
}
