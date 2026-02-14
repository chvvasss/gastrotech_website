"use client";

import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronRight, Layers, Package, Filter, ArrowRight, Sparkles, Check, Tag } from "lucide-react";
import { fetchNav, fetchSeries, fetchTaxonomyTree, fetchProducts, fetchBrands } from "@/lib/api";
import { TaxonomyNode } from "@/lib/api/schemas";
import { ScrollArea } from "@/components/ui/scroll-area";
import { getMediaUrl, cn } from "@/lib/utils";

export function Explorer() {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [selectedSeries, setSelectedSeries] = useState<string | null>(null);
  const [selectedBrand, setSelectedBrand] = useState<string | null>(null);
  const [selectedNode, setSelectedNode] = useState<string | null>(null);

  // Fetch navigation categories
  const { data: categories = [], isLoading: loadingCategories } = useQuery({
    queryKey: ["nav"],
    queryFn: fetchNav,
  });

  // Fetch series for selected category
  const { data: seriesList = [], isLoading: loadingSeries } = useQuery({
    queryKey: ["series", selectedCategory],
    queryFn: () => (selectedCategory ? fetchSeries(selectedCategory) : Promise.resolve([])),
    enabled: !!selectedCategory,
  });

  // Fetch brands for selected series
  const { data: brandsList = [], isLoading: loadingBrands } = useQuery({
    queryKey: ["brands", selectedSeries],
    queryFn: () => (selectedSeries ? fetchBrands(selectedSeries) : Promise.resolve([])),
    enabled: !!selectedSeries,
  });

  // Fetch taxonomy for selected series
  const { data: taxonomyNodes = [], isLoading: loadingTaxonomy } = useQuery({
    queryKey: ["taxonomy", selectedSeries],
    queryFn: () => (selectedSeries ? fetchTaxonomyTree(selectedSeries) : Promise.resolve([])),
    enabled: !!selectedSeries,
  });

  // Fetch featured products based on selection
  const { data: productsData, isLoading: loadingProducts } = useQuery({
    queryKey: ["products-preview", selectedCategory, selectedSeries, selectedBrand, selectedNode],
    queryFn: () =>
      fetchProducts({
        category: selectedCategory || undefined,
        series: selectedSeries || undefined,
        brand: selectedBrand || undefined,
        node: selectedNode || undefined,
        page_size: 3,
        sort: "featured",
      }),
    enabled: !!selectedCategory || !!selectedSeries,
  });

  const products = productsData?.results || [];

  const handleCategorySelect = (slug: string) => {
    setSelectedCategory(slug);
    setSelectedSeries(null);
    setSelectedBrand(null);
    setSelectedNode(null);
  };

  const handleSeriesSelect = (slug: string) => {
    setSelectedSeries(slug);
    setSelectedBrand(null);
    setSelectedNode(null);
  };

  const handleBrandSelect = (slug: string) => {
    setSelectedBrand(slug);
    setSelectedNode(null);
  };

  // Step indicator component
  const StepIndicator = ({ step, active, completed }: { step: number; active: boolean; completed: boolean }) => (
    <motion.div
      className={cn(
        "flex h-8 w-8 items-center justify-center rounded-sm text-sm font-bold transition-all",
        completed
          ? "bg-primary text-primary-foreground shadow-md shadow-primary/25"
          : active
            ? "bg-primary/20 text-primary ring-2 ring-primary/30"
            : "bg-muted text-muted-foreground"
      )}
      animate={{ scale: active ? 1.1 : 1 }}
    >
      {completed ? <Check className="h-4 w-4" /> : step}
    </motion.div>
  );

  return (
    <motion.div
      className="relative overflow-hidden rounded-sm bg-background p-6 lg:p-10 shadow-2xl shadow-primary/20"
      initial={{ opacity: 0, y: 20 }}
      whileInView={{ opacity: 1, y: 0 }}
      viewport={{ once: true }}
    >
      {/* Decorative elements */}
      <div className="absolute -right-20 -top-20 h-64 w-64 rounded-sm bg-primary/5 blur-[80px]" />
      <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-sm bg-primary/5 blur-[80px]" />

      {/* Grid Pattern */}
      <div
        className="absolute inset-0 opacity-[0.03] pointer-events-none"
        style={{
          backgroundImage: 'radial-gradient(circle, #E63946 1px, transparent 1px)',
          backgroundSize: '24px 24px'
        }}
      />

      <div className="relative grid gap-8 lg:grid-cols-12">
        {/* Selection Steps */}
        <div className="lg:col-span-8 space-y-8">

          <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">
            {/* Step 1: Category */}
            <motion.div
              className="space-y-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.1 }}
            >
              <div className="flex items-center gap-3 text-sm font-medium text-foreground/80">
                <StepIndicator step={1} active={!selectedCategory} completed={!!selectedCategory} />
                <span className="font-semibold text-foreground">Kategori</span>
                {selectedCategory && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="ml-auto rounded-sm bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                  >
                    ✓ Seçildi
                  </motion.span>
                )}
              </div>
              <ScrollArea className="h-64 rounded-sm border border-border bg-card/50 shadow-sm">
                {loadingCategories ? (
                  <div className="space-y-2 p-3">
                    {[1, 2, 3, 4].map((i) => (
                      <div key={i} className="h-12 w-full rounded-sm bg-muted animate-pulse" />
                    ))}
                  </div>
                ) : (
                  <div className="space-y-1.5 p-2">
                    {categories.map((cat, index) => (
                      <motion.button
                        key={cat.id}
                        onClick={() => handleCategorySelect(cat.slug)}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.03 }}
                        whileHover={selectedCategory === cat.slug ? {} : { x: 4, backgroundColor: "rgba(230, 57, 70, 0.05)" }}
                        whileTap={{ scale: 0.98 }}
                        className={cn(
                          "flex w-full items-center gap-3 rounded-sm px-3 py-3 text-left text-sm transition-all border",
                          selectedCategory === cat.slug
                            ? "bg-white border-primary text-primary font-bold shadow-md shadow-primary/10 scale-[1.02]"
                            : "border-transparent text-foreground hover:bg-muted/50 hover:border-border/50"
                        )}
                      >
                        <Layers className={cn("h-4 w-4 shrink-0", selectedCategory === cat.slug ? "text-primary" : "text-muted-foreground")} />
                        <span className="truncate">{cat.menu_label || cat.name}</span>
                        {selectedCategory === cat.slug && (
                          <ChevronRight className="ml-auto h-4 w-4 shrink-0 text-primary" />
                        )}
                      </motion.button>
                    ))}
                  </div>
                )}
              </ScrollArea>
            </motion.div>

            {/* Step 2: Series */}
            <motion.div
              className="space-y-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
            >
              <div className="flex items-center gap-3 text-sm font-medium text-foreground/80">
                <StepIndicator
                  step={2}
                  active={!!selectedCategory && !selectedSeries}
                  completed={!!selectedSeries}
                />
                <span className="font-semibold text-foreground">Seri</span>
                {selectedSeries && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="ml-auto rounded-sm bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                  >
                    ✓ Seçildi
                  </motion.span>
                )}
              </div>
              <ScrollArea className={cn(
                "h-64 rounded-sm border transition-all shadow-sm",
                selectedCategory
                  ? "bg-card/50 border-border"
                  : "bg-muted/30 border-dashed border-border"
              )}>
                <AnimatePresence mode="wait">
                  {!selectedCategory ? (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex h-full items-center justify-center p-4 text-center text-sm text-muted-foreground"
                    >
                      <div>
                        <Layers className="mx-auto mb-2 h-10 w-10 opacity-20" />
                        <span>Kategori seçiniz</span>
                      </div>
                    </motion.div>
                  ) : loadingSeries ? (
                    <div className="space-y-2 p-3">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-12 w-full rounded-sm bg-muted animate-pulse" />
                      ))}
                    </div>
                  ) : seriesList.length === 0 ? (
                    <motion.div
                      key="no-series"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex h-full items-center justify-center p-4 text-center text-sm text-muted-foreground"
                    >
                      Bu kategoride seri yok
                    </motion.div>
                  ) : (
                    <motion.div
                      key="series-list"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-1.5 p-2"
                    >
                      {seriesList.map((series, index) => (
                        <motion.button
                          key={series.id}
                          onClick={() => handleSeriesSelect(series.slug)}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.03 }}
                          whileHover={selectedSeries === series.slug ? {} : { x: 4, backgroundColor: "rgba(230, 57, 70, 0.05)" }}
                          whileTap={{ scale: 0.98 }}
                          className={cn(
                            "flex w-full items-center gap-3 rounded-sm px-3 py-3 text-left text-sm transition-all border",
                            selectedSeries === series.slug
                              ? "bg-white border-primary text-primary font-bold shadow-md shadow-primary/10 scale-[1.02]"
                              : "border-transparent text-foreground hover:bg-muted/50 hover:border-border/50"
                          )}
                        >
                          <Package className={cn("h-4 w-4 shrink-0", selectedSeries === series.slug ? "text-primary" : "text-muted-foreground")} />
                          <span className="truncate">{series.name}</span>
                          {selectedSeries === series.slug && (
                            <ChevronRight className="ml-auto h-4 w-4 shrink-0 text-primary" />
                          )}
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </ScrollArea>
            </motion.div>

            {/* Step 3: Brand */}
            <motion.div
              className="space-y-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.25 }}
            >
              <div className="flex items-center gap-3 text-sm font-medium text-foreground/80">
                <StepIndicator
                  step={3}
                  active={!!selectedSeries && !selectedBrand}
                  completed={!!selectedBrand}
                />
                <span className="font-semibold text-foreground">Marka</span>
                {selectedBrand && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="ml-auto rounded-sm bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                  >
                    ✓ Seçildi
                  </motion.span>
                )}
              </div>
              <ScrollArea className={cn(
                "h-64 rounded-sm border transition-all shadow-sm",
                selectedSeries
                  ? "bg-card/50 border-border"
                  : "bg-muted/30 border-dashed border-border"
              )}>
                <AnimatePresence mode="wait">
                  {!selectedSeries ? (
                    <motion.div
                      key="empty"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex h-full items-center justify-center p-4 text-center text-sm text-muted-foreground"
                    >
                      <div>
                        <Package className="mx-auto mb-2 h-10 w-10 opacity-20" />
                        <span>Seri seçiniz</span>
                      </div>
                    </motion.div>
                  ) : loadingBrands ? (
                    <div className="space-y-2 p-3">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-12 w-full rounded-sm bg-muted animate-pulse" />
                      ))}
                    </div>
                  ) : brandsList.length === 0 ? (
                    <motion.div
                      key="no-brands"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex h-full items-center justify-center p-4 text-center text-sm text-muted-foreground"
                    >
                      <div>
                        <Tag className="mx-auto mb-2 h-10 w-10 opacity-20" />
                        <span>Marka yok</span>
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="brands-list"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="space-y-1.5 p-2"
                    >
                      {brandsList.map((brand, index) => (
                        <motion.button
                          key={brand.id}
                          onClick={() => handleBrandSelect(brand.slug)}
                          initial={{ opacity: 0, x: -10 }}
                          animate={{ opacity: 1, x: 0 }}
                          transition={{ delay: index * 0.03 }}
                          whileHover={selectedBrand === brand.slug ? {} : { x: 4, backgroundColor: "rgba(230, 57, 70, 0.05)" }}
                          whileTap={{ scale: 0.98 }}
                          className={cn(
                            "flex w-full items-center gap-3 rounded-sm px-3 py-3 text-left text-sm transition-all border",
                            selectedBrand === brand.slug
                              ? "bg-white border-primary text-primary font-bold shadow-md shadow-primary/10 scale-[1.02]"
                              : "border-transparent text-foreground hover:bg-muted/50 hover:border-border/50"
                          )}
                        >
                          {brand.logo_url ? (
                            <div className="relative h-6 w-6 shrink-0 overflow-hidden rounded bg-white p-0.5">
                              <Image
                                src={getMediaUrl(brand.logo_url) || ""}
                                alt={brand.name}
                                fill
                                className="object-contain"
                              />
                            </div>
                          ) : (
                            <Tag className={cn("h-4 w-4 shrink-0", selectedBrand === brand.slug ? "text-primary" : "text-muted-foreground")} />
                          )}
                          <span className="truncate">{brand.name}</span>
                          {selectedBrand === brand.slug && (
                            <ChevronRight className="ml-auto h-4 w-4 shrink-0 text-primary" />
                          )}
                        </motion.button>
                      ))}
                    </motion.div>
                  )}
                </AnimatePresence>
              </ScrollArea>
            </motion.div>

            {/* Step 4: Taxonomy */}
            <motion.div
              className="space-y-4"
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
            >
              <div className="flex items-center gap-3 text-sm font-medium text-foreground/80">
                <StepIndicator
                  step={4}
                  active={!!selectedBrand && !selectedNode}
                  completed={!!selectedNode}
                />
                <span className="font-semibold text-foreground">Özellik</span>
                {selectedNode && (
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className="ml-auto rounded-sm bg-primary/10 px-2.5 py-0.5 text-xs font-medium text-primary"
                  >
                    ✓ Seçildi
                  </motion.span>
                )}
              </div>
              <ScrollArea className={cn(
                "h-64 rounded-sm border transition-all shadow-sm",
                selectedBrand
                  ? "bg-card/50 border-border"
                  : "bg-muted/30 border-dashed border-border"
              )}>
                <AnimatePresence mode="wait">
                  {!selectedSeries ? (
                    <motion.div
                      key="empty-series"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex h-full items-center justify-center p-4 text-center text-sm text-muted-foreground"
                    >
                      <div>
                        <Package className="mx-auto mb-2 h-10 w-10 opacity-20" />
                        <span>Seri seçiniz</span>
                      </div>
                    </motion.div>
                  ) : !selectedBrand ? (
                    <motion.div
                      key="empty-brand"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      exit={{ opacity: 0 }}
                      className="flex h-full items-center justify-center p-4 text-center text-sm text-muted-foreground"
                    >
                      <div>
                        <Tag className="mx-auto mb-2 h-10 w-10 opacity-20" />
                        <span>Marka seçiniz</span>
                      </div>
                    </motion.div>
                  ) : loadingTaxonomy ? (
                    <div className="space-y-2 p-3">
                      {[1, 2, 3].map((i) => (
                        <div key={i} className="h-12 w-full rounded-sm bg-muted animate-pulse" />
                      ))}
                    </div>
                  ) : taxonomyNodes.length === 0 ? (
                    <motion.div
                      key="optional"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                      className="flex h-full items-center justify-center p-4 text-center text-sm text-muted-foreground"
                    >
                      <div>
                        <Filter className="mx-auto mb-2 h-10 w-10 opacity-20" />
                        <span>Filtre yok</span>
                      </div>
                    </motion.div>
                  ) : (
                    <motion.div
                      key="taxonomy"
                      initial={{ opacity: 0 }}
                      animate={{ opacity: 1 }}
                    >
                      <TaxonomyTree
                        nodes={taxonomyNodes}
                        selectedNode={selectedNode}
                        onSelect={setSelectedNode}
                      />
                    </motion.div>
                  )}
                </AnimatePresence>
              </ScrollArea>
            </motion.div>
          </div>
        </div>

        {/* Product Preview - Premium */}
        <motion.div
          className="lg:col-span-4"
          initial={{ opacity: 0, x: 20 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: 0.4 }}
        >
          <div className="h-full rounded-sm border border-primary/20 bg-primary/5 p-5">
            <h3 className="mb-4 flex items-center gap-2 font-semibold text-primary">
              <Sparkles className="h-4 w-4" />
              Ürün Önizleme
            </h3>
            <ScrollArea className="h-[340px] pr-2">
              <AnimatePresence mode="wait">
                {loadingProducts ? (
                  <motion.div
                    key="loading"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-3"
                  >
                    {[1, 2, 3].map((i) => (
                      <div key={i} className="h-20 w-full rounded-sm bg-muted animate-pulse" />
                    ))}
                  </motion.div>
                ) : products.length === 0 ? (
                  <motion.div
                    key="empty"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="flex h-60 items-center justify-center text-center text-sm text-muted-foreground"
                  >
                    {selectedCategory || selectedSeries ? (
                      <div>
                        <Package className="mx-auto mb-3 h-12 w-12 opacity-20" />
                        <span>Ürün bulunamadı</span>
                      </div>
                    ) : (
                      <div>
                        <Layers className="mx-auto mb-3 h-12 w-12 opacity-20" />
                        <span>Seçim yaparak ürünleri görün</span>
                      </div>
                    )}
                  </motion.div>
                ) : (
                  <motion.div
                    key="products"
                    initial={{ opacity: 0 }}
                    animate={{ opacity: 1 }}
                    exit={{ opacity: 0 }}
                    className="space-y-3"
                  >
                    {products.map((product, index) => (
                      <motion.div
                        key={product.slug}
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ delay: index * 0.1 }}
                      >
                        <Link
                          href={`/urun/${product.slug}`}
                          className="flex items-center gap-3 rounded-sm bg-background p-3 transition-all hover:bg-background/80 hover:scale-[1.02] shadow-sm group border border-border/50"
                        >
                          <div className="relative h-14 w-14 overflow-hidden rounded-sm bg-muted flex-shrink-0 border border-border">
                            {product.primary_image_url ? (
                              <Image
                                src={getMediaUrl(product.primary_image_url)}
                                alt={product.title_tr || product.slug}
                                fill
                                className="object-cover transition-transform group-hover:scale-110"
                              />
                            ) : (
                              <div className="flex h-full w-full items-center justify-center text-xs text-muted-foreground">
                                —
                              </div>
                            )}
                          </div>
                          <div className="flex-1 min-w-0">
                            <p className="truncate text-sm font-bold text-foreground group-hover:text-primary transition-colors">
                              {product.title_tr || product.slug}
                            </p>
                            <p className="flex items-center gap-1.5 text-xs text-muted-foreground font-medium">
                              <span className="h-1.5 w-1.5 rounded-sm bg-primary/70" />
                              {product.variants_count} model
                            </p>
                          </div>
                          <ArrowRight className="h-4 w-4 shrink-0 text-primary opacity-0 -translate-x-2 transition-all group-hover:opacity-100 group-hover:translate-x-0" />
                        </Link>
                      </motion.div>
                    ))}

                    {(selectedCategory || selectedSeries) && (
                      <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        transition={{ delay: 0.3 }}
                        className="pt-2"
                      >
                        <Link
                          href={`/urunler?${selectedSeries ? `series=${selectedSeries}` : `category=${selectedCategory}`}${selectedBrand ? `&brand=${selectedBrand}` : ''}${selectedNode ? `&node=${selectedNode}` : ''}`}
                          className="flex w-full items-center justify-center gap-2 rounded-sm bg-primary py-3 text-sm font-semibold text-primary-foreground transition-all hover:bg-primary/90 shadow-md shadow-primary/20"
                        >
                          Tüm Ürünleri Gör
                          <ArrowRight className="h-4 w-4" />
                        </Link>
                      </motion.div>
                    )}
                  </motion.div>
                )}
              </AnimatePresence>
            </ScrollArea>
          </div>
        </motion.div>
      </div>
    </motion.div>
  );
}

