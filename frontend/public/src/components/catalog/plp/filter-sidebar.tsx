"use client";

import { useState } from "react";
import Link from "next/link";
import { PLPBrandFacet, PLPCategoryFacet, PLPPriceFacet, PLPSeriesFacet, PLPAttributeFacet } from "@/lib/api/schemas";
import { cn } from "@/lib/utils";
import { ChevronDown, ChevronUp, X, Filter, Check, ChevronRight } from "lucide-react";

interface FilterSidebarProps {
    // Facet data
    brandFacets: PLPBrandFacet[];
    categoryFacets: PLPCategoryFacet[];
    priceFacet: PLPPriceFacet;
    seriesFacets?: PLPSeriesFacet[];
    attributeFacets?: PLPAttributeFacet[];

    // Selected values
    selectedBrands: string[];
    selectedCategories?: string[];
    selectedSeries?: string[];
    selectedAttributes?: Record<string, string>;
    selectedPriceMin: number | null;
    selectedPriceMax: number | null;
    inStockOnly: boolean;

    // Handlers
    onToggleBrand: (brandSlug: string) => void;
    onToggleCategory?: (categorySlug: string) => void;
    onToggleSeries?: (seriesSlug: string) => void;
    onToggleAttribute?: (key: string, value: string) => void;
    onPriceChange: (min: number | null, max: number | null) => void;
    onStockToggle: () => void;
    onClearAll: () => void;

    // Loading state
    isLoading?: boolean;
}

function FacetSection({
    title,
    children,
    defaultOpen = true,
}: {
    title: string;
    children: React.ReactNode;
    defaultOpen?: boolean;
}) {
    const [isOpen, setIsOpen] = useState(defaultOpen);

    return (
        <div className="border-b border-border py-4 first:pt-0 last:border-0">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex w-full items-center justify-between text-sm font-bold uppercase tracking-wider text-foreground hover:text-destructive transition-colors py-1"
            >
                {title}
                {isOpen ? (
                    <ChevronUp className="h-4 w-4 text-muted-foreground" />
                ) : (
                    <ChevronDown className="h-4 w-4 text-muted-foreground" />
                )}
            </button>
            {isOpen && <div className="mt-3 animate-in slide-in-from-top-1 duration-200">{children}</div>}
        </div>
    );
}

export function CheckboxItem({
    label,
    count,
    checked,
    onChange,
    imageUrl,
}: {
    label: string;
    count: number;
    checked: boolean;
    onChange: () => void;
    imageUrl?: string | null;
}) {
    return (
        <button
            type="button"
            onClick={onChange}
            className={cn(
                "group flex w-full cursor-pointer items-center gap-3 py-1.5 text-sm transition-colors text-left",
                checked ? "text-foreground font-semibold" : "text-muted-foreground hover:text-foreground"
            )}
        >
            <div
                className={cn(
                    "flex h-4.5 w-4.5 flex-shrink-0 items-center justify-center border transition-all rounded-sm",
                    checked
                        ? "border-destructive bg-destructive text-white"
                        : "border-muted-foreground/30 bg-white group-hover:border-foreground"
                )}
            >
                {checked && <Check className="h-3.5 w-3.5" strokeWidth={3} />}
            </div>

            {/* Optional Image */}
            {imageUrl && (
                <div className="relative h-10 w-16 flex-shrink-0 overflow-hidden rounded-md bg-white border border-border/50 shadow-sm p-0.5">
                    <img
                        src={imageUrl}
                        alt={label}
                        className="h-full w-full object-contain"
                    />
                </div>
            )}

            {/* Show label text only if no logo */}
            {!imageUrl && <span className="flex-1 leading-snug text-sm">{label}</span>}
            {/* Count hidden as per previous code, keeping specific font size for it if visible */}
            <span className="text-xs text-muted-foreground/50 tabular-nums">
                ({count})
            </span>
        </button>
    );
}

