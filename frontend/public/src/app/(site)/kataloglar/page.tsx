"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, Download, Eye, BookOpen, FolderOpen } from "lucide-react";
import { fetchCatalogAssets, fetchAllCategoryCatalogs } from "@/lib/api";
import { getMediaUrl } from "@/lib/utils";
import { Container } from "@/components/layout";
import type { CatalogAsset, CategoryCatalog } from "@/lib/api/schemas";

function formatFileSize(bytes: number | null): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function CatalogCard({ title, fileUrl, fileSize, description, isPrimary }: {
  title: string;
  fileUrl: string | null;
  fileSize: number | null;
  description?: string | null;
  isPrimary?: boolean;
}) {
  return (
    <div className="group relative bg-white border border-border/50 rounded-sm p-5 hover:shadow-md hover:border-primary/30 transition-all duration-200">
      <div className="flex items-start gap-3 mb-3">
        <div className="flex-shrink-0 h-10 w-10 rounded-sm bg-red-50 text-red-600 flex items-center justify-center">
          <FileText className="h-5 w-5" />
        </div>
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2">
            <h3 className="font-semibold text-foreground text-sm leading-snug line-clamp-2">
              {title}
            </h3>
            {isPrimary && (
              <span className="flex-shrink-0 px-1.5 py-0.5 text-[10px] font-bold bg-primary/10 text-primary rounded-sm">
                ANA
              </span>
            )}
          </div>
        </div>
      </div>

      {description && (
        <p className="text-xs text-muted-foreground line-clamp-2 mb-3">
          {description}
        </p>
      )}

      {fileSize && (
        <p className="text-[10px] text-muted-foreground/70 mb-3">
          PDF - {formatFileSize(fileSize)}
        </p>
      )}

      <div className="flex items-center gap-2">
        {fileUrl && (
          <>
            <a
              href={getMediaUrl(fileUrl)}
              target="_blank"
              rel="noreferrer"
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm bg-primary text-white text-xs font-medium hover:bg-primary/90 transition-colors"
            >
              <Eye className="h-3.5 w-3.5" />
              Goruntule
            </a>
            <a
              href={getMediaUrl(fileUrl)}
              download
              className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-sm border border-border text-foreground text-xs font-medium hover:bg-muted transition-colors"
            >
              <Download className="h-3.5 w-3.5" />
              Indir
            </a>
          </>
        )}
      </div>
    </div>
  );
}

function SkeletonGrid({ count }: { count: number }) {
  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className="h-40 animate-pulse rounded-sm bg-muted/50 border border-border/30" />
      ))}
    </div>
  );
}

