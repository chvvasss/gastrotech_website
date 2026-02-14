"use client";

import { useEffect, useCallback } from "react";
import { useForm, Controller } from "react-hook-form";
import { Save, X, AlertCircle } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { MissingEndpointBanner } from "@/components/catalog";
import { ListEditor } from "@/components/ui/list-editor";
import { useAdminCapabilities } from "@/hooks/use-admin-capabilities";
import { usePatchProduct } from "@/hooks/use-admin-products";
import { useBrands } from "@/hooks/use-admin-brands";
import { useToast } from "@/hooks/use-toast";
import type { ProductDetail, ProductStatus } from "@/types/api";

interface OverviewTabProps {
  product: ProductDetail;
}

interface FormData {
  title_tr: string;
  title_en: string;
  status: ProductStatus;
  is_featured: boolean;
  general_features: string[];
  notes: string;
  pdf_ref: string;
  seo_title: string;
  seo_description: string;
  long_description: string;
  brand_slug: string | null;
}

// Brand selector sub-component
function BrandSelector({ control, canEdit }: { control: any; canEdit: boolean }) {
  const { data: brands, isLoading } = useBrands();

  if (isLoading) {
    return (
      <div className="space-y-2">
        <Label>Marka</Label>
        <div className="h-10 bg-stone-100 animate-pulse rounded" />
      </div>
    );
  }

  return (
    <div className="space-y-2">
      <Label htmlFor="brand_slug">Marka</Label>
      <Controller
        name="brand_slug"
        control={control}
        render={({ field }) => (
          <Select
            value={field.value || "__none__"}
            onValueChange={(v) => field.onChange(v === "__none__" ? null : v)}
            disabled={!canEdit}
          >
            <SelectTrigger id="brand_slug">
              <SelectValue placeholder="Marka seçin" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="__none__">Marka Yok</SelectItem>
              {brands?.map((brand) => (
                <SelectItem key={brand.id} value={brand.slug}>
                  {brand.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}
      />
    </div>
  );
}

export function OverviewTab({ product }: OverviewTabProps) {
  const { toast } = useToast();
  const { data: capabilities, isLoading: capabilitiesLoading } = useAdminCapabilities();
  const patchMutation = usePatchProduct(product.slug);

  const canEdit = !capabilitiesLoading && capabilities?.canPatchProduct;
  const showMissingBanner = !capabilitiesLoading && capabilities && !capabilities.canPatchProduct;

  // Form setup
  const { control, handleSubmit, reset, formState: { isDirty, errors } } = useForm<FormData>({
    defaultValues: {
      title_tr: product.title_tr || "",
      title_en: product.title_en || "",
      status: product.status,
      is_featured: product.is_featured,
      general_features: product.general_features || [],
      notes: typeof product.notes === "string" ? product.notes : "",
      pdf_ref: product.pdf_ref || "",
      seo_title: product.seo_title || "",
      seo_description: product.seo_description || "",
      long_description: product.long_description || "",
      brand_slug: (product as any).brand_slug || null,
    },
  });

  // Reset form when product changes
  useEffect(() => {
    reset({
      title_tr: product.title_tr || "",
      title_en: product.title_en || "",
      status: product.status,
      is_featured: product.is_featured,
      general_features: product.general_features || [],
      notes: typeof product.notes === "string" ? product.notes : "",
      pdf_ref: product.pdf_ref || "",
      seo_title: product.seo_title || "",
      seo_description: product.seo_description || "",
      long_description: product.long_description || "",
      brand_slug: (product as any).brand_slug || null,
    });
  }, [product, reset]);

  const handleCancel = useCallback(() => {
    reset();
  }, [reset]);

  const onSubmit = useCallback(async (data: FormData) => {
    try {
      await patchMutation.mutateAsync({
        title_tr: data.title_tr,
        title_en: data.title_en || undefined,
        status: data.status,
        is_featured: data.is_featured,
        general_features: data.general_features.length > 0 ? data.general_features : undefined,
        notes: data.notes ? [data.notes] : undefined,
        pdf_ref: data.pdf_ref || undefined,
        seo_title: data.seo_title || undefined,
        seo_description: data.seo_description || undefined,
        long_description: data.long_description || undefined,
        brand_slug: data.brand_slug || undefined,
      });
      toast({
        title: "Kaydedildi",
        description: "Ürün bilgileri güncellendi",
      });
    } catch (error) {
      const message = error instanceof Error ? error.message : "Kayıt başarısız";
      toast({
        title: "Hata",
        description: message,
        variant: "destructive",
      });
    }
  }, [patchMutation, toast]);

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-6">
      {/* Unsaved changes indicator + actions */}
      {isDirty && canEdit && (
        <div className="sticky top-0 z-10 flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center gap-2 text-amber-800">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Kaydedilmemiş değişiklikler var</span>
          </div>
          <div className="flex gap-2">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={patchMutation.isPending}
            >
              <X className="h-4 w-4 mr-1" />
              İptal
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={patchMutation.isPending}
            >
              <Save className="h-4 w-4 mr-1" />
              {patchMutation.isPending ? "Kaydediliyor..." : "Kaydet"}
            </Button>
          </div>
        </div>
      )}

      {/* Read-only notice */}
      {showMissingBanner && (
        <MissingEndpointBanner
          endpoint="PATCH /api/v1/admin/products/{id}/"
          description="Genel bilgileri düzenlemek için admin CRUD API gerekli"
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Basic Info */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Temel Bilgiler</CardTitle>
            <CardDescription className="text-stone-500">
              Ürün tanımlayıcı bilgileri
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Title TR */}
            <div className="space-y-2">
              <Label htmlFor="title_tr">Başlık (TR) *</Label>
              <Controller
                name="title_tr"
                control={control}
                rules={{ required: "Başlık zorunlu" }}
                render={({ field }) => (
                  <Input
                    {...field}
                    id="title_tr"
                    disabled={!canEdit}
                    className={errors.title_tr ? "border-red-500" : ""}
                  />
                )}
              />
              {errors.title_tr && (
                <p className="text-xs text-red-500">{errors.title_tr.message}</p>
              )}
            </div>

            {/* Title EN */}
            <div className="space-y-2">
              <Label htmlFor="title_en">Başlık (EN)</Label>
              <Controller
                name="title_en"
                control={control}
                render={({ field }) => (
                  <Input {...field} id="title_en" disabled={!canEdit} />
                )}
              />
            </div>

            {/* Slug (read-only) */}
            <div className="space-y-2">
              <Label>Slug</Label>
              <p className="font-mono text-sm text-stone-700 p-2 bg-stone-50 rounded">
                {product.slug}
              </p>
            </div>

            {/* Status + Featured */}
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="status">Durum</Label>
                <Controller
                  name="status"
                  control={control}
                  render={({ field }) => (
                    <Select
                      value={field.value}
                      onValueChange={field.onChange}
                      disabled={!canEdit}
                    >
                      <SelectTrigger id="status">
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="draft">Taslak</SelectItem>
                        <SelectItem value="active">Aktif</SelectItem>
                        <SelectItem value="archived">Arşiv</SelectItem>
                      </SelectContent>
                    </Select>
                  )}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="is_featured">Öne Çıkan</Label>
                <Controller
                  name="is_featured"
                  control={control}
                  render={({ field }) => (
                    <div className="flex items-center gap-2 pt-2">
                      <Switch
                        id="is_featured"
                        checked={field.value}
                        onCheckedChange={field.onChange}
                        disabled={!canEdit}
                      />
                      <span className="text-sm text-stone-600">
                        {field.value ? "Evet" : "Hayır"}
                      </span>
                    </div>
                  )}
                />
              </div>
            </div>

            {/* PDF Reference */}
            <div className="space-y-2">
              <Label htmlFor="pdf_ref">PDF Referans</Label>
              <Controller
                name="pdf_ref"
                control={control}
                render={({ field }) => (
                  <Input {...field} id="pdf_ref" disabled={!canEdit} placeholder="örn: katalog-2024" />
                )}
              />
            </div>
          </CardContent>
        </Card>

        {/* Hierarchy (read-only) */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Hiyerarşi</CardTitle>
            <CardDescription className="text-stone-500">
              Kategori ve seri bilgileri
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div>
              <p className="text-sm text-stone-500">Kategori</p>
              <p className="font-medium text-stone-900">{product.category_name}</p>
              <p className="text-xs text-stone-400">{product.category_slug}</p>
            </div>
            <div>
              <p className="text-sm text-stone-500">Seri</p>
              <p className="font-medium text-stone-900">{product.series_name}</p>
              <p className="text-xs text-stone-400">{product.series_slug}</p>
            </div>
            {product.primary_node_slug && (
              <div>
                <p className="text-sm text-stone-500">Primary Node</p>
                <p className="font-mono text-sm text-stone-700">{product.primary_node_slug}</p>
              </div>
            )}
            <BrandSelector control={control} canEdit={canEdit ?? false} />
          </CardContent>
        </Card>

        {/* General Features */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Genel Özellikler</CardTitle>
            <CardDescription className="text-stone-500">
              Ürün özellikleri listesi
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Controller
              name="general_features"
              control={control}
              render={({ field }) => (
                <ListEditor
                  value={field.value}
                  onChange={field.onChange}
                  placeholder="Yeni özellik ekle..."
                  maxItems={20}
                  maxLength={200}
                  disabled={!canEdit}
                />
              )}
            />
          </CardContent>
        </Card>

        {/* Notes */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Notlar</CardTitle>
            <CardDescription className="text-stone-500">
              Ek bilgiler ve notlar
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Controller
              name="notes"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  placeholder="Ürün hakkında notlar..."
                  rows={4}
                  disabled={!canEdit}
                  className="resize-none"
                />
              )}
            />
          </CardContent>
        </Card>
      </div>

      {/* Long Description */}
      <Card className="border-stone-200 bg-white">
        <CardHeader>
          <CardTitle className="text-lg text-stone-900">Uzun Açıklama</CardTitle>
          <CardDescription className="text-stone-500">
            Detaylı ürün açıklaması
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Controller
            name="long_description"
            control={control}
            render={({ field }) => (
              <Textarea
                {...field}
                placeholder="Ürün hakkında detaylı açıklama..."
                rows={6}
                disabled={!canEdit}
                className="resize-none"
              />
            )}
          />
        </CardContent>
      </Card>

      {/* SEO */}
      <Card className="border-stone-200 bg-white">
        <CardHeader>
          <CardTitle className="text-lg text-stone-900">SEO</CardTitle>
          <CardDescription className="text-stone-500">
            Arama motoru optimizasyonu
          </CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="space-y-2">
            <Label htmlFor="seo_title">SEO Başlığı</Label>
            <Controller
              name="seo_title"
              control={control}
              render={({ field }) => (
                <Input
                  {...field}
                  id="seo_title"
                  disabled={!canEdit}
                  placeholder="Arama sonuçlarında görünecek başlık"
                  maxLength={60}
                />
              )}
            />
            <p className="text-xs text-stone-400">
              Maksimum 60 karakter
            </p>
          </div>
          <div className="space-y-2">
            <Label htmlFor="seo_description">SEO Açıklaması</Label>
            <Controller
              name="seo_description"
              control={control}
              render={({ field }) => (
                <Textarea
                  {...field}
                  id="seo_description"
                  disabled={!canEdit}
                  placeholder="Arama sonuçlarında görünecek açıklama"
                  rows={3}
                  maxLength={160}
                  className="resize-none"
                />
              )}
            />
            <p className="text-xs text-stone-400">
              Maksimum 160 karakter
            </p>
          </div>
        </CardContent>
      </Card>

      {/* Bottom save button */}
      {canEdit && (
        <div className="flex justify-end gap-2">
          <Button
            type="button"
            variant="outline"
            onClick={handleCancel}
            disabled={!isDirty || patchMutation.isPending}
          >
            İptal
          </Button>
          <Button
            type="submit"
            disabled={!isDirty || patchMutation.isPending}
          >
            <Save className="h-4 w-4 mr-2" />
            {patchMutation.isPending ? "Kaydediliyor..." : "Değişiklikleri Kaydet"}
          </Button>
        </div>
      )}
    </form>
  );
}
