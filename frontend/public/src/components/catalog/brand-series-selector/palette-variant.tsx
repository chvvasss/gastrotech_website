"use client";

import Image from "next/image";
import { useState } from "react";
import { Brand, Series } from "@/lib/api/schemas";
import { getMediaUrl, cn } from "@/lib/utils";
import {
    Check,
    ChevronRight,
    ChevronDown,
    Tag,
    Layers,
    Package,
    ArrowRight,
    Search,
    X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

interface PaletteVariantProps {
    brands: Brand[];
    series: Series[];
    singletonProducts?: Series[];  // Series with exactly 1 product - display as product cards
    selectedBrand: string | null;
    selectedSeries: string | null;
    onBrandSelect: (brandSlug: string | null) => void;
    onSeriesSelect: (seriesSlug: string | null) => void;
    brandsLoading?: boolean;
    seriesLoading?: boolean;
    categoryName?: string;
}

export function PaletteVariant({
    brands,
    series,
    singletonProducts: _singletonProducts = [],
    selectedBrand,
    selectedSeries: _selectedSeries,
    onBrandSelect,
    onSeriesSelect,
    brandsLoading = false,
    seriesLoading = false,
}: PaletteVariantProps) {
    const [brandOpen, setBrandOpen] = useState(false);
    const [brandSearch, setBrandSearch] = useState("");
    const selectedBrandObj = brands.find((b) => b.slug === selectedBrand);
    const currentStep = !selectedBrand ? 1 : 2;

    const filteredBrands = brands.filter((b) =>
        b.name.toLowerCase().includes(brandSearch.toLowerCase())
    );

    return (
        <div className="space-y-6">
            {/* Step Indicator - Minimal */}
            <div className="flex items-center gap-3 text-sm">
                <div
                    className={cn(
                        "flex items-center gap-1.5",
                        currentStep === 1 ? "text-primary font-medium" :
                            selectedBrand ? "text-muted-foreground" : "text-muted-foreground"
                    )}
                >
                    <span className={cn(
                        "flex h-5 w-5 items-center justify-center rounded-sm text-xs",
                        currentStep === 1 ? "bg-primary text-primary-foreground" :
                            selectedBrand ? "bg-primary/20 text-primary" : "bg-muted"
                    )}>
                        {selectedBrand ? <Check className="h-3 w-3" /> : "1"}
                    </span>
                    Marka
                </div>
                <ChevronRight className="h-3.5 w-3.5 text-muted-foreground/50" />
                <div
                    className={cn(
                        "flex items-center gap-1.5",
                        currentStep === 2 ? "text-primary font-medium" : "text-muted-foreground"
                    )}
                >
                    <span className={cn(
                        "flex h-5 w-5 items-center justify-center rounded-sm text-xs",
                        currentStep === 2 ? "bg-primary text-primary-foreground" : "bg-muted"
                    )}>
                        2
                    </span>
                    Seri
                </div>
            </div>

            {/* Brand Selector - Dropdown Style */}
            <div className="flex flex-col sm:flex-row sm:items-start gap-3">
                <div className="relative w-full sm:w-[280px]">
                    <Button
                        variant="outline"
                        onClick={() => setBrandOpen(!brandOpen)}
                        className={cn(
                            "w-full justify-between h-11",
                            !selectedBrand && "text-muted-foreground"
                        )}
                    >
                        <div className="flex items-center gap-2 truncate">
                            <Tag className="h-4 w-4 shrink-0" />
                            {selectedBrandObj ? (
                                <>
                                    {selectedBrandObj.logo_url && (
                                        <div className="relative h-5 w-8 shrink-0">
                                            <Image
                                                src={getMediaUrl(selectedBrandObj.logo_url)}
                                                alt=""
                                                fill
                                                className="object-contain"
                                                sizes="32px"
                                            />
                                        </div>
                                    )}
                                    <span className="truncate">{selectedBrandObj.name}</span>
                                </>
                            ) : (
                                "Marka seçin..."
                            )}
                        </div>
                        <ChevronDown className={cn(
                            "ml-2 h-4 w-4 shrink-0 opacity-50 transition-transform",
                            brandOpen && "rotate-180"
                        )} />
                    </Button>

                    {/* Dropdown Panel */}
                    {brandOpen && (
                        <div className="absolute z-50 top-full left-0 right-0 mt-1 rounded-sm border bg-card shadow-lg overflow-hidden">
                            {/* Search */}
                            <div className="p-2 border-b">
                                <div className="relative">
                                    <Search className="absolute left-2.5 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
                                    <Input
                                        placeholder="Marka ara..."
                                        value={brandSearch}
                                        onChange={(e) => setBrandSearch(e.target.value)}
                                        className="pl-8 h-9"
                                        autoFocus
                                    />
                                </div>
                            </div>

                            {/* List */}
                            <div className="max-h-[300px] overflow-y-auto">
                                {filteredBrands.length > 0 ? (
                                    <div className="p-1">
                                        {filteredBrands.map((brand) => (
                                            <button
                                                key={brand.id}
                                                onClick={() => {
                                                    onBrandSelect(brand.slug);
                                                    setBrandOpen(false);
                                                    setBrandSearch("");
                                                }}
                                                className={cn(
                                                    "flex items-center gap-3 w-full p-2.5 rounded-sm text-left transition-all",
                                                    "hover:bg-muted focus:bg-muted focus:outline-none",
                                                    selectedBrand === brand.slug && "bg-primary/5"
                                                )}
                                            >
                                                <div className="relative h-8 w-12 flex-shrink-0 bg-white rounded-sm border p-0.5">
                                                    {brand.logo_url ? (
                                                        <Image
                                                            src={getMediaUrl(brand.logo_url)}
                                                            alt={brand.name}
                                                            fill
                                                            className="object-contain p-0.5"
                                                        />
                                                    ) : (
                                                        <div className="flex h-full w-full items-center justify-center bg-muted rounded">
                                                            <Package className="h-3 w-3 text-muted-foreground/40" />
                                                        </div>
                                                    )}
                                                </div>
                                                <span className="flex-1 truncate text-sm">{brand.name}</span>
                                                {selectedBrand === brand.slug && (
                                                    <Check className="h-4 w-4 text-primary shrink-0" />
                                                )}
                                            </button>
                                        ))}
                                    </div>
                                ) : (
                                    <div className="p-4 text-center text-sm text-muted-foreground">
                                        Marka bulunamadı
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>

                {selectedBrand && (
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onBrandSelect(null)}
                        className="text-muted-foreground shrink-0"
                    >
                        <X className="h-4 w-4 mr-1" />
                        Temizle
                    </Button>
                )}
            </div>

            {/* Click outside to close */}
            {brandOpen && (
                <div
                    className="fixed inset-0 z-40"
                    onClick={() => {
                        setBrandOpen(false);
                        setBrandSearch("");
                    }}
                />
            )}

            {/* Series Grid - Minimal Cards */}
            {selectedBrand && (
                <div className="space-y-4">
                    <h3 className="text-sm font-medium text-muted-foreground flex items-center gap-2">
                        <Layers className="h-4 w-4" />
                        {selectedBrandObj?.name} Serileri
                    </h3>

                    {seriesLoading ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                            {[1, 2, 3, 4].map((i) => (
                                <div key={i} className="h-24 animate-pulse rounded-sm bg-muted" />
                            ))}
                        </div>
                    ) : series.length > 0 ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
                            {series.map((s) => (
                                <button
                                    key={s.id}
                                    onClick={() => onSeriesSelect(s.slug)}
                                    className={cn(
                                        "group relative flex flex-col p-4 rounded-sm border-2 bg-card text-left transition-all",
                                        "hover:border-primary hover:shadow-md",
                                        "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                                        "active:scale-[0.98]"
                                    )}
                                >
                                    {/* Badges */}
                                    <div className="flex items-center gap-1 mb-2">
                                        {s.is_featured && (
                                            <Badge className="bg-amber-100 text-amber-700 text-[10px] px-1.5 py-0">
                                                Öne Çıkan
                                            </Badge>
                                        )}
                                        <Badge variant="secondary" className="text-[10px] px-1.5 py-0">
                                            {s.products_count || 0} ürün
                                        </Badge>
                                    </div>

                                    {/* Name */}
                                    <h4 className="font-semibold text-sm line-clamp-2 flex-1">
                                        {s.name}
                                    </h4>

                                    {/* Arrow */}
                                    <ArrowRight className="h-4 w-4 text-muted-foreground mt-2 transition-transform group-hover:translate-x-1 group-hover:text-primary" />
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="flex flex-col items-center justify-center py-12 text-center rounded-sm border border-dashed bg-muted/20">
                            <Layers className="h-8 w-8 text-muted-foreground/20 mb-2" />
                            <p className="font-medium text-sm">Seri bulunamadı</p>
                            <p className="text-xs text-muted-foreground mt-1">
                                Bu markaya ait seri yok
                            </p>
                        </div>
                    )}
                </div>
            )}

            {/* Initial State */}
            {!selectedBrand && !brandsLoading && brands.length > 0 && (
                <div className="flex flex-col items-center justify-center py-12 text-center rounded-sm border border-dashed bg-muted/10">
                    <div className="h-12 w-12 rounded-sm bg-primary/10 flex items-center justify-center mb-3">
                        <Tag className="h-6 w-6 text-primary" />
                    </div>
                    <p className="font-medium">Bir marka seçerek başlayın</p>
                    <p className="text-sm text-muted-foreground mt-1">
                        Yukarıdaki açılır menüden marka seçin
                    </p>
                </div>
            )}
        </div>
    );
}