export default function KataloglarPage() {
  const { data: assets = [], isLoading: loadingAssets } = useQuery({
    queryKey: ["catalog-assets"],
    queryFn: fetchCatalogAssets,
    staleTime: 5 * 60 * 1000,
  });

  const { data: categoryCatalogs = [], isLoading: loadingCategoryCatalogs } = useQuery({
    queryKey: ["all-category-catalogs"],
    queryFn: fetchAllCategoryCatalogs,
    staleTime: 5 * 60 * 1000,
  });

  // Group category catalogs by category
  const catalogsByCategory = categoryCatalogs.reduce<Record<string, { name: string; catalogs: CategoryCatalog[] }>>((acc, catalog) => {
    const key = catalog.category_slug;
    if (!acc[key]) {
      acc[key] = { name: catalog.category_name, catalogs: [] };
    }
    acc[key].catalogs.push(catalog);
    return acc;
  }, {});

  // Sort catalogs within each category
  Object.values(catalogsByCategory).forEach((group) => {
    group.catalogs.sort((a, b) => a.order - b.order);
  });

  // Sort assets by order
  const sortedAssets = [...assets].sort((a, b) => a.order - b.order);

  const hasAssets = sortedAssets.length > 0;
  const hasCategoryCatalogs = Object.keys(catalogsByCategory).length > 0;
  const isLoading = loadingAssets || loadingCategoryCatalogs;

  return (
    <>
      {/* Header */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary via-primary to-primary/90 py-16 lg:py-24">
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-sm bg-white/10 blur-[100px]" />
        <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-sm bg-black/20 blur-[100px]" />
        <div className="absolute top-8 left-8 w-20 h-20 border-2 border-white/20 rounded-sm hidden lg:block" />
        <div className="absolute bottom-8 right-8 w-24 h-24 border-2 border-white/15 rounded-sm hidden lg:block" />
        <div className="absolute top-1/2 right-16 w-4 h-4 bg-white/20 rotate-45 -translate-y-1/2 hidden md:block" />

        <Container className="relative text-center z-10">
          <h1 className="text-3xl font-bold text-white lg:text-5xl">Kataloglar</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/90">
            Urun kataloglarimizi indirerek tum urun yelpazemizi detayli inceleyebilirsiniz.
          </p>
        </Container>
      </section>

      {/* General Catalog Assets Section */}
      <section className="py-12 lg:py-16 border-b">
        <Container>
          <div className="mb-8 flex items-center gap-4">
            <div className="h-10 w-1.5 rounded-sm bg-primary shadow-sm" />
            <div>
              <h2 className="text-2xl font-bold lg:text-3xl text-foreground tracking-tight">
                Genel Kataloglar
              </h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Tum urun gruplarina ait ana katalog dosyalari
              </p>
            </div>
          </div>

          {loadingAssets ? (
            <SkeletonGrid count={3} />
          ) : hasAssets ? (
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
              {sortedAssets.map((asset) => (
                <CatalogCard
                  key={asset.id}
                  title={asset.title_tr}
                  fileUrl={asset.file_url}
                  fileSize={asset.file_size}
                  isPrimary={asset.is_primary}
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="h-14 w-14 rounded-full bg-muted/50 flex items-center justify-center mb-3">
                <BookOpen className="h-7 w-7 text-muted-foreground/50" />
              </div>
              <p className="text-sm text-muted-foreground">
                Henuz genel katalog yuklenmemistir.
              </p>
            </div>
          )}
        </Container>
      </section>

      {/* Category Catalogs Section */}
      <section className="py-12 lg:py-16">
        <Container>
          <div className="mb-8 flex items-center gap-4">
            <div className="h-10 w-1.5 rounded-sm bg-primary shadow-sm" />
            <div>
              <h2 className="text-2xl font-bold lg:text-3xl text-foreground tracking-tight">
                Kategori Kataloglari
              </h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Urun kategorilerine ozel katalog dosyalari
              </p>
            </div>
          </div>

          {loadingCategoryCatalogs ? (
            <SkeletonGrid count={6} />
          ) : hasCategoryCatalogs ? (
            <div className="space-y-10">
              {Object.entries(catalogsByCategory).map(([slug, group]) => (
                <div key={slug}>
                  <div className="flex items-center gap-2 mb-4">
                    <FolderOpen className="h-5 w-5 text-primary" />
                    <h3 className="text-lg font-semibold text-foreground">
                      {group.name}
                    </h3>
                    <span className="text-xs text-muted-foreground">
                      ({group.catalogs.length} katalog)
                    </span>
                  </div>
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
                    {group.catalogs.map((catalog) => (
                      <CatalogCard
                        key={catalog.id}
                        title={catalog.title_tr}
                        fileUrl={catalog.file_url}
                        fileSize={catalog.file_size}
                        description={catalog.description}
                      />
                    ))}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <div className="h-14 w-14 rounded-full bg-muted/50 flex items-center justify-center mb-3">
                <FolderOpen className="h-7 w-7 text-muted-foreground/50" />
              </div>
              <p className="text-sm text-muted-foreground">
                Henuz kategori katalogu yuklenmemistir.
              </p>
            </div>
          )}
        </Container>
      </section>

      {/* Empty State - Show only if BOTH sections are empty and not loading */}
      {!isLoading && !hasAssets && !hasCategoryCatalogs && (
        <section className="py-16">
          <Container>
            <div className="flex flex-col items-center justify-center text-center">
              <div className="h-20 w-20 rounded-full bg-muted/30 flex items-center justify-center mb-6">
                <BookOpen className="h-10 w-10 text-muted-foreground/40" />
              </div>
              <h3 className="text-xl font-semibold text-foreground/70 mb-2">
                Katalog Bulunamadi
              </h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Katalog dosyalari yakinda eklenecektir. Daha sonra tekrar kontrol edebilirsiniz.
              </p>
            </div>
          </Container>
        </section>
      )}
    </>
  );
}
