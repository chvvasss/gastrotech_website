"use client";

import { useState, useMemo, useCallback, useEffect } from "react";
import { Search, Plus, X, Save, GripVertical, Loader2, Wand2, AlertCircle } from "lucide-react";
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragEndEvent,
} from "@dnd-kit/core";
import {
  arrayMove,
  SortableContext,
  sortableKeyboardCoordinates,
  useSortable,
  verticalListSortingStrategy,
} from "@dnd-kit/sortable";
import { CSS } from "@dnd-kit/utilities";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
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
import { useAdminCapabilities } from "@/hooks/use-admin-capabilities";
import { usePatchProduct } from "@/hooks/use-admin-products";
import { useSpecKeys, useSpecTemplates, useApplySpecTemplate } from "@/hooks/use-spec-keys";
import { useToast } from "@/hooks/use-toast";
import type { ProductDetail, SpecKey } from "@/types/api";

interface SpecsLayoutTabProps {
  product: ProductDetail;
}

interface SortableSpecKeyProps {
  specKey: SpecKey;
  onRemove: (slug: string) => void;
}

function SortableSpecKey({ specKey, onRemove }: SortableSpecKeyProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: specKey.slug });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className="flex items-center gap-2 p-2 bg-white border border-stone-200 rounded-lg group"
    >
      <button
        className="p-1 cursor-grab hover:bg-stone-100 rounded transition-colors"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-4 w-4 text-stone-400" />
      </button>
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-stone-900 truncate">
          {specKey.label_tr}
        </p>
        <p className="text-xs text-stone-500 font-mono">{specKey.slug}</p>
      </div>
      {specKey.unit && (
        <Badge variant="outline" className="text-xs">
          {specKey.unit}
        </Badge>
      )}
      <Button
        variant="ghost"
        size="sm"
        onClick={() => onRemove(specKey.slug)}
        className="h-8 w-8 p-0 opacity-0 group-hover:opacity-100 transition-opacity text-stone-400 hover:text-red-500"
      >
        <X className="h-4 w-4" />
      </Button>
    </div>
  );
}

