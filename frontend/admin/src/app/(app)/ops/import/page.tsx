"use client";

import { useState, useCallback } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Upload,
  FileSpreadsheet,
  CheckCircle,
  XCircle,
  AlertCircle,
  Clock,
  Loader2,
  Eye,
  Play,
} from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Switch } from "@/components/ui/switch";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { toast } from "@/hooks/use-toast";
import { opsApi, type ImportJob } from "@/lib/api/ops";
import { ExcelBulkUpload } from "@/components/catalog/bulk-upload/excel-bulk-upload";

const statusConfig: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  pending: { icon: Clock, color: "bg-stone-100 text-stone-700", label: "Bekliyor" },
  validating: { icon: Loader2, color: "bg-blue-100 text-blue-700", label: "Doğrulanıyor" },
  running: { icon: Loader2, color: "bg-blue-100 text-blue-700", label: "Çalışıyor" },
  success: { icon: CheckCircle, color: "bg-green-100 text-green-700", label: "Başarılı" },
  failed: { icon: XCircle, color: "bg-red-100 text-red-700", label: "Başarısız" },
  partial: { icon: AlertCircle, color: "bg-amber-100 text-amber-700", label: "Kısmi Başarı" },
};

const kindLabels: Record<string, string> = {
  variants_csv: "Varyantlar CSV",
  products_csv: "Ürünler CSV",
  taxonomy_csv: "Taksonomi CSV",
};