// Recursive Taxonomy Tree Component with animations
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
    <div className={cn("space-y-1", depth === 0 && "p-2")}>
      {nodes.map((node, index) => (
        <motion.div
          key={node.id}
          initial={{ opacity: 0, x: -10 }}
          animate={{ opacity: 1, x: 0 }}
          transition={{ delay: index * 0.03 }}
        >
          <motion.button
            onClick={() => onSelect(node.slug)}
            whileHover={selectedNode === node.slug ? {} : { x: 4, backgroundColor: "rgba(230, 57, 70, 0.05)" }}
            whileTap={{ scale: 0.98 }}
            className={cn(
              "flex w-full items-center gap-2 rounded-sm px-3 py-2.5 text-left text-sm transition-all border",
              selectedNode === node.slug
                ? "bg-white border-primary text-primary font-bold shadow-md shadow-primary/10 scale-[1.02]"
                : "border-transparent text-foreground hover:bg-muted/50 hover:border-border/50"
            )}
            style={{ paddingLeft: `${depth * 12 + 12}px` }}
          >
            <Filter className={cn("h-4 w-4 shrink-0", selectedNode === node.slug ? "text-primary" : "text-muted-foreground")} />
            <span className="truncate">{node.name}</span>
            {selectedNode === node.slug && (
              <ChevronRight className="ml-auto h-4 w-4 shrink-0 text-primary" />
            )}
          </motion.button>
          {node.children && node.children.length > 0 && (
            <TaxonomyTree
              nodes={node.children}
              selectedNode={selectedNode}
              onSelect={onSelect}
              depth={depth + 1}
            />
          )}
        </motion.div>
      ))}
    </div>
  );
}
