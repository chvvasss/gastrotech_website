"use client";

import { useState, useMemo, useEffect, useCallback } from "react";
import Link from "next/link";
import {
  Search,
  Loader2,
  Wand2,
  X,
  Eye,
  CheckCircle,
  AlertCircle,
  Copy,
  ExternalLink,
  Plus,
  Edit2,
  Trash2,
  ChevronRight,
  ChevronDown,
  FolderTree,
  MoreHorizontal,
  Tag,
  Globe,
  Image as ImageIcon,
} from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { Label } from "@/components/ui/label";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
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
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "@/components/ui/tabs";
import { useToast } from "@/hooks/use-toast";
import { getMediaUrl as buildMediaUrl } from "@/lib/media-url";
import { useNav } from "@/hooks/use-navigation";
import { useTaxonomyTree, useGenerateProductsFromLeafNodes } from "@/hooks/use-taxonomy";
import {
  useAdminTaxonomyNodes,
  useCreateTaxonomyNode,
  useUpdateTaxonomyNode,
  useDeleteTaxonomyNode,
} from "@/hooks/use-admin-taxonomy";
import { SeriesSelect, ALL_SERIES, MissingEndpointBanner } from "@/components/catalog";
import { checkEndpointExists } from "@/lib/api/capabilities";
import type { TaxonomyNode } from "@/types/api";
import type { AdminTaxonomyNode, CreateTaxonomyNodePayload, UpdateTaxonomyNodePayload } from "@/lib/api/admin-taxonomy";
import {
  useBrands,
  useCreateBrand,
  useUpdateBrand,
  useDeleteBrand,
} from "@/hooks/use-admin-brands";
import type { AdminBrand, CreateBrandPayload, UpdateBrandPayload } from "@/lib/api/admin-brands";
import { Switch } from "@/components/ui/switch";
import { Textarea } from "@/components/ui/textarea";
import Image from "next/image";

// =============================================================================
// Types
// =============================================================================

interface PreviewItem {
  node_slug: string;
  node_path: string;
  expected_slug: string;
  status: "will_create" | "exists";
  existing_product_slug: string | null;
}

interface GenerationResult {
  created: number;
  skipped_existing: number;
  skipped_non_leaf: number;
  created_slugs: string[];
  skipped_existing_slugs: string[];
  preview: PreviewItem[];
  errors: Array<{ slug: string; error: string }>;
  dry_run: boolean;
}

// =============================================================================
// Tree Node Component
// =============================================================================

interface TreeNodeProps {
  node: TaxonomyNode;
  level: number;
  selectedLeafSlugs: Set<string>;
  onToggleSelect: (slug: string) => void;
  onEdit: (node: TaxonomyNode) => void;
  onDelete: (node: TaxonomyNode) => void;
  onAddChild: (parentId: string, parentName: string) => void;
  searchTerm: string;
}

