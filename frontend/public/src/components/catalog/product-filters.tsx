"use client";

import { X } from "lucide-react";
import Image from "next/image";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn, getMediaUrl } from "@/lib/utils";
import { NavCategory } from "@/lib/api/schemas";

interface Brand {
    id: string;
    name: string;
    slug: string;
    logo_url?: string | null;
}

interface ProductFiltersProps {
    search: string;
    onSearchChange: (value: string) => void;
    selectedCategory: string;
    onCategorySelect: (categorySlug: string, seriesSlug?: string) => void;
    selectedSeries: string;
    onSeriesSelect: (seriesSlug: string) => void;
    categories: NavCategory[];
    brands?: Brand[];
    selectedBrand?: string;
    onBrandSelect?: (brandSlug: string) => void;
    hasActiveFilters: boolean;
    clearFilters: () => void;
}

export function ProductFilters({
    search,
    onSearchChange,
    selectedCategory,
    onCategorySelect,
    selectedSeries,
    onSeriesSelect,
    categories,
    brands = [],
    selectedBrand = "",
    onBrandSelect,
    hasActiveFilters,
    clearFilters,
}: ProductFiltersProps) {

    return (
        <div className="flex flex-col h-full max-h-[calc(100vh-200px)]">
            {/* Brands Section - Single column list with larger hit areas */}
            {brands.length > 0 && onBrandSelect && (
                <div className="mb-5 pb-5 border-b">
                    <label className="mb-3 block text-sm font-medium">Marka</label>
                    <ScrollArea className="max-h-[180px]">
                        <div className="space-y-1 pr-2">
                            <button
                                onClick={() => onBrandSelect("")}
                                className={cn(
                                    "w-full flex items-center gap-3 rounded-sm px-3 py-2.5 text-left text-sm transition-all hover:bg-muted",
                                    !selectedBrand
                                        ? "bg-primary/10 text-primary font-medium"
                                        : "text-foreground"
                                )}
                            >
                                <span className="w-8 h-8 rounded bg-muted flex items-center justify-center text-xs font-medium">
                                    Tüm
                                </span>
                                <span>Tüm Markalar</span>
                            </button>
                            {brands.map((brand) => (
                                <button
                                    key={brand.id}
                                    onClick={() => onBrandSelect(brand.slug)}
                                    className={cn(
                                        "w-full flex items-center gap-3 rounded-sm px-3 py-2.5 text-left text-sm transition-all hover:bg-muted",
                                        selectedBrand === brand.slug
                                            ? "bg-primary/10 text-primary font-medium"
                                            : "text-foreground"
                                    )}
                                    title={brand.name}
                                >
                                    {brand.logo_url ? (
                                        <div className="relative h-6 w-12 mr-2">
                                            <Image
                                                src={getMediaUrl(brand.logo_url)}
                                                alt={brand.name}
                                                fill
                                                className="object-contain"
                                            />
                                        </div>
                                    ) : (
                                        <span className="w-8 h-8 rounded bg-muted flex items-center justify-center text-xs font-medium flex-shrink-0">
                                            {brand.name.charAt(0)}
                                        </span>
                                    )}
                                    <span className="truncate">{brand.name}</span>
                                </button>
                            ))}
                        </div>
                    </ScrollArea>
                </div>
            )}

            {/* Scrollable Filter Area */}
            <ScrollArea className="flex-1">
                <div className="space-y-6 pr-4">
                    {/* Search */}
                    <div>
                        <label className="mb-2 block text-sm font-medium">Ara</label>
                        <Input
                            placeholder="Ürün adı veya model kodu..."
                            value={search}
                            onChange={(e) => onSearchChange(e.target.value)}
                        />
                    </div>

                    {/* Categories */}
                    <div>
                        <label className="mb-2 block text-sm font-medium">Kategori</label>
                        <div className="space-y-1 max-h-[300px] overflow-y-auto">
                            <button
                                onClick={() => onCategorySelect("")}
                                className={cn(
                                    "w-full rounded-sm px-3 py-2 text-left text-sm hover:bg-muted",
                                    !selectedCategory && "bg-primary/10 text-primary"
                                )}
                            >
                                Tüm Kategoriler
                            </button>
                            {categories.map((cat) => (
                                <button
                                    key={cat.id}
                                    onClick={() => onCategorySelect(cat.slug)}
                                    className={cn(
                                        "w-full rounded-sm px-3 py-2 text-left text-sm hover:bg-muted",
                                        selectedCategory === cat.slug && "bg-primary/10 text-primary"
                                    )}
                                >
                                    {cat.menu_label || cat.name}
                                </button>
                            ))}
                        </div>
                    </div>

                    {/* Series (if category selected) */}
                    {selectedCategory && (
                        <div>
                            <label className="mb-2 block text-sm font-medium">Seri</label>
                            <div className="space-y-1 max-h-[200px] overflow-y-auto">
                                <button
                                    onClick={() => onSeriesSelect("")}
                                    className={cn(
                                        "w-full rounded-sm px-3 py-2 text-left text-sm hover:bg-muted",
                                        !selectedSeries && "bg-primary/10 text-primary"
                                    )}
                                >
                                    Tüm Seriler
                                </button>
                                {categories
                                    .find((c) => c.slug === selectedCategory)
                                    ?.series.map((series) => (
                                        <button
                                            key={series.id}
                                            onClick={() => onSeriesSelect(series.slug)}
                                            className={cn(
                                                "w-full rounded-sm px-3 py-2 text-left text-sm hover:bg-muted",
                                                selectedSeries === series.slug && "bg-primary/10 text-primary"
                                            )}
                                        >
                                            {series.name}
                                        </button>
                                    ))}
                            </div>
                        </div>
                    )}
                </div>
            </ScrollArea>

            {/* Clear Filters - Fixed at Bottom */}
            {hasActiveFilters && (
                <div className="mt-4 pt-4 border-t">
                    <Button variant="outline" className="w-full" onClick={clearFilters}>
                        <X className="mr-2 h-4 w-4" />
                        Filtreleri Temizle
                    </Button>
                </div>
            )}
        </div>
    );
}
