"use client";

import { useState, useCallback } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { 
  ArrowLeft, 
  Mail, 
  Phone, 
  Building2, 
  Globe, 
  ExternalLink,
  Package,
  Save,
  Loader2,
  Clock,
  CheckCircle,
  AlertCircle,
} from "lucide-react";
import { AppShell } from "@/components/layout";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { useInquiry, useUpdateInquiryStatus, useUpdateInquiryNote } from "@/hooks/use-inquiries";
import { useToast } from "@/hooks/use-toast";
import type { InquiryStatus } from "@/types/api";

const STATUS_CONFIG: Record<InquiryStatus, { label: string; color: string; icon: typeof Clock }> = {
  new: { label: "Yeni", color: "bg-primary/10 text-primary", icon: AlertCircle },
  in_progress: { label: "İşlemde", color: "bg-amber-100 text-amber-800", icon: Clock },
  closed: { label: "Kapalı", color: "bg-green-100 text-green-800", icon: CheckCircle },
};

export default function InquiryDetailPage() {
  const params = useParams();
  const id = params.id as string;
  const { toast } = useToast();
  
  const { data: inquiry, isLoading, error } = useInquiry(id);
  const updateStatusMutation = useUpdateInquiryStatus();
  const updateNoteMutation = useUpdateInquiryNote();
  
  const [localNote, setLocalNote] = useState<string | null>(null);
  const noteValue = localNote !== null ? localNote : (inquiry?.internal_note || "");
  const noteDirty = localNote !== null && localNote !== (inquiry?.internal_note || "");

  const handleStatusChange = useCallback(async (newStatus: InquiryStatus) => {
    try {
      await updateStatusMutation.mutateAsync({ id, status: newStatus });
      toast({ title: "Durum güncellendi" });
    } catch {
      toast({
        title: "Hata",
        description: "Durum güncellenemedi",
        variant: "destructive",
      });
    }
  }, [id, updateStatusMutation, toast]);

  const handleSaveNote = useCallback(async () => {
    if (localNote === null) return;
    try {
      await updateNoteMutation.mutateAsync({ id, internal_note: localNote });
      toast({ title: "Not kaydedildi" });
      setLocalNote(null);
    } catch {
      toast({
        title: "Hata",
        description: "Not kaydedilemedi",
        variant: "destructive",
      });
    }
  }, [id, localNote, updateNoteMutation, toast]);

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleString("tr-TR", {
      dateStyle: "medium",
      timeStyle: "short",
    });
  };

  if (isLoading) {
    return (
      <AppShell
        breadcrumbs={[
          { label: "Talepler", href: "/inquiries" },
          { label: "Yükleniyor..." },
        ]}
      >
        <div className="space-y-6">
          <Skeleton className="h-10 w-[300px]" />
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            <Skeleton className="h-[300px] lg:col-span-2" />
            <Skeleton className="h-[300px]" />
          </div>
        </div>
      </AppShell>
    );
  }

  if (error || !inquiry) {
    return (
      <AppShell
        breadcrumbs={[
          { label: "Talepler", href: "/inquiries" },
          { label: "Hata" },
        ]}
      >
        <div className="flex flex-col items-center justify-center py-16 text-center">
          <h2 className="text-xl font-semibold text-stone-900 mb-2">
            Talep bulunamadı
          </h2>
          <p className="text-stone-500">
            ID: {id}
          </p>
          <Button asChild className="mt-4">
            <Link href="/inquiries">Talep Listesine Dön</Link>
          </Button>
        </div>
      </AppShell>
    );
  }

  const statusConfig = STATUS_CONFIG[inquiry.status];
  const StatusIcon = statusConfig.icon;

  return (
    <AppShell
      breadcrumbs={[
        { label: "Talepler", href: "/inquiries" },
        { label: inquiry.full_name },
      ]}
    >
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <div className="flex items-center gap-4">
          <Button variant="ghost" size="sm" asChild>
            <Link href="/inquiries">
              <ArrowLeft className="h-4 w-4 mr-1" />
              Geri
            </Link>
          </Button>
          <div>
            <h1 className="text-2xl font-bold text-stone-900">{inquiry.full_name}</h1>
            <p className="text-stone-500 text-sm">{formatDate(inquiry.created_at)}</p>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <Select
            value={inquiry.status}
            onValueChange={(v) => handleStatusChange(v as InquiryStatus)}
            disabled={updateStatusMutation.isPending}
          >
            <SelectTrigger className="w-[140px]">
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="new">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-red-500" />
                  Yeni
                </div>
              </SelectItem>
              <SelectItem value="in_progress">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-amber-500" />
                  İşlemde
                </div>
              </SelectItem>
              <SelectItem value="closed">
                <div className="flex items-center gap-2">
                  <div className="w-2 h-2 rounded-full bg-green-500" />
                  Kapalı
                </div>
              </SelectItem>
            </SelectContent>
          </Select>
          <Badge className={statusConfig.color}>
            <StatusIcon className="h-3 w-3 mr-1" />
            {statusConfig.label}
          </Badge>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Contact Info + Items */}
        <div className="lg:col-span-2 space-y-6">
          {/* Contact Information */}
          <Card className="border-stone-200 bg-white">
            <CardHeader>
              <CardTitle className="text-lg text-stone-900">İletişim Bilgileri</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="flex items-center gap-3">
                  <div className="h-10 w-10 rounded-full bg-stone-100 flex items-center justify-center">
                    <Mail className="h-5 w-5 text-stone-500" />
                  </div>
                  <div>
                    <p className="text-xs text-stone-500">E-posta</p>
                    <a 
                      href={`mailto:${inquiry.email}`}
                      className="text-sm font-medium text-primary hover:underline"
                    >
                      {inquiry.email}
                    </a>
                  </div>
                </div>
                {inquiry.phone && (
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-stone-100 flex items-center justify-center">
                      <Phone className="h-5 w-5 text-stone-500" />
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">Telefon</p>
                      <a 
                        href={`tel:${inquiry.phone}`}
                        className="text-sm font-medium text-primary hover:underline"
                      >
                        {inquiry.phone}
                      </a>
                    </div>
                  </div>
                )}
                {inquiry.company && (
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-stone-100 flex items-center justify-center">
                      <Building2 className="h-5 w-5 text-stone-500" />
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">Şirket</p>
                      <p className="text-sm font-medium text-stone-900">{inquiry.company}</p>
                    </div>
                  </div>
                )}
                {inquiry.source_url && (
                  <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-full bg-stone-100 flex items-center justify-center">
                      <Globe className="h-5 w-5 text-stone-500" />
                    </div>
                    <div>
                      <p className="text-xs text-stone-500">Kaynak URL</p>
                      <a 
                        href={inquiry.source_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-sm text-primary hover:underline flex items-center gap-1"
                      >
                        {new URL(inquiry.source_url).pathname}
                        <ExternalLink className="h-3 w-3" />
                      </a>
                    </div>
                  </div>
                )}
              </div>

              {/* UTM Parameters */}
              {(inquiry.utm_source || inquiry.utm_medium || inquiry.utm_campaign) && (
                <div className="pt-4 border-t border-stone-100">
                  <p className="text-xs text-stone-500 mb-2">UTM Parametreleri</p>
                  <div className="flex gap-2 flex-wrap">
                    {inquiry.utm_source && (
                      <Badge variant="outline" className="text-xs">
                        source: {inquiry.utm_source}
                      </Badge>
                    )}
                    {inquiry.utm_medium && (
                      <Badge variant="outline" className="text-xs">
                        medium: {inquiry.utm_medium}
                      </Badge>
                    )}
                    {inquiry.utm_campaign && (
                      <Badge variant="outline" className="text-xs">
                        campaign: {inquiry.utm_campaign}
                      </Badge>
                    )}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Message */}
          {inquiry.message && (
            <Card className="border-stone-200 bg-white">
              <CardHeader>
                <CardTitle className="text-lg text-stone-900">Mesaj</CardTitle>
              </CardHeader>
              <CardContent>
                <p className="text-sm text-stone-700 whitespace-pre-wrap">
                  {inquiry.message}
                </p>
              </CardContent>
            </Card>
          )}

          {/* Items */}
          {inquiry.items && inquiry.items.length > 0 && (
            <Card className="border-stone-200 bg-white">
              <CardHeader>
                <CardTitle className="text-lg text-stone-900">
                  Talep Edilen Ürünler ({inquiry.items.length})
                </CardTitle>
              </CardHeader>
              <CardContent className="p-0">
                <Table>
                  <TableHeader>
                    <TableRow className="bg-stone-50">
                      <TableHead className="text-stone-600">Model Kodu</TableHead>
                      <TableHead className="text-stone-600">Ürün</TableHead>
                      <TableHead className="text-stone-600">Model Adı</TableHead>
                      <TableHead className="text-stone-600 text-right">Adet</TableHead>
                      <TableHead className="text-stone-600 w-12"></TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {inquiry.items.map((item) => (
                      <TableRow key={item.id}>
                        <TableCell className="font-mono font-medium text-stone-900">
                          {item.model_code_snapshot}
                        </TableCell>
                        <TableCell className="text-stone-700">
                          {item.product_title_tr_snapshot || "-"}
                        </TableCell>
                        <TableCell className="text-stone-600">
                          {item.model_name_tr_snapshot || "-"}
                        </TableCell>
                        <TableCell className="text-right font-medium">
                          {item.qty}
                        </TableCell>
                        <TableCell>
                          {item.product_slug_snapshot && (
                            <Button
                              variant="ghost"
                              size="sm"
                              asChild
                              className="h-8 w-8 p-0"
                            >
                              <Link href={`/catalog/products/${item.product_slug_snapshot}`}>
                                <Package className="h-4 w-4 text-stone-400" />
                              </Link>
                            </Button>
                          )}
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </CardContent>
            </Card>
          )}
        </div>

        {/* Sidebar */}
        <div className="space-y-6">
          {/* Internal Note */}
          <Card className="border-stone-200 bg-white">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-stone-900">İç Not</CardTitle>
              <CardDescription className="text-stone-500">
                Sadece ekip tarafından görülür
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-3">
              <Textarea
                value={noteValue}
                onChange={(e) => setLocalNote(e.target.value)}
                placeholder="Dahili not ekle..."
                rows={4}
                className="resize-none"
              />
              {noteDirty && (
                <Button
                  onClick={handleSaveNote}
                  disabled={updateNoteMutation.isPending}
                  className="w-full"
                >
                  {updateNoteMutation.isPending ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Kaydediliyor...
                    </>
                  ) : (
                    <>
                      <Save className="h-4 w-4 mr-2" />
                      Notu Kaydet
                    </>
                  )}
                </Button>
              )}
            </CardContent>
          </Card>

          {/* Timestamps */}
          <Card className="border-stone-200 bg-white">
            <CardHeader className="pb-3">
              <CardTitle className="text-lg text-stone-900">Zaman Bilgisi</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div>
                <p className="text-xs text-stone-500">Oluşturulma</p>
                <p className="text-sm font-medium text-stone-900">
                  {formatDate(inquiry.created_at)}
                </p>
              </div>
              <div>
                <p className="text-xs text-stone-500">Güncelleme</p>
                <p className="text-sm font-medium text-stone-900">
                  {formatDate(inquiry.updated_at)}
                </p>
              </div>
            </CardContent>
          </Card>

          {/* Legacy Snapshots */}
          {(inquiry.product_slug_snapshot || inquiry.model_code_snapshot) && (
            <Card className="border-stone-200 bg-white">
              <CardHeader className="pb-3">
                <CardTitle className="text-lg text-stone-900">Ürün Referansı</CardTitle>
                <CardDescription className="text-stone-500">
                  Talep formundan
                </CardDescription>
              </CardHeader>
              <CardContent className="space-y-2">
                {inquiry.model_code_snapshot && (
                  <div>
                    <p className="text-xs text-stone-500">Model Kodu</p>
                    <p className="font-mono text-sm text-stone-900">{inquiry.model_code_snapshot}</p>
                  </div>
                )}
                {inquiry.product_slug_snapshot && (
                  <div>
                    <p className="text-xs text-stone-500">Ürün</p>
                    <Link 
                      href={`/catalog/products/${inquiry.product_slug_snapshot}`}
                      className="text-sm text-primary hover:underline flex items-center gap-1"
                    >
                      {inquiry.product_slug_snapshot}
                      <ExternalLink className="h-3 w-3" />
                    </Link>
                  </div>
                )}
              </CardContent>
            </Card>
          )}
        </div>
      </div>
    </AppShell>
  );
}
