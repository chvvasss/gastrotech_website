"use client";

import { useMemo } from "react";
import {
  Select,
  SelectContent,
  SelectGroup,
  SelectItem,
  SelectLabel,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Skeleton } from "@/components/ui/skeleton";
import type { NavCategory } from "@/types/api";

interface SeriesOption {
  value: string;
  label: string;
  categoryName: string;
  productsCount?: number;
  isVisible?: boolean;
}

interface SeriesSelectProps {
  value: string;
  onValueChange: (value: string) => void;
  categories: NavCategory[] | undefined;
  isLoading?: boolean;
  placeholder?: string;
  showAllOption?: boolean;
  allOptionLabel?: string;
  className?: string;
  showHidden?: boolean; // Include hidden (single-product) series
}

const ALL_SERIES = "_all";

export function SeriesSelect({
  value,
  onValueChange,
  categories,
  isLoading,
  placeholder = "Seri seçin...",
  showAllOption = true,
  allOptionLabel = "Tüm seriler",
  className,
  showHidden = true, // In admin, show all series by default
}: SeriesSelectProps) {
  // Group series by category
  const groupedSeries = useMemo(() => {
    if (!categories) return [];

    const groups: { categoryName: string; series: SeriesOption[] }[] = [];

    for (const category of categories) {
      if (category.series && category.series.length > 0) {
        const seriesList = showHidden
          ? category.series
          : category.series.filter(s => s.is_visible !== false);

        if (seriesList.length > 0) {
          groups.push({
            categoryName: category.name,
            series: seriesList.map((s) => ({
              value: s.slug,
              label: s.name,
              categoryName: category.name,
              productsCount: s.products_count,
              isVisible: s.is_visible,
            })),
          });
        }
      }
    }

    return groups;
  }, [categories, showHidden]);

  if (isLoading) {
    return <Skeleton className="h-10 w-[180px]" />;
  }

  return (
    <Select value={value} onValueChange={onValueChange}>
      <SelectTrigger className={className || "w-[180px] bg-white border-stone-200"}>
        <SelectValue placeholder={placeholder} />
      </SelectTrigger>
      <SelectContent>
        {showAllOption && (
          <SelectItem value={ALL_SERIES}>{allOptionLabel}</SelectItem>
        )}
        {groupedSeries.map((group) => (
          <SelectGroup key={group.categoryName}>
            <SelectLabel className="text-xs text-stone-400 uppercase tracking-wider">
              {group.categoryName}
            </SelectLabel>
            {group.series.map((series) => (
              <SelectItem key={series.value} value={series.value}>
                <span className="flex items-center gap-2">
                  {series.label}
                  {series.isVisible === false && (
                    <span className="text-xs text-amber-600 bg-amber-50 px-1.5 py-0.5 rounded">
                      gizli: {series.productsCount ?? 0} ürün
                    </span>
                  )}
                </span>
              </SelectItem>
            ))}
          </SelectGroup>
        ))}
      </SelectContent>
    </Select>
  );
}

export { ALL_SERIES };
