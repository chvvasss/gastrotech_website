"use client";

import { useState, useRef, useCallback, useMemo } from "react";
import { Upload, Trash2, Star, GripVertical, Loader2, ImageIcon, FileText, Film } from "lucide-react";
import { useQueryClient } from "@tanstack/react-query";
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
import { Button } from "@/components/ui/button";
import { useToast } from "@/hooks/use-toast";
import { useProductMediaUpload, useProductMediaReorder, useProductMediaDelete } from "@/hooks/use-catalog-products";
import { getMediaUrl } from "@/lib/media-url";
import type { ProductDetail, ProductMedia } from "@/types/api";

interface MediaTabProps {
  product: ProductDetail;
}

interface SortableMediaItemProps {
  media: ProductMedia;
  onDelete: (id: number) => void;
  onSetPrimary: (id: number) => void;
  isDeleting: boolean;
}

function SortableMediaItem({ media, onDelete, onSetPrimary, isDeleting }: SortableMediaItemProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ id: media.id });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    opacity: isDragging ? 0.5 : 1,
  };

  const getIcon = () => {
    switch (media.kind) {
      case "pdf":
        return <FileText className="h-8 w-8 text-red-500" />;
      case "video":
        return <Film className="h-8 w-8 text-blue-500" />;
      default:
        return null;
    }
  };

  return (
    <div
      ref={setNodeRef}
      style={style}
      className={`flex items-center gap-4 p-3 rounded-lg border bg-white ${
        media.is_primary ? "border-primary/50 bg-primary/5" : "border-stone-200"
      }`}
    >
      {/* Drag Handle */}
      <button
        className="p-1 cursor-grab hover:bg-stone-100 rounded transition-colors"
        {...attributes}
        {...listeners}
      >
        <GripVertical className="h-5 w-5 text-stone-400" />
      </button>

      {/* Thumbnail */}
      <div className="w-16 h-16 rounded-lg bg-stone-100 overflow-hidden flex-shrink-0 flex items-center justify-center">
        {media.kind === "image" ? (
          <img
            src={getMediaUrl(media.file_url)}
            alt={media.alt || media.filename}
            className="w-full h-full object-cover"
          />
        ) : (
          getIcon()
        )}
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <p className="text-sm font-medium text-stone-900 truncate">
          {media.filename}
        </p>
        <p className="text-xs text-stone-500">
          {media.kind} {media.width && media.height && `• ${media.width}×${media.height}`}
        </p>
        {media.alt && (
          <p className="text-xs text-stone-400 truncate">{media.alt}</p>
        )}
      </div>

      {/* Primary Badge */}
      {media.is_primary && (
        <div className="px-2 py-1 bg-primary/10 text-primary text-xs font-medium rounded">
          Primary
        </div>
      )}

      {/* Actions */}
      <div className="flex items-center gap-1">
        {!media.is_primary && (
          <Button
            variant="ghost"
            size="sm"
            onClick={() => onSetPrimary(media.id)}
            title="Primary olarak ayarla"
          >
            <Star className="h-4 w-4" />
          </Button>
        )}
        <Button
          variant="ghost"
          size="sm"
          onClick={() => onDelete(media.id)}
          disabled={isDeleting}
          className="text-red-500 hover:text-red-700 hover:bg-red-50"
        >
          {isDeleting ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <Trash2 className="h-4 w-4" />
          )}
        </Button>
      </div>
    </div>
  );
}

