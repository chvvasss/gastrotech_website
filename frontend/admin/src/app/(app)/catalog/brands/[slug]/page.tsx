"use client";

import { use } from "react";
import { useRouter } from "next/navigation";
import { useState, useEffect } from "react";
import {
  ArrowLeft,
  Save,
  Loader2,
  Tag,
  Plus,
  X,
  Check,
  ChevronUp,
  ChevronDown,
} from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { useToast } from "@/hooks/use-toast";
import { catalogApi } from "@/lib/api/catalog";
import { getMediaUrl } from "@/lib/media-url";
import type { BrandDetail, BrandCategory, Category } from "@/types/api";

export default function BrandDetailPage({
  params,
}: {
  params: Promise<{ slug: string }>;
}) {
  const { slug } = use(params);
  const router = useRouter();
  const { toast } = useToast();

  const [brand, setBrand] = useState<BrandDetail | null>(null);
  const [categories, setCategories] = useState<Category[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  // Brand categories state
  const [brandCategories, setBrandCategories] = useState<BrandCategory[]>([]);
  const [newCategoryId, setNewCategoryId] = useState<string>("");

  useEffect(() => {
    loadData();
  }, [slug]);

  const loadData = async () => {
    try {
      setIsLoading(true);
      const [brandData, categoriesData] = await Promise.all([
        catalogApi.getBrand(slug),
        catalogApi.listCategories(),
      ]);

      setBrand(brandData);
      setCategories(categoriesData);
      setBrandCategories(brandData.categories_list || []);
    } catch (error) {
      console.error("Load error:", error);
      toast({
        title: "Hata",
        description: "Marka bilgileri yüklenemedi",
        variant: "destructive",
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleAddCategory = () => {
    if (!newCategoryId) return;

    const category = categories.find((c) => c.id === newCategoryId);
    if (!category) return;

    // Check if already exists
    if (brandCategories.some((bc) => bc.category === newCategoryId)) {
      toast({
        title: "Uyarı",
        description: "Bu kategori zaten ekli",
        variant: "destructive",
      });
      return;
    }

    // Add new brand-category
    setBrandCategories([
      ...brandCategories,
      {
        category: newCategoryId,
        category_name: category.name,
        category_slug: category.slug,
        is_active: true,
        order: brandCategories.length,
      },
    ]);
    setNewCategoryId("");
  };

  const handleRemoveCategory = (categoryId: string) => {
    setBrandCategories(brandCategories.filter((bc) => bc.category !== categoryId));
  };

  const handleToggleActive = (categoryId: string) => {
    setBrandCategories(
      brandCategories.map((bc) =>
        bc.category === categoryId ? { ...bc, is_active: !bc.is_active } : bc
      )
    );
  };

  const handleMoveUp = (index: number) => {
    if (index === 0) return;
    const newList = [...brandCategories];
    [newList[index - 1], newList[index]] = [newList[index], newList[index - 1]];
    // Update order field
    newList.forEach((bc, idx) => {
      bc.order = idx;
    });
    setBrandCategories(newList);
  };

  const handleMoveDown = (index: number) => {
    if (index === brandCategories.length - 1) return;
    const newList = [...brandCategories];
    [newList[index], newList[index + 1]] = [newList[index + 1], newList[index]];
    // Update order field
    newList.forEach((bc, idx) => {
      bc.order = idx;
    });
    setBrandCategories(newList);
  };

  const handleSave = async () => {
    try {
      setIsSaving(true);

      // Prepare data for API
      const categoriesToSave = brandCategories.map((bc) => ({
        category: bc.category,
        is_active: bc.is_active,
        order: bc.order,
      }));

      // Call API
      const updatedBrand = await catalogApi.updateBrandCategories(slug, categoriesToSave);

      // Update local state with response
      setBrand(updatedBrand);
      setBrandCategories(updatedBrand.categories_list || []);

      toast({
        title: "Başarılı",
        description: "Kategoriler başarıyla güncellendi",
      });
    } catch (error: any) {
      console.error("Failed to save categories:", error);
      toast({
        title: "Hata",
        description: error.response?.data?.error || "Kategoriler kaydedilirken bir hata oluştu",
        variant: "destructive",
      });
    } finally {
      setIsSaving(false);
    }
  };

  if (isLoading) {
    return (
      <AppShell
        breadcrumbs={[
          { label: "Katalog", href: "/catalog/products" },
          { label: "Markalar", href: "/catalog/brands" },
          { label: "Yükleniyor..." },
        ]}
      >
        <div className="space-y-4">
          <Skeleton className="h-32 w-full" />
          <Skeleton className="h-96 w-full" />
        </div>
      </AppShell>
    );
  }

  if (!brand) {
    return (
      <AppShell
        breadcrumbs={[
          { label: "Katalog", href: "/catalog/products" },
          { label: "Markalar", href: "/catalog/brands" },
          { label: "Bulunamadı" },
        ]}
      >
        <Card>
          <CardContent className="py-12 text-center">
            <Tag className="h-12 w-12 mx-auto mb-4 opacity-20" />
            <p className="text-stone-500">Marka bulunamadı</p>
            <Button
              variant="outline"
              className="mt-4"
              onClick={() => router.push("/catalog/brands")}
            >
              <ArrowLeft className="h-4 w-4 mr-2" />
              Markalara Dön
            </Button>
          </CardContent>
        </Card>
      </AppShell>
    );
  }

  return (
    <AppShell
      breadcrumbs={[
        { label: "Katalog", href: "/catalog/products" },
        { label: "Markalar", href: "/catalog/brands" },
        { label: brand.name },
      ]}
    >
      <PageHeader
        title={brand.name}
        description={`${brand.product_count || 0} ürün · ${brand.category_count || 0} kategori`}
        actions={
          <div className="flex gap-2">
            <Button variant="outline" onClick={() => router.push("/catalog/brands")}>
              <ArrowLeft className="h-4 w-4 mr-2" />
              Geri
            </Button>
            <Button onClick={handleSave} disabled={isSaving}>
              {isSaving && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              <Save className="h-4 w-4 mr-2" />
              Kaydet
            </Button>
          </div>
        }
      />

      <div className="grid gap-6">
        {/* Brand Info */}
        <Card>
          <CardHeader>
            <CardTitle>Marka Bilgileri</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <Label className="text-stone-600 text-sm">Ad</Label>
                  <p className="font-medium">{brand.name}</p>
                </div>
                <div>
                  <Label className="text-stone-600 text-sm">Slug</Label>
                  <p className="font-mono text-sm text-stone-500">{brand.slug}</p>
                </div>
              </div>

              {brand.description && (
                <div>
                  <Label className="text-stone-600 text-sm">Açıklama</Label>
                  <p className="text-sm text-stone-700">{brand.description}</p>
                </div>
              )}

              <div className="grid grid-cols-3 gap-4">
                <div>
                  <Label className="text-stone-600 text-sm">Durum</Label>
                  <div className="mt-1">
                    {brand.is_active ? (
                      <Badge className="bg-green-100 text-green-700">
                        <Check className="h-3 w-3 mr-1" />
                        Aktif
                      </Badge>
                    ) : (
                      <Badge variant="secondary">
                        <X className="h-3 w-3 mr-1" />
                        Pasif
                      </Badge>
                    )}
                  </div>
                </div>
                <div>
                  <Label className="text-stone-600 text-sm">Sıra</Label>
                  <p className="font-medium">#{brand.order}</p>
                </div>
                <div>
                  <Label className="text-stone-600 text-sm">Ürün Sayısı</Label>
                  <p className="font-medium">{brand.product_count || 0}</p>
                </div>
              </div>

              {brand.logo_url && (
                <div>
                  <Label className="text-stone-600 text-sm">Logo</Label>
                  <div className="mt-2">
                    <img
                      src={getMediaUrl(brand.logo_url)}
                      alt={brand.name}
                      className="h-20 w-auto object-contain border rounded p-2"
                    />
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Brand Categories */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center justify-between">
              <span>Kategoriler</span>
              <Badge variant="secondary">{brandCategories.length} kategori</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {/* Add Category */}
              <div className="flex gap-2">
                <Select value={newCategoryId} onValueChange={setNewCategoryId}>
                  <SelectTrigger className="flex-1">
                    <SelectValue placeholder="Kategori seçin..." />
                  </SelectTrigger>
                  <SelectContent>
                    {categories
                      .filter(
                        (cat) => !brandCategories.some((bc) => bc.category === cat.id)
                      )
                      .map((cat) => (
                        <SelectItem key={cat.id} value={cat.id}>
                          {cat.name}
                        </SelectItem>
                      ))}
                  </SelectContent>
                </Select>
                <Button onClick={handleAddCategory} disabled={!newCategoryId}>
                  <Plus className="h-4 w-4 mr-2" />
                  Ekle
                </Button>
              </div>

              {/* Categories Table */}
              {brandCategories.length === 0 ? (
                <div className="text-center py-8 text-stone-500 border rounded-lg bg-stone-50">
                  <Tag className="h-8 w-8 mx-auto mb-2 opacity-20" />
                  <p className="text-sm">Henüz kategori eklenmemiş</p>
                </div>
              ) : (
                <Table>
                  <TableHeader>
                    <TableRow>
                      <TableHead>Kategori</TableHead>
                      <TableHead>Slug</TableHead>
                      <TableHead className="text-center">Durum</TableHead>
                      <TableHead className="text-center">Sıra</TableHead>
                      <TableHead className="text-right">İşlemler</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {brandCategories.map((bc, index) => (
                      <TableRow key={bc.category}>
                        <TableCell className="font-medium">
                          {bc.category_name}
                        </TableCell>
                        <TableCell className="text-stone-500 font-mono text-sm">
                          {bc.category_slug}
                        </TableCell>
                        <TableCell className="text-center">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleToggleActive(bc.category)}
                          >
                            {bc.is_active ? (
                              <Badge className="bg-green-100 text-green-700">
                                <Check className="h-3 w-3 mr-1" />
                                Aktif
                              </Badge>
                            ) : (
                              <Badge variant="secondary">
                                <X className="h-3 w-3 mr-1" />
                                Pasif
                              </Badge>
                            )}
                          </Button>
                        </TableCell>
                        <TableCell className="text-center">
                          <div className="flex items-center justify-center gap-1">
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => handleMoveUp(index)}
                              disabled={index === 0}
                            >
                              <ChevronUp className="h-4 w-4" />
                            </Button>
                            <span className="text-sm text-stone-400 w-8 text-center">
                              #{bc.order}
                            </span>
                            <Button
                              variant="ghost"
                              size="icon"
                              className="h-6 w-6"
                              onClick={() => handleMoveDown(index)}
                              disabled={index === brandCategories.length - 1}
                            >
                              <ChevronDown className="h-4 w-4" />
                            </Button>
                          </div>
                        </TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleRemoveCategory(bc.category)}
                            className="text-red-600 hover:text-red-700 hover:bg-red-50"
                          >
                            <X className="h-4 w-4 mr-1" />
                            Kaldır
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              )}
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
