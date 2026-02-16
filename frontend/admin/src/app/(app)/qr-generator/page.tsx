"use client";

import { useState, useRef, useCallback } from "react";
import {
    QrCode,
    Upload,
    Trash2,
    Download,
    RefreshCw,
    FileText,
    X,
    Eye,
    Plus,
    Loader2,
    ExternalLink,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { AppShell, PageHeader } from "@/components/layout";
import {
    useInfoSheets,
    useCreateInfoSheet,
    useDeleteInfoSheet,
    useRegenerateQr,
} from "@/hooks/use-admin-qr";
import { useToast } from "@/hooks/use-toast";
import type { InfoSheet } from "@/lib/api/admin-qr";

// ============================================================================
// QR Code Generator Page
// ============================================================================

export default function QrGeneratorPage() {
    const { data: sheets, isLoading, error } = useInfoSheets();
    const createMutation = useCreateInfoSheet();
    const deleteMutation = useDeleteInfoSheet();
    const regenerateMutation = useRegenerateQr();
    const { toast } = useToast();

    const [showUploadForm, setShowUploadForm] = useState(false);
    const [previewSheet, setPreviewSheet] = useState<InfoSheet | null>(null);
    const [deleteTarget, setDeleteTarget] = useState<InfoSheet | null>(null);
    const [title, setTitle] = useState("");
    const [selectedFile, setSelectedFile] = useState<File | null>(null);
    const [isDragging, setIsDragging] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);

    // ---- Upload Handlers ----
    const handleFileSelect = (file: File) => {
        if (file.type !== "application/pdf") {
            toast({
                title: "Hata",
                description: "Lütfen sadece PDF dosyası seçin.",
                variant: "destructive",
            });
            return;
        }
        setSelectedFile(file);
        // Auto-fill title from filename if empty
        if (!title) {
            const name = file.name.replace(/\.pdf$/i, "");
            setTitle(name);
        }
    };

    const handleDrop = useCallback(
        (e: React.DragEvent) => {
            e.preventDefault();
            setIsDragging(false);
            const file = e.dataTransfer.files[0];
            if (file) handleFileSelect(file);
        },
        [title]
    );

    const handleDragOver = (e: React.DragEvent) => {
        e.preventDefault();
        setIsDragging(true);
    };

    const handleDragLeave = () => {
        setIsDragging(false);
    };

    const handleSubmit = async () => {
        if (!title.trim()) {
            toast({ title: "Hata", description: "Başlık gerekli.", variant: "destructive" });
            return;
        }
        if (!selectedFile) {
            toast({ title: "Hata", description: "PDF dosyası seçin.", variant: "destructive" });
            return;
        }

        try {
            await createMutation.mutateAsync({ title: title.trim(), pdfFile: selectedFile });
            toast({ title: "Başarılı", description: "Bilgi formu yüklendi ve QR kod üretildi." });
            setTitle("");
            setSelectedFile(null);
            setShowUploadForm(false);
        } catch {
            toast({
                title: "Hata",
                description: "Yükleme sırasında bir hata oluştu.",
                variant: "destructive",
            });
        }
    };

    const handleDelete = async () => {
        if (!deleteTarget) return;
        try {
            await deleteMutation.mutateAsync(deleteTarget.id);
            toast({ title: "Silindi", description: `"${deleteTarget.title}" başarıyla silindi.` });
            setDeleteTarget(null);
        } catch {
            toast({ title: "Hata", description: "Silme işlemi başarısız.", variant: "destructive" });
        }
    };

    const handleRegenerateQr = async (sheet: InfoSheet) => {
        try {
            await regenerateMutation.mutateAsync(sheet.id);
            toast({ title: "Başarılı", description: "QR kod yeniden üretildi." });
        } catch {
            toast({
                title: "Hata",
                description: "QR kod üretilirken hata oluştu.",
                variant: "destructive",
            });
        }
    };

    const handleDownloadQr = async (sheet: InfoSheet) => {
        if (!sheet.qr_url) return;
        try {
            const response = await fetch(sheet.qr_url);
            const blob = await response.blob();
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `QR_${sheet.title.replace(/\s+/g, "_")}.png`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
        } catch {
            // Fallback: direct link
            window.open(sheet.qr_url, "_blank");
        }
    };

    const formatDate = (dateStr: string) => {
        return new Date(dateStr).toLocaleDateString("tr-TR", {
            day: "2-digit",
            month: "2-digit",
            year: "numeric",
            hour: "2-digit",
            minute: "2-digit",
        });
    };

    return (
        <AppShell breadcrumbs={[{ label: "Operasyonlar" }, { label: "QR Kod Üretici" }]}>
            <PageHeader
                title="QR Kod Üretici"
                description="Ürün bilgilendirme formlarını PDF olarak yükleyin ve QR kod çıktısı alın."
            />

            {/* Upload Button */}
            <div className="flex justify-end">
                <Button
                    onClick={() => setShowUploadForm(!showUploadForm)}
                    className="gap-2"
                >
                    {showUploadForm ? (
                        <>
                            <X className="h-4 w-4" />
                            İptal
                        </>
                    ) : (
                        <>
                            <Plus className="h-4 w-4" />
                            Yeni PDF Yükle
                        </>
                    )}
                </Button>
            </div>

            {/* Upload Form */}
            {showUploadForm && (
                <div className="border border-stone-200 bg-white p-6 shadow-sm space-y-5">
                    <h3 className="text-base font-semibold text-stone-800 flex items-center gap-2">
                        <Upload className="h-5 w-5 text-primary" />
                        PDF Yükle & QR Kod Üret
                    </h3>

                    {/* Title Input */}
                    <div className="space-y-2">
                        <Label htmlFor="title">Belge Başlığı</Label>
                        <Input
                            id="title"
                            placeholder="Örn: GT-600 Serisi Ürün Bilgi Formu"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                        />
                    </div>

                    {/* Drag & Drop Area */}
                    <div className="space-y-2">
                        <Label>PDF Dosyası</Label>
                        <div
                            onDrop={handleDrop}
                            onDragOver={handleDragOver}
                            onDragLeave={handleDragLeave}
                            onClick={() => fileInputRef.current?.click()}
                            className={`
                flex flex-col items-center justify-center gap-3 border-2 border-dashed p-8 cursor-pointer
                transition-all duration-200
                ${isDragging
                                    ? "border-primary bg-primary/5 scale-[1.01]"
                                    : selectedFile
                                        ? "border-emerald-400 bg-emerald-50"
                                        : "border-stone-300 hover:border-primary/50 hover:bg-stone-50"
                                }
              `}
                        >
                            {selectedFile ? (
                                <>
                                    <FileText className="h-10 w-10 text-emerald-500" />
                                    <div className="text-center">
                                        <p className="text-sm font-medium text-stone-800">{selectedFile.name}</p>
                                        <p className="text-xs text-stone-500 mt-1">
                                            {(selectedFile.size / 1024 / 1024).toFixed(2)} MB
                                        </p>
                                    </div>
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        onClick={(e) => {
                                            e.stopPropagation();
                                            setSelectedFile(null);
                                        }}
                                        className="text-stone-500 hover:text-red-500"
                                    >
                                        <X className="h-3 w-3 mr-1" />
                                        Kaldır
                                    </Button>
                                </>
                            ) : (
                                <>
                                    <Upload className="h-10 w-10 text-stone-400" />
                                    <div className="text-center">
                                        <p className="text-sm font-medium text-stone-600">
                                            PDF dosyasını buraya sürükleyin
                                        </p>
                                        <p className="text-xs text-stone-400 mt-1">veya tıklayarak seçin</p>
                                    </div>
                                </>
                            )}
                            <input
                                ref={fileInputRef}
                                type="file"
                                accept=".pdf,application/pdf"
                                className="hidden"
                                onChange={(e) => {
                                    const file = e.target.files?.[0];
                                    if (file) handleFileSelect(file);
                                }}
                            />
                        </div>
                    </div>

                    {/* Submit Button */}
                    <div className="flex justify-end gap-3">
                        <Button
                            variant="outline"
                            onClick={() => {
                                setShowUploadForm(false);
                                setTitle("");
                                setSelectedFile(null);
                            }}
                        >
                            İptal
                        </Button>
                        <Button
                            onClick={handleSubmit}
                            disabled={createMutation.isPending || !title.trim() || !selectedFile}
                            className="gap-2"
                        >
                            {createMutation.isPending ? (
                                <Loader2 className="h-4 w-4 animate-spin" />
                            ) : (
                                <QrCode className="h-4 w-4" />
                            )}
                            Yükle & QR Üret
                        </Button>
                    </div>
                </div>
            )}

            {/* Loading State */}
            {isLoading && (
                <div className="flex items-center justify-center py-20">
                    <Loader2 className="h-8 w-8 animate-spin text-primary" />
                </div>
            )}

            {/* Error State */}
            {error && (
                <div className="rounded-xl border border-red-200 bg-red-50 p-6 text-center">
                    <p className="text-sm text-red-600">Veriler yüklenirken hata oluştu.</p>
                </div>
            )}

            {/* Empty State */}
            {!isLoading && !error && sheets?.length === 0 && (
                <div className="border border-stone-200 bg-white p-12 text-center">
                    <QrCode className="h-16 w-16 mx-auto text-stone-300 mb-4" />
                    <h3 className="text-lg font-medium text-stone-700">Henüz belge yok</h3>
                    <p className="text-sm text-stone-500 mt-2">
                        İlk ürün bilgi formunuzu yükleyerek QR kod üretmeye başlayın.
                    </p>
                </div>
            )}

            {/* Sheets Grid */}
            {sheets && sheets.length > 0 && (
                <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
                    {sheets.map((sheet) => (
                        <div
                            key={sheet.id}
                            className="group border border-stone-200 bg-white overflow-hidden shadow-sm hover:shadow-md transition-all duration-200"
                        >
                            {/* QR Code Preview */}
                            <div
                                className="relative flex items-center justify-center bg-stone-50 p-6 cursor-pointer"
                                onClick={() => setPreviewSheet(sheet)}
                            >
                                {sheet.qr_url ? (
                                    <img
                                        src={sheet.qr_url}
                                        alt={`QR kod: ${sheet.title}`}
                                        className="h-40 w-40 object-contain"
                                    />
                                ) : (
                                    <div className="h-40 w-40 flex items-center justify-center border-2 border-dashed border-stone-300">
                                        <QrCode className="h-12 w-12 text-stone-300" />
                                    </div>
                                )}
                                {/* Hover overlay */}
                                <div className="absolute inset-0 bg-black/0 group-hover:bg-black/5 transition-colors flex items-center justify-center opacity-0 group-hover:opacity-100">
                                    <Eye className="h-6 w-6 text-stone-600" />
                                </div>
                            </div>

                            {/* Info */}
                            <div className="p-4 space-y-3">
                                <h4 className="font-medium text-stone-800 truncate" title={sheet.title}>
                                    {sheet.title}
                                </h4>
                                <p className="text-xs text-stone-500">
                                    {formatDate(sheet.created_at)}
                                </p>

                                {/* Actions */}
                                <div className="flex items-center gap-1.5 pt-1">
                                    {/* View PDF */}
                                    {sheet.pdf_url && (
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="gap-1.5 text-xs h-8"
                                            onClick={() => window.open(sheet.pdf_url!, "_blank")}
                                        >
                                            <ExternalLink className="h-3.5 w-3.5" />
                                            PDF
                                        </Button>
                                    )}

                                    {/* Download QR */}
                                    {sheet.qr_url && (
                                        <Button
                                            variant="outline"
                                            size="sm"
                                            className="gap-1.5 text-xs h-8"
                                            onClick={() => handleDownloadQr(sheet)}
                                        >
                                            <Download className="h-3.5 w-3.5" />
                                            QR İndir
                                        </Button>
                                    )}

                                    {/* Regenerate QR */}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-8 w-8 p-0"
                                        title="QR kodu yeniden üret"
                                        onClick={() => handleRegenerateQr(sheet)}
                                        disabled={regenerateMutation.isPending}
                                    >
                                        <RefreshCw className={`h-3.5 w-3.5 ${regenerateMutation.isPending ? "animate-spin" : ""}`} />
                                    </Button>

                                    {/* Delete */}
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="h-8 w-8 p-0 text-red-500 hover:text-red-700 hover:bg-red-50 ml-auto"
                                        title="Sil"
                                        onClick={() => setDeleteTarget(sheet)}
                                    >
                                        <Trash2 className="h-3.5 w-3.5" />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}

            {/* QR Preview Modal */}
            {previewSheet && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm"
                    onClick={() => setPreviewSheet(null)}
                >
                    <div
                        className="relative bg-white shadow-2xl p-8 max-w-lg w-full mx-4 space-y-4"
                        onClick={(e) => e.stopPropagation()}
                    >
                        {/* Close */}
                        <Button
                            variant="ghost"
                            size="sm"
                            className="absolute top-3 right-3 h-8 w-8 p-0"
                            onClick={() => setPreviewSheet(null)}
                        >
                            <X className="h-4 w-4" />
                        </Button>

                        {/* Title */}
                        <h3 className="text-lg font-semibold text-stone-800 pr-8">{previewSheet.title}</h3>

                        {/* QR Code */}
                        <div className="flex justify-center p-4 bg-white border border-stone-100">
                            {previewSheet.qr_url ? (
                                <img
                                    src={previewSheet.qr_url}
                                    alt={`QR kod: ${previewSheet.title}`}
                                    className="h-64 w-64 object-contain"
                                />
                            ) : (
                                <div className="h-64 w-64 flex items-center justify-center text-stone-400">
                                    <QrCode className="h-24 w-24" />
                                </div>
                            )}
                        </div>

                        {/* Info */}
                        <p className="text-xs text-stone-500 text-center">
                            QR kodu tarayarak PDF belgesine ulaşabilirsiniz.
                        </p>

                        {/* Actions */}
                        <div className="flex gap-3 justify-center">
                            {previewSheet.qr_url && (
                                <Button
                                    className="gap-2"
                                    onClick={() => handleDownloadQr(previewSheet)}
                                >
                                    <Download className="h-4 w-4" />
                                    QR Kodu İndir (PNG)
                                </Button>
                            )}
                            {previewSheet.pdf_url && (
                                <Button
                                    variant="outline"
                                    className="gap-2"
                                    onClick={() => window.open(previewSheet.pdf_url!, "_blank")}
                                >
                                    <ExternalLink className="h-4 w-4" />
                                    PDF&apos;i Aç
                                </Button>
                            )}
                        </div>
                    </div>
                </div>
            )}

            {/* Delete Confirm Modal */}
            {deleteTarget && (
                <div
                    className="fixed inset-0 z-[100] flex items-center justify-center bg-black/50 backdrop-blur-sm"
                    onClick={() => setDeleteTarget(null)}
                >
                    <div
                        className="bg-white shadow-2xl p-6 max-w-sm w-full mx-4 space-y-4"
                        onClick={(e) => e.stopPropagation()}
                    >
                        <h3 className="text-lg font-semibold text-stone-800">Silme Onayı</h3>
                        <p className="text-sm text-stone-600">
                            <strong>&ldquo;{deleteTarget.title}&rdquo;</strong> belgesini ve QR kodunu kalıcı olarak
                            silmek istediğinize emin misiniz?
                        </p>
                        <div className="flex gap-3 justify-end">
                            <Button variant="outline" onClick={() => setDeleteTarget(null)}>
                                İptal
                            </Button>
                            <Button
                                variant="destructive"
                                onClick={handleDelete}
                                disabled={deleteMutation.isPending}
                                className="gap-2"
                            >
                                {deleteMutation.isPending ? (
                                    <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                    <Trash2 className="h-4 w-4" />
                                )}
                                Sil
                            </Button>
                        </div>
                    </div>
                </div>
            )}
        </AppShell>
    );
}
