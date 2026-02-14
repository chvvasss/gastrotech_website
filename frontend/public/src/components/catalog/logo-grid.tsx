"use client";

import Image from "next/image";
import { motion } from "framer-motion";
import { ChevronRight, Package } from "lucide-react";
import { LogoGroup, LogoGroupSeries } from "@/lib/api/schemas";
import { getMediaUrl, cn } from "@/lib/utils";
import { useState, useEffect } from "react";

interface LogoGridProps {
    logoGroups: LogoGroup[];
    onSeriesSelect: (seriesSlug: string) => void;
    categorySlug: string;
    selectedBrandSlug?: string | null;
}

export function LogoGrid({ logoGroups, onSeriesSelect, selectedBrandSlug }: LogoGridProps) {
    const [selectedGroupId, setSelectedGroupId] = useState<string | null>(null);
    const [selectedHeadingIndex, setSelectedHeadingIndex] = useState<number | null>(null);

    // Sync selectedBrandSlug prop to internal state
    useEffect(() => {
        if (selectedBrandSlug) {
            const group = logoGroups.find(lg => lg.brand_slug === selectedBrandSlug);
            if (group) {
                setSelectedGroupId(group.id);
            }
        } else {
            setSelectedGroupId(null);
        }
    }, [selectedBrandSlug, logoGroups]);

    // Reset heading selection when group changes
    useEffect(() => {
        setSelectedHeadingIndex(null);
    }, [selectedGroupId]);

    const selectedGroup = logoGroups.find(lg => lg.id === selectedGroupId);

    // Helper: Group series by headings
    const getGroupedSeries = (seriesList: LogoGroupSeries[]) => {
        const groups: { heading: LogoGroupSeries | null, items: LogoGroupSeries[] }[] = [];
        let currentGroup: { heading: LogoGroupSeries | null, items: LogoGroupSeries[] } | null = null;

        seriesList.forEach(item => {
            if (item.is_heading) {
                if (currentGroup) {
                    groups.push(currentGroup);
                }
                currentGroup = { heading: item, items: [] };
            } else {
                if (!currentGroup) {
                    // Items before any heading go into a "misc" group
                    currentGroup = { heading: null, items: [] };
                }
                currentGroup.items.push(item);
            }
        });

        if (currentGroup) {
            groups.push(currentGroup);
        }

        return groups;
    };

    // If no logo selected, show the logo grid
    if (!selectedGroupId) {
        return (
            <div className="space-y-6">
                <div className="flex items-center gap-2 text-lg font-semibold text-foreground border-b pb-4">
                    <Package className="h-5 w-5 text-primary" />
                    Marka Seçimi
                </div>

                <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
                    {logoGroups.map((group, index) => (
                        <motion.button
                            key={group.id}
                            initial={{ opacity: 0, y: 10 }}
                            animate={{ opacity: 1, y: 0 }}
                            transition={{ duration: 0.3, delay: index * 0.05 }}
                            onClick={() => setSelectedGroupId(group.id)}
                            className={cn(
                                "group flex flex-col items-center justify-center p-6 rounded-sm",
                                "bg-white border border-border/50 hover:border-primary/50",
                                "hover:shadow-lg transition-all duration-300",
                                "min-h-[160px]"
                            )}
                        >
                            {/* Logo Image */}
                            <div className="relative w-full h-20 mb-4">
                                {group.logo_url ? (
                                    <Image
                                        src={getMediaUrl(group.logo_url)}
                                        alt={group.brand_name}
                                        fill
                                        className="object-contain p-2 transition-transform duration-300 group-hover:scale-110"
                                        sizes="(max-width: 640px) 50vw, 25vw"
                                    />
                                ) : (
                                    <div className="flex h-full w-full items-center justify-center bg-primary/5 rounded-sm">
                                        <span className="text-2xl font-black text-primary/30">
                                            {group.brand_name.charAt(0)}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Brand Name */}
                            <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors">
                                {group.brand_name}
                            </h3>

                            {/* Series Count */}
                            <p className="text-xs text-muted-foreground mt-1">
                                {group.series_list.length} ürün grubu
                            </p>
                        </motion.button>
                    ))}
                </div>
            </div>
        );
    }

    const groupedSeries = selectedGroup ? getGroupedSeries(selectedGroup.series_list) : [];
    // Check if we effectively have headings (more than 1 group, or 1 group that IS a heading)
    const hasHeadings = groupedSeries.some(g => g.heading !== null);

    // Scenario 1: Showing drill-down for a specific sub-heading logic
    if (selectedHeadingIndex !== null && hasHeadings) {
        const activeGroup = groupedSeries[selectedHeadingIndex];

        return (
            <div className="space-y-6">
                {/* Back Button + Breadcrumbs */}
                <div className="flex flex-col gap-2 border-b pb-4">
                    <div className="flex items-center gap-2 text-sm text-muted-foreground">
                        <button onClick={() => setSelectedGroupId(null)} className="hover:text-primary transition-colors">
                            Markalar
                        </button>
                        <ChevronRight className="h-3 w-3" />
                        <button onClick={() => setSelectedHeadingIndex(null)} className="hover:text-primary transition-colors">
                            {selectedGroup?.brand_name}
                        </button>
                        <ChevronRight className="h-3 w-3" />
                        <span className="font-semibold text-foreground">
                            {activeGroup.heading?.series_name}
                        </span>
                    </div>
                </div>

                {/* Series List Implementation */}
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                    {activeGroup.items.map((series, index) => (
                        <SeriesCard
                            key={series.series_id}
                            series={series}
                            index={index}
                            onSelect={() => onSeriesSelect(series.series_slug)}
                        />
                    ))}
                </div>
            </div>
        )
    }

    // Scenario 2: Brand Selected -> Show Headings (if available) OR Flat List (if no headings)
    return (
        <div className="space-y-6">
            {/* Back Button + Brand Header */}
            <div className="flex items-center gap-4 border-b pb-4">
                <button
                    onClick={() => setSelectedGroupId(null)}
                    className="flex items-center gap-1 text-sm text-muted-foreground hover:text-primary transition-colors"
                >
                    <ChevronRight className="h-4 w-4 rotate-180" />
                    Markalara Dön
                </button>

                <div className="flex items-center gap-3">
                    {selectedGroup?.logo_url && (
                        <div className="relative w-12 h-8">
                            <Image
                                src={getMediaUrl(selectedGroup.logo_url)}
                                alt={selectedGroup.brand_name}
                                fill
                                className="object-contain"
                            />
                        </div>
                    )}
                    <h2 className="text-lg font-semibold text-foreground">
                        {selectedGroup?.brand_name}
                    </h2>
                </div>
            </div>

            {/* Content Area */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {hasHeadings ? (
                    // Render List of Headings as Cards
                    groupedSeries.map((group, index) => {
                        if (!group.heading) return null;
                        return (
                            <motion.button
                                key={group.heading.series_id}
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                transition={{ duration: 0.2, delay: index * 0.05 }}
                                onClick={() => setSelectedHeadingIndex(index)}
                                className="group relative aspect-[4/3] w-full overflow-hidden rounded-sm border border-border bg-card transition-all duration-300 hover:border-primary/50 hover:shadow-md"
                            >
                                {/* Image Area */}
                                <div className="absolute inset-0 bg-muted">
                                    {group.heading.cover_media_url ? (
                                        <Image
                                            src={getMediaUrl(group.heading.cover_media_url)}
                                            alt={group.heading.series_name}
                                            fill
                                            className="object-cover transition-transform duration-500 group-hover:scale-105"
                                        />
                                    ) : (
                                        <div className="flex h-full w-full items-center justify-center bg-primary/5">
                                            <Package className="h-10 w-10 text-primary/20" />
                                        </div>
                                    )}

                                    {/* Gradient Overlay */}
                                    <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
                                </div>

                                {/* Title Overlay */}
                                <div className="absolute bottom-0 left-0 right-0 p-4 text-left">
                                    <h3 className="text-lg font-bold leading-tight text-white drop-shadow-sm">
                                        {group.heading.series_name}
                                    </h3>
                                    <span className="mt-2 inline-flex items-center text-xs font-medium text-white/80 group-hover:text-white transition-colors">
                                        Grubu İncele <ChevronRight className="ml-1 h-3 w-3" />
                                    </span>
                                </div>
                            </motion.button>
                        )
                    })
                ) : (
                    // Flat List Fallback as Cards
                    selectedGroup?.series_list.map((series, index) => (
                        <SeriesCard
                            key={series.series_id}
                            series={series}
                            index={index}
                            onSelect={() => onSeriesSelect(series.series_slug)}
                        />
                    ))
                )}
            </div>
        </div>
    );
}

// Reusable Card Component for Leaf Series
function SeriesCard({ series, index, onSelect }: { series: LogoGroupSeries, index: number, onSelect: () => void }) {
    if (series.is_heading) return <></>;

    return (
        <motion.button
            initial={{ opacity: 0, y: 10 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.2, delay: index * 0.05 }}
            onClick={onSelect}
            className="group relative aspect-[4/3] w-full overflow-hidden rounded-sm border border-border bg-card transition-all duration-300 hover:border-primary/50 hover:shadow-md"
        >
            <div className="absolute inset-0 bg-muted">
                {series.cover_media_url ? (
                    <Image
                        src={getMediaUrl(series.cover_media_url)}
                        alt={series.series_name}
                        fill
                        className="object-cover transition-transform duration-500 group-hover:scale-105"
                    />
                ) : (
                    <div className="flex h-full w-full items-center justify-center bg-secondary/10">
                        <Package className="h-10 w-10 text-muted-foreground/30" />
                    </div>
                )}
                <div className="absolute inset-x-0 bottom-0 h-2/3 bg-gradient-to-t from-black/80 via-black/40 to-transparent" />
            </div>

            <div className="absolute bottom-0 left-0 right-0 p-4 text-left">
                <h3 className="text-lg font-bold leading-tight text-white drop-shadow-sm">
                    {series.series_name}
                </h3>
                <span className="mt-2 inline-flex items-center text-xs font-medium text-white/80 group-hover:text-white transition-colors">
                    Seriyi İncele <ChevronRight className="ml-1 h-3 w-3" />
                </span>
            </div>
        </motion.button>
    );
}
