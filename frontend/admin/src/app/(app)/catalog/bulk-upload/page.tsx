"use client";

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { BulkUploadResults } from "@/components/catalog/bulk-upload/results";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { UploadCloud, FileSpreadsheet, Loader2 } from "lucide-react";
import { Toaster } from "@/components/ui/toaster";
import { useToast } from "@/hooks/use-toast";
import { TokenStore } from "@/lib/api";

export default function BulkUploadPage() {
    const [file, setFile] = useState<File | null>(null);
    const [dryRun, setDryRun] = useState(true);
    const [loading, setLoading] = useState(false);
    const [results, setResults] = useState<any>(null);
    const { toast } = useToast();

    const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
        if (e.target.files && e.target.files[0]) {
            setFile(e.target.files[0]);
            setResults(null); // Reset results on new file
        }
    };

    const handeUpload = async () => {
        if (!file) return;

        setLoading(true);
        const formData = new FormData();
        formData.append("file", file);
        formData.append("dry_run", String(dryRun));

        try {
            // Gateway üzerinden relative path kullan (same-origin)
            const token = TokenStore.getAccessToken();
            const response = await fetch("/api/v1/admin/catalog/bulk-upload/", {
                method: "POST",
                body: formData,
                headers: {
                    ...(token ? { "Authorization": `Bearer ${token}` } : {}),
                },
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || "Upload failed");
            }

            const data = await response.json();
            setResults(data);

            toast({
                title: "İşlem Tamamlandı",
                description: dryRun ? "Simülasyon tamamlandı." : "Yükleme tamamlandı.",
            });
        } catch (error: any) {
            console.error("Upload error:", error);
            toast({
                variant: "destructive",
                title: "Hata",
                description: error.message || "Bir hata oluştu.",
            });
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="container py-10 space-y-8">
            <div className="flex items-center justify-between">
                <div className="space-y-1">
                    <h2 className="text-3xl font-bold tracking-tight">Toplu Ürün Yükleme</h2>
                    <p className="text-muted-foreground">
                        Excel dosyası kullanarak ürün kataloğunu güncelleyin.
                    </p>
                </div>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                <Card>
                    <CardHeader>
                        <CardTitle>Dosya Yükleme</CardTitle>
                        <CardDescription>
                            .xlsx formatında hazırlanmış dosyanızı yükleyin.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-6">
                        <div className="grid w-full max-w-sm items-center gap-1.5">
                            <Label htmlFor="excel-file">Excel Dosyası</Label>
                            <Input
                                id="excel-file"
                                type="file"
                                accept=".xlsx"
                                onChange={handleFileChange}
                            />
                        </div>

                        <div className="flex items-center space-x-2">
                            <Checkbox
                                id="dry-run"
                                checked={dryRun}
                                onCheckedChange={(c) => setDryRun(Boolean(c))}
                            />
                            <div className="grid gap-1.5 leading-none">
                                <Label htmlFor="dry-run" className="font-medium cursor-pointer">
                                    Simülasyon Modu (Dry Run)
                                </Label>
                                <p className="text-sm text-muted-foreground">
                                    Değişiklikleri kaydetmeden önce hataları kontrol eder.
                                </p>
                            </div>
                        </div>

                        <Button
                            onClick={handeUpload}
                            disabled={!file || loading}
                            className="w-full"
                        >
                            {loading ? (
                                <>
                                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                                    İşleniyor...
                                </>
                            ) : (
                                <>
                                    <UploadCloud className="mr-2 h-4 w-4" />
                                    {dryRun ? "Simülasyonu Başlat" : "Yüklemeyi Başlat"}
                                </>
                            )}
                        </Button>
                    </CardContent>
                </Card>

                <Card>
                    <CardHeader>
                        <CardTitle>Yardım & Şablon</CardTitle>
                        <CardDescription>
                            Doğru formatlama için örnek şablonu kullanın.
                        </CardDescription>
                    </CardHeader>
                    <CardContent className="space-y-4">
                        <div className="text-sm text-muted-foreground space-y-2">
                            <p>Zorunlu Alanlar:</p>
                            <ul className="list-disc list-inside">
                                <li>Brand</li>
                                <li>Category</li>
                                <li>Series</li>
                                <li>Product Name</li>
                                <li>Model Code</li>
                                <li>Title TR</li>
                            </ul>
                        </div>
                        <Button
                            variant="outline"
                            className="w-full"
                            onClick={() => window.location.href = "/api/v1/admin/catalog/bulk-upload/template/"}
                        >
                            <FileSpreadsheet className="mr-2 h-4 w-4" />
                            Örnek Şablon İndir
                        </Button>
                    </CardContent>
                </Card>
            </div>

            {results && (
                <Card>
                    <CardHeader>
                        <CardTitle>Sonuç Raporu</CardTitle>
                    </CardHeader>
                    <CardContent>
                        <BulkUploadResults results={results} />
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