export function MediaTab({ product }: MediaTabProps) {
  const { toast } = useToast();
  useQueryClient(); // Keep for potential future use
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [uploading, setUploading] = useState(false);
  const [deletingId, setDeletingId] = useState<number | null>(null);

  const mediaItems = useMemo(() => product.product_media || [], [product.product_media]);

  const uploadMutation = useProductMediaUpload(product.id);
  const reorderMutation = useProductMediaReorder(product.id);
  const deleteMutation = useProductMediaDelete(product.id);

  const sensors = useSensors(
    useSensor(PointerSensor),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleFileSelect = useCallback(async (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (!files || files.length === 0) return;

    setUploading(true);

    try {
      for (const file of Array.from(files)) {
        await uploadMutation.mutateAsync({ file });
      }
      toast({
        title: "Yükleme tamamlandı",
        description: `${files.length} dosya yüklendi`,
      });
    } catch {
      toast({
        title: "Yükleme hatası",
        description: "Bazı dosyalar yüklenemedi",
        variant: "destructive",
      });
    } finally {
      setUploading(false);
      if (fileInputRef.current) {
        fileInputRef.current.value = "";
      }
    }
  }, [uploadMutation, toast]);

  const handleDragEnd = useCallback(async (event: DragEndEvent) => {
    const { active, over } = event;

    if (!over || active.id === over.id) return;

    const oldIndex = mediaItems.findIndex((m) => m.id === active.id);
    const newIndex = mediaItems.findIndex((m) => m.id === over.id);

    if (oldIndex === -1 || newIndex === -1) return;

    const reordered = arrayMove(mediaItems, oldIndex, newIndex);

    // Build reorder payload
    const items = reordered.map((m, idx) => ({
      product_media_id: String(m.id),
      sort_order: (idx + 1) * 10,
    }));

    try {
      await reorderMutation.mutateAsync(items);
      toast({
        title: "Sıralama güncellendi",
      });
    } catch {
      toast({
        title: "Hata",
        description: "Sıralama güncellenemedi",
        variant: "destructive",
      });
    }
  }, [mediaItems, reorderMutation, toast]);

  const handleDelete = useCallback(async (id: number) => {
    setDeletingId(id);
    try {
      await deleteMutation.mutateAsync(String(id));
      toast({
        title: "Medya silindi",
      });
    } catch {
      toast({
        title: "Hata",
        description: "Medya silinemedi",
        variant: "destructive",
      });
    } finally {
      setDeletingId(null);
    }
  }, [deleteMutation, toast]);

  const handleSetPrimary = useCallback(async (id: number) => {
    const items = mediaItems.map((m) => ({
      product_media_id: String(m.id),
      sort_order: m.sort_order,
      is_primary: m.id === id,
    }));

    try {
      await reorderMutation.mutateAsync(items);
      toast({
        title: "Primary güncellendi",
      });
    } catch {
      toast({
        title: "Hata",
        description: "Primary güncellenemedi",
        variant: "destructive",
      });
    }
  }, [mediaItems, reorderMutation, toast]);

  return (
    <div className="space-y-6">
      {/* Upload Area */}
      <Card className="border-stone-200 bg-white">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-stone-900">Medya Yükle</CardTitle>
          <CardDescription className="text-stone-500">
            Görsel, PDF veya video dosyaları yükleyin
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div
            className="border-2 border-dashed border-stone-200 rounded-lg p-8 text-center hover:border-primary/50 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              multiple
              accept="image/*,application/pdf,video/*"
              onChange={handleFileSelect}
              className="hidden"
            />
            {uploading ? (
              <div className="flex flex-col items-center">
                <Loader2 className="h-10 w-10 text-primary animate-spin mb-3" />
                <p className="text-sm text-stone-500">Yükleniyor...</p>
              </div>
            ) : (
              <>
                <Upload className="h-10 w-10 text-stone-400 mx-auto mb-3" />
                <p className="text-sm font-medium text-stone-900">
                  Dosya seçmek için tıklayın
                </p>
                <p className="text-xs text-stone-500 mt-1">
                  veya sürükleyip bırakın
                </p>
              </>
            )}
          </div>
        </CardContent>
      </Card>

      {/* Media List */}
      <Card className="border-stone-200 bg-white">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg text-stone-900">
            Mevcut Medya ({mediaItems.length})
          </CardTitle>
          <CardDescription className="text-stone-500">
            Sıralamak için sürükleyip bırakın
          </CardDescription>
        </CardHeader>
        <CardContent>
          {mediaItems.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <ImageIcon className="h-12 w-12 text-stone-300 mb-4" />
              <p className="text-stone-500">Henüz medya yok</p>
              <p className="text-sm text-stone-400">
                Yukarıdaki alana dosya yükleyin
              </p>
            </div>
          ) : (
            <DndContext
              sensors={sensors}
              collisionDetection={closestCenter}
              onDragEnd={handleDragEnd}
            >
              <SortableContext
                items={mediaItems.map((m) => m.id)}
                strategy={verticalListSortingStrategy}
              >
                <div className="space-y-2">
                  {mediaItems.map((media) => (
                    <SortableMediaItem
                      key={media.id}
                      media={media}
                      onDelete={handleDelete}
                      onSetPrimary={handleSetPrimary}
                      isDeleting={deletingId === media.id}
                    />
                  ))}
                </div>
              </SortableContext>
            </DndContext>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
