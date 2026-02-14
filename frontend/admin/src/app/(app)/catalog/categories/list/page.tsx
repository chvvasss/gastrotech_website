"use client";

import { useState } from "react";
import Link from "next/link";
import { Search, Package, Layers, Loader2 } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { useCategoriesWithCounts } from "@/hooks/use-catalog-categories";

export default function CategoriesListPage() {
  const [search, setSearch] = useState("");
  const { data: categories, isLoading, error } = useCategoriesWithCounts({ search });

  return (
    <AppShell
      breadcrumbs={[
        { label: "Katalog", href: "/catalog/categories/list" },
        { label: "Kategoriler" },
      ]}
    >
      <PageHeader
        title="Kategoriler"
        description="Kategori seçerek ürünlere ulaşın"
      />

      <div className="mb-6">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" />
          <Input
            placeholder="Kategori ara..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="pl-10"
          />
        </div>
      </div>

      {isLoading ? (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <Skeleton key={i} className="h-48" />
          ))}
        </div>
      ) : error ? (
        <Card className="border-red-200 bg-red-50">
          <CardContent className="p-6 text-center">
            <p className="text-red-600">Kategoriler yüklenirken hata oluştu</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => window.location.reload()}
            >
              Yeniden Dene
            </Button>
          </CardContent>
        </Card>
      ) : !categories || categories.length === 0 ? (
        <div className="text-center py-12 text-stone-500">
          <Package className="h-16 w-16 mx-auto mb-4 opacity-20" />
          <p className="text-lg font-medium mb-2">Kategori bulunamadı</p>
          <p className="text-sm">
            {search ? "Arama kriterlerinize uygun kategori yok" : "Henüz kategori eklenmemiş"}
          </p>
        </div>
      ) : (
        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {categories.map((category) => (
            <Card key={category.id} className="hover:shadow-lg transition-all hover:border-stone-300">
              <CardContent className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <div className="flex-1">
                    <h3 className="font-semibold text-lg mb-2 text-stone-900">
                      {category.name}
                    </h3>
                    {category.description_short && (
                      <p className="text-sm text-stone-500 line-clamp-2">
                        {category.description_short}
                      </p>
                    )}
                  </div>
                  {category.cover_media_url && (
                    <div className="ml-3 flex-shrink-0">
                      <img
                        src={category.cover_media_url}
                        alt={category.name}
                        className="w-16 h-16 object-cover rounded border border-stone-200"
                      />
                    </div>
                  )}
                </div>

                <div className="flex gap-2 mb-4">
                  <Badge variant="outline" className="text-xs">
                    <Layers className="h-3 w-3 mr-1" />
                    {category.series_count} Seri
                  </Badge>
                  <Badge variant="outline" className="text-xs">
                    <Package className="h-3 w-3 mr-1" />
                    {category.products_count} Ürün
                  </Badge>
                </div>

                <Link href={`/catalog/categories/${category.slug}`}>
                  <Button className="w-full">
                    Kategoriyi Aç
                  </Button>
                </Link>
              </CardContent>
            </Card>
          ))}
        </div>
      )}
    </AppShell>
  );
}