function TreeNode({
  node,
  level,
  selectedLeafSlugs,
  onToggleSelect,
  onEdit,
  onDelete,
  onAddChild,
  searchTerm,
}: TreeNodeProps) {
  const [isOpen, setIsOpen] = useState(level < 2 || !!searchTerm);
  const hasChildren = node.children && node.children.length > 0;
  const isLeaf = !hasChildren;
  const isSelected = selectedLeafSlugs.has(node.slug);

  // Filter by search
  const matchesSearch = searchTerm
    ? node.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
    node.slug.toLowerCase().includes(searchTerm.toLowerCase())
    : true;

  const childrenMatch = (node.children || []).some(
    (c) =>
      c.name.toLowerCase().includes(searchTerm.toLowerCase()) ||
      c.slug.toLowerCase().includes(searchTerm.toLowerCase())
  );

  if (searchTerm && !matchesSearch && !childrenMatch) {
    return null;
  }

  return (
    <div>
      <div
        className={`flex items-center gap-2 py-1.5 px-2 rounded-lg group transition-colors ${isSelected ? "bg-primary/10" : "hover:bg-stone-50"
          }`}
        style={{ paddingLeft: `${level * 16 + 8}px` }}
      >
        {/* Expand/Collapse */}
        <button
          onClick={() => setIsOpen(!isOpen)}
          className={`p-0.5 rounded hover:bg-stone-200 transition-colors ${!hasChildren ? "invisible" : ""
            }`}
        >
          {isOpen ? (
            <ChevronDown className="h-4 w-4 text-stone-500" />
          ) : (
            <ChevronRight className="h-4 w-4 text-stone-500" />
          )}
        </button>

        {/* Checkbox for leaves */}
        {isLeaf && (
          <Checkbox
            checked={isSelected}
            onCheckedChange={() => onToggleSelect(node.slug)}
            className="h-5 w-5 border-2 border-stone-300 data-[state=checked]:bg-green-500 data-[state=checked]:border-green-500 rounded-md shadow-sm transition-all duration-150 hover:border-green-400 hover:shadow-md"
          />
        )}

        {/* Icon */}
        <FolderTree
          className={`h-4 w-4 ${isLeaf ? "text-green-500" : "text-stone-400"}`}
        />

        {/* Name */}
        <span
          className={`flex-1 text-sm ${matchesSearch && searchTerm ? "font-semibold text-primary" : "text-stone-700"
            }`}
        >
          {node.name}
        </span>

        {/* Leaf badge */}
        {isLeaf && (
          <Badge className="text-xs bg-green-100 text-green-700 border-green-200 hover:bg-green-100">
            Yaprak
          </Badge>
        )}

        {/* Actions */}
        <div className="opacity-0 group-hover:opacity-100 transition-opacity">
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="icon" className="h-7 w-7">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onEdit(node)}>
                <Edit2 className="h-4 w-4 mr-2" />
                Düzenle
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onAddChild(node.id, node.name)}>
                <Plus className="h-4 w-4 mr-2" />
                Alt Düğüm Ekle
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={() => onDelete(node)}
                className="text-red-600 focus:text-red-600"
              >
                <Trash2 className="h-4 w-4 mr-2" />
                Sil
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Children */}
      {isOpen && hasChildren && (
        <div>
          {node.children.map((child) => (
            <TreeNode
              key={child.id}
              node={child}
              level={level + 1}
              selectedLeafSlugs={selectedLeafSlugs}
              onToggleSelect={onToggleSelect}
              onEdit={onEdit}
              onDelete={onDelete}
              onAddChild={onAddChild}
              searchTerm={searchTerm}
            />
          ))}
        </div>
      )}
    </div>
  );
}

// =============================================================================
// Main Page Component
// =============================================================================

