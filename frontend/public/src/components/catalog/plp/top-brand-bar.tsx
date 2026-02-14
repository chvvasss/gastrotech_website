"use client";

import Image from "next/image";
import { PLPBrandFacet } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";
import { cn } from "@/lib/utils";
import { X, Check } from "lucide-react";

interface TopBrandBarProps {
    brands: PLPBrandFacet[];
    selectedBrands: string[];
    onToggleBrand: (brandSlug: string) => void;
    onClearAll: () => void;
    isLoading?: boolean;
}

export function TopBrandBar({
    brands,
    selectedBrands,
    onToggleBrand,
    onClearAll,
    isLoading = false,
}: TopBrandBarProps) {
    if (isLoading) {
        return (
            <div className="flex gap-3 overflow-x-auto py-3 scrollbar-hide">
                {Array.from({ length: 6 }).map((_, i) => (
                    <div
                        key={i}
                        className="h-12 w-24 flex-shrink-0 animate-pulse rounded-full bg-muted"
                    />
                ))}
            </div>
        );
    }

    if (brands.length === 0) {
        return null;
    }

    const hasSelection = selectedBrands.length > 0;

    return (
        <div className="relative">
            {/* Changed to flex-wrap grid instead of scrollable */}
            <div className="flex flex-wrap items-center gap-2 py-1 px-1">
                {/* Clear all button - shown when there's a selection */}
                {hasSelection && (
                    <button
                        onClick={onClearAll}
                        className="flex flex-shrink-0 items-center gap-2 rounded-sm border border-destructive/40 bg-destructive/10 px-5 py-2.5 text-sm font-semibold text-destructive transition-all hover:bg-destructive/20"
                    >
                        <X className="h-4 w-4" />
                        Temizle
                    </button>
                )}

                {/* Brand pills - Large & Colorful */}
                {brands.map((brand) => {
                    const isSelected = selectedBrands.includes(brand.slug);

                    return (
                        <button
                            key={brand.slug}
                            onClick={() => onToggleBrand(brand.slug)}
                            className={cn(
                                // Base
                                "group relative flex flex-shrink-0 items-center gap-3 rounded-sm border px-5 py-2.5 transition-all",
                                // Selected state - BRAND RED
                                isSelected
                                    ? "border-destructive/50 bg-destructive/10 shadow-sm"
                                    : "border-border bg-card hover:border-destructive/30 hover:bg-muted/50",
                            )}
                        >
                            {/* Brand Logo if available */}
                            {brand.logo_url && (
                                <div className="relative h-12 w-24 flex-shrink-0 overflow-hidden rounded-sm bg-white/50">
                                    <Image
                                        src={brand.logo_url}
                                        alt={brand.name}
                                        fill
                                        className="object-contain p-0.5"
                                    />
                                </div>
                            )}

                            {/* Brand Name */}
                            <span
                                className={cn(
                                    "text-sm font-semibold transition-colors",
                                    isSelected ? "text-destructive" : "text-foreground group-hover:text-destructive",
                                )}
                            >
                                {brand.name}
                            </span>

                            {/* Checkmark for selected */}
                            {isSelected && (
                                <Check className="h-4 w-4 flex-shrink-0 text-destructive" />
                            )}
                        </button>
                    );
                })}
            </div>
        </div>
    );
}
