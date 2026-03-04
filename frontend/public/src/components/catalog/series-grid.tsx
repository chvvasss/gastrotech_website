"use client";

import Image from "next/image";
import { Series } from "@/lib/api/schemas";
import { getMediaUrl } from "@/lib/utils";
import { Layers, ArrowRight } from "lucide-react";
import { useRouter } from "next/navigation";

interface SeriesGridProps {
    series: Series[];
    onSelect?: (seriesSlug: string) => void;
    isLoading?: boolean;
}

export function SeriesGrid({ series, onSelect, isLoading = false }: SeriesGridProps) {
    const router = useRouter();

    const handleSelect = (item: Series) => {
        if (item.single_product_slug) {
            router.push(`/urun/${item.single_product_slug}`);
        } else {
            onSelect?.(item.slug);
        }
    };

    if (isLoading) {
        return (
            <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-2">
                {Array.from({ length: 3 }).map((_, i) => (
                    <div key={i} className="aspect-[3/4] sm:aspect-[4/3] animate-pulse rounded-sm bg-muted" />
                ))}
            </div>
        );
    }

    if (series.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-10 text-center rounded-sm border border-dashed border-border bg-muted/5">
                <Layers className="h-10 w-10 text-muted-foreground/20" />
                <p className="mt-3 text-sm font-medium text-muted-foreground">
                    Bu kategoride henüz seri bulunmuyor.
                </p>
            </div>
        );
    }

    return (
        <div className="grid grid-cols-2 gap-3 sm:gap-5 lg:grid-cols-2">
            {series.map((item) => (
                <div
                    key={item.id}
                    className="group relative cursor-pointer overflow-hidden rounded-sm border border-border bg-card transition-all duration-300 hover:border-primary/50 hover:shadow-md"
                    onClick={() => handleSelect(item)}
                >
                    {/* Image Area */}
                    <div className="relative aspect-[3/4] sm:aspect-[4/3] w-full overflow-hidden bg-zinc-50">
                        {item.single_product_image_url || item.cover_media_url ? (
                            <Image
                                src={getMediaUrl(item.single_product_image_url || item.cover_media_url)}
                                alt={item.single_product_name || item.name}
                                fill
                                className="object-contain p-2 sm:p-4 transition-transform duration-500 group-hover:scale-105"
                                sizes="(max-width: 768px) 50vw, (max-width: 1200px) 50vw, 33vw"
                            />
                        ) : (
                            <div className="flex h-full w-full flex-col items-center justify-center gap-2 bg-secondary/10 text-muted-foreground/30">
                                <Layers className="h-8 w-8 sm:h-10 sm:w-10" />
                            </div>
                        )}

                        {/* Gradient Overlay */}
                        <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />

                        {/* Title Overlay */}
                        <div className="absolute bottom-0 left-0 right-0 p-2.5 sm:p-4">
                            <h3 className="text-sm sm:text-lg font-bold leading-tight text-white drop-shadow-sm">
                                {item.single_product_name || item.name}
                            </h3>
                            {item.description_short && (
                                <p className="mt-1 line-clamp-2 text-[10px] sm:text-xs text-white/80 hidden sm:block">
                                    {item.description_short}
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Action Bar */}
                    <div className="border-t border-border/50 px-2 sm:px-3 py-1.5 sm:py-2.5 flex items-center justify-between text-xs bg-card">
                        <span className="font-medium text-muted-foreground uppercase tracking-wide text-[9px] sm:text-[10px] hidden sm:inline">
                            {item.single_product_slug ? "Tek Ürün" : "Ürün Serisi"}
                        </span>
                        <span className="flex items-center gap-1 sm:gap-1.5 font-semibold text-primary group-hover:text-primary/80 transition-colors text-[10px] sm:text-xs">
                            {item.single_product_slug ? "İncele" : "Keşfet"}
                            <ArrowRight className="h-3 w-3 sm:h-3.5 sm:w-3.5 transition-transform group-hover:translate-x-1" />
                        </span>
                    </div>
                </div>
            ))}
        </div>
    );
}