export default function TaxonomyPage() {
  const { toast } = useToast();
  const [selectedSeries, setSelectedSeries] = useState<string>(ALL_SERIES);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedLeafSlugs, setSelectedLeafSlugs] = useState<Set<string>>(new Set());
  const [canGenerateProducts, setCanGenerateProducts] = useState<boolean | null>(null);
  const [activeTab, setActiveTab] = useState<"tree" | "generate">("tree");

  // Node CRUD state
  const [nodeFormOpen, setNodeFormOpen] = useState(false);
  const [deleteDialogOpen, setDeleteDialogOpen] = useState(false);
  const [editingNode, setEditingNode] = useState<TaxonomyNode | null>(null);
  const [deletingNode, setDeletingNode] = useState<TaxonomyNode | null>(null);
  const [parentForNew, setParentForNew] = useState<{ id: string; name: string } | null>(null);

  // Node form state
  const [nodeFormData, setNodeFormData] = useState<CreateTaxonomyNodePayload>({
    name: "",
    slug: "",
    series_slug: "",
    parent_id: null,
    order: 0,
  });

  // Preview/Generate state
  const [previewModalOpen, setPreviewModalOpen] = useState(false);
  const [resultModalOpen, setResultModalOpen] = useState(false);
  const [previewData, setPreviewData] = useState<GenerationResult | null>(null);
  const [resultData, setResultData] = useState<GenerationResult | null>(null);
  const [newProductStatus, setNewProductStatus] = useState<"draft" | "active">("draft");
  const [isPreviewLoading, setIsPreviewLoading] = useState(false);

  const { data: categories, isLoading: navLoading } = useNav();
  const { data: taxonomyTree, isLoading: treeLoading, refetch: refetchTree } = useTaxonomyTree(
    selectedSeries !== ALL_SERIES ? selectedSeries : null
  );

  const generateMutation = useGenerateProductsFromLeafNodes();
  const createNodeMutation = useCreateTaxonomyNode();
  const updateNodeMutation = useUpdateTaxonomyNode();
  const deleteNodeMutation = useDeleteTaxonomyNode();

  // Brand state
  const [brandSearchTerm, setBrandSearchTerm] = useState("");
  const [brandFormOpen, setBrandFormOpen] = useState(false);
  const [brandDeleteDialogOpen, setBrandDeleteDialogOpen] = useState(false);
  const [editingBrand, setEditingBrand] = useState<AdminBrand | null>(null);
  const [deletingBrand, setDeletingBrand] = useState<AdminBrand | null>(null);
  const [brandFormData, setBrandFormData] = useState<CreateBrandPayload>({
    name: "",
    slug: "",
    description: "",
    website_url: "",
    is_active: true,
    order: 0,
  });

  // Brand hooks
  const { data: brands, isLoading: brandsLoading } = useBrands();
  const createBrandMutation = useCreateBrand();
  const updateBrandMutation = useUpdateBrand();
  const deleteBrandMutation = useDeleteBrand();

  // Check if endpoint exists
  useEffect(() => {
    checkEndpointExists("POST", "/admin/taxonomy/generate-products/").then(
      setCanGenerateProducts
    );
  }, []);

  // Clear selection when series changes
  useEffect(() => {
    setSelectedLeafSlugs(new Set());
    setSearchTerm("");
  }, [selectedSeries]);

  // ==========================================================================
  // Handlers - Node Selection
  // ==========================================================================

  const handleToggleSelect = (slug: string) => {
    setSelectedLeafSlugs((prev) => {
      const newSet = new Set(prev);
      if (newSet.has(slug)) {
        newSet.delete(slug);
      } else {
        newSet.add(slug);
      }
      return newSet;
    });
  };

  const handleClearSelection = () => {
    setSelectedLeafSlugs(new Set());
  };

  // ==========================================================================
  // Handlers - Node CRUD
  // ==========================================================================

  const handleOpenCreateNode = (parentId?: string, parentName?: string) => {
    setEditingNode(null);
    setParentForNew(parentId ? { id: parentId, name: parentName || "" } : null);
    setNodeFormData({
      name: "",
      slug: "",
      series_slug: selectedSeries !== ALL_SERIES ? selectedSeries : "",
      parent_id: parentId || null,
      order: 0,
    });
    setNodeFormOpen(true);
  };

  const handleOpenEditNode = (node: TaxonomyNode) => {
    setEditingNode(node);
    setParentForNew(null);
    setNodeFormData({
      name: node.name,
      slug: node.slug,
      series_slug: selectedSeries !== ALL_SERIES ? selectedSeries : "",
      parent_id: node.parent_slug ? undefined : null,
      order: node.order,
    });
    setNodeFormOpen(true);
  };

  const handleOpenDeleteNode = (node: TaxonomyNode) => {
    setDeletingNode(node);
    setDeleteDialogOpen(true);
  };

  const handleSubmitNode = async () => {
    try {
      if (editingNode) {
        await updateNodeMutation.mutateAsync({
          id: editingNode.id,
          payload: {
            name: nodeFormData.name,
            slug: nodeFormData.slug || undefined,
            order: nodeFormData.order,
          } as UpdateTaxonomyNodePayload,
        });
        toast({ title: "Düğüm güncellendi" });
      } else {
        await createNodeMutation.mutateAsync(nodeFormData);
        toast({ title: "Düğüm oluşturuldu" });
      }
      setNodeFormOpen(false);
      refetchTree();
    } catch (error) {
      toast({
        title: "Hata",
        description: "İşlem başarısız oldu",
        variant: "destructive",
      });
    }
  };

  const handleDeleteNode = async () => {
    if (!deletingNode) return;
    try {
      await deleteNodeMutation.mutateAsync(deletingNode.id);
      toast({ title: "Düğüm silindi" });
      setDeleteDialogOpen(false);
      refetchTree();
    } catch (error) {
      toast({
        title: "Hata",
        description: "Silme işlemi başarısız oldu",
        variant: "destructive",
      });
    }
  };

  // ==========================================================================
  // Handlers - Product Generation
  // ==========================================================================

  const handlePreview = useCallback(async () => {
    if (!canGenerateProducts) return;
    if (selectedSeries === ALL_SERIES || selectedLeafSlugs.size === 0) return;

    setIsPreviewLoading(true);
    try {
      const result = await generateMutation.mutateAsync({
        series: selectedSeries,
        leaf_slugs: Array.from(selectedLeafSlugs),
        dry_run: true,
        status: newProductStatus,
      });
      setPreviewData(result as GenerationResult);
      setPreviewModalOpen(true);
    } catch {
      toast({
        title: "Hata",
        description: "Önizleme alınamadı",
        variant: "destructive",
      });
    } finally {
      setIsPreviewLoading(false);
    }
  }, [canGenerateProducts, selectedSeries, selectedLeafSlugs, newProductStatus, generateMutation, toast]);

  const handleGenerate = useCallback(async () => {
    if (!canGenerateProducts) return;
    if (selectedSeries === ALL_SERIES || selectedLeafSlugs.size === 0) return;

    try {
      const result = await generateMutation.mutateAsync({
        series: selectedSeries,
        leaf_slugs: Array.from(selectedLeafSlugs),
        dry_run: false,
        status: newProductStatus,
      });

      setResultData(result as GenerationResult);
      setPreviewModalOpen(false);
      setResultModalOpen(true);
      setSelectedLeafSlugs(new Set());

      toast({
        title: "Ürün sayfaları oluşturuldu",
        description: `${result.created} oluşturuldu, ${result.skipped_existing} mevcut`,
      });
    } catch {
      toast({
        title: "Hata",
        description: "Ürün sayfaları oluşturulamadı",
        variant: "destructive",
      });
    }
  }, [canGenerateProducts, selectedSeries, selectedLeafSlugs, newProductStatus, generateMutation, toast]);

  const handleCopyReport = useCallback(() => {
    if (!resultData) return;

    const lines = [
      "=== Ürün Oluşturma Raporu ===",
      `Oluşturulan: ${resultData.created}`,
      `Mevcut (atlandı): ${resultData.skipped_existing}`,
      "",
      "Oluşturulan ürünler:",
      ...resultData.created_slugs.map((s) => `  - ${s}`),
      "",
      "Mevcut ürünler:",
      ...resultData.skipped_existing_slugs.map((s) => `  - ${s}`),
    ];

    if (resultData.errors.length > 0) {
      lines.push("", "Hatalar:");
      resultData.errors.forEach((e) => lines.push(`  - ${e.slug}: ${e.error}`));
    }

    navigator.clipboard.writeText(lines.join("\n"));
    toast({ title: "Rapor kopyalandı" });
  }, [resultData, toast]);

  const selectedLeafsList = useMemo(() => {
    return Array.from(selectedLeafSlugs);
  }, [selectedLeafSlugs]);

  const previewCounts = useMemo(() => {
    if (!previewData?.preview) return { willCreate: 0, exists: 0 };
    return {
      willCreate: previewData.preview.filter((p) => p.status === "will_create").length,
      exists: previewData.preview.filter((p) => p.status === "exists").length,
    };
  }, [previewData]);

  const isNodePending = createNodeMutation.isPending || updateNodeMutation.isPending;

  const getMediaUrlById = (id?: string | null) => {
    if (!id) return null;
    return buildMediaUrl(`/api/v1/media/${id}/file/`);
  };

  return (
    <AppShell
      breadcrumbs={[
        { label: "Katalog", href: "/catalog/products" },
        { label: "Taksonomi" },
      ]}
    >
      <PageHeader
        title="Taksonomi Yönetimi"
        description="Seri bazlı taksonomi ağacını yönetin ve ürün sayfaları oluşturun"
        actions={
          selectedSeries !== ALL_SERIES && (
            <Button onClick={() => handleOpenCreateNode()}>
              <Plus className="h-4 w-4 mr-2" />
              Yeni Düğüm
            </Button>
          )
        }
      />

      {/* Controls Row */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <SeriesSelect
          value={selectedSeries}
          onValueChange={setSelectedSeries}
          categories={categories}
          isLoading={navLoading}
          placeholder="Seri seçin..."
          className="w-[220px]"
        />

        {selectedSeries !== ALL_SERIES && (
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
            <Input
              placeholder="Düğüm ara..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-10 bg-white border-stone-200"
            />
          </div>
        )}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Tree Panel */}
        <Card className="lg:col-span-2 border-stone-200 bg-white">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg text-stone-900 flex items-center gap-2">
              <FolderTree className="h-5 w-5" />
              Taksonomi Ağacı
              {taxonomyTree && taxonomyTree.length > 0 && (
                <Badge variant="secondary" className="ml-2">
                  {taxonomyTree.length} kök düğüm
                </Badge>
              )}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {selectedSeries === ALL_SERIES ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <div className="h-16 w-16 rounded-full bg-stone-100 flex items-center justify-center mb-4">
                  <Search className="h-8 w-8 text-stone-400" />
                </div>
                <p className="text-stone-500 font-medium">Seri Seçin</p>
                <p className="text-sm text-stone-400 mt-1">
                  Taksonomi ağacını görüntülemek için bir seri seçin
                </p>
              </div>
            ) : treeLoading ? (
              <div className="space-y-2">
                {[...Array(8)].map((_, i) => (
                  <Skeleton key={i} className="h-8 w-full" />
                ))}
              </div>
            ) : !taxonomyTree || taxonomyTree.length === 0 ? (
              <div className="flex flex-col items-center justify-center py-12 text-center">
                <FolderTree className="h-12 w-12 text-stone-300 mb-4" />
                <p className="text-stone-500 font-medium">Henüz düğüm yok</p>
                <p className="text-sm text-stone-400 mt-1">
                  Bu seri için ilk taksonomi düğümünü ekleyin
                </p>
                <Button
                  variant="outline"
                  className="mt-4"
                  onClick={() => handleOpenCreateNode()}
                >
                  <Plus className="h-4 w-4 mr-2" />
                  İlk Düğümü Ekle
                </Button>
              </div>
            ) : (
              <div className="max-h-[600px] overflow-y-auto">
                {taxonomyTree.map((node) => (
                  <TreeNode
                    key={node.id}
                    node={node}
                    level={0}
                    selectedLeafSlugs={selectedLeafSlugs}
                    onToggleSelect={handleToggleSelect}
                    onEdit={handleOpenEditNode}
                    onDelete={handleOpenDeleteNode}
                    onAddChild={handleOpenCreateNode}
                    searchTerm={searchTerm}
                  />
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* Selection Panel */}
        <Card className="border-stone-200 bg-white">
          <CardHeader className="pb-3">
            <CardTitle className="text-lg text-stone-900 flex items-center justify-between">
              <span>Ürün Oluşturma</span>
              <Badge variant="secondary" className="ml-2">
                {selectedLeafSlugs.size} seçili
              </Badge>
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Missing endpoint banner */}
            {canGenerateProducts === false && (
              <MissingEndpointBanner
                endpoint="POST /api/v1/admin/taxonomy/generate-products/"
                description="Endpoint mevcut değil"
                className="mb-4"
              />
            )}

            {/* Options */}
            {selectedLeafSlugs.size > 0 && (
              <div className="p-3 bg-stone-50 rounded-lg space-y-3">
                <div className="flex items-center justify-between">
                  <Label htmlFor="status" className="text-sm text-stone-600">
                    Yeni ürün durumu
                  </Label>
                  <Select
                    value={newProductStatus}
                    onValueChange={(v) => setNewProductStatus(v as "draft" | "active")}
                  >
                    <SelectTrigger className="w-[100px] h-8 text-sm">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="draft">Taslak</SelectItem>
                      <SelectItem value="active">Aktif</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>
            )}

            {/* Action buttons */}
            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handlePreview}
                disabled={
                  selectedLeafSlugs.size === 0 ||
                  selectedSeries === ALL_SERIES ||
                  isPreviewLoading ||
                  canGenerateProducts === false
                }
                className="flex-1"
              >
                {isPreviewLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : (
                  <>
                    <Eye className="h-4 w-4 mr-2" />
                    Önizle
                  </>
                )}
              </Button>
              <Button
                variant="outline"
                onClick={handleClearSelection}
                disabled={selectedLeafSlugs.size === 0}
              >
                <X className="h-4 w-4" />
              </Button>
            </div>

            {/* Selected leaves list */}
            {selectedLeafsList.length > 0 ? (
              <div className="space-y-2 max-h-[400px] overflow-y-auto">
                {selectedLeafsList.map((slug) => (
                  <div
                    key={slug}
                    className="flex items-center justify-between py-1.5 px-2 rounded bg-stone-50"
                  >
                    <span className="text-sm text-stone-700 truncate">{slug}</span>
                    <button
                      onClick={() => handleToggleSelect(slug)}
                      className="p-0.5 hover:bg-stone-200 rounded transition-colors"
                    >
                      <X className="h-3.5 w-3.5 text-stone-500" />
                    </button>
                  </div>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-400 text-center py-4">
                Yaprak düğümleri seçmek için checkbox&apos;ları kullanın
              </p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Node Create/Edit Dialog */}
      <Dialog open={nodeFormOpen} onOpenChange={setNodeFormOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {editingNode ? "Düğüm Düzenle" : "Yeni Düğüm"}
            </DialogTitle>
            <DialogDescription>
              {editingNode
                ? "Düğüm bilgilerini güncelleyin"
                : parentForNew
                  ? `"${parentForNew.name}" altına yeni düğüm ekleyin`
                  : "Kök düzeyde yeni düğüm ekleyin"}
            </DialogDescription>
          </DialogHeader>

          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label htmlFor="node-name">Düğüm Adı *</Label>
              <Input
                id="node-name"
                value={nodeFormData.name}
                onChange={(e) =>
                  setNodeFormData({ ...nodeFormData, name: e.target.value })
                }
                placeholder="örn: Gazlı Ocaklar"
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="node-slug">Slug</Label>
              <Input
                id="node-slug"
                value={nodeFormData.slug}
                onChange={(e) =>
                  setNodeFormData({ ...nodeFormData, slug: e.target.value })
                }
                placeholder="otomatik oluşturulur"
              />
              <p className="text-xs text-stone-500">
                Boş bırakılırsa otomatik oluşturulur
              </p>
            </div>

            <div className="space-y-2">
              <Label htmlFor="node-order">Sıra</Label>
              <Input
                id="node-order"
                type="number"
                value={nodeFormData.order}
                onChange={(e) =>
                  setNodeFormData({
                    ...nodeFormData,
                    order: parseInt(e.target.value) || 0,
                  })
                }
              />
            </div>
          </div>

          <DialogFooter>
            <Button variant="outline" onClick={() => setNodeFormOpen(false)}>
              İptal
            </Button>
            <Button
              onClick={handleSubmitNode}
              disabled={isNodePending || !nodeFormData.name}
            >
              {isNodePending && <Loader2 className="h-4 w-4 mr-2 animate-spin" />}
              {editingNode ? "Güncelle" : "Oluştur"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Delete Node Confirmation */}
      <AlertDialog open={deleteDialogOpen} onOpenChange={setDeleteDialogOpen}>
        <AlertDialogContent>
          <AlertDialogHeader>
            <AlertDialogTitle>Düğümü Sil</AlertDialogTitle>
            <AlertDialogDescription>
              <strong>{deletingNode?.name}</strong> düğümünü silmek istediğinizden
              emin misiniz? Alt düğümler de silinecek. Bu işlem geri alınamaz.
            </AlertDialogDescription>
          </AlertDialogHeader>
          <AlertDialogFooter>
            <AlertDialogCancel>İptal</AlertDialogCancel>
            <AlertDialogAction
              onClick={handleDeleteNode}
              className="bg-red-600 hover:bg-red-700"
              disabled={deleteNodeMutation.isPending}
            >
              {deleteNodeMutation.isPending && (
                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
              )}
              Sil
            </AlertDialogAction>
          </AlertDialogFooter>
        </AlertDialogContent>
      </AlertDialog>

      {/* Preview Modal */}
      <Dialog open={previewModalOpen} onOpenChange={setPreviewModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle>Ürün Oluşturma Önizlemesi</DialogTitle>
            <DialogDescription>
              Aşağıdaki ürün sayfaları oluşturulacak. Mevcut olanlar atlanacak.
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-4 py-2">
            <Badge className="bg-green-100 text-green-800">
              <CheckCircle className="h-3 w-3 mr-1" />
              {previewCounts.willCreate} oluşturulacak
            </Badge>
            <Badge variant="secondary">{previewCounts.exists} mevcut</Badge>
          </div>

          <div className="flex-1 overflow-y-auto space-y-2 py-2">
            {previewData?.preview?.map((item) => (
              <div
                key={item.node_slug}
                className={`flex items-center justify-between p-3 rounded-lg border ${item.status === "will_create"
                  ? "bg-green-50 border-green-200"
                  : "bg-stone-50 border-stone-200"
                  }`}
              >
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium text-stone-900 truncate">
                    {item.node_path}
                  </p>
                  <p className="text-xs font-mono text-stone-500 truncate">
                    {item.expected_slug}
                  </p>
                </div>
                <div className="ml-2">
                  {item.status === "will_create" ? (
                    <Badge className="bg-green-100 text-green-800 text-xs">
                      Oluşturulacak
                    </Badge>
                  ) : (
                    <Badge variant="secondary" className="text-xs">
                      Mevcut
                    </Badge>
                  )}
                </div>
              </div>
            ))}
          </div>

          <DialogFooter className="pt-4 border-t">
            <Button variant="outline" onClick={() => setPreviewModalOpen(false)}>
              İptal
            </Button>
            <Button
              onClick={handleGenerate}
              disabled={generateMutation.isPending || previewCounts.willCreate === 0}
            >
              {generateMutation.isPending ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Oluşturuluyor...
                </>
              ) : (
                <>
                  <Wand2 className="h-4 w-4 mr-2" />
                  {previewCounts.willCreate} Ürün Oluştur
                </>
              )}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Results Modal */}
      <Dialog open={resultModalOpen} onOpenChange={setResultModalOpen}>
        <DialogContent className="max-w-2xl max-h-[80vh] overflow-hidden flex flex-col">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <CheckCircle className="h-5 w-5 text-green-600" />
              Oluşturma Tamamlandı
            </DialogTitle>
            <DialogDescription>
              {resultData?.created} ürün sayfası başarıyla oluşturuldu.
            </DialogDescription>
          </DialogHeader>

          <div className="flex gap-4 py-2">
            <Badge className="bg-green-100 text-green-800">
              {resultData?.created} oluşturuldu
            </Badge>
            <Badge variant="secondary">{resultData?.skipped_existing} atlandı</Badge>
            {resultData?.errors && resultData.errors.length > 0 && (
              <Badge className="bg-red-100 text-red-800">
                <AlertCircle className="h-3 w-3 mr-1" />
                {resultData.errors.length} hata
              </Badge>
            )}
          </div>

          <div className="flex-1 overflow-y-auto space-y-4 py-2">
            {/* Created Products */}
            {resultData?.created_slugs && resultData.created_slugs.length > 0 && (
              <div>
                <p className="text-sm font-medium text-stone-700 mb-2">
                  Oluşturulan Ürünler:
                </p>
                <div className="space-y-1">
                  {resultData.created_slugs.map((slug) => (
                    <Link
                      key={slug}
                      href={`/catalog/products/${slug}`}
                      className="flex items-center justify-between p-2 rounded bg-green-50 hover:bg-green-100 transition-colors"
                    >
                      <span className="text-sm font-mono text-stone-700">{slug}</span>
                      <ExternalLink className="h-4 w-4 text-stone-400" />
                    </Link>
                  ))}
                </div>
              </div>
            )}

            {/* Errors */}
            {resultData?.errors && resultData.errors.length > 0 && (
              <div>
                <p className="text-sm font-medium text-red-700 mb-2">Hatalar:</p>
                <div className="space-y-1">
                  {resultData.errors.map((e, i) => (
                    <div key={i} className="p-2 rounded bg-red-50 text-sm">
                      <span className="font-mono text-red-800">{e.slug}</span>
                      <span className="text-red-600 ml-2">{e.error}</span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>

          <DialogFooter className="pt-4 border-t gap-2">
            <Button variant="outline" onClick={handleCopyReport}>
              <Copy className="h-4 w-4 mr-2" />
              Raporu Kopyala
            </Button>
            <Button onClick={() => setResultModalOpen(false)}>Kapat</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </AppShell>
  );
}
