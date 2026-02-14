"use client";

import { Brand, Series } from "@/lib/api/schemas";
import { BentoVariant } from "./bento-variant";
import { PanelVariant } from "./panel-variant";
import { PaletteVariant } from "./palette-variant";

// Feature toggle - change this to switch between variants
// Options: "bento" | "panel" | "palette"
export const UI_VARIANT = (process.env.NEXT_PUBLIC_BRAND_SERIES_UI as SelectorVariant) ?? "bento";

export type SelectorVariant = "bento" | "panel" | "palette";

export interface BrandSeriesSelectorProps {
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
    variant?: SelectorVariant;
}

export function BrandSeriesSelector({
    variant = UI_VARIANT,
    ...props
}: BrandSeriesSelectorProps) {
    switch (variant) {
        case "panel":
            return <PanelVariant {...props} />;
        case "palette":
            return <PaletteVariant {...props} />;
        case "bento":
        default:
            return <BentoVariant {...props} />;
    }
}

// Re-export for convenience
export { BentoVariant, PanelVariant, PaletteVariant };
