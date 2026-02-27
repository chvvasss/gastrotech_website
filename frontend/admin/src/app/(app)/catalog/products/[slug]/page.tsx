"use client";

import { useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { Star, ExternalLink } from "lucide-react";
import { AppShell } from "@/components/layout";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useProductDetail } from "@/hooks/use-catalog-products";
import { BadgeStatus } from "@/components/catalog";
import { OverviewTab } from "./_components/overview-tab";
import { VariantsTab } from "./_components/variants-tab";
import { MediaTab } from "./_components/media-tab";
import { SpecsLayoutTab } from "./_components/specs-layout-tab";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [activeTab, setActiveTab] = useState("overview");

  const { data: product, isLoading, error } = useProductDetail(slug);

  const backendUrl = process.env.NEXT_PUBLIC_BACKEND_URL ?? "";

  if (isLoading) {
    return (
      <AppShell
        breadcrumbs={[
          { label: "Katalog", href: "/catalog/categories/list" },
          { label: "Kategoriler", href: "/catalog/categories/list" },
          { label: "Yükleniyor..." },
        ]}
      >
        <div className="space-y-6">
          <Skeleton className="h-10 w-[300px]" />
          <Skeleton className="h-6 w-[200px]" />
          <Skeleton className="h-[400px] w-full" />
        </div>
      </AppShell>
    );
  }

  if (error || !product) {
    return (
      <AppShell
        breadcrumbs={[
          { label: "Katalog", href: "/catalog/categories/list" },
          { label: "Kategoriler", href: "/catalog/categories/list" },
          { label: "Hata" },
        ]}
      >
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <h2 className="text-xl font-semibold text-stone-900 mb-2">
            Ürün bulunamadı
          </h2>
          <p className="text-stone-500">
            {slug} slug&apos;ına sahip ürün bulunamadı veya bir hata oluştu.
          </p>
          <Button asChild className="mt-4">
            <Link href="/catalog/products">Ürün Listesine Dön</Link>
          </Button>
        </div>
      </AppShell>
    );
  }

  return (
    <AppShell
      breadcrumbs={[
        { label: "Katalog", href: "/catalog/categories/list" },
        { label: "Kategoriler", href: "/catalog/categories/list" },
        { label: product.category_name, href: `/catalog/categories/${product.category_slug}` },
        { label: "Ürünler", href: `/catalog/products?category=${product.category_slug}` },
        { label: product.title_tr },
      ]}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div>
          <div className="flex items-center gap-3 mb-2">
            <h1 className="text-2xl font-bold text-stone-900">
              {product.title_tr}
            </h1>
            <BadgeStatus status={product.status} />
            {product.is_featured && (
              <Star className="h-5 w-5 text-amber-500 fill-amber-500" />
            )}
          </div>
          <p className="text-stone-500">
            {product.category_name} &gt; {product.series_name}
            {product.primary_node_slug && ` > ${product.primary_node_slug}`}
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" asChild>
            <a
              href={`${backendUrl}/admin/catalog/product/${product.slug}/change/`}
              target="_blank"
              rel="noopener noreferrer"
            >
              <ExternalLink className="h-4 w-4 mr-2" />
              Django Admin
            </a>
          </Button>
        </div>
      </div>

      {/* Tabs */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="bg-stone-100 p-1">
          <TabsTrigger value="overview" className="data-[state=active]:bg-white">
            Genel Bakış
          </TabsTrigger>
          <TabsTrigger value="variants" className="data-[state=active]:bg-white">
            Varyantlar ({product.variants?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="media" className="data-[state=active]:bg-white">
            Medya ({product.product_media?.length || 0})
          </TabsTrigger>
          <TabsTrigger value="specs" className="data-[state=active]:bg-white">
            Spec Layout
          </TabsTrigger>
        </TabsList>

        <div className="mt-6">
          <TabsContent value="overview" className="mt-0">
            <OverviewTab product={product} />
          </TabsContent>

          <TabsContent value="variants" className="mt-0">
            <VariantsTab product={product} />
          </TabsContent>

          <TabsContent value="media" className="mt-0">
            <MediaTab product={product} />
          </TabsContent>

          <TabsContent value="specs" className="mt-0">
            <SpecsLayoutTab product={product} />
          </TabsContent>
        </div>
      </Tabs>
    </AppShell>
  );
}
