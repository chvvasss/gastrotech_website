"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Switch } from "@/components/ui/switch";
import { UploadCloud, FileSpreadsheet, Loader2, CheckCircle, XCircle, AlertCircle, Play, FolderTree } from "lucide-react";
import { useToast } from "@/hooks/use-toast";
import { opsApi, type ImportJob } from "@/lib/api/ops";

export function ExcelBulkUpload() {
    const [file, setFile] = useState<File | null>(null);
    const [mode, setMode] = useState<"strict" | "smart">("smart");
    const [loading, setLoading] = useState(false);
    const [validationJob, setValidationJob] = useState<ImportJob | null>(null);
    const [commitLoading, setCommitLoading] = useState(false);
    const { toast } = useToast();

    // Hierarchy options
    const [treatSlashAsHierarchy, setTreatSlashAsHierarchy] = useState(true);
    const [allowCreateMissingCategories, setAllowCreateMissingCategories] = useState(true);

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setValidationJob(null);
        }
    };

    const handleValidate = async () => {
        if (!file) return;

        // Validate file size (max 10MB)
        const maxSize = 10 * 1024 * 1024;
        if (file.size > maxSize) {
            toast({
                variant: "destructive",
                title: "Dosya çok büyük",
                description: "Dosya boyutu maksimum 10MB olmalıdır.",
            });
            return;
        }

        // Validate file extension
        if (!file.name.endsWith('.xlsx') && !file.name.endsWith('.csv')) {
            toast({
                variant: "destructive",
                title: "Geçersiz dosya formatı",
                description: "Sadece .xlsx veya .csv formatında dosyalar yüklenebilir.",
            });
            return;
        }

        setLoading(true);
        try {
            const response = await opsApi.validateImport(file, {
                mode,
                kind: "catalog_import",
                treatSlashAsHierarchy,
                allowCreateMissingCategories,
            });

            // Handle both normal response and duplicate file response
            // Duplicate: {message, existing_job_id, job: ImportJob}
            // Normal: ImportJob directly
            const job = 'job' in response ? response.job : response;
            const isDuplicate = 'existing_job_id' in response;

            setValidationJob(job);

            if (isDuplicate) {
                toast({
                    title: "Dosya Zaten İçe Aktarılmış",
                    description: "Bu dosya daha önce başarıyla içe aktarılmış.",
                    variant: "default",
                });
                return;
            }

            const report = job.report_json;
            const hasErrors = job.error_count > 0;
            const counts = report?.counts;
            // Check for status mismatch: no reported errors but job status is failed
            const hasStatusMismatch = !hasErrors && job.status === "failed";

            if (hasStatusMismatch) {
                toast({
                    title: "Doğrulama Başarısız",
                    description: "Dosya işlenirken dahili bir hata oluştu. Lütfen tekrar deneyin.",
                    variant: "destructive",
                });
            } else {
                toast({
                    title: hasErrors ? "Doğrulama Tamamlandı (Hatalar Var)" : "Doğrulama Başarılı",
                    description: hasErrors
                        ? `${job.error_count} hata bulundu. Lütfen hataları inceleyin.`
                        : `${counts?.valid_product_rows ?? 0} ürün, ${counts?.valid_variant_rows ?? 0} varyant doğrulandı. Uygulayabilirsiniz.`,
                    variant: hasErrors ? "destructive" : "default",
                });
            }
        } catch (error: any) {
            console.error("Validation error:", error);

            let errorMessage = "Bir hata oluştu.";
            if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.response?.data?.detail) {
                errorMessage = error.response.data.detail;
            } else if (error.message) {
                errorMessage = error.message;
            }

            toast({
                variant: "destructive",
                title: "Doğrulama Hatası",
                description: errorMessage,
            });
            setValidationJob(null);
        } finally {
            setLoading(false);
        }
    };

    const handleCommit = async () => {
        if (!validationJob) return;

        setCommitLoading(true);
        try {
            const result = await opsApi.commitImport(validationJob.id, {
                allowPartial: false,
                treatSlashAsHierarchy,
                allowCreateMissingCategories,
            });

            // Check db_verify
            const dbVerify = result.result?.db_verify;
            if (dbVerify?.created_entities_found_in_db) {
                const counts = result.result.counts;
                toast({
                    title: "İçe Aktarma Başarılı ✓",
                    description: `${counts.products_created} ürün, ${counts.variants_created} varyant oluşturuldu. Veritabanına yazıldı.`,
                });
                setValidationJob(null);
                setFile(null);
            } else {
                toast({
                    variant: "destructive",
                    title: "Veritabanı Doğrulama Hatası",
                    description: "Commit başarılı görünüyor ancak varlıklar veritabanında bulunamadı.",
                });
            }
        } catch (error: any) {
            console.error("Commit error:", error);

            let errorMessage = "Bir hata oluştu.";
            if (error.response?.data?.error) {
                errorMessage = error.response.data.error;
            } else if (error.message) {
                errorMessage = error.message;
            }

            toast({
                variant: "destructive",
                title: "Uygulama Hatası",
                description: errorMessage,
            });
        } finally {
            setCommitLoading(false);
        }
    };

    const handleDownloadTemplate = async () => {
        try {
            const blob = await opsApi.downloadTemplate("xlsx", true);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = "import_template.xlsx";
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error: any) {
            console.error("Template download error:", error);
            toast({
                variant: "destructive",
                title: "İndirme Hatası",
                description: error.message || "Şablon indirilemedi.",
            });
        }
    };

    const handleDownloadReport = async () => {
        if (!validationJob) return;

        try {
            const blob = await opsApi.downloadReport(validationJob.id);
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `import_report_${validationJob.id}.xlsx`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        } catch (error: any) {
            console.error("Report download error:", error);
            toast({
                variant: "destructive",
                title: "İndirme Hatası",
                description: error.message || "Rapor indirilemedi.",
            });
        }
    };

    const renderValidationResults = () => {
        if (!validationJob) return null;

        const report = validationJob.report_json;
        const hasErrors = validationJob.error_count > 0;
        const canCommit = (validationJob.status === "pending" || validationJob.status === "partial") && !hasErrors;
        // Detect status mismatch: no errors shown but job can't be committed
        const hasStatusMismatch = !hasErrors && validationJob.status === "failed";

        return (
            <Card className="border-stone-200">
                <CardHeader>
                    <CardTitle className="text-base flex items-center gap-2">
                        {hasErrors || hasStatusMismatch ? (
                            <XCircle className="h-5 w-5 text-red-500" />
                        ) : (
                            <CheckCircle className="h-5 w-5 text-green-500" />
                        )}
                        Doğrulama Sonucu
                        {hasStatusMismatch && (
                            <span className="ml-2 text-xs font-normal text-red-600 bg-red-50 px-2 py-0.5 rounded">
                                Durum: {validationJob.status_display || validationJob.status}
                            </span>
                        )}
                    </CardTitle>
                </CardHeader>
                <CardContent className="space-y-4">
                    {/* Status mismatch warning */}
                    {hasStatusMismatch && (
                        <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                            <div className="flex items-start gap-2">
                                <XCircle className="h-5 w-5 text-red-500 flex-shrink-0 mt-0.5" />
                                <div>
                                    <div className="font-medium text-red-700">Doğrulama Başarısız</div>
                                    <div className="text-sm text-red-600 mt-1">
                                        Dosya işlenirken dahili bir hata oluştu. Lütfen dosyayı tekrar yükleyin.
                                        Sorun devam ederse sistem yöneticisiyle iletişime geçin.
                                    </div>
                                </div>
                            </div>
                        </div>
                    )}

                    {/* Summary Stats */}
                    <div className="grid grid-cols-4 gap-4">
                        <div className="p-3 bg-stone-50 rounded-lg text-center">
                            <div className="text-2xl font-bold">{report.counts.valid_product_rows}</div>
                            <div className="text-xs text-stone-500">Ürün</div>
                        </div>
                        <div className="p-3 bg-stone-50 rounded-lg text-center">
                            <div className="text-2xl font-bold">{report.counts.valid_variant_rows}</div>
                            <div className="text-xs text-stone-500">Varyant</div>
                        </div>
                        <div className="p-3 bg-green-50 rounded-lg text-center">
                            <div className="text-2xl font-bold text-green-700">{report.counts.products_to_create}</div>
                            <div className="text-xs text-stone-500">Oluşturulacak</div>
                        </div>
                        <div className="p-3 bg-red-50 rounded-lg text-center">
                            <div className="text-2xl font-bold text-red-700">{validationJob.error_count}</div>
                            <div className="text-xs text-stone-500">Hata</div>
                        </div>
                    </div>

                    {/* Candidates (Smart Mode) */}
                    {report.candidates && (
                        <div className="space-y-2">
                            {report.candidates.categories.length > 0 && (
                                <div className="flex items-center gap-2 text-sm">
                                    <AlertCircle className="h-4 w-4 text-amber-500" />
                                    <span>{report.candidates.categories.length} yeni kategori oluşturulacak</span>
                                </div>
                            )}
                            {report.candidates.brands.length > 0 && (
                                <div className="flex items-center gap-2 text-sm">
                                    <AlertCircle className="h-4 w-4 text-amber-500" />
                                    <span>{report.candidates.brands.length} yeni marka oluşturulacak</span>
                                </div>
                            )}
                            {report.candidates.series.length > 0 && (
                                <div className="flex items-center gap-2 text-sm">
                                    <AlertCircle className="h-4 w-4 text-amber-500" />
                                    <span>{report.candidates.series.length} yeni seri oluşturulacak</span>
                                </div>
                            )}
                        </div>
                    )}

                    {/* Issues */}
                    {report.issues && report.issues.length > 0 && (
                        <div className="max-h-48 overflow-y-auto border rounded-lg p-2 bg-stone-50">
                            <div className="text-sm font-medium mb-2">Hatalar & Uyarılar ({report.issues.length})</div>
                            <ul className="text-xs space-y-1">
                                {report.issues.slice(0, 20).map((issue, i) => (
                                    <li key={i} className={`${issue.severity === "error" ? "text-red-600" : issue.severity === "warning" ? "text-amber-600" : "text-stone-600"}`}>
                                        {issue.row && `Satır ${issue.row}: `}{issue.message}
                                    </li>
                                ))}
                                {report.issues.length > 20 && (
                                    <li className="text-stone-500">... ve {report.issues.length - 20} daha fazla</li>
                                )}
                            </ul>
                        </div>
                    )}

                    {/* Actions */}
                    <div className="flex gap-2 pt-4 border-t">
                        <Button variant="outline" onClick={handleDownloadReport}>
                            <FileSpreadsheet className="h-4 w-4 mr-2" />
                            Raporu İndir
                        </Button>

                        {canCommit && (
                            <Button onClick={handleCommit} disabled={commitLoading}>
                                {commitLoading ? (
                                    <>
                                        <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                        Uygulanıyor...
                                    </>
                                ) : (
                                    <>
                                        <Play className="h-4 w-4 mr-2" />
                                        Veritabanına Uygula
                                    </>
                                )}
                            </Button>
                        )}
                    </div>
                </CardContent>
            </Card>
        );
    };

    return (
        <div className="space-y-6">
            <div className="grid gap-6 md:grid-cols-2">
                <Card className="bg-stone-50/50 border-stone-200">
                    <CardHeader>
                        <CardTitle className="text-base">Dosya Yükleme (V5)</CardTitle>
                        <CardDescription>
                            .xlsx veya .csv formatında hazırlanmış dosyanızı yükleyin.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="grid w-full max-w-sm items-center gap-1.5">
                            <Label htmlFor="excel-file">Excel/CSV Dosyası</Label>
                            <Input
                                id="excel-file"
                                type="file"
                                accept=".xlsx,.csv"
                                onChange={handleFileChange}
                                className="bg-white"
                            />
                        </div>

                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="smart-mode"
                                checked={mode === "smart"}
                                onCheckedChange={(c) => setMode(c ? "smart" : "strict")}
                            />
                            <div className="grid gap-1.5 leading-none">
                                <Label htmlFor="smart-mode" className="font-medium cursor-pointer">
                                    Smart Mode (Otomatik Oluşturma)
                                </Label>
                                <p className="text-sm text-muted-foreground">
                                    Eksik kategori, marka ve serileri otomatik oluşturur.
                                </p>
                            </div>
                        </div>

                        {/* Hierarchy Options */}
                        <div className="space-y-3 pt-2 border-t border-stone-200">
                            <div className="flex items-center justify-between">
                                <div className="space-y-0.5">
                                    <Label htmlFor="hierarchy-mode" className="text-sm font-medium flex items-center gap-2">
                                        <FolderTree className="h-4 w-4" />
                                        Hiyerarşik Kategoriler
                                    </Label>
                                    <p className="text-xs text-muted-foreground">
                                        &quot;/&quot; veya &quot;&gt;&quot; ile ayrılmış yolları alt kategorilere dönüştürür
                                    </p>
                                </div>
                                <Switch
                                    id="hierarchy-mode"
                                    checked={treatSlashAsHierarchy}
                                    onCheckedChange={setTreatSlashAsHierarchy}
                                />
                            </div>

                            {treatSlashAsHierarchy && mode === "smart" && (
                                <div className="flex items-center justify-between pl-6">
                                    <div className="space-y-0.5">
                                        <Label htmlFor="create-categories" className="text-sm">
                                            Eksik Kategorileri Oluştur
                                        </Label>
                                        <p className="text-xs text-muted-foreground">
                                            Hiyerarşideki eksik kategorileri otomatik oluşturur
                                        </p>
                                    </div>
                                    <Switch
                                        id="create-categories"
                                        checked={allowCreateMissingCategories}
                                        onCheckedChange={setAllowCreateMissingCategories}
                                    />
                                </div>
                            )}
                        </div>

                        <Button
                            onClick={handleValidate}
                            disabled={!file || loading}
                            className="w-full"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    Doğrulanıyor...
                                </>
                            ) : (
                                <>
                                    <UploadCloud className="mr-2 h-4 w-4" />
                                    Doğrula
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                <Card className="bg-stone-50/50 border-stone-200">
                    <CardHeader>
                        <CardTitle className="text-base">Yardım & Şablon</CardTitle>
                        <CardDescription>
                            V5 formatında şablon indirin.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="text-sm text-muted-foreground space-y-2">
                            <p>V5 Import Özellikleri:</p>
                            <ul className="list-disc list-inside text-xs">
                                <li>Products + Variants sayfa yapısı</li>
                                <li>Snapshot tabanlı commit (güvenli)</li>
                                <li>db_verify ile doğrulama</li>
                                <li>Smart mode: Eksikleri otomatik oluştur</li>
                            </ul>
                        </div>
                        <Button
                            variant="outline"
                            className="w-full bg-white"
                            onClick={handleDownloadTemplate}
                        >
                            <FileSpreadsheet className="mr-2 h-4 w-4 text-green-600" />
                            V5 Şablonunu İndir
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {renderValidationResults()}
        </div>
    );
}
