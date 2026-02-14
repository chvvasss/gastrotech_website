import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import { AlertCircle, CheckCircle2 } from "lucide-react";

interface UploadResults {
    categories_created: number;
    series_created: number;
    brands_created: number;
    products_created: number;
    products_updated: number;
    variants_created: number;
    variants_updated: number;
    rows_processed: number;
    errors: string[];
    dry_run: boolean;
}

interface BulkUploadResultsProps {
    results: UploadResults;
}

export function BulkUploadResults({ results }: BulkUploadResultsProps) {
    const hasErrors = results.errors.length > 0;
    const hasSuccess = results.rows_processed > 0;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium">Yükleme Sonucu</h3>
                {results.dry_run && (
                    <Badge variant="secondary" className="text-sm">
                        Simülasyon Modu (Kayıt Yapılmadı)
                    </Badge>
                )}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                <StatCard label="İşlenen Satır" value={results.rows_processed} />
                <StatCard label="Yeni Kategori" value={results.categories_created} />
                <StatCard label="Yeni Seri" value={results.series_created} />
                <StatCard label="Yeni Marka" value={results.brands_created} />
                <StatCard label="Yeni Ürün" value={results.products_created} />
                <StatCard label="Güncellenen Ürün" value={results.products_updated} />
                <StatCard label="Yeni Varyant" value={results.variants_created} />
                <StatCard label="Güncellenen Varyant" value={results.variants_updated} />
            </div>

            {hasErrors && (
                <Alert variant="destructive">
                    <AlertCircle className="h-4 w-4" />
                    <AlertTitle>Hatalar ({results.errors.length})</AlertTitle>
                    <AlertDescription>
                        Bazı satırlar işlenirken hata oluştu. Lütfen hataları düzeltip tekrar deneyin.
                        {results.dry_run && " Simülasyon modunda olduğunuz için değişiklikler kaydedilmedi."}
                    </AlertDescription>
                </Alert>
            )}

            {!hasErrors && hasSuccess && (
                <Alert className="border-green-500 bg-green-50 text-green-800">
                    <CheckCircle2 className="h-4 w-4" />
                    <AlertTitle>Başarılı!</AlertTitle>
                    <AlertDescription>
                        {results.dry_run
                            ? "Tüm satırlar doğrulandı. Simülasyon modu kapatılıp gerçek yükleme yapılabilir."
                            : "Tüm satırlar başarıyla işlendi ve veritabanına kaydedildi."
                        }
                    </AlertDescription>
                </Alert>
            )}

            {hasErrors && (
                <div className="rounded-md border p-4">
                    <h4 className="mb-2 font-medium text-sm">Hata Detayları</h4>
                    <ScrollArea className="h-[200px]">
                        <ul className="space-y-1 text-sm text-destructive">
                            {results.errors.map((error, i) => (
                                <li key={i} className="flex items-start gap-2">
                                    <span className="mt-1">•</span>
                                    <span>{error}</span>
                                </li>
                            ))}
                        </ul>
                    </ScrollArea>
                </div>
            )}
        </div>
    );
}

function StatCard({ label, value }: { label: string; value: number }) {
    return (
        <div className="rounded-lg border p-3">
            <div className="text-sm text-muted-foreground">{label}</div>
            <div className="text-2xl font-bold">{value}</div>
        </div>
    );
}
