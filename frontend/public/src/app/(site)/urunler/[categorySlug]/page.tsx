"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchCategoryDetail, fetchSeries } from "@/lib/api";
import { Container } from "@/components/layout";
import { SeriesGrid } from "@/components/catalog/series-grid";
import { LogoGrid } from "@/components/catalog/logo-grid";
import { BentoCategoryGrid } from "@/components/catalog/bento-category-grid";
import { Button } from "@/components/ui/button";
import { Layers, FolderOpen } from "lucide-react";

export default function CategorySeriesPage() {
    const params = useParams();
    const router = useRouter();
    const categorySlug = params.categorySlug as string;

    // Fetch Category Detail (with logo_groups and subcategories)
    const { data: category, isLoading: categoryLoading } = useQuery({
        queryKey: ["category-detail", categorySlug],
        queryFn: () => fetchCategoryDetail(categorySlug),
        enabled: !!categorySlug,
    });

    // Fetch Series for this Category (as fallback)
    const { data: allSeries = [], isLoading: seriesLoading } = useQuery({
        queryKey: ["series", "category", categorySlug],
        queryFn: () => fetchSeries(categorySlug),
        enabled: !!categorySlug,
    });


    // Determine display mode based on category data
    const hasLogoGroups = category?.logo_groups && category.logo_groups.length > 0;
    const hasSubcategories = category?.subcategories && category.subcategories.length > 0;

    // Filter to only show visible series (2+ products)
    const series = allSeries.filter(s => s.is_visible !== false && (s.products_count ?? 0) >= 2);
    const hasDirectSeries = series.length > 0;

    const handleSeriesSelect = (seriesSlug: string) => {
        router.push(`/urunler/${categorySlug}/${seriesSlug}`);
    };

    const isLoading = categoryLoading || seriesLoading;

    return (
        <Container className="py-8 lg:py-12 overflow-x-hidden">
            {/* Header */}
            <div className="mb-8">
                <nav className="mb-4 text-sm text-muted-foreground">
                    <Link href="/" className="hover:text-primary">Ana Sayfa</Link>
                    <span className="mx-2">/</span>
                    <Link href="/urunler" className="hover:text-primary">Ürünler</Link>
                    <span className="mx-2">/</span>
                    {category?.parent_slug && (
                        <>
                            <Link href={`/urunler/${category.parent_slug}`} className="hover:text-primary">
                                {/* Would need parent name - for now just show slug */}
                                {category.parent_slug.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ')}
                            </Link>
                            <span className="mx-2">/</span>
                        </>
                    )}
                    <span className="text-foreground font-medium">{category?.name || categorySlug}</span>
                </nav>

                <h1 className="text-3xl font-bold tracking-tight lg:text-4xl mb-4">
                    {category?.name || categorySlug}
                </h1>
                {category?.description_short && (
                    <p className="text-lg text-muted-foreground max-w-3xl">
                        {category.description_short}
                    </p>
                )}
            </div>

            <div className="space-y-6">
                {/* Display Mode 1: Show Subcategories if available */}
                {hasSubcategories && (
                    <>
                        <div className="flex items-center gap-2 text-lg font-semibold text-foreground border-b pb-4">
                            <FolderOpen className="h-5 w-5 text-primary" />
                            Alt Kategoriler
                        </div>

                        <BentoCategoryGrid
                            categories={category.subcategories!.map(sub => ({
                                id: sub.id,
                                name: sub.name,
                                slug: sub.slug,
                                menu_label: sub.menu_label || null,
                                order: sub.order,
                                is_featured: sub.is_featured || false,
                                cover_media_url: sub.cover_media_url,
                                series: [],
                            }))}
                            variant="grid"
                        />
                    </>
                )}

                {/* Display Mode 2: Show Logo Grid if available (for subcategories with brands) */}
                {hasLogoGroups && (
                    <LogoGrid
                        logoGroups={category.logo_groups!}
                        onSeriesSelect={handleSeriesSelect}
                        categorySlug={categorySlug}
                    />
                )}

                {/* Display Mode 3: Show Direct Series (Orphans) */}
                {hasDirectSeries && (
                    <>
                        {/* Only show separator header if we also showed subcategories/logos above */}
                        {(hasSubcategories || hasLogoGroups) && (
                            <div className="flex items-center gap-2 text-lg font-semibold text-foreground border-b pb-4 pt-8">
                                <Layers className="h-5 w-5 text-primary" />
                                {category?.name ? `${category.name} Modelleri` : "Diğer Ürünler"}
                            </div>
                        )}

                        {/* If this is the ONLY mode, maybe show a header too? Or keep it simple. */}
                        {(!hasSubcategories && !hasLogoGroups) && (
                            <div className="flex items-center gap-2 text-lg font-semibold text-foreground border-b pb-4">
                                <Layers className="h-5 w-5 text-primary" />
                                Seri Seçimi
                            </div>
                        )}

                        <SeriesGrid
                            series={series}
                            isLoading={isLoading}
                            onSelect={handleSeriesSelect}
                        />
                    </>
                )}

                {/* Empty State */}
                {!isLoading && !hasSubcategories && !hasLogoGroups && !hasDirectSeries && (
                    <div className="rounded-sm border border-dashed p-8 text-center text-muted-foreground">
                        <p className="mb-4">Bu kategoride içerik bulunamadı.</p>
                        <Button onClick={() => router.push('/urunler')}>
                            Kategorilere Dön
                        </Button>
                    </div>
                )}
            </div>
        </Container>
    );
}
