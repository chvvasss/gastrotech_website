"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { MessageSquare, Copy, Check, Loader2 } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { useToast } from "@/hooks/use-toast";
import { inquiriesApi } from "@/lib/api/inquiries";
import type { Variant, QuoteComposeResponse } from "@/types/api";

interface ComposeQuoteModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  variants: Variant[];
  productTitle?: string;
}

export function ComposeQuoteModal({
  open,
  onOpenChange,
  variants,
  productTitle,
}: ComposeQuoteModalProps) {
  const { toast } = useToast();
  const [copied, setCopied] = useState(false);
  const [result, setResult] = useState<QuoteComposeResponse | null>(null);

  const composeMutation = useMutation({
    mutationFn: () =>
      inquiriesApi.composeQuote({
        items: variants.map((v) => ({ model_code: v.model_code, qty: 1 })),
      }),
    onSuccess: (data) => {
      setResult(data);
    },
    onError: () => {
      toast({
        title: "Hata",
        description: "Teklif mesajı oluşturulamadı",
        variant: "destructive",
      });
    },
  });

  const handleOpen = (isOpen: boolean) => {
    if (isOpen && !result) {
      composeMutation.mutate();
    }
    if (!isOpen) {
      setResult(null);
      setCopied(false);
    }
    onOpenChange(isOpen);
  };

  const handleCopy = async () => {
    if (!result?.message_tr) return;
    try {
      await navigator.clipboard.writeText(result.message_tr);
      setCopied(true);
      toast({
        title: "Kopyalandı",
        description: "Mesaj panoya kopyalandı",
      });
      setTimeout(() => setCopied(false), 2000);
    } catch {
      toast({
        title: "Hata",
        description: "Kopyalama başarısız",
        variant: "destructive",
      });
    }
  };

  return (
    <Dialog open={open} onOpenChange={handleOpen}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            <MessageSquare className="h-5 w-5 text-primary" />
            Teklif Mesajı
          </DialogTitle>
          <DialogDescription>
            {productTitle && <span className="font-medium">{productTitle}</span>}
            {" - "}
            {variants.length} model seçildi
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-4">
          {composeMutation.isPending ? (
            <div className="flex items-center justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
              <span className="ml-2 text-stone-500">Oluşturuluyor...</span>
            </div>
          ) : result ? (
            <>
              <Textarea
                value={result.message_tr}
                readOnly
                className="min-h-[300px] font-mono text-sm bg-stone-50"
              />
              <div className="flex justify-end gap-2">
                <Button variant="outline" onClick={() => handleOpen(false)}>
                  Kapat
                </Button>
                <Button onClick={handleCopy} className="gap-2">
                  {copied ? (
                    <>
                      <Check className="h-4 w-4" />
                      Kopyalandı
                    </>
                  ) : (
                    <>
                      <Copy className="h-4 w-4" />
                      Kopyala
                    </>
                  )}
                </Button>
              </div>
            </>
          ) : null}
        </div>
      </DialogContent>
    </Dialog>
  );
}