export function FilterSidebar({
    brandFacets,
    categoryFacets,
    priceFacet,
    seriesFacets,
    attributeFacets,
    selectedBrands,
    selectedCategories,
    selectedSeries,
    selectedAttributes,
    selectedPriceMin,
    selectedPriceMax,
    inStockOnly,
    onToggleBrand,
    onToggleCategory,
    onToggleSeries,
    onToggleAttribute,
    onPriceChange,
    onStockToggle,
    onClearAll,
    isLoading = false,
}: FilterSidebarProps) {
    const [priceMinInput, setPriceMinInput] = useState(
        selectedPriceMin?.toString() ?? ""
    );
    const [priceMaxInput, setPriceMaxInput] = useState(
        selectedPriceMax?.toString() ?? ""
    );
    const [brandSearch, setBrandSearch] = useState("");

    const hasActiveFilters =
        selectedBrands.length > 0 ||
        selectedPriceMin !== null ||
        selectedPriceMax !== null ||
        inStockOnly;

    const handlePriceApply = () => {
        const min = priceMinInput ? parseFloat(priceMinInput) : null;
        const max = priceMaxInput ? parseFloat(priceMaxInput) : null;
        onPriceChange(min, max);
    };

    // Filter brands by search
    const filteredBrands = brandFacets.filter(b =>
        b.name.toLowerCase().includes(brandSearch.toLowerCase())
    );

    if (isLoading) {
        return (
            <div className="space-y-6 animate-pulse">
                <div className="h-6 w-24 bg-muted" />
                <div className="space-y-3">
                    {Array.from({ length: 5 }).map((_, i) => (
                        <div key={i} className="h-5 w-full bg-muted" />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <aside className="w-full space-y-1 bg-card rounded-lg border border-border/50 p-4 shadow-sm">
            {/* Header with clear button */}
            <div className="flex items-center justify-between border-b border-border pb-3 mb-2">
                <div className="flex items-center gap-2 text-sm font-bold text-destructive">
                    <Filter className="h-4 w-4 text-destructive" />
                    Filtreler
                </div>
                {hasActiveFilters && (
                    <button
                        onClick={onClearAll}
                        className="flex items-center gap-1 text-[10px] font-bold uppercase tracking-wider text-destructive hover:text-destructive/80 transition-colors bg-destructive/5 px-2 py-1 rounded-full"
                    >
                        <X className="h-3 w-3" />
                        Temizle
                    </button>
                )}
            </div>

            {/* Selected filters chips */}
            {hasActiveFilters && (
                <div className="flex flex-wrap gap-1.5 pb-3 border-b border-border/50 mb-2">
                    {selectedBrands.map((brandSlug) => {
                        const brand = brandFacets.find((b) => b.slug === brandSlug);
                        return (
                            <button
                                key={brandSlug}
                                onClick={() => onToggleBrand(brandSlug)}
                                className="flex items-center gap-1 rounded-full bg-destructive/10 px-2.5 py-0.5 text-[10px] font-semibold text-destructive hover:bg-destructive/20 transition-colors border border-destructive/10"
                            >
                                {brand?.name ?? brandSlug}
                                <X className="h-2.5 w-2.5" />
                            </button>
                        );
                    })}
                    {(selectedPriceMin !== null || selectedPriceMax !== null) && (
                        <button
                            onClick={() => {
                                setPriceMinInput("");
                                setPriceMaxInput("");
                                onPriceChange(null, null);
                            }}
                            className="flex items-center gap-1 rounded-full bg-destructive/10 px-2.5 py-0.5 text-[10px] font-semibold text-destructive hover:bg-destructive/20 transition-colors border border-destructive/10"
                        >
                            {selectedPriceMin ?? 0} TL - {selectedPriceMax ?? "∞"}
                            <X className="h-2.5 w-2.5" />
                        </button>
                    )}
                </div>
            )}

            {/* Stock availability toggle */}
            <div className="py-4 border-b border-border/50">
                <button
                    type="button"
                    onClick={onStockToggle}
                    className="flex w-full cursor-pointer items-center justify-between mb-1"
                >
                    <span className={cn("text-sm font-semibold transition-colors", inStockOnly ? "text-destructive" : "text-muted-foreground")}>
                        Sadece Stoktakiler
                    </span>
                    <div
                        className={cn(
                            "relative h-5 w-9 rounded-full transition-colors",
                            inStockOnly ? "bg-destructive" : "bg-muted"
                        )}
                    >
                        <div
                            className="absolute top-0.5 h-4 w-4 rounded-full bg-white shadow-sm transition-all"
                            style={{ left: inStockOnly ? "18px" : "2px" }}
                        />
                    </div>
                </button>
            </div>

            {/* Category facets - Checkbox filters - REMOVED PER USER REQUEST
            {categoryFacets.length > 0 && onToggleCategory && (
                <FacetSection title="Kategoriler" defaultOpen>
                    <div className="max-h-[300px] overflow-y-auto pr-1 scrollbar-thin space-y-0.5">
                        {categoryFacets.map((cat) => (
                            <CheckboxItem
                                key={cat.id}
                                label={cat.name}
                                count={0}
                                checked={selectedCategories?.includes(cat.slug) || false}
                                onChange={() => onToggleCategory(cat.slug)}
                            />
                        ))}
                    </div>
                </FacetSection>
            )}
            */}

            {/* Brand facets - Search & Square Checks */}
            {brandFacets.length > 0 && (
                <FacetSection title="Markalar" defaultOpen>
                    {brandFacets.length > 6 && (
                        <div className="mb-3">
                            <input
                                type="text"
                                placeholder="ARA..."
                                value={brandSearch}
                                onChange={(e) => setBrandSearch(e.target.value)}
                                className="w-full text-xs font-medium border-b border-border bg-transparent px-0 py-2 focus:border-destructive outline-none transition-all placeholder:text-muted-foreground/50 uppercase tracking-widest text-destructive"
                            />
                        </div>
                    )}
                    <div className="max-h-[300px] overflow-y-auto pr-1 scrollbar-thin space-y-0.5">
                        {filteredBrands.length > 0 ? (
                            filteredBrands.map((brand) => (
                                <CheckboxItem
                                    key={brand.id}
                                    label={brand.name}
                                    count={0} // Hidden in component
                                    checked={selectedBrands.includes(brand.slug)}
                                    onChange={() => onToggleBrand(brand.slug)}
                                    imageUrl={brand.logo_url}
                                />
                            ))
                        ) : (
                            <p className="py-2 text-[10px] text-muted-foreground uppercase">
                                Bulunamadı
                            </p>
                        )}
                    </div>
                </FacetSection>
            )}

            {/* Series Facets */}
            {seriesFacets && seriesFacets.length > 0 && onToggleSeries && (
                <FacetSection title="Modeller" defaultOpen>
                    <div className="space-y-0.5 max-h-[200px] overflow-y-auto pr-1 scrollbar-thin">
                        {seriesFacets.map((series) => {
                            const checked = selectedSeries?.includes(series.slug);
                            return (
                                <CheckboxItem
                                    key={series.id}
                                    label={series.name}
                                    count={0}
                                    checked={checked || false}
                                    onChange={() => onToggleSeries(series.slug)}
                                />
                            );
                        })}
                    </div>
                </FacetSection>
            )}

            {/* Dynamic Attribute Facets */}
            {attributeFacets && attributeFacets.map((facet) => (
                <FacetSection key={facet.key} title={facet.label} defaultOpen={false}>
                    <div className="space-y-0.5 max-h-[200px] overflow-y-auto pr-1 scrollbar-thin">
                        {facet.options.map((option) => {
                            const isSelected = selectedAttributes?.[facet.key] === option.value;
                            return (
                                <CheckboxItem
                                    key={option.value}
                                    label={option.label}
                                    count={0}
                                    checked={isSelected}
                                    onChange={() => onToggleAttribute?.(facet.key, option.value)}
                                />
                            );
                        })}
                    </div>
                </FacetSection>
            ))}

            {/* Price filter removed per user request */}
        </aside>
    );
}
