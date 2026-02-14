"use client";

import { useState, useEffect } from "react";
import { Loader2, AlertTriangle, CheckCircle2, Package } from "lucide-react";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Label } from "@/components/ui/label";
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from "@/components/ui/select";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
    adminProductsApi,
    type BulkBrandUpdatePayload,
    type BulkBrandUpdateResponse,
} from "@/lib/api/admin-products";
import { adminBrandsApi, type AdminBrand } from "@/lib/api/admin-brands";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";

interface BulkBrandChangeModalProps {
    open: boolean;
    onOpenChange: (open: boolean) => void;
    selectedIds: string[];
    filters?: {
        series?: string;
        category?: string;
        status?: string;
        search?: string;
        brand?: string;
    };
    selectionMode: "explicit" | "filtered";
    onSuccess?: () => void;
}

const NO_BRAND = "__remove__";

export function BulkBrandChangeModal({
    open,
    onOpenChange,
    selectedIds,
    filters,
    selectionMode,
    onSuccess,
}: BulkBrandChangeModalProps) {
    const { toast } = useToast();
    const queryClient = useQueryClient();

    const [targetBrand, setTargetBrand] = useState<string>("");
    const [previewData, setPreviewData] = useState<BulkBrandUpdateResponse | null>(null);
    const [step, setStep] = useState<"select" | "preview" | "done">("select");

    // Fetch brands
    const { data: brands, isLoading: brandsLoading } = useQuery({
        queryKey: ["admin-brands-active"],
        queryFn: () => adminBrandsApi.list({ is_active: true }),
        enabled: open,
    });

    // Preview mutation (dry_run: true)
    const previewMutation = useMutation({
        mutationFn: () => {
            const payload: BulkBrandUpdatePayload = {
                ...(selectionMode === "explicit"
                    ? { product_ids: selectedIds }
                    : { filters }),
                brand_slug: targetBrand === NO_BRAND ? null : targetBrand,
                dry_run: true,
            };
            return adminProductsApi.bulkUpdateBrand(payload);
        },
        onSuccess: (data) => {
            setPreviewData(data);
            setStep("preview");
        },
        onError: (error: Error) => {
            toast({
                title: "Hata",
                description: error.message || "Önizleme alınamadı",
                variant: "destructive",
            });
        },
    });

    // Commit mutation (dry_run: false)
    const commitMutation = useMutation({
        mutationFn: () => {
            const payload: BulkBrandUpdatePayload = {
                ...(selectionMode === "explicit"
                    ? { product_ids: selectedIds }
                    : { filters }),
                brand_slug: targetBrand === NO_BRAND ? null : targetBrand,
                dry_run: false,
            };
            return adminProductsApi.bulkUpdateBrand(payload);
        },
        onSuccess: (data) => {
            setStep("done");
            toast({
                title: "Tamamlandı",
                description: data.message,
            });
            queryClient.invalidateQueries({ queryKey: ["admin-products"] });
            queryClient.invalidateQueries({ queryKey: ["catalog-products"] });
            onSuccess?.();
        },
        onError: (error: Error) => {
            toast({
                title: "Hata",
                description: error.message || "Güncelleme başarısız",
                variant: "destructive",
            });
        },
    });

    // Reset state when modal closes
    useEffect(() => {
        if (!open) {
            setStep("select");
            setTargetBrand("");
            setPreviewData(null);
        }
    }, [open]);

    const handlePreview = () => {
        if (!targetBrand) return;
        previewMutation.mutate();
    };

    const handleCommit = () => {
        commitMutation.mutate();
    };

    const selectedBrandName = targetBrand === NO_BRAND
        ? "Markasız"
        : brands?.find(b => b.slug === targetBrand)?.name || "";

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-lg">
                <DialogHeader>
                    <DialogTitle className="flex items-center gap-2">
                        <Package className="h-5 w-5" />
                        Toplu Marka Değiştir
                    </DialogTitle>
                    <DialogDescription>
                        {selectionMode === "explicit"
                            ? `${selectedIds.length} ürün seçildi`
                            : "Filtrelenen tüm ürünler güncellenecek"}
                    </DialogDescription>
                </DialogHeader>

                {step === "select" && (
                    <>
                        <div className="space-y-4 py-4">
                            <div className="space-y-2">
                                <Label>Yeni Marka</Label>
                                <Select value={targetBrand} onValueChange={setTargetBrand}>
                                    <SelectTrigger>
                                        <SelectValue placeholder={brandsLoading ? "Yükleniyor..." : "Marka seçin"} />
                                    </SelectTrigger>
                                    <SelectContent>
                                        <SelectItem value={NO_BRAND}>
                                            <span className="text-stone-500">Markayı Kaldır</span>
                                        </SelectItem>
                                        {brands?.map((brand) => (
                                            <SelectItem key={brand.id} value={brand.slug}>
                                                {brand.name}
                                            </SelectItem>
                                        ))}
                                    </SelectContent>
                                </Select>
                            </div>
                        </div>

                        <DialogFooter>
                            <Button variant="outline" onClick={() => onOpenChange(false)}>
                                İptal
                            </Button>
                            <Button
                                onClick={handlePreview}
                                disabled={!targetBrand || previewMutation.isPending}
                            >
                                {previewMutation.isPending && (
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                )}
                                Önizleme
                            </Button>
                        </DialogFooter>
                    </>
                )}

                {step === "preview" && previewData && (
                    <>
                        <div className="space-y-4 py-4">
                            <div className="flex items-center gap-2 p-3 bg-amber-50 border border-amber-200 rounded-lg">
                                <AlertTriangle className="h-5 w-5 text-amber-600" />
                                <div>
                                    <p className="font-medium text-amber-900">
                                        {previewData.affected_count} ürün güncellenecek
                                    </p>
                                    <p className="text-sm text-amber-700">
                                        Marka: <strong>{selectedBrandName}</strong>
                                    </p>
                                </div>
                            </div>

                            {previewData.products_preview && previewData.products_preview.length > 0 && (
                                <div className="space-y-2">
                                    <Label>Önizleme (ilk 20)</Label>
                                    <ScrollArea className="h-48 border rounded-lg">
                                        <div className="p-2 space-y-1">
                                            {previewData.products_preview.map((p) => (
                                                <div
                                                    key={p.id}
                                                    className="flex items-center justify-between p-2 bg-stone-50 rounded text-sm"
                                                >
                                                    <span className="truncate flex-1">{p.title_tr}</span>
                                                    <div className="flex items-center gap-1 ml-2">
                                                        <Badge variant="outline" className="text-xs">
                                                            {p.current_brand || "Yok"}
                                                        </Badge>
                                                        <span className="text-stone-400">→</span>
                                                        <Badge className="text-xs">
                                                            {p.new_brand || "Yok"}
                                                        </Badge>
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </ScrollArea>
                                </div>
                            )}
                        </div>

                        <DialogFooter>
                            <Button variant="outline" onClick={() => setStep("select")}>
                                Geri
                            </Button>
                            <Button
                                onClick={handleCommit}
                                disabled={commitMutation.isPending}
                                className="bg-primary"
                            >
                                {commitMutation.isPending && (
                                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                )}
                                Onayla ve Uygula
                            </Button>
                        </DialogFooter>
                    </>
                )}

                {step === "done" && (
                    <>
                        <div className="flex flex-col items-center justify-center py-8">
                            <CheckCircle2 className="h-12 w-12 text-green-500 mb-4" />
                            <p className="text-lg font-medium text-stone-900">
                                Güncelleme Tamamlandı
                            </p>
                            <p className="text-sm text-stone-500">
                                {previewData?.affected_count} ürün güncellendi
                            </p>
                        </div>

                        <DialogFooter>
                            <Button onClick={() => onOpenChange(false)}>
                                Kapat
                            </Button>
                        </DialogFooter>
                    </>
                )}
            </DialogContent>
        </Dialog>
    );
}
