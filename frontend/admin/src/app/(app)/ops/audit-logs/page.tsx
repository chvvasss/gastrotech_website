"use client";

import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import {
  Search,
  Loader2,
  User,
  Package,
  GitBranch,
  Image,
  FileText,
  Edit,
  Trash,
  Plus,
  ArrowRight,
  Filter,
  Trash2,
} from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Label } from "@/components/ui/label";
import { useToast } from "@/hooks/use-toast";
import { opsApi, type AuditLog } from "@/lib/api/ops";

const actionConfig: Record<string, { icon: React.ElementType; color: string; label: string }> = {
  create: { icon: Plus, color: "bg-green-100 text-green-700", label: "Oluşturma" },
  update: { icon: Edit, color: "bg-blue-100 text-blue-700", label: "Güncelleme" },
  delete: { icon: Trash, color: "bg-red-100 text-red-700", label: "Silme" },
  status_change: { icon: ArrowRight, color: "bg-amber-100 text-amber-700", label: "Durum Değişikliği" },
  media_upload: { icon: Image, color: "bg-purple-100 text-purple-700", label: "Medya Yükleme" },
  media_delete: { icon: Trash, color: "bg-red-100 text-red-700", label: "Medya Silme" },
  media_reorder: { icon: ArrowRight, color: "bg-blue-100 text-blue-700", label: "Medya Sıralama" },
  taxonomy_generate: { icon: GitBranch, color: "bg-teal-100 text-teal-700", label: "Taksonomi Üretim" },
  import_apply: { icon: FileText, color: "bg-indigo-100 text-indigo-700", label: "İçe Aktarma" },
  template_apply: { icon: FileText, color: "bg-cyan-100 text-cyan-700", label: "Şablon Uygulama" },
  login: { icon: User, color: "bg-stone-100 text-stone-700", label: "Giriş" },
  logout: { icon: User, color: "bg-stone-100 text-stone-700", label: "Çıkış" },
};

const entityIcons: Record<string, React.ElementType> = {
  product: Package,
  variant: Package,
  media: Image,
  taxonomy: GitBranch,
  user: User,
};

const ALL_VALUE = "__all__";

