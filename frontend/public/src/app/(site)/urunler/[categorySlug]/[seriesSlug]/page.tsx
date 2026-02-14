"use client";

import { useQuery } from "@tanstack/react-query";
import { useParams, useRouter } from "next/navigation";
import Link from "next/link";
import { fetchSeries, fetchBrands, fetchCategoriesTree } from "@/lib/api";
import { Container } from "@/components/layout";
import { BrandGrid } from "@/components/catalog/brand-grid";
import { Button } from "@/components/ui/button";
import { Tag } from "lucide-react";

export default function SeriesBrandPage() {
    const params = useParams();
    const router = useRouter();
    const categorySlug = params.categorySlug as string;
    const seriesSlug = params.seriesSlug as string;

    // Fetch Category Info (optional, for breadcrumb name if needed more than slug)
    const { data: categories = [] } = useQuery({
        queryKey: ["categories"],
        queryFn: () => fetchCategoriesTree(),
    });

    // Flatten tree to find current category
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const findCategory = (cats: any[], targetSlug: string): any => {
        for (const cat of cats) {
            if (cat.slug === targetSlug) return cat;
            if (cat.children) {
                const found = findCategory(cat.children, targetSlug);
                if (found) return found;
            }
        }
        return null;
    };

    const category = findCategory(categories, categorySlug);

    // Fetch Series Info
    const { data: seriesList = [] } = useQuery({
        queryKey: ["series", "category", categorySlug],
        queryFn: () => fetchSeries(categorySlug),
        enabled: !!categorySlug,
    });
    const series = seriesList.find((s) => s.slug === seriesSlug);

    // Fetch Brands for this Series
    const { data: brands = [], isLoading: brandsLoading } = useQuery({
        queryKey: ["brands", "series", seriesSlug],
        queryFn: () => fetchBrands(seriesSlug),
        enabled: !!seriesSlug,
    });

    const handleBrandSelect = (brandSlug: string) => {
        router.push(`/urunler/${categorySlug}/${seriesSlug}/${brandSlug}`);
    };

    return (
        <Container className="py-8 lg:py-12 overflow-x-hidden">
            {/* Breadcrumb */}
            <nav className="mb-4 text-sm text-muted-foreground">
                <Link href="/" className="hover:text-primary">Ana Sayfa</Link>
                <span className="mx-2">/</span>
                <Link href="/urunler" className="hover:text-primary">Ürünler</Link>
                <span className="mx-2">/</span>
                <Link href={`/urunler/${categorySlug}`} className="hover:text-primary">
                    {category?.name || categorySlug}
                </Link>
                <span className="mx-2">/</span>
                <span className="text-foreground font-medium">{series?.name || seriesSlug}</span>
            </nav>

            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold tracking-tight lg:text-4xl mb-4">
                    {series?.name || seriesSlug}
                </h1>
                {series?.description_short && (
                    <p className="text-lg text-muted-foreground max-w-3xl">
                        {series.description_short}
                    </p>
                )}
            </div>

            <div className="space-y-6">
                <div className="flex items-center gap-2 text-lg font-semibold text-foreground border-b pb-4">
                    <Tag className="h-5 w-5 text-primary" />
                    Marka Seçimi
                </div>

                <div className="flex justify-end">
                    <Button
                        variant="secondary"
                        onClick={() => router.push(`/urunler/${categorySlug}/${seriesSlug}/tumu`)}
                        className="gap-2"
                    >
                        Tüm Ürünleri Gör
                        <Tag className="h-4 w-4" />
                    </Button>
                </div>

                <BrandGrid
                    brands={brands}
                    isLoading={brandsLoading}
                    onSelect={handleBrandSelect}
                />

                {/* Empty State */}
                {!brandsLoading && brands.length === 0 && (
                    <div className="rounded-sm border border-dashed p-8 text-center text-muted-foreground">
                        <p className="mb-4">Bu seride marka bulunamadı.</p>
                        <Button onClick={() => router.push(`/urunler/${categorySlug}`)}>
                            Serilere Dön
                        </Button>
                    </div>
                )}
            </div>
        </Container>
    );
}
