"use client";

import { useSearchParams, useRouter } from "next/navigation";
import { useInfiniteQuery } from "@tanstack/react-query";
import { useCallback, useMemo } from "react";
import { fetchPLP } from "@/lib/api/client";
import { PLPSearchParams } from "@/lib/api/endpoints";
import { PLPResponse } from "@/lib/api/schemas";

interface UsePLPQueryOptions {
    categorySlug: string;
    initialData?: PLPResponse;
}

interface PLPFilters {
    brands: string[];
    categories: string[]; // Added category filtering
    priceMin: number | null;
    priceMax: number | null;
    inStock: boolean;
    sort: string;
    page: number;
    series: string[];
    attrs: Record<string, string>; // key -> value (currently single select per key for simplicity)
}

export function usePLPQuery({ categorySlug, initialData }: UsePLPQueryOptions) {
    const router = useRouter();
    const searchParams = useSearchParams();

    // Parse current filter state from URL
    const filters: PLPFilters = useMemo(() => {
        const brandsParam = searchParams.get("brands");
        const categoriesParam = searchParams.get("categories");
        const priceMinParam = searchParams.get("price_min");
        const priceMaxParam = searchParams.get("price_max");
        const inStockParam = searchParams.get("in_stock");
        const sortParam = searchParams.get("sort");
        // Page param is ignored for infinite scroll initial load, we always start from 1
        const seriesParam = searchParams.get("series");
        const attrsParam = searchParams.get("attrs");

        // Parse attributes from "key:value,key2:value2"
        const attrs: Record<string, string> = {};
        if (attrsParam) {
            attrsParam.split(",").forEach(pair => {
                const [key, val] = pair.split(":");
                if (key && val) attrs[key] = val;
            });
        }

        return {
            brands: brandsParam ? brandsParam.split(",").filter(Boolean) : [],
            categories: categoriesParam ? categoriesParam.split(",").filter(Boolean) : [],
            priceMin: priceMinParam ? parseFloat(priceMinParam) : null,
            priceMax: priceMaxParam ? parseFloat(priceMaxParam) : null,
            inStock: inStockParam === "true",
            sort: sortParam || "name_asc",
            page: 1, // Always start at page 1 for infinite scroll
            series: seriesParam ? seriesParam.split(",").filter(Boolean) : [],
            attrs,
        };
    }, [searchParams]);

    // Build API params helper
    const getApiParams = useCallback((page: number): PLPSearchParams => ({
        category: categorySlug,
        brands: filters.brands.length > 0 ? filters.brands : undefined,
        categories: filters.categories.length > 0 ? filters.categories : undefined,
        price_min: filters.priceMin ?? undefined,
        price_max: filters.priceMax ?? undefined,
        in_stock: filters.inStock || undefined,
        sort: filters.sort as PLPSearchParams["sort"],
        page: page,
        page_size: 24,
        series: filters.series.length > 0 ? filters.series : undefined,
        attrs: Object.keys(filters.attrs).length > 0
            ? Object.entries(filters.attrs).map(([k, v]) => `${k}:${v}`).join(",")
            : undefined,
    }), [categorySlug, filters]);

    // Infinite Query
    const {
        data,
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,
        isLoading,
        isFetching,
        error
    } = useInfiniteQuery({
        queryKey: ["plp", "infinite", getApiParams(1)], // Use generic params as key base
        queryFn: ({ pageParam = 1 }) => fetchPLP(getApiParams(pageParam)),
        initialPageParam: 1,
        getNextPageParam: (lastPage) => {
            if (lastPage.pagination.has_next) {
                return lastPage.pagination.page + 1;
            }
            return undefined;
        },
        // We can optionally use initialData if it matches the structure, 
        // but often initialData is just the first page (PLPResponse), not InfiniteData<PLPResponse>.
        // For simplicity in this refactor, we rely on client fetching or hydration if properly set up.
        staleTime: 30 * 1000,
    });

    // Flatten products
    const products = useMemo(() => {
        return data?.pages.flatMap(page => page.products) ?? [];
    }, [data]);

    // Get metadata from first page (facets, category info etc usually don't change across pages of same query)
    const firstPage = data?.pages[0];
    const facets = firstPage?.facets ?? {
        brands: [],
        categories: [],
        price: { min: 0, max: 0 },
        series: [],
        attributes: []
    };
    const categoryInfo = firstPage?.category;
    const catalogMode = firstPage?.catalog_mode ?? false;
    const catalogs = firstPage?.catalogs ?? [];

    // Update URL with new filters
    const updateFilters = useCallback(
        (updates: Partial<PLPFilters>) => {
            const newFilters = { ...filters, ...updates };

            // Removing "page" parameter logic as we are scrolling now

            const params = new URLSearchParams();

            if (newFilters.brands.length > 0) {
                params.set("brands", newFilters.brands.join(","));
            }
            if (newFilters.categories.length > 0) {
                params.set("categories", newFilters.categories.join(","));
            }
            if (newFilters.priceMin !== null) {
                params.set("price_min", newFilters.priceMin.toString());
            }
            if (newFilters.priceMax !== null) {
                params.set("price_max", newFilters.priceMax.toString());
            }
            if (newFilters.inStock) {
                params.set("in_stock", "true");
            }
            if (newFilters.series.length > 0) {
                params.set("series", newFilters.series.join(","));
            }
            if (Object.keys(newFilters.attrs).length > 0) {
                const attrsStr = Object.entries(newFilters.attrs)
                    .map(([k, v]) => `${k}:${v}`)
                    .join(",");
                params.set("attrs", attrsStr);
            }
            if (newFilters.sort && newFilters.sort !== "name_asc") {
                params.set("sort", newFilters.sort);
            }

            // Allow preserving scroll if just creating URL (but router.push might reset scroll if not careful)
            // For filter changes, we generally WANT to reset to top.

            const queryString = params.toString();
            const newUrl = queryString
                ? `/kategori/${categorySlug}?${queryString}`
                : `/kategori/${categorySlug}`;

            router.push(newUrl, { scroll: false });
        },
        [filters, categorySlug, router]
    );

    // Individual filter handlers
    const toggleBrand = useCallback(
        (brandSlug: string) => {
            const newBrands = filters.brands.includes(brandSlug) ? [] : [brandSlug];
            updateFilters({ brands: newBrands });
        },
        [filters.brands, updateFilters]
    );

    const setPriceRange = useCallback(
        (min: number | null, max: number | null) => {
            updateFilters({ priceMin: min, priceMax: max });
        },
        [updateFilters]
    );

    const toggleInStock = useCallback(() => {
        updateFilters({ inStock: !filters.inStock });
    }, [filters.inStock, updateFilters]);

    const setSort = useCallback(
        (sortKey: string) => {
            updateFilters({ sort: sortKey });
        },
        [updateFilters]
    );

    const clearAllFilters = useCallback(() => {
        updateFilters({
            brands: [],
            categories: [],
            priceMin: null,
            priceMax: null,
            inStock: false,
            sort: "name_asc",
            series: [],
            attrs: {},
        });
    }, [updateFilters]);

    const clearBrands = useCallback(() => {
        updateFilters({ brands: [] });
    }, [updateFilters]);

    const toggleSeries = useCallback(
        (seriesSlug: string) => {
            const newSeries = filters.series.includes(seriesSlug) ? [] : [seriesSlug];
            updateFilters({ series: newSeries });
        },
        [filters.series, updateFilters]
    );

    const toggleCategory = useCallback(
        (categorySlug: string) => {
            const newCategories = filters.categories.includes(categorySlug) ? [] : [categorySlug];
            updateFilters({ categories: newCategories });
        },
        [filters.categories, updateFilters]
    );

    const toggleAttribute = useCallback(
        (key: string, value: string) => {
            const currentVal = filters.attrs[key];
            const newAttrs = { ...filters.attrs };

            if (currentVal === value) {
                delete newAttrs[key];
            } else {
                newAttrs[key] = value;
            }
            updateFilters({ attrs: newAttrs });
        },
        [filters.attrs, updateFilters]
    );

    return {
        // Data
        products,
        facets,
        categoryInfo,
        catalogMode,
        catalogs,
        pagination: firstPage?.pagination, // Only for total count info if needed
        sortOptions: firstPage?.sort_options || [],

        // Infinite Scroll
        fetchNextPage,
        hasNextPage,
        isFetchingNextPage,

        // State
        filters,
        isLoading: isLoading, // Initial loading
        isFetching, // Background updating
        error,

        // Actions
        toggleBrand,
        toggleCategory,
        setPriceRange,
        toggleInStock,
        setSort,
        // setPage removed/not exposed
        clearAllFilters,
        clearBrands,
        toggleSeries,
        toggleAttribute,
    };
}
