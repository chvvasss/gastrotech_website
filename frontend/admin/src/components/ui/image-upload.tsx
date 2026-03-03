"use client";

import { useState, useRef, useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Upload, X, Loader2 } from "lucide-react";
import { useMediaUpload } from "@/hooks/use-media";
import { useToast } from "@/hooks/use-toast";
import { cn } from "@/lib/utils";

const MAX_FILE_SIZE_MB = 100;
const MAX_FILE_SIZE_BYTES = MAX_FILE_SIZE_MB * 1024 * 1024;

interface ImageUploadProps {
    value?: string; // Media ID
    onChange: (value: string | null) => void;
    currentImageUrl?: string; // Display URL for existing image
    className?: string;
}

export function ImageUpload({ value, onChange, currentImageUrl, className }: ImageUploadProps) {
    const fileInputRef = useRef<HTMLInputElement>(null);
    const [preview, setPreview] = useState<string | null>(currentImageUrl || null);
    const uploadMutation = useMediaUpload();
    const { toast } = useToast();

    // Sync preview when currentImageUrl prop changes (e.g. opening edit for a different item)
    useEffect(() => {
        setPreview(currentImageUrl || null);
    }, [currentImageUrl]);

    const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        // Client-side file size validation
        if (file.size > MAX_FILE_SIZE_BYTES) {
            const sizeMB = (file.size / (1024 * 1024)).toFixed(1);
            toast({
                title: "Dosya çok büyük",
                description: `Dosya boyutu ${sizeMB} MB. Maksimum ${MAX_FILE_SIZE_MB} MB yüklenebilir.`,
                variant: "destructive",
            });
            if (fileInputRef.current) fileInputRef.current.value = "";
            return;
        }

        // Save previous state to restore on failure
        const previousPreview = preview;
        const previousValue = value || null;

        // Create local preview
        const objectUrl = URL.createObjectURL(file);
        setPreview(objectUrl);

        try {
            const response = await uploadMutation.mutateAsync(file);
            onChange(response.data.id);
        } catch (error: any) {
            // Restore previous state on failure instead of clearing
            setPreview(previousPreview);
            onChange(previousValue);
            URL.revokeObjectURL(objectUrl);

            // Show specific error from backend if available
            const backendError = error?.response?.data?.error;
            if (backendError) {
                toast({
                    title: "Yükleme başarısız",
                    description: backendError,
                    variant: "destructive",
                });
            }
            // useMediaUpload onError will also fire for generic errors
        }

        if (fileInputRef.current) fileInputRef.current.value = "";
    };

    const handleRemove = () => {
        setPreview(null);
        onChange(null);
        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };

    return (
        <div className={cn("space-y-4", className)}>
            <div
                className={cn(
                    "relative flex flex-col items-center justify-center rounded-lg border-2 border-dashed border-stone-200 p-6 transition-colors hover:border-primary/50",
                    preview ? "border-solid p-0 overflow-hidden" : "cursor-pointer"
                )}
                onClick={() => !preview && !uploadMutation.isPending && fileInputRef.current?.click()}
            >
                {preview ? (
                    <div className="relative w-full aspect-video">
                        <img
                            src={preview}
                            alt="Preview"
                            className="h-full w-full object-cover"
                        />
                        {uploadMutation.isPending && (
                            <div className="absolute inset-0 flex items-center justify-center bg-black/40">
                                <Loader2 className="h-8 w-8 animate-spin text-white" />
                            </div>
                        )}
                        {!uploadMutation.isPending && (
                            <Button
                                variant="destructive"
                                size="icon"
                                className="absolute right-2 top-2 h-8 w-8 rounded-full"
                                onClick={(e) => {
                                    e.stopPropagation();
                                    handleRemove();
                                }}
                            >
                                <X className="h-4 w-4" />
                            </Button>
                        )}
                    </div>
                ) : (
                    <div className="flex flex-col items-center gap-2 text-center">
                        {uploadMutation.isPending ? (
                            <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                        ) : (
                            <Upload className="h-8 w-8 text-muted-foreground" />
                        )}
                        <div className="text-sm font-medium text-stone-900">
                            {uploadMutation.isPending ? "Yükleniyor..." : "Görsel Yükle"}
                        </div>
                        {!uploadMutation.isPending && (
                            <p className="text-xs text-muted-foreground">
                                Tıklayın veya sürükleyip bırakın (maks. {MAX_FILE_SIZE_MB} MB)
                            </p>
                        )}
                    </div>
                )}
                <input
                    ref={fileInputRef}
                    type="file"
                    className="hidden"
                    accept="image/*"
                    onChange={handleFileSelect}
                    disabled={uploadMutation.isPending}
                />
            </div>
        </div>
    );
}