export function SpecsLayoutTab({ product }: SpecsLayoutTabProps) {
  const { toast } = useToast();
  const { data: capabilities, isLoading: capabilitiesLoading } = useAdminCapabilities();
  const { data: allSpecKeys, isLoading: specKeysLoading } = useSpecKeys();
  const { data: templates, isLoading: templatesLoading } = useSpecTemplates();
  
  const patchMutation = usePatchProduct(product.slug);
  const applyTemplateMutation = useApplySpecTemplate(product.slug);

  // State
  const [localLayout, setLocalLayout] = useState<string[]>(product.spec_layout || []);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedTemplateId, setSelectedTemplateId] = useState<string>("");
  const [overwriteOnApply, setOverwriteOnApply] = useState(false);

  // Reset local layout when product changes
  useEffect(() => {
    setLocalLayout(product.spec_layout || []);
  }, [product.spec_layout]);

  // Capabilities
  const canEdit = !capabilitiesLoading && capabilities?.canPatchProduct;
  const canApplyTemplate = !capabilitiesLoading && capabilities?.canApplyTemplate;
  const showMissingBanner = !capabilitiesLoading && capabilities && !capabilities.canListTemplates;

  // Compute isDirty
  const isDirty = useMemo(() => {
    const originalLayout = product.spec_layout || [];
    if (localLayout.length !== originalLayout.length) return true;
    return localLayout.some((slug, i) => slug !== originalLayout[i]);
  }, [localLayout, product.spec_layout]);

  // Sensors for DnD
  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  // Ensure allSpecKeys is always an array
  const specKeysArray = useMemo(() => {
    if (Array.isArray(allSpecKeys)) return allSpecKeys;
    return [];
  }, [allSpecKeys]);

  // Map slug to SpecKey for display
  const specKeyMap = useMemo(() => {
    const map: Record<string, SpecKey> = {};
    specKeysArray.forEach(key => {
      map[key.slug] = key;
    });
    return map;
  }, [specKeysArray]);

  // Current layout as SpecKey objects
  const layoutSpecKeys = useMemo(() => {
    return localLayout
      .map(slug => specKeyMap[slug])
      .filter(Boolean) as SpecKey[];
  }, [localLayout, specKeyMap]);

  // Available spec keys (not in layout)
  const availableSpecKeys = useMemo(() => {
    const layoutSet = new Set(localLayout);
    return specKeysArray
      .filter(key => !layoutSet.has(key.slug))
      .filter(key => {
        if (!searchTerm) return true;
        const term = searchTerm.toLowerCase();
        return (
          key.slug.toLowerCase().includes(term) ||
          key.label_tr.toLowerCase().includes(term) ||
          (key.label_en || "").toLowerCase().includes(term)
        );
      });
  }, [specKeysArray, localLayout, searchTerm]);

  // Handlers
  const handleDragEnd = useCallback((event: DragEndEvent) => {
    const { active, over } = event;
    if (!over || active.id === over.id) return;

    const oldIndex = localLayout.indexOf(active.id as string);
    const newIndex = localLayout.indexOf(over.id as string);

    if (oldIndex !== -1 && newIndex !== -1) {
      setLocalLayout(arrayMove(localLayout, oldIndex, newIndex));
    }
  }, [localLayout]);

  const handleAddSpecKey = useCallback((slug: string) => {
    if (!localLayout.includes(slug)) {
      setLocalLayout([...localLayout, slug]);
    }
  }, [localLayout]);

  const handleRemoveSpecKey = useCallback((slug: string) => {
    setLocalLayout(localLayout.filter(s => s !== slug));
  }, [localLayout]);

  const handleSave = useCallback(async () => {
    try {
      await patchMutation.mutateAsync({
        spec_layout: localLayout,
      });
      toast({
        title: "Kaydedildi",
        description: "Spec layout güncellendi",
      });
    } catch {
      toast({
        title: "Hata",
        description: "Kayıt başarısız",
        variant: "destructive",
      });
    }
  }, [localLayout, patchMutation, toast]);

  const handleCancel = useCallback(() => {
    setLocalLayout(product.spec_layout || []);
  }, [product.spec_layout]);

  const handleApplyTemplate = useCallback(async () => {
    if (!selectedTemplateId) return;
    
    try {
      const result = await applyTemplateMutation.mutateAsync({
        productId: product.id,
        templateId: selectedTemplateId,
        overwrite: overwriteOnApply,
      });
      toast({
        title: "Şablon uygulandı",
        description: `Güncellenen alanlar: ${result.updated_fields.join(", ") || "yok"}`,
      });
      setSelectedTemplateId("");
    } catch {
      toast({
        title: "Hata",
        description: "Şablon uygulanamadı",
        variant: "destructive",
      });
    }
  }, [selectedTemplateId, overwriteOnApply, product.id, applyTemplateMutation, toast]);

  return (
    <div className="space-y-6">
      {/* Unsaved changes indicator */}
      {isDirty && canEdit && (
        <div className="flex items-center justify-between p-3 bg-amber-50 border border-amber-200 rounded-lg">
          <div className="flex items-center gap-2 text-amber-800">
            <AlertCircle className="h-4 w-4" />
            <span className="text-sm font-medium">Kaydedilmemiş değişiklikler var</span>
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={handleCancel}
              disabled={patchMutation.isPending}
            >
              <X className="h-4 w-4 mr-1" />
              İptal
            </Button>
            <Button
              size="sm"
              onClick={handleSave}
              disabled={patchMutation.isPending}
            >
              {patchMutation.isPending ? (
                <Loader2 className="h-4 w-4 mr-1 animate-spin" />
              ) : (
                <Save className="h-4 w-4 mr-1" />
              )}
              Kaydet
            </Button>
          </div>
        </div>
      )}

      {/* Template notice */}
      {showMissingBanner && (
        <MissingEndpointBanner
          endpoint="GET /api/v1/admin/spec-templates/"
          description="SpecTemplate listesi ve uygulama için admin API gerekli"
        />
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Current Layout */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Mevcut Spec Layout</CardTitle>
            <CardDescription className="text-stone-500">
              Sıralamak için sürükleyip bırakın. {layoutSpecKeys.length} sütun.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {localLayout.length === 0 ? (
              <div className="rounded-lg bg-amber-50 border border-amber-200 p-4">
                <p className="text-sm font-medium text-amber-800">
                  Spec Layout tanımlı değil
                </p>
                <p className="text-sm text-amber-700 mt-1">
                  Sağdaki listeden sütun ekleyin veya bir şablon uygulayın.
                </p>
              </div>
            ) : (
              <DndContext
                sensors={sensors}
                collisionDetection={closestCenter}
                onDragEnd={handleDragEnd}
              >
                <SortableContext
                  items={localLayout}
                  strategy={verticalListSortingStrategy}
                >
                  <div className="space-y-2">
                    {layoutSpecKeys.map((specKey) => (
                      <SortableSpecKey
                        key={specKey.slug}
                        specKey={specKey}
                        onRemove={handleRemoveSpecKey}
                      />
                    ))}
                  </div>
                </SortableContext>
              </DndContext>
            )}
          </CardContent>
        </Card>

        {/* Available Spec Keys + Templates */}
        <div className="space-y-6">
          {/* Apply Template */}
          {canApplyTemplate && !templatesLoading && Array.isArray(templates) && templates.length > 0 && (
            <Card className="border-stone-200 bg-white">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-stone-900">Şablon Uygula</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                <Select
                  value={selectedTemplateId}
                  onValueChange={setSelectedTemplateId}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Şablon seçin..." />
                  </SelectTrigger>
                  <SelectContent>
                    {templates.map(template => (
                      <SelectItem key={template.id} value={template.id}>
                        {template.name} ({template.spec_layout.length} sütun)
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                
                <div className="flex items-center gap-2">
                  <Switch
                    id="overwrite"
                    checked={overwriteOnApply}
                    onCheckedChange={setOverwriteOnApply}
                  />
                  <Label htmlFor="overwrite" className="text-sm text-stone-600">
                    Mevcut layout&apos;u değiştir
                  </Label>
                </div>

                <Button
                  onClick={handleApplyTemplate}
                  disabled={!selectedTemplateId || applyTemplateMutation.isPending}
                  className="w-full"
                >
                  {applyTemplateMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Uygulanıyor...
                    </>
                  ) : (
                    <>
                      <Wand2 className="h-4 w-4 mr-2" />
                      Şablonu Uygula
                    </>
                  )}
                </Button>
              </CardContent>
            </Card>
          )}

          {/* Available Spec Keys */}
          <Card className="border-stone-200 bg-white">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-stone-900">Kullanılabilir Sütunlar</CardTitle>
              <CardDescription className="text-stone-500">
                Eklemek için tıklayın
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
                <Input
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Sütun ara..."
                  className="pl-10"
                />
              </div>

              {specKeysLoading ? (
                <div className="flex justify-center py-8">
                  <Loader2 className="h-6 w-6 animate-spin text-stone-400" />
                </div>
              ) : (
                <div className="max-h-[300px] overflow-y-auto space-y-1">
                  {availableSpecKeys.map((specKey) => (
                    <button
                      key={specKey.slug}
                      onClick={() => handleAddSpecKey(specKey.slug)}
                      disabled={!canEdit}
                      className="w-full flex items-center gap-2 p-2 text-left rounded-lg hover:bg-stone-50 transition-colors disabled:opacity-50"
                    >
                      <Plus className="h-4 w-4 text-stone-400" />
                      <div className="flex-1 min-w-0">
                        <p className="text-sm font-medium text-stone-900 truncate">
                          {specKey.label_tr}
                        </p>
                        <p className="text-xs text-stone-500 font-mono">{specKey.slug}</p>
                      </div>
                      {specKey.unit && (
                        <Badge variant="outline" className="text-xs">
                          {specKey.unit}
                        </Badge>
                      )}
                    </button>
                  ))}
                  {availableSpecKeys.length === 0 && (
                    <p className="text-sm text-stone-400 text-center py-4">
                      {searchTerm ? "Sonuç bulunamadı" : "Tüm sütunlar ekli"}
                    </p>
                  )}
                </div>
              )}
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Variant Specs Preview */}
      {product.variants && product.variants.length > 0 && localLayout.length > 0 && (
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Varyant Spec Önizleme</CardTitle>
            <CardDescription className="text-stone-500">
              Spec layout&apos;a göre varyant değerleri (ilk 10)
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-stone-200">
                    <th className="text-left py-2 px-3 text-stone-500 font-medium">Model</th>
                    {localLayout.map((slug) => {
                      const key = specKeyMap[slug];
                      return (
                        <th key={slug} className="text-left py-2 px-3 text-stone-500 font-medium">
                          {key?.label_tr || slug}
                          {key?.unit && <span className="text-stone-400 ml-1">({key.unit})</span>}
                        </th>
                      );
                    })}
                  </tr>
                </thead>
                <tbody>
                  {product.variants.slice(0, 10).map((variant) => (
                    <tr key={variant.model_code} className="border-b border-stone-100">
                      <td className="py-2 px-3 font-mono font-medium text-stone-900">
                        {variant.model_code}
                      </td>
                      {localLayout.map((slug) => {
                        const specRow = variant.spec_row?.find((s) => s.key === slug);
                        const value = specRow?.value ?? variant.specs?.[slug] ?? "-";
                        return (
                          <td key={slug} className="py-2 px-3 text-stone-700">
                            {String(value)}
                          </td>
                        );
                      })}
                    </tr>
                  ))}
                </tbody>
              </table>
              {product.variants.length > 10 && (
                <p className="text-xs text-stone-400 mt-2 text-center">
                  ... ve {product.variants.length - 10} varyant daha
                </p>
              )}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Bottom save button */}
      {canEdit && isDirty && (
        <div className="flex justify-end gap-2">
          <Button variant="outline" onClick={handleCancel} disabled={patchMutation.isPending}>
            İptal
          </Button>
          <Button onClick={handleSave} disabled={patchMutation.isPending}>
            {patchMutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                Kaydediliyor...
              </>
            ) : (
              <>
                <Save className="h-4 w-4 mr-2" />
                Değişiklikleri Kaydet
              </>
            )}
          </Button>
        </div>
      )}
    </div>
  );
}