export default function AuditLogsPage() {
  const { toast } = useToast();
  const queryClient = useQueryClient();
  const [entityType, setEntityType] = useState<string>(ALL_VALUE);
  const [action, setAction] = useState<string>(ALL_VALUE);
  const [actorSearch, setActorSearch] = useState("");
  const [selectedLog, setSelectedLog] = useState<AuditLog | null>(null);
  const [cleanupDialogOpen, setCleanupDialogOpen] = useState(false);
  const [cleanupDays, setCleanupDays] = useState("30");

  // Convert filter values (ALL_VALUE means no filter)
  const entityTypeFilter = entityType === ALL_VALUE ? undefined : entityType;
  const actionFilter = action === ALL_VALUE ? undefined : action;

  // Fetch audit logs
  const { data: logs = [], isLoading, refetch } = useQuery({
    queryKey: ["audit-logs", entityTypeFilter, actionFilter, actorSearch],
    queryFn: () =>
      opsApi.listAuditLogs({
        entity_type: entityTypeFilter,
        action: actionFilter,
        actor: actorSearch || undefined,
      }),
  });

  // Fetch log detail when selected
  const { data: logDetail, isLoading: isLoadingDetail } = useQuery({
    queryKey: ["audit-log", selectedLog?.id],
    queryFn: () => (selectedLog ? opsApi.getAuditLog(selectedLog.id) : null),
    enabled: !!selectedLog,
  });

  // Cleanup mutation
  const cleanupMutation = useMutation({
    mutationFn: (days: number) => opsApi.cleanupAuditLogs(days),
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["audit-logs"] });
      toast({
        title: "Temizleme Başarılı",
        description: `${data.deleted_count} kayıt silindi.`,
      });
      setCleanupDialogOpen(false);
    },
    onError: () => {
      toast({
        title: "Hata",
        description: "Temizleme işlemi başarısız oldu.",
        variant: "destructive",
      });
    },
  });

  const handleCleanup = () => {
    const days = parseInt(cleanupDays);
    if (isNaN(days) || days < 1) {
      toast({
        title: "Geçersiz Gün Sayısı",
        description: "Lütfen geçerli bir gün sayısı girin.",
        variant: "destructive",
      });
      return;
    }
    cleanupMutation.mutate(days);
  };

  return (
    <AppShell
      breadcrumbs={[
        { label: "Operasyonlar" },
        { label: "İşlem Geçmişi" },
      ]}
    >
      <PageHeader
        title="İşlem Geçmişi"
        description="Tüm admin işlemlerinin kaydı ve denetim günlüğü"
        actions={
          <Button
            variant="destructive"
            onClick={() => setCleanupDialogOpen(true)}
          >
            <Trash2 className="h-4 w-4 mr-2" />
            Temizle
          </Button>
        }
      />

      {/* Filters */}
      <Card>
        <CardHeader className="pb-3">
          <CardTitle className="text-base flex items-center gap-2">
            <Filter className="h-4 w-4" />
            Filtreler
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex gap-4 flex-wrap">
            <div className="w-48">
              <Select value={entityType} onValueChange={setEntityType}>
                <SelectTrigger>
                  <SelectValue placeholder="Tüm varlıklar" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_VALUE}>Tüm varlıklar</SelectItem>
                  <SelectItem value="product">Ürün</SelectItem>
                  <SelectItem value="variant">Varyant</SelectItem>
                  <SelectItem value="media">Medya</SelectItem>
                  <SelectItem value="taxonomy">Taksonomi</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="w-48">
              <Select value={action} onValueChange={setAction}>
                <SelectTrigger>
                  <SelectValue placeholder="Tüm işlemler" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value={ALL_VALUE}>Tüm işlemler</SelectItem>
                  <SelectItem value="create">Oluşturma</SelectItem>
                  <SelectItem value="update">Güncelleme</SelectItem>
                  <SelectItem value="delete">Silme</SelectItem>
                  <SelectItem value="status_change">Durum Değişikliği</SelectItem>
                  <SelectItem value="media_upload">Medya Yükleme</SelectItem>
                  <SelectItem value="import_apply">İçe Aktarma</SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div className="flex-1 min-w-48">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-stone-400" />
                <Input
                  placeholder="Kullanıcı ara..."
                  value={actorSearch}
                  onChange={(e) => setActorSearch(e.target.value)}
                  className="pl-9"
                />
              </div>
            </div>
            <Button variant="outline" onClick={() => refetch()}>
              Yenile
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* Logs Table */}
      <Card>
        <CardContent className="p-0">
          {isLoading ? (
            <div className="flex justify-center py-12">
              <Loader2 className="h-8 w-8 animate-spin text-stone-400" />
            </div>
          ) : logs.length === 0 ? (
            <div className="text-center py-12 text-stone-500">
              Kayıt bulunamadı
            </div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Tarih</TableHead>
                  <TableHead>Kullanıcı</TableHead>
                  <TableHead>İşlem</TableHead>
                  <TableHead>Varlık</TableHead>
                  <TableHead>Etiket</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {logs.map((log) => {
                  const actionCfg = actionConfig[log.action] || {
                    icon: Edit,
                    color: "bg-stone-100 text-stone-700",
                    label: log.action,
                  };
                  const ActionIcon = actionCfg.icon;
                  const EntityIcon = entityIcons[log.entity_type] || Package;

                  return (
                    <TableRow
                      key={log.id}
                      className="cursor-pointer hover:bg-stone-50"
                      onClick={() => setSelectedLog(log as AuditLog)}
                    >
                      <TableCell className="text-sm text-stone-500">
                        {new Date(log.created_at).toLocaleString("tr-TR")}
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <User className="h-4 w-4 text-stone-400" />
                          <span className="text-sm">{log.actor_email || "Sistem"}</span>
                        </div>
                      </TableCell>
                      <TableCell>
                        <Badge className={actionCfg.color}>
                          <ActionIcon className="h-3 w-3 mr-1" />
                          {actionCfg.label}
                        </Badge>
                      </TableCell>
                      <TableCell>
                        <div className="flex items-center gap-2">
                          <EntityIcon className="h-4 w-4 text-stone-400" />
                          <span className="text-sm capitalize">{log.entity_type}</span>
                          <code className="text-xs bg-stone-100 px-1 rounded">
                            {log.entity_id.slice(0, 8)}...
                          </code>
                        </div>
                      </TableCell>
                      <TableCell className="text-sm font-medium">
                        {log.entity_label || "-"}
                      </TableCell>
                    </TableRow>
                  );
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      {/* Detail Dialog */}
      <Dialog open={!!selectedLog} onOpenChange={() => setSelectedLog(null)}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle>İşlem Detayı</DialogTitle>
            <DialogDescription>
              {selectedLog && new Date(selectedLog.created_at).toLocaleString("tr-TR")}
            </DialogDescription>
          </DialogHeader>

          {isLoadingDetail ? (
            <div className="flex justify-center py-8">
              <Loader2 className="h-8 w-8 animate-spin text-stone-400" />
            </div>
          ) : logDetail ? (
            <div className="space-y-4">
              {/* Summary */}
              <div className="grid grid-cols-2 gap-4">
                <div className="p-3 bg-stone-50 rounded-lg">
                  <div className="text-xs text-stone-500 mb-1">Kullanıcı</div>
                  <div className="font-medium">{logDetail.actor_email || "Sistem"}</div>
                </div>
                <div className="p-3 bg-stone-50 rounded-lg">
                  <div className="text-xs text-stone-500 mb-1">İşlem</div>
                  <div className="font-medium capitalize">{actionConfig[logDetail.action]?.label || logDetail.action}</div>
                </div>
                <div className="p-3 bg-stone-50 rounded-lg">
                  <div className="text-xs text-stone-500 mb-1">Varlık</div>
                  <div className="font-medium capitalize">{logDetail.entity_type}</div>
                </div>
                <div className="p-3 bg-stone-50 rounded-lg">
                  <div className="text-xs text-stone-500 mb-1">Varlık ID</div>
                  <code className="text-xs">{logDetail.entity_id}</code>
                </div>
              </div>

              {/* Entity Label */}
              {logDetail.entity_label && (
                <div className="p-3 bg-stone-50 rounded-lg">
                  <div className="text-xs text-stone-500 mb-1">Etiket</div>
                  <div className="font-medium">{logDetail.entity_label}</div>
                </div>
              )}

              {/* Before/After */}
              {Object.keys(logDetail.before_json || {}).length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">Önceki Değerler:</div>
                  <pre className="p-3 bg-red-50 border border-red-200 rounded-lg text-xs overflow-auto">
                    {JSON.stringify(logDetail.before_json, null, 2)}
                  </pre>
                </div>
              )}

              {Object.keys(logDetail.after_json || {}).length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">Sonraki Değerler:</div>
                  <pre className="p-3 bg-green-50 border border-green-200 rounded-lg text-xs overflow-auto">
                    {JSON.stringify(logDetail.after_json, null, 2)}
                  </pre>
                </div>
              )}

              {/* Metadata */}
              {Object.keys(logDetail.metadata || {}).length > 0 && (
                <div>
                  <div className="text-sm font-medium mb-2">Ek Bilgiler:</div>
                  <pre className="p-3 bg-stone-100 rounded-lg text-xs overflow-auto">
                    {JSON.stringify(logDetail.metadata, null, 2)}
                  </pre>
                </div>
              )}

              {/* Request Info */}
              <div className="text-xs text-stone-400 pt-2 border-t">
                <p>IP: {logDetail.ip_address || "Bilinmiyor"}</p>
                {logDetail.user_agent && (
                  <p className="truncate" title={logDetail.user_agent}>
                    User-Agent: {logDetail.user_agent}
                  </p>
                )}
              </div>
            </div>
          ) : null}
        </DialogContent>
      </Dialog>

      {/* Cleanup Confirmation Dialog */}
      <AlertDialog open={cleanupDialogOpen} onOpenChange={setCleanupDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>İşlem Geçmişini Temizle</AlertDialogTitle>
            <AlertDialogDescription>
              Belirtilen gün sayısından eski tüm kayıtlar silinecek. Bu işlem geri alınamaz.
            </AlertDialogDescription>
          </AlertDialogHeader>

          <div className="py-4">
            <Label htmlFor="cleanup-days">Kaç gün önceki kayıtları silelim?</Label>
            <Select value={cleanupDays} onValueChange={setCleanupDays}>
              <SelectTrigger id="cleanup-days" className="mt-2">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="7">7 gün önceki</SelectItem>
                <SelectItem value="30">30 gün önceki</SelectItem>
                <SelectItem value="60">60 gün önceki</SelectItem>
                <SelectItem value="90">90 gün önceki</SelectItem>
                <SelectItem value="180">180 gün önceki</SelectItem>
              </SelectContent>
            </Select>
          </div>

          <AlertDialogFooter>
            <AlertDialogCancel>İptal</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleCleanup}
              className="bg-red-600 hover:bg-red-700"
              disabled={cleanupMutation.isPending}
            >
              {cleanupMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Temizle
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>
    </AppShell>
  );
}