export default function ImportCenterPage() {
  const [activeTab, setActiveTab] = useState<"variants" | "products" | "excel">("variants");
  const [selectedJob, setSelectedJob] = useState<ImportJob | null>(null);
  const [dryRun, setDryRun] = useState(true);
  const [allowPartial, setAllowPartial] = useState(false);
  const [isUploading, setIsUploading] = useState(false);

  const queryClient = useQueryClient();

  // Fetch import jobs - only poll when page is visible
  const { data: jobs = [], isLoading } = useQuery({
    queryKey: ["import-jobs"],
    queryFn: () => opsApi.listImportJobs(),
    refetchInterval: 5000, // Poll for updates
    refetchIntervalInBackground: false, // Stop polling when tab is hidden
  });

  // Apply mutation
  const applyMutation = useMutation({
    mutationFn: (id: string) => opsApi.applyImportJob(id),
    onSuccess: (response) => {
      queryClient.invalidateQueries({ queryKey: ["import-jobs"] });

      // V5: CRITICAL - Check db_verify before showing success
      const dbVerify = response.result?.db_verify;

      if (!dbVerify) {
        // db_verify missing - this should never happen in V5
        toast({
          title: "İçe aktarma uyarısı",
          description: `Commit tamamlandı ancak veritabanı doğrulaması eksik. İş ID: ${response.job_id}`,
          variant: "destructive",
        });
        return;
      }

      if (!dbVerify.created_entities_found_in_db) {
        // db_verify failed - entities NOT found in DB
        toast({
          title: "Veritabanı doğrulama hatası",
          description: `Commit başarılı görünüyor ancak varlıklar veritabanında bulunamadı. İş ID: ${response.job_id}. Lütfen raporu indirin ve destek ekibiyle iletişime geçin.`,
          variant: "destructive",
        });

        // Show verification details
        const details = dbVerify.verification_details;
        console.error("[V5 Import] DB verification failed:", {
          job_id: response.job_id,
          verification_details: details,
          created_slugs: {
            categories: dbVerify.created_category_slugs,
            brands: dbVerify.created_brand_slugs,
            series: dbVerify.created_series_slugs,
            products: dbVerify.created_product_slugs,
            variants: dbVerify.created_variant_model_codes,
          },
        });

        return;
      }

      // SUCCESS: db_verify passed
      const counts = response.result.counts;
      const totalCreated = (counts.categories_created || 0) + (counts.brands_created || 0) +
        (counts.series_created || 0) + (counts.products_created || 0) +
        (counts.variants_created || 0);

      toast({
        title: "İçe aktarma başarılı ✓",
        description: `${totalCreated} varlık oluşturuldu (Kategoriler: ${counts.categories_created}, Markalar: ${counts.brands_created}, Seriler: ${counts.series_created}, Ürünler: ${counts.products_created}, Varyantlar: ${counts.variants_created}). Veritabanı doğrulandı.`,
      });

      // Optionally refresh the job to show updated status
      queryClient.invalidateQueries({ queryKey: ["import-job", response.job_id] });
    },
    onError: (error: Error) => {
      toast({
        title: "İçe aktarma hatası",
        description: error.message,
        variant: "destructive",
      });
    },
  });

  // Handle file upload
  const handleFileUpload = useCallback(
    async (event: React.ChangeEvent<HTMLInputElement>) => {
      const file = event.target.files?.[0];
      if (!file) return;

      setIsUploading(true);
      try {
        const response = activeTab === "variants"
          ? await opsApi.uploadVariantsCSV(file, { dryRun, allowPartial })
          : await opsApi.uploadProductsCSV(file, { dryRun, allowPartial });

        // Handle both normal response and duplicate file response
        const job = 'job' in response ? response.job : response;
        const isDuplicate = 'existing_job_id' in response;

        queryClient.invalidateQueries({ queryKey: ["import-jobs"] });
        setSelectedJob(job);

        if (isDuplicate) {
          toast({
            title: "Dosya Zaten İçe Aktarılmış",
            description: "Bu dosya daha önce başarıyla içe aktarılmış.",
          });
        } else if (dryRun) {
          toast({
            title: "Doğrulama tamamlandı",
            description: job.error_count === 0
              ? `${job.total_rows} satır doğrulandı. Uygulamak için devam edin.`
              : `${job.error_count} hata bulundu.`,
            variant: job.error_count === 0 ? "default" : "destructive",
          });
        } else {
          toast({
            title: "İçe aktarma tamamlandı",
            description: `${job.created_count} oluşturuldu, ${job.updated_count} güncellendi`,
          });
        }
      } catch (error) {
        toast({
          title: "Dosya yükleme hatası",
          description: error instanceof Error ? error.message : "Bilinmeyen hata",
          variant: "destructive",
        });
      } finally {
        setIsUploading(false);
        // Reset input
        event.target.value = "";
      }
    },
    [activeTab, dryRun, allowPartial, queryClient]
  );

  return (
    <AppShell
      breadcrumbs={[
        { label: "Operasyonlar" },
        { label: "İçe Aktarma" },
      ]}
    >
      <PageHeader
        title="İçe Aktarma Merkezi"
        description="CSV dosyaları ile toplu ürün ve varyant içe aktarımı yapın"
      />

      {/* Upload Section */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Upload className="h-5 w-5" />
            Yeni İçe Aktarma
          </CardTitle>
          <CardDescription>
            Varyant veya ürün verilerini CSV formatında yükleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Tabs value={activeTab} onValueChange={(v) => setActiveTab(v as typeof activeTab)}>
            <TabsList>
              <TabsTrigger value="variants">Varyantlar (CSV)</TabsTrigger>
              <TabsTrigger value="products">Ürünler (CSV)</TabsTrigger>
              <TabsTrigger value="excel" className="relative">
                Excel Otomasyonu
                <Badge className="ml-2 h-4 px-1 text-[10px]" variant="secondary">Yeni</Badge>
              </TabsTrigger>
            </TabsList>

            <TabsContent value="variants" className="space-y-4 mt-4">
              <div className="p-4 bg-stone-50 rounded-lg text-sm">
                <p className="font-medium mb-2">Gerekli Kolonlar (CSV, ; ile ayrılmış):</p>
                <code className="text-xs bg-white px-2 py-1 rounded">
                  model_code;product_slug;name_tr;dimensions;list_price;weight_kg
                </code>
              </div>
            </TabsContent>

            <TabsContent value="products" className="space-y-4 mt-4">
              <div className="p-4 bg-stone-50 rounded-lg text-sm">
                <p className="font-medium mb-2">Gerekli Kolonlar (CSV, ; ile ayrılmış):</p>
                <code className="text-xs bg-white px-2 py-1 rounded">
                  slug;series_slug;title_tr;title_en;status;is_featured
                </code>
              </div>
            </TabsContent>

            <TabsContent value="excel" className="mt-4">
              <ExcelBulkUpload />
            </TabsContent>
          </Tabs>

          {/* Options (Hidden for Excel) */}
          {activeTab !== "excel" && (
            <>
              <div className="flex items-center gap-6 mt-4 p-4 border rounded-lg">
                <div className="flex items-center gap-2">
                  <Switch
                    id="dry-run"
                    checked={dryRun}
                    onCheckedChange={setDryRun}
                  />
                  <Label htmlFor="dry-run" className="text-sm">
                    Önce doğrula (dry-run)
                  </Label>
                </div>
                <div className="flex items-center gap-2">
                  <Switch
                    id="allow-partial"
                    checked={allowPartial}
                    onCheckedChange={setAllowPartial}
                  />
                  <Label htmlFor="allow-partial" className="text-sm">
                    Kısmi başarıya izin ver
                  </Label>
                </div>
              </div>

              {/* Upload Button */}
              <div className="mt-4">
                <label>
                  <input
                    type="file"
                    accept=".csv"
                    onChange={handleFileUpload}
                    disabled={isUploading}
                    className="hidden"
                  />
                  <Button
                    variant="default"
                    className="cursor-pointer"
                    disabled={isUploading}
                    asChild
                  >
                    <span>
                      {isUploading ? (
                        <>
                          <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                          Yükleniyor...
                        </>
                      ) : (
                        <>
                          <FileSpreadsheet className="h-4 w-4 mr-2" />
                          CSV Yükle
                        </>
                      )}
                    </span>
                  </Button>
                </label>
              </div>
            </>
          )}
        </CardContent>
      </Card>

      {/* Jobs History */}
      <Card>
        <CardHeader>
          <CardTitle>İçe Aktarma Geçmişi</CardTitle>
          <CardDescription>Son içe aktarma işlemleri</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-stone-400" />
            </div>
          ) : jobs.length === 0 ? (
            <div className="text-center py-8 text-stone-500">
              Henüz içe aktarma işlemi bulunmuyor
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tür</TableHead>
                  <TableHead>Durum</TableHead>
                  <TableHead>Satır</TableHead>
                  <TableHead>Oluşturulan</TableHead>
                  <TableHead>Güncellenen</TableHead>
                  <TableHead>Hata</TableHead>
                  <TableHead>Tarih</TableHead>
                  <TableHead></TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {jobs.map((job) => {
                  const config = statusConfig[job.status];
                  const StatusIcon = config?.icon || Clock;
                  return (
                    <TableRow key={job.id}>
                      <TableCell className="font-medium">
                        {kindLabels[job.kind] || job.kind}
                      </TableCell>
                      <TableCell>
                        <Badge className={config?.color}>
                          <StatusIcon className={`h-3 w-3 mr-1 ${job.status === "running" || job.status === "validating" ? "animate-spin" : ""}`} />
                          {config?.label}
                          {job.is_preview && job.status === "success" && " (Önizleme)"}
                        </Badge>
                      </TableCell>
                      <TableCell>{job.total_rows}</TableCell>
                      <TableCell className="text-green-600">{job.created_count}</TableCell>
                      <TableCell className="text-blue-600">{job.updated_count}</TableCell>
                      <TableCell className="text-red-600">{job.error_count}</TableCell>
                      <TableCell className="text-stone-500 text-sm">
                        {new Date(job.created_at).toLocaleString("tr-TR")}
                      </TableCell>
                      <TableCell>
                        <div className="flex gap-2">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => setSelectedJob(job)}
                          >
                            <Eye className="h-4 w-4" />
                          </Button>
                          {job.is_preview && (job.status === "pending" || job.status === "partial") && job.error_count === 0 && (
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => applyMutation.mutate(job.id)}
                              disabled={applyMutation.isPending}
                            >
                              <Play className="h-4 w-4 mr-1" />
                              Uygula
                            </Button>
                          )}
                        </div>
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Job Detail Dialog */}
      <Dialog open={!!selectedJob} onOpenChange={() => setSelectedJob(null)}>
        <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>
              İçe Aktarma Detayı
              {selectedJob?.is_preview && (
                <Badge variant="outline" className="ml-2">Önizleme</Badge>
              )}
            </DialogTitle>
            <DialogDescription>
              {selectedJob && kindLabels[selectedJob.kind]} - {selectedJob && new Date(selectedJob.created_at).toLocaleString("tr-TR")}
            </DialogDescription>
          </DialogHeader>

          {selectedJob && (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-4 gap-4">
                <div className="p-3 bg-stone-50 rounded-lg text-center">
                  <div className="text-2xl font-bold">{selectedJob.total_rows}</div>
                  <div className="text-xs text-stone-500">Toplam Satır</div>
                </div>
                <div className="p-3 bg-green-50 rounded-lg text-center">
                  <div className="text-2xl font-bold text-green-700">{selectedJob.created_count}</div>
                  <div className="text-xs text-stone-500">Oluşturulan</div>
                </div>
                <div className="p-3 bg-blue-50 rounded-lg text-center">
                  <div className="text-2xl font-bold text-blue-700">{selectedJob.updated_count}</div>
                  <div className="text-xs text-stone-500">Güncellenen</div>
                </div>
                <div className="p-3 bg-red-50 rounded-lg text-center">
                  <div className="text-2xl font-bold text-red-700">{selectedJob.error_count}</div>
                  <div className="text-xs text-stone-500">Hata</div>
                </div>
              </div>

              {/* Column error */}
              {selectedJob.report_json?.column_error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <strong>Kolon hatası:</strong> {selectedJob.report_json.column_error}
                </div>
              )}

              {/* Parse error */}
              {selectedJob.report_json?.parse_error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <strong>Ayrıştırma hatası:</strong> {selectedJob.report_json.parse_error}
                </div>
              )}

              {/* Execution error */}
              {selectedJob.report_json?.execution_error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg text-red-700">
                  <strong>Uygulama hatası:</strong> {selectedJob.report_json.execution_error}
                </div>
              )}

              {/* Columns found */}
              {selectedJob.report_json?.columns_found && (
                <div className="p-3 bg-stone-50 rounded-lg">
                  <div className="text-sm font-medium mb-1">Bulunan Kolonlar:</div>
                  <div className="flex flex-wrap gap-1">
                    {selectedJob.report_json.columns_found.map((col: string) => (
                      <Badge key={col} variant="outline" className="text-xs">
                        {col}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}

              {/* Row details */}
              {selectedJob.report_json?.rows && selectedJob.report_json.rows.length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">Satır Detayları (ilk 50):</div>
                  <div className="max-h-64 overflow-y-auto border rounded-lg">
                    <Table>
                      <TableHeader>
                        <TableRow>
                          <TableHead className="w-16">Satır</TableHead>
                          <TableHead>Anahtar</TableHead>
                          <TableHead>İşlem</TableHead>
                          <TableHead>Hatalar</TableHead>
                        </TableRow>
                      </TableHeader>
                      <TableBody>
                        {selectedJob.report_json.rows.slice(0, 50).map((row: any) => (
                          <TableRow key={row.row}>
                            <TableCell>{row.row}</TableCell>
                            <TableCell className="font-mono text-sm">
                              {row.model_code || row.slug}
                            </TableCell>
                            <TableCell>
                              <Badge variant={row.action === "create" ? "default" : "outline"}>
                                {row.action === "create" ? "Oluştur" : row.action === "update" ? "Güncelle" : "?"}
                              </Badge>
                            </TableCell>
                            <TableCell>
                              {row.errors.length > 0 ? (
                                <ul className="text-xs text-red-600 list-disc list-inside">
                                  {row.errors.map((err: string, i: number) => (
                                    <li key={i}>{err}</li>
                                  ))}
                                </ul>
                              ) : (
                                <CheckCircle className="h-4 w-4 text-green-600" />
                              )}
                            </TableCell>
                          </TableRow>
                        ))}
                      </TableBody>
                    </Table>
                  </div>
                </div>
              )}

              {/* Execution Errors (List) */}
              {selectedJob.report_json?.execution_errors && selectedJob.report_json.execution_errors.length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2 text-red-600">İşlem Hataları:</div>
                  <div className="max-h-64 overflow-y-auto border border-red-200 bg-red-50 rounded-lg p-2">
                    <ul className="text-sm space-y-1">
                      {selectedJob.report_json.execution_errors.map((err: any, i: number) => (
                        <li key={i} className="text-red-700">
                          <span className="font-semibold">Satır {err.row}:</span> {err.error}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}

              {/* Apply button for dry-run */}
              {selectedJob.is_preview && (selectedJob.status === "pending" || selectedJob.status === "partial") && selectedJob.error_count === 0 && (
                <div className="flex justify-end pt-4 border-t">
                  <Button
                    onClick={() => applyMutation.mutate(selectedJob.id)}
                    disabled={applyMutation.isPending}
                  >
                    {applyMutation.isPending ? (
                      <>
                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                        Uygulanıyor...
                      </>
                    ) : (
                      <>
                        <Play className="h-4 w-4 mr-2" />
                        İçe Aktarmayı Uygula
                      </>
                    )}
                  </Button>
                </div>
              )}
            </div>
          )}
        </DialogContent>
      </Dialog>

    </AppShell>
  );
}
