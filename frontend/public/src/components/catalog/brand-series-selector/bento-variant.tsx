"use client";

import Image from "next/image";
import Link from "next/link";
import { useState } from "react";
import { Brand, Series } from "@/lib/api/schemas";
import { getMediaUrl, cn } from "@/lib/utils";
import {
    Search,
    X,
    Check,
    ChevronRight,
    Tag,
    Layers,
    ShoppingBag
} from "lucide-react";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
// import { Badge } from "@/components/ui/badge"; // Removed unused Badge

interface BentoVariantProps {
    brands: Brand[];
    series: Series[];
    singletonProducts?: Series[];
    selectedBrand: string | null;
    selectedSeries: string | null;
    onBrandSelect: (brandSlug: string | null) => void;
    onSeriesSelect: (seriesSlug: string | null) => void;
    brandsLoading?: boolean;
    seriesLoading?: boolean;
    // categoryName?: string; // Removed unused prop
}

export function BentoVariant({
    brands,
    series,
    singletonProducts = [],
    selectedBrand,
    selectedSeries,
    onBrandSelect,
    onSeriesSelect,
    brandsLoading = false,
    seriesLoading = false,
    // categoryName, // Removed unused prop
}: BentoVariantProps) {
    const [brandSearch, setBrandSearch] = useState("");

    const filteredBrands = brands.filter((b) =>
        b.name.toLowerCase().includes(brandSearch.toLowerCase())
    );

    const selectedBrandObj = brands.find((b) => b.slug === selectedBrand);

    // Step indicator
    const currentStep = !selectedBrand ? 1 : !selectedSeries ? 2 : 3;

    return (
        <div className="space-y-6 overflow-x-hidden">
            {/* Step Indicator - Compact */}
            <div className="flex items-center gap-2 text-xs border-b pb-4">
                <div
                    className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1 rounded-sm transition-all",
                        currentStep === 1
                            ? "bg-primary text-primary-foreground font-medium"
                            : selectedBrand
                                ? "bg-secondary text-foreground"
                                : "text-muted-foreground"
                    )}
                >
                    <span className="flex h-4 w-4 items-center justify-center rounded-sm bg-current/20 text-[10px] font-bold">
                        {selectedBrand ? <Check className="h-3 w-3" /> : "1"}
                    </span>
                    <span>Marka</span>
                </div>
                <ChevronRight className="h-3 w-3 text-muted-foreground" />
                <div
                    className={cn(
                        "flex items-center gap-1.5 px-2.5 py-1 rounded-sm transition-all",
                        currentStep === 2
                            ? "bg-primary text-primary-foreground font-medium"
                            : selectedSeries
                                ? "bg-secondary text-foreground"
                                : "text-muted-foreground"
                    )}
                >
                    <span className="flex h-4 w-4 items-center justify-center rounded-sm bg-current/20 text-[10px] font-bold">
                        {selectedSeries ? <Check className="h-3 w-3" /> : "2"}
                    </span>
                    <span>Seri</span>
                </div>
            </div>

            {/* BRAND SELECTION VIEW */}
            {!selectedBrand && (
                <div className="space-y-6">
                    {/* Header & Search */}
                    <div className="flex flex-col sm:flex-row gap-4 items-start sm:items-center justify-between">
                        <div>
                            <h2 className="text-lg font-semibold tracking-tight">Marka Seçimi</h2>
                            <p className="text-xs text-muted-foreground">Devam etmek için bir marka seçin.</p>
                        </div>

                        <div className="relative w-full sm:w-64">
                            <Search className="absolute left-3 top-1/2 h-3.5 w-3.5 -translate-y-1/2 text-muted-foreground" />
                            <Input
                                placeholder="Marka ara..."
                                value={brandSearch}
                                onChange={(e) => setBrandSearch(e.target.value)}
                                className="pl-9 pr-9 h-9 text-sm rounded-sm border-border/60 bg-background/50 focus:bg-background transition-colors"
                            />
                            {brandSearch && (
                                <button
                                    onClick={() => setBrandSearch("")}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                                >
                                    <X className="h-3.5 w-3.5" />
                                </button>
                            )}
                        </div>
                    </div>

                    {/* Brand Grid - Compact & Dense */}
                    {brandsLoading ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                            {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                                <div key={i} className="h-24 animate-pulse rounded-sm bg-muted" />
                            ))}
                        </div>
                    ) : filteredBrands.length > 0 ? (
                        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-3">
                            {filteredBrands.map((brand) => (
                                <button
                                    key={brand.id}
                                    onClick={() => onBrandSelect(brand.slug)}
                                    className={cn(
                                        "group relative flex flex-col items-center justify-center p-3 h-28 rounded-sm border border-border bg-card transition-all duration-200",
                                        "hover:border-primary/50 hover:shadow-md"
                                    )}
                                >
                                    {/* Logo Area */}
                                    <div className="relative h-12 w-full mb-3 flex items-center justify-center">
                                        {brand.logo_url ? (
                                            <Image
                                                src={getMediaUrl(brand.logo_url)}
                                                alt={brand.name}
                                                fill
                                                className="object-contain opacity-90 group-hover:opacity-100 transition-opacity"
                                                sizes="150px"
                                            />
                                        ) : (
                                            <span className="text-2xl font-bold text-muted-foreground/20 group-hover:text-primary/40 transition-colors">
                                                {brand.name.charAt(0).toUpperCase()}
                                            </span>
                                        )}
                                    </div>

                                    {/* Name */}
                                    <span className="text-xs font-medium text-center line-clamp-1 group-hover:text-primary transition-colors">
                                        {brand.name}
                                    </span>
                                </button>
                            ))}
                        </div>
                    ) : (
                        <div className="py-12 text-center text-sm text-muted-foreground">
                            Marka bulunamadı.
                        </div>
                    )}
                </div>
            )}

            {/* SERIES SELECTION VIEW */}
            {selectedBrand && !selectedSeries && (
                <div className="space-y-6">
                    {/* Selected Brand Header */}
                    <div className="flex items-center justify-between rounded-sm border border-border/60 bg-muted/20 p-3">
                        <div className="flex items-center gap-3">
                            <Tag className="h-4 w-4 text-primary" />
                            <div>
                                <p className="text-[10px] text-muted-foreground uppercase font-semibold">Seçili Marka</p>
                                <p className="text-sm font-medium">{selectedBrandObj?.name || selectedBrand}</p>
                            </div>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => onBrandSelect(null)}
                            className="h-7 text-xs hover:bg-background hover:text-foreground"
                        >
                            <X className="h-3 w-3 mr-1.5" />
                            Değiştir
                        </Button>
                    </div>

                    {/* Series Grid - Compact */}
                    {seriesLoading ? (
                        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                            {[1, 2, 3].map((i) => (
                                <div key={i} className="aspect-[3/2] animate-pulse rounded-sm bg-muted" />
                            ))}
                        </div>
                    ) : series.length > 0 || singletonProducts.length > 0 ? (
                        <div className="space-y-8">
                            {/* Series List */}
                            {series.length > 0 && (
                                <div>
                                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 text-foreground/80">
                                        <Layers className="h-4 w-4" />
                                        Ürün Serileri
                                    </h3>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
                                        {series.map((s) => (
                                            <button
                                                key={s.id}
                                                onClick={() => onSeriesSelect(s.slug)}
                                                className="group relative overflow-hidden rounded-sm border border-border bg-card transition-all hover:border-primary/50 hover:shadow-md text-left"
                                            >
                                                <div className="relative aspect-[16/9] w-full bg-muted">
                                                    {s.cover_media_url ? (
                                                        <Image
                                                            src={getMediaUrl(s.cover_media_url)}
                                                            alt={s.name}
                                                            fill
                                                            className="object-cover transition-transform duration-500 group-hover:scale-105"
                                                        />
                                                    ) : (
                                                        <div className="flex h-full w-full items-center justify-center">
                                                            <Layers className="h-8 w-8 text-muted-foreground/20" />
                                                        </div>
                                                    )}
                                                    <div className="absolute inset-0 bg-gradient-to-t from-black/80 via-transparent to-transparent opacity-80" />

                                                    <div className="absolute bottom-2 left-3 right-3">
                                                        <h4 className="text-sm font-bold text-white leading-tight mb-0.5">{s.name}</h4>
                                                        <p className="text-[10px] text-white/80">{s.products_count} Ürün</p>
                                                    </div>
                                                </div>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                            )}

                            {/* Products List */}
                            {singletonProducts.length > 0 && (
                                <div>
                                    <h3 className="text-sm font-semibold mb-3 flex items-center gap-2 text-foreground/80">
                                        <ShoppingBag className="h-4 w-4" />
                                        Ürünler
                                    </h3>
                                    <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                                        {singletonProducts.map((s) => (
                                            <Link
                                                key={s.id}
                                                href={`/urun/${s.single_product_slug}`}
                                                className="group relative rounded-sm border border-border bg-card p-3 hover:border-primary/50 hover:shadow-sm transition-all flex flex-col"
                                            >
                                                <div className="relative aspect-square w-full mb-3 bg-muted rounded-sm overflow-hidden">
                                                    {s.single_product_image_url || s.cover_media_url ? (
                                                        <Image
                                                            src={getMediaUrl(s.single_product_image_url || s.cover_media_url)}
                                                            alt={s.single_product_name || s.name}
                                                            fill
                                                            className="object-contain p-2 transition-transform duration-500 group-hover:scale-110"
                                                        />
                                                    ) : (
                                                        <div className="flex h-full w-full items-center justify-center text-muted-foreground/20 text-2xl font-bold">
                                                            {(s.single_product_name || s.name).charAt(0)}
                                                        </div>
                                                    )}
                                                </div>
                                                <h4 className="text-xs font-semibold line-clamp-2 min-h-[2.5em] group-hover:text-primary transition-colors flex-grow">
                                                    {s.single_product_name || s.name}
                                                </h4>
                                                <div className="mt-3">
                                                    <Button
                                                        size="sm"
                                                        variant="secondary"
                                                        className="w-full h-7 text-xs bg-muted/50 group-hover:bg-primary group-hover:text-primary-foreground transition-colors pointer-events-none"
                                                    >
                                                        İncele
                                                    </Button>
                                                </div>
                                            </Link>
                                        ))}
                                    </div>
                                </div>
                            )}
                        </div>
                    ) : (
                        <div className="py-12 text-center text-sm text-muted-foreground">
                            Bu markaya ait seri veya ürün bulunamadı.
                        </div>
                    )}
                </div>
            )}
        </div>
    );
}
