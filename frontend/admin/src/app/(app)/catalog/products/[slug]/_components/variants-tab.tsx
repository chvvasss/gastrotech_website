"use client";

import { useState, useMemo, useCallback } from "react";
import { Copy, MessageSquare, Plus, Edit2, Trash2, Save, X, ClipboardPaste, Loader2 } from "lucide-react";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { useToast } from "@/hooks/use-toast";
import { MissingEndpointBanner, CopyButton, ComposeQuoteModal } from "@/components/catalog";
import { useAdminCapabilities } from "@/hooks/use-admin-capabilities";
import { useCreateVariant, usePatchVariant, useDeleteVariant, useBulkUpdateVariants } from "@/hooks/use-admin-variants";
import type { ProductDetail, Variant } from "@/types/api";

interface VariantsTabProps {
  product: ProductDetail;
}

interface EditingVariant {
  model_code: string;
  name_tr: string;
  dimensions: string;
  weight_kg: string;
  list_price: string;
}

export function VariantsTab({ product }: VariantsTabProps) {
  const { toast } = useToast();
  const { data: capabilities, isLoading: capabilitiesLoading } = useAdminCapabilities();
  
  // State
  const [selectedCodes, setSelectedCodes] = useState<Set<string>>(new Set());
  const [quoteModalOpen, setQuoteModalOpen] = useState(false);
  const [addModalOpen, setAddModalOpen] = useState(false);
  const [bulkPasteModalOpen, setBulkPasteModalOpen] = useState(false);
  const [editingModelCode, setEditingModelCode] = useState<string | null>(null);
  const [editingData, setEditingData] = useState<EditingVariant | null>(null);
  
  // New variant form
  const [newVariant, setNewVariant] = useState({
    model_code: "",
    name_tr: "",
    dimensions: "",
    weight_kg: "",
    list_price: "",
  });
  
  // Bulk paste
  const [bulkPasteText, setBulkPasteText] = useState("");
  const [bulkPastePreview, setBulkPastePreview] = useState<Array<{
    model_code: string;
    name_tr: string;
    dimensions: string;
    list_price: string;
    valid: boolean;
  }>>([]);

  const variants = useMemo(() => product.variants || [], [product.variants]);
  
  // Capabilities
  const canEdit = !capabilitiesLoading && capabilities?.canPatchVariant;
  const canCreate = !capabilitiesLoading && capabilities?.canCreateVariant;
  const canDelete = !capabilitiesLoading && capabilities?.canDeleteVariant;
  const canBulkUpdate = !capabilitiesLoading && capabilities?.canBulkUpdateVariants;
  const showMissingBanner = !capabilitiesLoading && capabilities && !capabilities.canPatchVariant;

  // Mutations
  const createMutation = useCreateVariant(product.slug);
  const patchMutation = usePatchVariant(product.slug);
  const deleteMutation = useDeleteVariant(product.slug);
  const bulkMutation = useBulkUpdateVariants(product.slug);

  // Handlers
  const handleToggleSelect = (modelCode: string) => {
    setSelectedCodes((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(modelCode)) {
        newSet.delete(modelCode);
      } else {
        newSet.add(modelCode);
      }
      return newSet;
    });
  };

  const handleSelectAll = () => {
    if (selectedCodes.size === variants.length) {
      setSelectedCodes(new Set());
    } else {
      setSelectedCodes(new Set(variants.map((v) => v.model_code)));
    }
  };

  const selectedVariants = useMemo(() => {
    return variants.filter((v) => selectedCodes.has(v.model_code));
  }, [variants, selectedCodes]);

  const handleCopyModelCodes = async () => {
    const codes = Array.from(selectedCodes).join("\n");
    try {
      await navigator.clipboard.writeText(codes);
      toast({
        title: "Kopyalandı",
        description: `${selectedCodes.size} model kodu panoya kopyalandı`,
      });
    } catch {
      toast({
        title: "Hata",
        description: "Kopyalama başarısız",
        variant: "destructive",
      });
    }
  };

  // Edit handlers
  const handleStartEdit = (variant: Variant) => {
    setEditingModelCode(variant.model_code);
    setEditingData({
      model_code: variant.model_code,
      name_tr: variant.name_tr || "",
      dimensions: variant.dimensions || "",
      weight_kg: variant.weight_kg?.toString() || "",
      list_price: variant.list_price?.toString() || "",
    });
  };

  const handleCancelEdit = () => {
    setEditingModelCode(null);
    setEditingData(null);
  };

  const handleSaveEdit = async () => {
    if (!editingData || !editingModelCode) return;
    
    try {
      await patchMutation.mutateAsync({
        modelCode: editingModelCode,
        payload: {
          name_tr: editingData.name_tr || undefined,
          dimensions: editingData.dimensions || undefined,
          weight_kg: editingData.weight_kg ? parseFloat(editingData.weight_kg) : null,
          list_price: editingData.list_price ? parseFloat(editingData.list_price) : null,
        },
      });
      toast({ title: "Varyant güncellendi" });
      handleCancelEdit();
    } catch {
      toast({
        title: "Hata",
        description: "Güncelleme başarısız",
        variant: "destructive",
      });
    }
  };

  // Delete handler
  const handleDelete = async (modelCode: string) => {
    if (!confirm(`${modelCode} varyantını silmek istediğinize emin misiniz?`)) return;
    
    try {
      await deleteMutation.mutateAsync(modelCode);
      toast({ title: "Varyant silindi" });
    } catch {
      toast({
        title: "Hata",
        description: "Silme başarısız",
        variant: "destructive",
      });
    }
  };

  // Add variant handler
  const handleAddVariant = async () => {
    if (!newVariant.model_code || !newVariant.name_tr) {
      toast({
        title: "Hata",
        description: "Model kodu ve isim zorunlu",
        variant: "destructive",
      });
      return;
    }
    
    try {
      await createMutation.mutateAsync({
        product_slug: product.slug,
        model_code: newVariant.model_code,
        name_tr: newVariant.name_tr,
        dimensions: newVariant.dimensions || undefined,
        weight_kg: newVariant.weight_kg ? parseFloat(newVariant.weight_kg) : undefined,
        list_price: newVariant.list_price ? parseFloat(newVariant.list_price) : undefined,
      });
      toast({ title: "Varyant eklendi" });
      setAddModalOpen(false);
      setNewVariant({ model_code: "", name_tr: "", dimensions: "", weight_kg: "", list_price: "" });
    } catch {
      toast({
        title: "Hata",
        description: "Ekleme başarısız",
        variant: "destructive",
      });
    }
  };

  // Bulk paste handlers
  const parseBulkPaste = useCallback((text: string) => {
    const lines = text.trim().split("\n").filter(l => l.trim());
    const parsed = lines.map(line => {
      // Support multiple delimiters: ; | \t
      const parts = line.split(/[;\|\t]/).map(p => p.trim());
      return {
        model_code: parts[0] || "",
        name_tr: parts[1] || "",
        dimensions: parts[2] || "",
        list_price: parts[3] || "",
        valid: Boolean(parts[0]),
      };
    });
    setBulkPastePreview(parsed);
  }, []);

  const handleBulkPaste = async () => {
    const validItems = bulkPastePreview.filter(p => p.valid);
    if (validItems.length === 0) {
      toast({
        title: "Hata",
        description: "Geçerli veri yok",
        variant: "destructive",
      });
      return;
    }
    
    const updates = validItems.map(item => ({
      model_code: item.model_code,
      name_tr: item.name_tr || undefined,
      dimensions: item.dimensions || undefined,
      list_price: item.list_price ? parseFloat(item.list_price) : undefined,
    }));
    
    try {
      const result = await bulkMutation.mutateAsync(updates);
      toast({
        title: "Toplu güncelleme tamamlandı",
        description: `${result.updated} güncellendi, ${result.not_found.length} bulunamadı`,
      });
      setBulkPasteModalOpen(false);
      setBulkPasteText("");
      setBulkPastePreview([]);
    } catch {
      toast({
        title: "Hata",
        description: "Toplu güncelleme başarısız",
        variant: "destructive",
      });
    }
  };

  const formatPrice = (price: number | null) => {
    if (!price) return "-";
    return new Intl.NumberFormat("tr-TR", {
      style: "currency",
      currency: "TRY",
    }).format(price);
  };

  if (variants.length === 0 && !canCreate) {
    return (
      <Card className="border-stone-200 bg-white">
        <CardContent className="py-12">
          <div className="flex flex-col items-center justify-center text-center">
            <p className="text-stone-500 font-medium">Varyant bulunamadı</p>
            <p className="text-sm text-stone-400 mt-1">
              Bu ürün grubuna henüz model eklenmemiş
            </p>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      {/* Read-only notice */}
      {showMissingBanner && (
        <MissingEndpointBanner
          endpoint="POST/PATCH/DELETE /api/v1/admin/variants/"
          description="Varyant CRUD için admin API gerekli"
        />
      )}

      {/* Actions */}
      <Card className="border-stone-200 bg-white">
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <div>
              <CardTitle className="text-lg text-stone-900">
                Varyantlar ({variants.length})
              </CardTitle>
              <CardDescription className="text-stone-500">
                {selectedCodes.size > 0
                  ? `${selectedCodes.size} model seçildi`
                  : "Model satırlarını yönetin"}
              </CardDescription>
            </div>
            <div className="flex gap-2">
              {selectedCodes.size > 0 && (
                <>
                  <Button variant="outline" size="sm" onClick={handleCopyModelCodes}>
                    <Copy className="h-4 w-4 mr-1" />
                    Kodları Kopyala
                  </Button>
                  <Button size="sm" onClick={() => setQuoteModalOpen(true)}>
                    <MessageSquare className="h-4 w-4 mr-1" />
                    Teklif Oluştur
                  </Button>
                </>
              )}
              {canBulkUpdate && (
                <Button variant="outline" size="sm" onClick={() => setBulkPasteModalOpen(true)}>
                  <ClipboardPaste className="h-4 w-4 mr-1" />
                  Toplu Yapıştır
                </Button>
              )}
              {canCreate && (
                <Button size="sm" onClick={() => setAddModalOpen(true)}>
                  <Plus className="h-4 w-4 mr-1" />
                  Varyant Ekle
                </Button>
              )}
            </div>
          </div>
        </CardHeader>
        <CardContent className="p-0">
          <div className="overflow-x-auto">
            <Table>
              <TableHeader>
                <TableRow className="bg-stone-50 hover:bg-stone-50">
                  <TableHead className="w-12">
                    <Checkbox
                      checked={selectedCodes.size === variants.length && variants.length > 0}
                      onCheckedChange={handleSelectAll}
                    />
                  </TableHead>
                  <TableHead className="text-stone-600">Model Kodu</TableHead>
                  <TableHead className="text-stone-600">İsim (TR)</TableHead>
                  <TableHead className="text-stone-600">Boyutlar</TableHead>
                  <TableHead className="text-stone-600 text-right">Ağırlık</TableHead>
                  <TableHead className="text-stone-600 text-right">Liste Fiyatı</TableHead>
                  {(canEdit || canDelete) && (
                    <TableHead className="text-stone-600 w-24">İşlem</TableHead>
                  )}
                </TableRow>
              </TableHeader>
              <TableBody>
                {variants.map((variant) => {
                  const isEditing = editingModelCode === variant.model_code;
                  
                  return (
                    <TableRow
                      key={variant.model_code}
                      className={selectedCodes.has(variant.model_code) ? "bg-primary/5" : ""}
                    >
                      <TableCell>
                        <Checkbox
                          checked={selectedCodes.has(variant.model_code)}
                          onCheckedChange={() => handleToggleSelect(variant.model_code)}
                        />
                      </TableCell>
                      <TableCell className="font-mono font-medium text-stone-900">
                        {variant.model_code}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Input
                            value={editingData?.name_tr || ""}
                            onChange={(e) => setEditingData(prev => prev ? { ...prev, name_tr: e.target.value } : null)}
                            className="h-8 w-full"
                          />
                        ) : (
                          <span className="text-stone-700">{variant.name_tr || "-"}</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {isEditing ? (
                          <Input
                            value={editingData?.dimensions || ""}
                            onChange={(e) => setEditingData(prev => prev ? { ...prev, dimensions: e.target.value } : null)}
                            className="h-8 w-32 font-mono text-sm"
                          />
                        ) : (
                          <span className="text-stone-600 font-mono text-sm">{variant.dimensions || "-"}</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {isEditing ? (
                          <Input
                            type="number"
                            step="0.1"
                            value={editingData?.weight_kg || ""}
                            onChange={(e) => setEditingData(prev => prev ? { ...prev, weight_kg: e.target.value } : null)}
                            className="h-8 w-20 text-right"
                          />
                        ) : (
                          <span className="text-stone-600">{variant.weight_kg ? `${variant.weight_kg} kg` : "-"}</span>
                        )}
                      </TableCell>
                      <TableCell className="text-right">
                        {isEditing ? (
                          <Input
                            type="number"
                            step="0.01"
                            value={editingData?.list_price || ""}
                            onChange={(e) => setEditingData(prev => prev ? { ...prev, list_price: e.target.value } : null)}
                            className="h-8 w-28 text-right"
                          />
                        ) : (
                          <span className="font-medium text-stone-900">{formatPrice(variant.list_price)}</span>
                        )}
                      </TableCell>
                      {(canEdit || canDelete) && (
                        <TableCell>
                          {isEditing ? (
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleSaveEdit}
                                disabled={patchMutation.isPending}
                                className="h-8 w-8 p-0 text-green-600"
                              >
                                {patchMutation.isPending ? (
                                  <Loader2 className="h-4 w-4 animate-spin" />
                                ) : (
                                  <Save className="h-4 w-4" />
                                )}
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={handleCancelEdit}
                                className="h-8 w-8 p-0 text-stone-500"
                              >
                                <X className="h-4 w-4" />
                              </Button>
                            </div>
                          ) : (
                            <div className="flex gap-1">
                              {canEdit && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleStartEdit(variant)}
                                  className="h-8 w-8 p-0 text-stone-500 hover:text-stone-700"
                                >
                                  <Edit2 className="h-4 w-4" />
                                </Button>
                              )}
                              {canDelete && (
                                <Button
                                  variant="ghost"
                                  size="sm"
                                  onClick={() => handleDelete(variant.model_code)}
                                  disabled={deleteMutation.isPending}
                                  className="h-8 w-8 p-0 text-stone-500 hover:text-red-600"
                                >
                                  <Trash2 className="h-4 w-4" />
                                </Button>
                              )}
                            </div>
                          )}
                        </TableCell>
                      )}
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          </div>
        </CardContent>
      </Card>

      {/* Quick Copy All */}
      <div className="flex justify-end">
        <CopyButton
          text={variants.map((v) => v.model_code).join("\n")}
          variant="outline"
          label="Tüm Kodları Kopyala"
        />
      </div>

      {/* Quote Modal */}
      <ComposeQuoteModal
        open={quoteModalOpen}
        onOpenChange={setQuoteModalOpen}
        variants={selectedVariants}
        productTitle={product.title_tr}
      />

      {/* Add Variant Modal */}
      <Dialog open={addModalOpen} onOpenChange={setAddModalOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Yeni Varyant Ekle</DialogTitle>
            <DialogDescription>
              {product.title_tr} ürününe yeni bir model ekleyin
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="new_model_code">Model Kodu *</Label>
              <Input
                id="new_model_code"
                value={newVariant.model_code}
                onChange={(e) => setNewVariant(prev => ({ ...prev, model_code: e.target.value }))}
                placeholder="örn: GKO6010"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new_name_tr">İsim (TR) *</Label>
              <Input
                id="new_name_tr"
                value={newVariant.name_tr}
                onChange={(e) => setNewVariant(prev => ({ ...prev, name_tr: e.target.value }))}
                placeholder="örn: Gazlı Ocak 2 Gözlü"
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="new_dimensions">Boyutlar</Label>
              <Input
                id="new_dimensions"
                value={newVariant.dimensions}
                onChange={(e) => setNewVariant(prev => ({ ...prev, dimensions: e.target.value }))}
                placeholder="örn: 400x600x280"
              />
            </div>
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="new_weight">Ağırlık (kg)</Label>
                <Input
                  id="new_weight"
                  type="number"
                  step="0.1"
                  value={newVariant.weight_kg}
                  onChange={(e) => setNewVariant(prev => ({ ...prev, weight_kg: e.target.value }))}
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="new_price">Liste Fiyatı (₺)</Label>
                <Input
                  id="new_price"
                  type="number"
                  step="0.01"
                  value={newVariant.list_price}
                  onChange={(e) => setNewVariant(prev => ({ ...prev, list_price: e.target.value }))}
                />
              </div>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setAddModalOpen(false)}>
              İptal
            </Button>
            <Button 
              onClick={handleAddVariant}
              disabled={createMutation.isPending}
            >
              {createMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Ekleniyor...
                </>
              ) : (
                <>
                  <Plus className="h-4 w-4 mr-2" />
                  Ekle
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Bulk Paste Modal */}
      <Dialog open={bulkPasteModalOpen} onOpenChange={setBulkPasteModalOpen}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>Toplu Varyant Güncelleme</DialogTitle>
            <DialogDescription>
              Her satır bir varyant. Format: MODEL_KODU ; İSİM ; BOYUTLAR ; FİYAT
            </DialogDescription>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <Textarea
              value={bulkPasteText}
              onChange={(e) => {
                setBulkPasteText(e.target.value);
                parseBulkPaste(e.target.value);
              }}
              placeholder={`GKO6010;Gazlı Ocak 2 Gözlü;400x600x280;1500
GKO6020;Gazlı Ocak 4 Gözlü;800x600x280;2500`}
              rows={8}
              className="font-mono text-sm"
            />
            
            {bulkPastePreview.length > 0 && (
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-stone-50 p-2 text-sm font-medium text-stone-700">
                  Önizleme ({bulkPastePreview.filter(p => p.valid).length} geçerli)
                </div>
                <div className="max-h-48 overflow-y-auto">
                  <Table>
                    <TableHeader>
                      <TableRow className="text-xs">
                        <TableHead>Model</TableHead>
                        <TableHead>İsim</TableHead>
                        <TableHead>Boyut</TableHead>
                        <TableHead>Fiyat</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {bulkPastePreview.slice(0, 10).map((item, i) => (
                        <TableRow 
                          key={i} 
                          className={item.valid ? "" : "bg-red-50"}
                        >
                          <TableCell className="font-mono text-xs py-1">{item.model_code || "-"}</TableCell>
                          <TableCell className="text-xs py-1">{item.name_tr || "-"}</TableCell>
                          <TableCell className="text-xs py-1">{item.dimensions || "-"}</TableCell>
                          <TableCell className="text-xs py-1">{item.list_price || "-"}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                  {bulkPastePreview.length > 10 && (
                    <p className="text-xs text-stone-500 p-2 text-center">
                      ... ve {bulkPastePreview.length - 10} satır daha
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setBulkPasteModalOpen(false)}>
              İptal
            </Button>
            <Button 
              onClick={handleBulkPaste}
              disabled={bulkMutation.isPending || bulkPastePreview.filter(p => p.valid).length === 0}
            >
              {bulkMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Güncelleniyor...
                </>
              ) : (
                <>
                  <ClipboardPaste className="h-4 w-4 mr-2" />
                  {bulkPastePreview.filter(p => p.valid).length} Varyant Güncelle
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
