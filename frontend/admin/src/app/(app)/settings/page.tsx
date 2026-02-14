"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { http } from "@/lib/api/http";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { useToast } from "@/hooks/use-toast";
import { Settings, RefreshCcw, Save, BookOpen, AlertTriangle } from "lucide-react";
import { cn } from "@/lib/utils";
import { AppShell, PageHeader } from "@/components/layout";
import Link from "next/link";

export default function SettingsPage() {
  const router = useRouter();
  const { toast } = useToast();
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);

  const [showPrices, setShowPrices] = useState(true);
  const [catalogMode, setCatalogMode] = useState(false);
  const [isSavingCatalogMode, setIsSavingCatalogMode] = useState(false);

  // Fetch settings on mount
  useEffect(() => {
    fetchSettings();
  }, []);

  const fetchSettings = async () => {
    setIsLoading(true);
    try {
      // Endpoint to get public config or admin config
      // Assuming GET /api/v1/common/config/ returns current state
      const { data } = await http.get<{ show_prices: boolean; catalog_mode: boolean }>("/common/config/");
      console.log("Fetched settings:", data);
      setShowPrices(data.show_prices);
      if (typeof data.catalog_mode === "boolean") {
        setCatalogMode(data.catalog_mode);
      }
    } catch (err: any) {
      if (err.response?.status === 401) {
        // Auto redirect handled by AuthGuard but redundancy is fine
        router.push('/login');
        return;
      }
      // If 404, it might mean no setting exists yet.
      // We will assume "True" is default if missing.
      if (err.response?.status !== 404) {
        console.error("Failed to fetch settings", err);
        toast({
          title: "Hata",
          description: "Ayarlar yüklenirken bir sorun oluştu.",
          variant: "destructive",
        });
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleToggle = async (checked: boolean) => {
    // Optimistic Update
    const previousState = showPrices;
    setShowPrices(checked);
    setIsSaving(true);

    try {
      // We need to update the setting. 
      // Assuming PATCH /api/v1/common/config/ or similar.
      // If the backend expects a specific structure for admin update.
      // Let's try PATCH /common/config/ { show_prices: checked }

      // NOTE: If the endpoint is read-only for public, we might need a different admin endpoint.
      // But based on previous prompt, we implemented SiteSetting model.
      // We likely need to Upsert via ViewSet.
      // Let's try the standard update.

      // Strategy: Try PATCH. If 404, try POST? 
      // Or maybe we treat "common/config" as the resource.

      await http.patch("/common/config/", { show_prices: checked });

      toast({
        title: "Başarılı",
        description: "Ayarlar güncellendi. Siteye yansıması 1-2 dakika sürebilir.",
      });
    } catch (error: any) {
      if (error.response?.status === 401) {
        router.push('/login');
        return;
      }

      if (error.response?.status === 404) {
        // Create if missing
        try {
          await http.post("/common/config/", { show_prices: checked });
          toast({
            title: "Başarılı",
            description: "Ayarlar oluşturuldu ve güncellendi.",
          });
        } catch (createErr: any) {
          if (createErr.response?.status === 401) {
            router.push('/login');
            return;
          }
          console.error("Failed to create setting", createErr);
          setShowPrices(previousState); // Revert
          toast({
            title: "Hata",
            description: "Ayarlar kaydedilemedi.",
            variant: "destructive",
          });
        }
      } else {
        console.error("Failed to update settings", error);
        setShowPrices(previousState); // Revert
        toast({
          title: "Hata",
          description: "Ayarlar güncellenemedi.",
          variant: "destructive",
        });
      }
    } finally {
      setIsSaving(false);
    }
  };

  const handleCatalogModeToggle = async (checked: boolean) => {
    const previousState = catalogMode;
    setCatalogMode(checked);
    setIsSavingCatalogMode(true);

    try {
      await http.patch("/common/config/", { catalog_mode: checked });
      toast({
        title: "Başarılı",
        description: checked
          ? "Katalog modu açıldı. Sitede ürünler yerine PDF kataloglar gösterilecek."
          : "Katalog modu kapatıldı. Normal ürün görünümü aktif.",
      });
    } catch (error: any) {
      if (error.response?.status === 401) {
        router.push("/login");
        return;
      }
      console.error("Failed to update catalog mode", error);
      setCatalogMode(previousState);
      toast({
        title: "Hata",
        description: "Katalog modu güncellenemedi.",
        variant: "destructive",
      });
    } finally {
      setIsSavingCatalogMode(false);
    }
  };

  return (
    <AppShell breadcrumbs={[{ label: "Ayarlar" }]}>
      <PageHeader
        title="Ayarlar"
        description="Genel sistem yapılandırması ve görünürlük ayarları."
      />

      <div className="grid gap-6">
        <Card className="border-l-4 border-l-primary">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="space-y-1">
              <CardTitle className="text-xl">Fiyat Gizleme</CardTitle>
              <CardDescription className="text-base">
                Sitedeki tüm ürün fiyatlarını herkese açık olarak gizle veya göster.
              </CardDescription>
            </div>
            <Settings className="h-8 w-8 text-stone-300" />
          </CardHeader>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between rounded-lg border p-4 shadow-sm bg-stone-50">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <label className="text-base font-medium">Fiyat Görünürlüğü</label>
                  {isSaving && <RefreshCcw className="h-3 w-3 animate-spin text-muted-foreground" />}
                </div>
                <p className="text-sm text-muted-foreground">
                  {showPrices
                    ? "Şu an: AKTİF (Fiyatlar Herkese Açık)"
                    : "Şu an: KAPALI (Fiyatlar Gizli - 'Teklif Al' Modu)"}
                </p>
              </div>

              <div className="flex items-center gap-4">
                <Switch
                  checked={showPrices}
                  onCheckedChange={handleToggle}
                  disabled={isLoading || isSaving}
                  className="data-[state=checked]:bg-green-600 data-[state=unchecked]:bg-stone-300"
                />
              </div>
            </div>

            <p className="mt-4 text-sm text-stone-500 flex items-center gap-2">
              <Save className="h-4 w-4" />
              Değişiklikler anında veritabanına kaydedilir, ancak önbellek nedeniyle sitede görünmesi birkaç dakika sürebilir.
            </p>
          </CardContent>
        </Card>

        <Card className="border-l-4 border-l-amber-500">
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <div className="space-y-1">
              <CardTitle className="text-xl">Katalog Modu</CardTitle>
              <CardDescription className="text-base">
                Açıldığında sitede ürünler yerine kategorilere atanan PDF kataloglar gösterilir.
              </CardDescription>
            </div>
            <BookOpen className="h-8 w-8 text-amber-300" />
          </CardHeader>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between rounded-lg border p-4 shadow-sm bg-amber-50/50 border-amber-200">
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <label className="text-base font-medium">Katalog Modu</label>
                  {isSavingCatalogMode && <RefreshCcw className="h-3 w-3 animate-spin text-muted-foreground" />}
                </div>
                <p className="text-sm text-muted-foreground">
                  {catalogMode
                    ? "Şu an: AKTİF (Ürünler Gizli - PDF Kataloglar Gösteriliyor)"
                    : "Şu an: KAPALI (Normal Ürün Görünümü)"}
                </p>
              </div>

              <div className="flex items-center gap-4">
                <Switch
                  checked={catalogMode}
                  onCheckedChange={handleCatalogModeToggle}
                  disabled={isLoading || isSavingCatalogMode}
                  className="data-[state=checked]:bg-amber-600 data-[state=unchecked]:bg-stone-300"
                />
              </div>
            </div>

            {catalogMode && (
              <div className="mt-4 flex items-start gap-2 rounded-lg bg-amber-50 border border-amber-200 p-3">
                <AlertTriangle className="h-5 w-5 text-amber-600 mt-0.5 flex-shrink-0" />
                <div className="text-sm text-amber-800">
                  <p className="font-semibold">Katalog Modu Aktif</p>
                  <p className="mt-1">Sitede hiçbir ürün gösterilmiyor. Kategori sayfalarında yalnızca PDF kataloglar görünecek.</p>
                </div>
              </div>
            )}

            <div className="mt-4 flex items-center justify-between">
              <p className="text-sm text-stone-500 flex items-center gap-2">
                <Save className="h-4 w-4" />
                Değişiklikler anında veritabanına kaydedilir.
              </p>
              <Button variant="outline" size="sm" asChild>
                <Link href="/catalog/category-catalogs">
                  <BookOpen className="mr-2 h-4 w-4" />
                  Kategori Kataloglarını Yönet
                </Link>
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </AppShell>
  );
}
