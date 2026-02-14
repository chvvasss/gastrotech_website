"use client";

import { useState } from "react";
import { useInfiniteQuery, useQuery } from "@tanstack/react-query";
import { useParams, useSearchParams, useRouter } from "next/navigation";
import Link from "next/link";
import { ENDPOINTS, fetchProducts, fetchBrands, fetchSeries, fetchCategoriesTree, fetchTaxonomyTree } from "@/lib/api";
import { Container } from "@/components/layout";
import { ProductGrid } from "@/components/catalog";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { cn } from "@/lib/utils";
import { Tag, ArrowRight, Filter, ChevronRight } from "lucide-react";
import { TaxonomyNode } from "@/lib/api/schemas";

const getCursorFromUrl = (url?: string | null) => {
    if (!url) return undefined;
    try {
        return new URL(url, ENDPOINTS.PRODUCTS).searchParams.get("cursor") || undefined;
    } catch {
        return undefined;
    }
};

export default function BrandProductMethodsPage() {
    const params = useParams();
    const searchParams = useSearchParams();
    const router = useRouter();

    const categorySlug = params.categorySlug as string;
    const seriesSlug = params.seriesSlug as string;
    const brandSlug = params.brandSlug as string;

    const selectedNodeSlug = searchParams.get("node");

    // --- Data Fetching ---

    // 1. Categories (for breadcrumb/info)
    const { data: categories = [] } = useQuery({
        queryKey: ["categories"],
        queryFn: () => fetchCategoriesTree(),
    });

    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const findCategory = (cats: any[], targetSlug: string): any => {
        for (const cat of cats) {
            if (cat.slug === targetSlug) return cat;
            if (cat.children) {
                const found = findCategory(cat.children, targetSlug);
                if (found) return found;
            }
        }
        return null;
    };
    const category = findCategory(categories, categorySlug);

    // 2. Series Info
    const { data: seriesList = [] } = useQuery({
        queryKey: ["series", "category", categorySlug],
        queryFn: () => fetchSeries(categorySlug),
    });
    const series = seriesList.find((s) => s.slug === seriesSlug);

    // 3. Brand Info
    const isAllProducts = brandSlug === "tumu";
    const { data: brands = [] } = useQuery({
        queryKey: ["brands", "series", seriesSlug],
        queryFn: () => fetchBrands(seriesSlug),
        enabled: !!seriesSlug && !isAllProducts,
    });
    const brand = isAllProducts ? null : brands.find(b => b.slug === brandSlug);

    // 4. Taxonomy (for filters)
    const { data: taxonomyNodes = [] } = useQuery({
        queryKey: ["taxonomy", seriesSlug],
        queryFn: () => fetchTaxonomyTree(seriesSlug),
        enabled: !!seriesSlug,
    });

    // 5. Products
    const [localSelectedNode, setLocalSelectedNode] = useState(selectedNodeSlug);
    if (selectedNodeSlug !== localSelectedNode) setLocalSelectedNode(selectedNodeSlug);

    const {
        data,
        isLoading: productsLoading,
        isFetchingNextPage,
        fetchNextPage,
        hasNextPage,
    } = useInfiniteQuery({
        queryKey: ["products", categorySlug, seriesSlug, brandSlug, localSelectedNode],
        queryFn: ({ pageParam }) =>
            fetchProducts({
                category: categorySlug,
                series: seriesSlug,
                brand: isAllProducts ? undefined : brandSlug,
                node: localSelectedNode || undefined,
                cursor: pageParam,
                page_size: 24,
            }),
        initialPageParam: undefined as string | undefined,
        getNextPageParam: (lastPage) => getCursorFromUrl(lastPage.next),
    });

    const products = data?.pages.flatMap((page) => page.results) || [];

    // --- Handlers ---

    const handleNodeSelect = (nodeSlug: string | null) => {
        setLocalSelectedNode(nodeSlug);
        const newParams = new URLSearchParams(searchParams.toString());
        if (nodeSlug) newParams.set("node", nodeSlug);
        else newParams.delete("node");
        newParams.delete("cursor");
        router.push(`?${newParams.toString()}`);
    };

    return (
        <Container className="py-8 lg:py-12 overflow-x-hidden">
            {/* Breadcrumb */}
            <nav className="mb-6 text-sm text-muted-foreground overflow-x-auto whitespace-nowrap pb-1 scrollbar-hide -mx-4 px-4 sm:mx-0 sm:px-0 flex items-center">
                <Link href="/" className="hover:text-primary">Ana Sayfa</Link>
                <span className="mx-2 text-muted-foreground/30">/</span>
                <Link href="/urunler" className="hover:text-primary">Ürünler</Link>
                <span className="mx-2 text-muted-foreground/30">/</span>
                <Link href={`/urunler/${categorySlug}`} className="hover:text-primary">
                    {category?.name || categorySlug}
                </Link>
                <span className="mx-2 text-muted-foreground/30">/</span>
                <Link href={`/urunler/${categorySlug}/${seriesSlug}`} className="hover:text-primary">
                    {series?.name || seriesSlug}
                </Link>
                <span className="mx-2 text-muted-foreground/30">/</span>
                <span className="text-foreground font-medium">{isAllProducts ? "Tüm Ürünler" : (brand?.name || brandSlug)}</span>
            </nav>

            {/* Header */}
            <div className="mb-10 flex items-center gap-4">
                <div className="h-16 w-2 bg-gradient-to-b from-primary via-primary to-primary/70 shadow-primary-soft" />
                <div>
                    <h1 className="text-3xl font-bold lg:text-4xl">
                        {isAllProducts ? "Tüm Ürünler" : brand?.name} {category?.name}
                    </h1>
                    <p className="mt-1 text-muted-foreground">
                        {isAllProducts
                            ? `${series?.name || ""} serisindeki tüm ürünler listeleniyor`
                            : `${brand?.name} markalı ${series?.name} ürünleri listeleniyor`
                        }
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
                                    {brand?.name || brandSlug}
                                </div>
                                <Button
                                    variant="outline"
                                    size="sm"
                                    asChild
                                    className="w-full gap-2 group"
                                >
                                    <Link href={`/urunler/${categorySlug}/${seriesSlug}`}>
                                        <ArrowRight className="h-3.5 w-3.5 rotate-180 transition-transform group-hover:-translate-x-1" />
                                        Marka Değiştir
                                    </Link>
                                </Button>
                                <Button
                                    variant="ghost"
                                    size="sm"
                                    asChild
                                    className="w-full text-muted-foreground hover:text-foreground"
                                >
                                    <Link href={`/urunler/${categorySlug}`}>Seri Değiştir</Link>
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

// Helpers

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
