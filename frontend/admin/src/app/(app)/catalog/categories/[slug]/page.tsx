"use client";

import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Package, Layers } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { ProductsTable } from "@/components/catalog/products-table";
import { useCategoryDetail } from "@/hooks/use-catalog-categories";

export default function CategoryDetailPage() {
    const { slug } = useParams<{ slug: string }>();
    const { data: category, isLoading } = useCategoryDetail(slug);

    const breadcrumbs = [
        { label: "Katalog", href: "/catalog/categories/list" },
        { label: "Kategoriler", href: "/catalog/categories/list" },
        { label: isLoading ? "Yükleniyor..." : (category?.name || slug) },
    ];

    const categoryName = isLoading ? "Yükleniyor..." : (category?.name || slug);
    const seriesCount = category?.series?.length ?? 0;
    const productsCount = category?.products_count ?? 0;

    return (
        <AppShell breadcrumbs={breadcrumbs}>
            <PageHeader
                title={categoryName}

                description={
                    isLoading
                        ? "Yükleniyor..."
                        : category?.description_short || `${category?.name || slug} kategorisindeki ürünler`
                }
                actions={
                    <div className="flex items-center gap-3">
                        {!isLoading && category && (
                            <div className="flex gap-2">
                                <Badge variant="outline" className="text-xs font-normal">
                                    <Layers className="h-3 w-3 mr-1" />
                                    {seriesCount} Seri
                                </Badge>
                                <Badge variant="outline" className="text-xs font-normal">
                                    <Package className="h-3 w-3 mr-1" />
                                    {productsCount} Ürün
                                </Badge>
                            </div>
                        )}
                        <Button variant="outline" asChild>
                            <Link href="/catalog/categories/list">
                                <ArrowLeft className="h-4 w-4 mr-2" />
                                Kategorilere Dön
                            </Link>
                        </Button>
                    </div>
                }
            />

            <div className="bg-white p-6 rounded-lg border border-stone-200">
                {isLoading ? (
                    <div className="space-y-4">
                        <Skeleton className="h-12 w-full" />
                        <Skeleton className="h-12 w-full" />
                        <Skeleton className="h-12 w-full" />
                    </div>
                ) : (
                    <ProductsTable scope="category" scopeId={slug} />
                )}
            </div>
        </AppShell>
    );
}
