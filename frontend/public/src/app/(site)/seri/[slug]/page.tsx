"use client";

import { useState } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ENDPOINTS, fetchProducts, fetchSeries, fetchTaxonomyTree, fetchBrands } from "@/lib/api";
import { Container } from "@/components/layout";
import { ProductGrid } from "@/components/catalog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { ChevronRight, Filter, Tag, ArrowRight } from "lucide-react";
import { TaxonomyNode, Brand } from "@/lib/api/schemas";
import { BrandGrid } from "@/components/catalog/brand-grid";

const getCursorFromUrl = (url?: string | null) => {
  if (!url) return undefined;
  try {
    return new URL(url, ENDPOINTS.PRODUCTS).searchParams.get("cursor") || undefined;
  } catch {
    return undefined;
  }
};

export default function SeriesPage() {
  const params = useParams();
  const searchParams = useSearchParams();
  const router = useRouter();
  const slug = params.slug as string;

  // URL States
  const selectedBrandSlug = searchParams.get("brand");
  const selectedNodeSlug = searchParams.get("node");

  // Fetch Series
  const { data: seriesList = [] } = useQuery({
    queryKey: ["series"],
    queryFn: () => fetchSeries(),
  });
  const series = seriesList.find((s) => s.slug === slug);

  // Fetch Brands
  const { data: brands = [], isLoading: brandsLoading } = useQuery({
    queryKey: ["brands", slug],
    queryFn: () => fetchBrands(slug),
  });

  // Handle Brand Selection
  const handleBrandSelect = (brandSlug: string | null) => {
    const newParams = new URLSearchParams(searchParams.toString());
    if (brandSlug) {
      newParams.set("brand", brandSlug);
    } else {
      newParams.delete("brand");
    }
    newParams.delete("cursor"); // Reset pagination
    router.push(`?${newParams.toString()}`);
  };

  // --- VIEW 1: BRAND SELECTION ---
  // Strictly show this view if no brand is selected
  if (!selectedBrandSlug) {
    return (
      <Container className="py-8 lg:py-12">
        {/* Simplified Header for Brand Screen */}
        <div className="mb-8">
          <nav className="mb-4 text-sm text-muted-foreground">
            <Link href="/" className="hover:text-primary">Ana Sayfa</Link>
            <span className="mx-2">/</span>
            {series?.category_slug && (
              <>
                <Link href={`/kategori/${series.category_slug}`} className="hover:text-primary">
                  {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                  {(series as any).category_name || series.category_slug}
                </Link>
                <span className="mx-2">/</span>
              </>
            )}
            <span className="text-foreground font-medium">{series?.name || slug}</span>
          </nav>

          <h1 className="text-3xl font-bold tracking-tight lg:text-4xl mb-4">
            {series?.name || slug}
          </h1>
          {series?.description_short && (
            <p className="text-lg text-muted-foreground max-w-3xl">
              {series.description_short}
            </p>
          )}
        </div>

        <div className="space-y-6">
          <div className="flex items-center gap-2 text-lg font-semibold text-foreground border-b pb-4">
            <Tag className="h-5 w-5 text-primary" />
            Marka Seçimi
          </div>

          <BrandGrid
            brands={brands}
            isLoading={brandsLoading}
            onSelect={handleBrandSelect}
          />

          {/* Empty State Fallback */}
          {!brandsLoading && brands.length === 0 && (
            <div className="rounded-sm border border-dashed p-8 text-center text-muted-foreground">
              <p className="mb-4">Bu seriye ait listelenecek marka bulunamadı.</p>
              <Button onClick={() => router.push('/urunler')}>
                Tüm Ürünleri Görüntüle
              </Button>
            </div>
          )}
        </div>
      </Container>
    );
  }

  // --- VIEW 2: PRODUCT LISTING ---
  // Only reachable if a brand is selected
  return (
    <ProductListingView
      slug={slug}
      series={series}
      brands={brands}
      selectedBrandSlug={selectedBrandSlug}
      selectedNodeSlug={selectedNodeSlug}
      onBrandChange={handleBrandSelect}
    />
  );
}

// Sub-component for Product View to keep main file clean
function ProductListingView({
  slug,
  series,
  brands,
  selectedBrandSlug,
  selectedNodeSlug,
  onBrandChange
}: {
  slug: string,
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  series: any,
  brands: Brand[],
  selectedBrandSlug: string,
  selectedNodeSlug: string | null,
  onBrandChange: (slug: string | null) => void
}) {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [localSelectedNode, setLocalSelectedNode] = useState(selectedNodeSlug);

  // Sync local state when URL changes
  if (selectedNodeSlug !== localSelectedNode) setLocalSelectedNode(selectedNodeSlug);

  const handleNodeSelect = (nodeSlug: string | null) => {
    setLocalSelectedNode(nodeSlug);
    const newParams = new URLSearchParams(searchParams.toString());
    if (nodeSlug) newParams.set("node", nodeSlug);
    else newParams.delete("node");
    newParams.delete("cursor");
    router.push(`?${newParams.toString()}`);
  };

  const selectedBrand = brands.find(b => b.slug === selectedBrandSlug);

  // Fetch taxonomy
  const { data: taxonomyNodes = [] } = useQuery({
    queryKey: ["taxonomy", slug],
    queryFn: () => fetchTaxonomyTree(slug),
    enabled: !!slug,
  });

  // Fetch products
  const {
    data,
    isLoading: productsLoading,
    isFetchingNextPage,
    fetchNextPage,
    hasNextPage,
  } = useInfiniteQuery({
    queryKey: ["products", slug, localSelectedNode, selectedBrandSlug],
    queryFn: ({ pageParam }) =>
      fetchProducts({
        series: slug,
        node: localSelectedNode || undefined,
        brand: selectedBrandSlug, // Always strictly filter by brand here
        cursor: pageParam,
        page_size: 24,
      }),
    initialPageParam: undefined as string | undefined,
    getNextPageParam: (lastPage) => getCursorFromUrl(lastPage.next),
  });

  const products = data?.pages.flatMap((page) => page.results) || [];

  return (
    <Container className="py-8 lg:py-12">
      {/* Breadcrumb - Extended for Product View */}
      <nav className="mb-6 text-sm text-muted-foreground">
        <Link href="/" className="hover:text-primary">Ana Sayfa</Link>
        <span className="mx-2">/</span>
        {series?.category_slug && (
          <>
            <Link href={`/kategori/${series.category_slug}`} className="hover:text-primary">
              {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
              {(series as any).category_name || series.category_slug}
            </Link>
            <span className="mx-2">/</span>
          </>
        )}
        <Link href={`/seri/${slug}`} onClick={(e) => { e.preventDefault(); onBrandChange(null); }} className="hover:text-primary">
          {series?.name || slug}
        </Link>
        <span className="mx-2">/</span>
        <span className="text-foreground font-medium">{selectedBrand?.name || selectedBrandSlug}</span>
      </nav>

      {/* Header */}
      <div className="mb-10 flex items-center gap-4">
        <div className="h-16 w-2 bg-gradient-to-b from-primary via-primary to-primary/70 shadow-primary-soft" />
        <div>
          <h1 className="text-3xl font-bold lg:text-4xl">
            {selectedBrand?.name} {series?.name}
          </h1>
          <p className="mt-1 text-muted-foreground">
            {selectedBrand?.name} markalı {series?.name || ""} ürünleri listeleniyor
          </p>
        </div>
      </div>

      <div className="lg:grid lg:grid-cols-12 lg:gap-8">
        {/* Sidebar */}
        <aside className="mb-6 lg:col-span-2 lg:mb-0">
          <div className="sticky top-24 space-y-4">
            {/* Selected Brand Box */}
            <div className="rounded-sm border bg-card p-4 shadow-sm">
              <h2 className="mb-3 flex items-center gap-2 font-semibold">
                <Tag className="h-4 w-4 text-primary" />
                Seçili Marka
              </h2>
              <div className="flex flex-col gap-3">
                <div className="font-medium text-lg text-primary">
                  {selectedBrand?.name}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => onBrandChange(null)}
                  className="w-full gap-2 group"
                >
                  <ArrowRight className="h-3.5 w-3.5 rotate-180 transition-transform group-hover:-translate-x-1" />
                  Marka Değiştir
                </Button>
              </div>
            </div>

            {/* Taxonomy Filter */}
            {taxonomyNodes.length > 0 && (
              <div className="rounded-sm border bg-card p-4 shadow-sm">
                <h2 className="mb-4 flex items-center gap-2 font-semibold">
                  <Filter className="h-4 w-4" />
                  Özellik Filtresi
                </h2>
                <ScrollArea className="max-h-[60vh]">
                  <button
                    onClick={() => handleNodeSelect(null)}
                    className={cn(
                      "mb-1 w-full rounded-sm px-3 py-2 text-left text-sm transition-colors",
                      !localSelectedNode
                        ? "bg-primary/10 text-primary font-medium"
                        : "hover:bg-muted text-muted-foreground hover:text-foreground"
                    )}
                  >
                    Tümü
                  </button>
                  <TaxonomyTree
                    nodes={taxonomyNodes}
                    selectedNode={localSelectedNode}
                    onSelect={handleNodeSelect}
                  />
                </ScrollArea>
              </div>
            )}
          </div>
        </aside>

        {/* Products Grid */}
        <div className="lg:col-span-8">
          {/* Active Filters Bar */}
          {localSelectedNode && (
            <div className="mb-6 flex items-center gap-2 text-sm bg-muted/30 p-2 rounded-sm border border-dashed">
              <span className="text-muted-foreground font-medium px-2">Aktif Filtre:</span>
              <span className="inline-flex items-center gap-1.5 rounded-sm bg-primary/10 px-3 py-1 text-primary text-xs font-semibold">
                {findNodeName(taxonomyNodes, localSelectedNode)}
                <button
                  onClick={() => handleNodeSelect(null)}
                  className="ml-1 hover:text-primary/70 focus:outline-none"
                >
                  ×
                </button>
              </span>
            </div>
          )}

          <ProductGrid products={products} isLoading={productsLoading} columns={3} />

          {hasNextPage && (
            <div className="mt-8 text-center">
              <Button
                variant="outline"
                size="lg"
                onClick={() => fetchNextPage()}
                disabled={isFetchingNextPage}
              >
                {isFetchingNextPage ? "Yükleniyor..." : "Daha Fazla Göster"}
              </Button>
            </div>
          )}
        </div>
      </div>
    </Container>
  );
}

// Recursive Taxonomy Tree
function TaxonomyTree({
  nodes,
  selectedNode,
  onSelect,
  depth = 0,
}: {
  nodes: TaxonomyNode[];
  selectedNode: string | null;
  onSelect: (slug: string) => void;
  depth?: number;
}) {
  return (
    <div className="space-y-1">
      {nodes.map((node) => (
        <div key={node.id}>
          <button
            onClick={() => onSelect(node.slug)}
            className={cn(
              "flex w-full items-center gap-2 rounded-sm px-3 py-2 text-left text-sm transition-colors",
              selectedNode === node.slug
                ? "bg-primary/10 text-primary font-medium"
                : "hover:bg-muted text-muted-foreground hover:text-foreground"
            )}
            style={{ paddingLeft: `${depth * 12 + 12}px` }}
          >
            {node.children && node.children.length > 0 && (
              <ChevronRight className="h-3 w-3 shrink-0" />
            )}
            <span className="truncate">{node.name}</span>
          </button>
          {node.children && node.children.length > 0 && (
            <TaxonomyTree
              nodes={node.children}
              selectedNode={selectedNode}
              onSelect={onSelect}
              depth={depth + 1}
            />
          )}
        </div>
      ))}
    </div>
  );
}

function findNodeName(nodes: TaxonomyNode[], slug: string): string {
  for (const node of nodes) {
    if (node.slug === slug) return node.name;
    if (node.children) {
      const found = findNodeName(node.children, slug);
      if (found) return found;
    }
  }
  return slug;
}
