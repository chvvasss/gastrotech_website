"use client";

import Image from "next/image";
import { Brand, Series } from "@/lib/api/schemas";
import { getMediaUrl, cn } from "@/lib/utils";
import {
    Check,
    ChevronRight,
    Tag,
    Layers,
    Package,
    ArrowRight,
    X
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";

interface PanelVariantProps {
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

export function PanelVariant({
    brands,
    series,
    singletonProducts: _singletonProducts = [],
    selectedBrand,
    selectedSeries: _selectedSeries,
    onBrandSelect,
    onSeriesSelect,
    brandsLoading = false,
    seriesLoading = false,
}: PanelVariantProps) {
    const selectedBrandObj = brands.find((b) => b.slug === selectedBrand);
    const currentStep = !selectedBrand ? 1 : 2;

    return (
        <div className="space-y-6">
            {/* Step Indicator - Enterprise Style */}
            <div className="flex items-center gap-1 p-1 bg-muted rounded-sm w-fit">
                <div
                    className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-all",
                        currentStep === 1
                            ? "bg-background text-foreground shadow-sm"
                            : selectedBrand
                                ? "text-primary"
                                : "text-muted-foreground"
                    )}
                >
                    <span className={cn(
                        "flex h-6 w-6 items-center justify-center rounded-sm text-xs font-bold",
                        currentStep === 1 ? "bg-primary text-primary-foreground" :
                            selectedBrand ? "bg-primary/20 text-primary" : "bg-muted-foreground/20"
                    )}>
                        {selectedBrand ? <Check className="h-3.5 w-3.5" /> : "1"}
                    </span>
                    Marka
                </div>
                <ChevronRight className="h-4 w-4 text-muted-foreground" />
                <div
                    className={cn(
                        "flex items-center gap-2 px-4 py-2 rounded-sm text-sm font-medium transition-all",
                        currentStep === 2
                            ? "bg-background text-foreground shadow-sm"
                            : "text-muted-foreground"
                    )}
                >
                    <span className={cn(
                        "flex h-6 w-6 items-center justify-center rounded-sm text-xs font-bold",
                        currentStep === 2 ? "bg-primary text-primary-foreground" : "bg-muted-foreground/20"
                    )}>
                        2
                    </span>
                    Seri
                </div>
            </div>

            {/* Two-Column Layout */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
                {/* Left Panel - Brand List */}
                <div className="lg:col-span-4">
                    <div className="rounded-sm border bg-card">
                        <div className="p-4 border-b">
                            <h3 className="font-semibold flex items-center gap-2">
                                <Tag className="h-4 w-4 text-primary" />
                                Marka Seçimi
                            </h3>
                            {selectedBrand && (
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    onClick={() => onBrandSelect(null)}
                                    className="mt-2 w-full justify-start text-muted-foreground"
                                >
                                    <X className="h-3.5 w-3.5 mr-2" />
                                    Seçimi Temizle
                                </Button>
                            )}
                        </div>

                        <ScrollArea className="h-[400px] lg:h-[500px]">
                            {brandsLoading ? (
                                <div className="p-4 space-y-3">
                                    {[1, 2, 3, 4, 5].map((i) => (
                                        <div key={i} className="h-12 animate-pulse rounded-sm bg-muted" />
                                    ))}
                                </div>
                            ) : brands.length > 0 ? (
                                <div className="p-2 space-y-1">
                                    {brands.map((brand) => (
                                        <button
                                            key={brand.id}
                                            onClick={() => onBrandSelect(brand.slug)}
                                            className={cn(
                                                "flex items-center gap-3 w-full p-3 rounded-sm text-left transition-all",
                                                "hover:bg-muted focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                                                selectedBrand === brand.slug && "bg-primary/5 border border-primary/20"
                                            )}
                                        >
                                            <div className={cn(
                                                "flex h-5 w-5 items-center justify-center rounded border shrink-0",
                                                selectedBrand === brand.slug
                                                    ? "border-primary bg-primary"
                                                    : "border-muted-foreground/40"
                                            )}>
                                                {selectedBrand === brand.slug && (
                                                    <Check className="h-3 w-3 text-primary-foreground" />
                                                )}
                                            </div>
                                            <div className="relative h-full w-full">
                                                {brand.logo_url ? (
                                                    <Image
                                                        src={getMediaUrl(brand.logo_url)}
                                                        alt={brand.name}
                                                        fill
                                                        className="object-contain p-2 transition-transform duration-300 group-hover:scale-110"
                                                    />
                                                ) : (
                                                    <div className="flex h-full w-full items-center justify-center bg-muted rounded">
                                                        <Package className="h-4 w-4 text-muted-foreground/40" />
                                                    </div>
                                                )}
                                            </div>
                                            <span className="font-medium flex-1 truncate">{brand.name}</span>
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center p-8 text-center">
                                    <Package className="h-8 w-8 text-muted-foreground/20 mb-2" />
                                    <p className="text-sm text-muted-foreground">Marka bulunamadı</p>
                                </div>
                            )}
                        </ScrollArea>
                    </div>
                </div>

                {/* Right Panel - Series List */}
                <div className="lg:col-span-8">
                    <div className="rounded-sm border bg-card">
                        <div className="p-4 border-b">
                            <h3 className="font-semibold flex items-center gap-2">
                                <Layers className="h-4 w-4 text-primary" />
                                Seri Seçimi
                                {selectedBrandObj && (
                                    <Badge variant="secondary" className="ml-2">
                                        {selectedBrandObj.name}
                                    </Badge>
                                )}
                            </h3>
                        </div>

                        <ScrollArea className="h-[400px] lg:h-[500px]">
                            {!selectedBrand ? (
                                <div className="flex flex-col items-center justify-center p-12 text-center">
                                    <div className="h-16 w-16 rounded-sm bg-muted flex items-center justify-center mb-4">
                                        <Tag className="h-8 w-8 text-muted-foreground/20" />
                                    </div>
                                    <p className="font-medium">Önce marka seçin</p>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        Soldaki listeden bir marka seçerek devam edin
                                    </p>
                                </div>
                            ) : seriesLoading ? (
                                <div className="p-4 space-y-3">
                                    {[1, 2, 3].map((i) => (
                                        <div key={i} className="h-20 animate-pulse rounded-sm bg-muted" />
                                    ))}
                                </div>
                            ) : series.length > 0 ? (
                                <div className="p-2 space-y-2">
                                    {series.map((s) => (
                                        <button
                                            key={s.id}
                                            onClick={() => onSeriesSelect(s.slug)}
                                            className={cn(
                                                "flex items-center gap-4 w-full p-3 rounded-sm text-left transition-all",
                                                "hover:bg-muted",
                                                "focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2",
                                                "active:bg-muted/80"
                                            )}
                                        >
                                            {/* Thumbnail */}
                                            <div className="relative h-14 w-20 shrink-0 rounded-sm overflow-hidden bg-muted">
                                                {s.cover_media_url ? (
                                                    <Image
                                                        src={getMediaUrl(s.cover_media_url)}
                                                        alt={s.name}
                                                        fill
                                                        className="object-cover"
                                                        sizes="80px"
                                                    />
                                                ) : (
                                                    <div className="flex h-full w-full items-center justify-center">
                                                        <Layers className="h-5 w-5 text-muted-foreground/30" />
                                                    </div>
                                                )}
                                            </div>

                                            {/* Content */}
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2">
                                                    <h4 className="font-medium truncate">{s.name}</h4>
                                                    {s.is_featured && (
                                                        <Badge className="bg-amber-100 text-amber-700 text-xs">Öne Çıkan</Badge>
                                                    )}
                                                </div>
                                                <p className="text-sm text-muted-foreground truncate mt-0.5">
                                                    {s.description_short || "Açıklama yok"}
                                                </p>
                                                <p className="text-xs text-muted-foreground mt-1">
                                                    {s.products_count || 0} ürün
                                                </p>
                                            </div>

                                            {/* Arrow */}
                                            <ArrowRight className="h-4 w-4 text-muted-foreground shrink-0" />
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="flex flex-col items-center justify-center p-12 text-center">
                                    <Layers className="h-10 w-10 text-muted-foreground/20 mb-3" />
                                    <p className="font-medium">Seri Bulunamadı</p>
                                    <p className="text-sm text-muted-foreground mt-1">
                                        Bu markaya ait seri bulunmuyor
                                    </p>
                                    <Button
                                        variant="link"
                                        onClick={() => onBrandSelect(null)}
                                        className="mt-2"
                                    >
                                        Farklı marka seç
                                    </Button>
                                </div>
                            )}
                        </ScrollArea>
                    </div>
                </div>
            </div>
        </div>
    );
}
