"use client"

import { useState } from "react"
import { useForm } from "react-hook-form"
import { useToast } from "@/hooks/use-toast"
import { Loader2, Upload, AlertCircle, CheckCircle2, RotateCcw } from "lucide-react"

import { AppShell } from "@/components/layout"
import { Button } from "@/components/ui/button"
import { Textarea } from "@/components/ui/textarea"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert"
import { http as axios } from "@/lib/api/http"

interface ImportStats {
    products_processed: number
    products_created: number
    products_updated: number
    variants_created: number
    variants_updated: number
    images_processed: number
    errors: string[]
    created_product_ids: string[]
}

interface ValidationResult {
    success: boolean
    stats: ImportStats
    dry_run_id?: string
    error?: string
}

interface CommitResult extends ValidationResult {
    job_id?: string
}

export default function JsonImportPage() {
    const [jsonInput, setJsonInput] = useState("")
    const [isLoading, setIsLoading] = useState(false)
    const [previewResult, setPreviewResult] = useState<ValidationResult | null>(null)
    const [commitResult, setCommitResult] = useState<CommitResult | null>(null)
    const { toast } = useToast()

    const breadcrumbs = [
        { label: "Katalog", href: "/catalog/categories" },
        { label: "JSON İçe Aktar" },
    ]

    const handlePreview = async () => {
        if (!jsonInput.trim()) {
            toast({
                title: "Hata",
                description: "Lütfen JSON verisi giriniz",
                variant: "destructive",
            })
            return
        }

        try {
            const parsed = JSON.parse(jsonInput)
            if (!Array.isArray(parsed)) {
                toast({
                    title: "Hata",
                    description: "JSON bir liste ([]) olmalıdır",
                    variant: "destructive",
                })
                return
            }

            setIsLoading(true)
            setPreviewResult(null)
            setCommitResult(null)

            const response = await axios.post("/admin/import/json/preview/", parsed)
            setPreviewResult(response.data)

            if (response.data.success) {
                toast({
                    title: "Başarılı",
                    description: "Önizleme başarılı",
                })
            } else {
                toast({
                    title: "Hata",
                    description: "Önizlemede hatalar bulundu",
                    variant: "destructive",
                })
            }
        } catch (e: any) {
            console.error(e)
            toast({
                title: "Hata",
                description: e.response?.data?.error || "JSON ayrıştırma hatası veya sunucu hatası",
                variant: "destructive",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleCommit = async () => {
        if (!previewResult) return

        try {
            setIsLoading(true)
            // We send the JSON again for simplicity and robustness (stateless)
            const parsed = JSON.parse(jsonInput)

            const response = await axios.post("/admin/import/json/commit/", parsed)
            setCommitResult(response.data)

            if (response.data.success) {
                toast({
                    title: "Başarılı",
                    description: "İçe aktarım tamamlandı",
                })
                setPreviewResult(null) // Clear preview to prevent double commit
            } else {
                toast({
                    title: "Hata",
                    description: "İçe aktarım sırasında hatalar oluştu",
                    variant: "destructive",
                })
            }
        } catch (e: any) {
            console.error(e)
            toast({
                title: "Hata",
                description: e.response?.data?.error || "İçe aktarım hatası",
                variant: "destructive",
            })
        } finally {
            setIsLoading(false)
        }
    }

    const handleUndo = async () => {
        if (!commitResult?.job_id) return

        if (!confirm("Bu işlemi geri almak istediğinize emin misiniz? Oluşturulan ürünler silinecektir.")) {
            return
        }

        try {
            setIsLoading(true)
            const response = await axios.post(`/admin/import/json/undo/${commitResult.job_id}/`)

            if (response.data.success) {
                toast({
                    title: "Başarılı",
                    description: `Geri alma başarılı: ${response.data.deleted_products} ürün silindi`,
                })
                setCommitResult(null) // Clear result
            }
        } catch (e: any) {
            console.error(e)
            toast({
                title: "Hata",
                description: "Geri alma hatası",
                variant: "destructive",
            })
        } finally {
            setIsLoading(false)
        }
    }

    return (
        <AppShell breadcrumbs={breadcrumbs}>
            <div className="space-y-6">
                <div className="flex flex-col gap-2">
                    <h1 className="text-3xl font-bold tracking-tight">JSON Ürün İçe Aktar</h1>
                    <p className="text-muted-foreground">
                        Toplu ürün yüklemek için JSON formatındaki verinizi buraya yapıştırın.
                    </p>
                </div>

                <div className="grid gap-6 md:grid-cols-2">
                    <div className="space-y-6">
                        <Card>
                            <CardHeader>
                                <CardTitle>Veri Girişi</CardTitle>
                                <CardDescription>
                                    JSON formatında ürün listesi yapıştırın.
                                </CardDescription>
                            </CardHeader>
                            <CardContent>
                                <Textarea
                                    placeholder='[{"slug": "urun-1", "name": "Ürün 1", ...}]'
                                    className="min-h-[500px] font-mono text-xs"
                                    value={jsonInput}
                                    onChange={(e) => setJsonInput(e.target.value)}
                                />
                                <div className="mt-4 flex justify-end gap-2">
                                    <Button
                                        onClick={handlePreview}
                                        disabled={isLoading || !jsonInput}
                                    >
                                        {isLoading && <Loader2 className="mr-2 h-4 w-4 animate-spin" />}
                                        <Upload className="mr-2 h-4 w-4" />
                                        Önizle ve Doğrula
                                    </Button>
                                </div>
                            </CardContent>
                        </Card>
                    </div>

                    <div className="space-y-6">
                        {previewResult && !commitResult && (
                            <Card className="border-blue-200 bg-blue-50/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2">
                                        {previewResult.success ? (
                                            <CheckCircle2 className="h-5 w-5 text-green-600" />
                                        ) : (
                                            <AlertCircle className="h-5 w-5 text-red-600" />
                                        )}
                                        Önizleme Sonucu
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div className="bg-white p-3 rounded border">
                                            <span className="block text-muted-foreground">İşlenen Ürün</span>
                                            <span className="text-xl font-bold">{previewResult.stats.products_processed}</span>
                                        </div>
                                        <div className="bg-white p-3 rounded border">
                                            <span className="block text-muted-foreground">Yeni Oluşturulacak</span>
                                            <span className="text-xl font-bold text-green-600">{previewResult.stats.products_created}</span>
                                        </div>
                                        <div className="bg-white p-3 rounded border">
                                            <span className="block text-muted-foreground">Güncellenecek</span>
                                            <span className="text-xl font-bold text-blue-600">{previewResult.stats.products_updated}</span>
                                        </div>
                                        <div className="bg-white p-3 rounded border">
                                            <span className="block text-muted-foreground">Varyantlar</span>
                                            <span className="text-xl font-bold">{previewResult.stats.variants_created + previewResult.stats.variants_updated}</span>
                                        </div>
                                    </div>

                                    {previewResult.stats.errors.length > 0 && (
                                        <Alert variant="destructive">
                                            <AlertTitle>Hatalar ({previewResult.stats.errors.length})</AlertTitle>
                                            <AlertDescription className="mt-2 max-h-[200px] overflow-y-auto text-xs font-mono">
                                                {previewResult.stats.errors.map((err, i) => (
                                                    <div key={i} className="mb-1 border-b border-red-200 pb-1 last:border-0">
                                                        {err}
                                                    </div>
                                                ))}
                                            </AlertDescription>
                                        </Alert>
                                    )}

                                    {previewResult.success && (
                                        <Button
                                            className="w-full"
                                            size="lg"
                                            variant="default"
                                            onClick={handleCommit}
                                            disabled={isLoading}
                                        >
                                            {isLoading ? "Yüklensin mi?" : "Onayla ve Yükle"}
                                        </Button>
                                    )}
                                </CardContent>
                            </Card>
                        )}

                        {commitResult && (
                            <Card className="border-green-200 bg-green-50/50">
                                <CardHeader>
                                    <CardTitle className="flex items-center gap-2 text-green-700">
                                        <CheckCircle2 className="h-6 w-6" />
                                        İçe Aktarım Başarılı
                                    </CardTitle>
                                </CardHeader>
                                <CardContent className="space-y-4">
                                    <div className="grid grid-cols-2 gap-4 text-sm">
                                        <div className="bg-white p-3 rounded border">
                                            <span className="block text-muted-foreground">Oluşturulan Ürün</span>
                                            <span className="text-xl font-bold text-green-700">{commitResult.stats.products_created}</span>
                                        </div>
                                        <div className="bg-white p-3 rounded border">
                                            <span className="block text-muted-foreground">Görseller</span>
                                            <span className="text-xl font-bold text-blue-700">{commitResult.stats.images_processed}</span>
                                        </div>
                                    </div>

                                    {commitResult.job_id && (
                                        <Alert className="bg-white border-orange-200">
                                            <AlertTitle className="text-orange-800">Geri Alma</AlertTitle>
                                            <AlertDescription className="text-orange-700">
                                                Bu işlem yeni yapıldı. Bir sorun varsa hemen geri alabilirsiniz.
                                            </AlertDescription>
                                            <Button
                                                variant="outline"
                                                className="mt-3 w-full border-orange-300 text-orange-700 hover:bg-orange-50 hover:text-orange-800"
                                                onClick={handleUndo}
                                                disabled={isLoading}
                                            >
                                                <RotateCcw className="mr-2 h-4 w-4" />
                                                İşlemi Geri Al (Undo)
                                            </Button>
                                        </Alert>
                                    )}

                                    <Button
                                        variant="secondary"
                                        className="w-full"
                                        onClick={() => {
                                            setCommitResult(null)
                                            setPreviewResult(null)
                                            setJsonInput("")
                                        }}
                                    >
                                        Yeni Yükleme Yap
                                    </Button>
                                </CardContent>
                            </Card>
                        )}
                    </div>
                </div>
            </div>
        </AppShell>
    )
}
