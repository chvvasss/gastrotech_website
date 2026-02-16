"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { FileText, Download, Eye, BookOpen, FolderOpen } from "lucide-react";
import { fetchCatalogAssets, fetchAllCategoryCatalogs } from "@/lib/api";
import { getMediaUrl } from "@/lib/utils";
import { Container } from "@/components/layout";
import type { CatalogAsset, CategoryCatalog } from "@/lib/api/schemas";

/* ── PDF.js Loader (singleton) ─────────────────────── */
let pdfJsLoadingPromise: Promise<void> | null = null;

const ensurePdfJs = (): Promise<void> => {
  if (typeof window !== "undefined" && (window as any).pdfjsLib) return Promise.resolve();
  if (pdfJsLoadingPromise) return pdfJsLoadingPromise;

  pdfJsLoadingPromise = new Promise((resolve, reject) => {
    if (document.getElementById("pdfjs-lib-script")) {
      const check = setInterval(() => {
        if ((window as any).pdfjsLib) { clearInterval(check); resolve(); }
      }, 100);
      return;
    }
    const s = document.createElement("script");
    s.src = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.min.js";
    s.id = "pdfjs-lib-script";
    s.onload = () => {
      if ((window as any).pdfjsLib) {
        (window as any).pdfjsLib.GlobalWorkerOptions.workerSrc =
          "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js";
        resolve();
      } else reject("PDF.js object missing");
    };
    s.onerror = reject;
    document.head.appendChild(s);
  });
  return pdfJsLoadingPromise;
};

/* ── PDF Thumbnail ─────────────────────────────────── */
function PDFThumbnail({ url, className }: { url: string; className?: string }) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [loaded, setLoaded] = useState(false);

  useEffect(() => {
    if (!url) return;
    let cancelled = false;
    ensurePdfJs().then(async () => {
      if (cancelled || !(window as any).pdfjsLib) return;
      try {
        const doc = await (window as any).pdfjsLib.getDocument(url).promise;
        const page = await doc.getPage(1);
        const viewport = page.getViewport({ scale: 0.8 });
        const canvas = canvasRef.current;
        if (canvas && !cancelled) {
          const ctx = canvas.getContext("2d");
          if (ctx) {
            canvas.width = viewport.width;
            canvas.height = viewport.height;
            canvas.style.width = "100%";
            canvas.style.height = "100%";
            await page.render({ canvasContext: ctx, viewport }).promise;
            if (!cancelled) setLoaded(true);
          }
        }
      } catch { }
    });
    return () => { cancelled = true; };
  }, [url]);

  return (
    <div className={`relative overflow-hidden bg-stone-100 ${className || ""}`}>
      {!loaded && (
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="h-5 w-5 animate-spin rounded-full border-2 border-stone-300 border-t-stone-600" />
        </div>
      )}
      <canvas
        ref={canvasRef}
        className={`w-full h-full object-cover transition-opacity duration-500 ${loaded ? "opacity-100" : "opacity-0"}`}
      />
    </div>
  );
}

/* ── Helpers ───────────────────────────────────────── */
function formatFileSize(bytes: number | null): string {
  if (!bytes) return "";
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

/* ── Catalog Card with PDF Preview ─────────────────── */
function CatalogCard({ title, fileUrl, fileSize, description, isPrimary, categoryName }: {
  title: string;
  fileUrl: string | null;
  fileSize: number | null;
  description?: string | null;
  isPrimary?: boolean;
  categoryName?: string;
}) {
  const mediaUrl = fileUrl ? getMediaUrl(fileUrl) : null;

  return (
    <div
      className="group relative flex flex-col cursor-pointer"
      onClick={() => { if (mediaUrl) window.open(mediaUrl, "_blank"); }}
    >
      {/* PDF Preview Thumbnail */}
      <div className="relative aspect-[1/1.4] w-full overflow-hidden rounded-sm shadow-sm bg-stone-100 border border-stone-200 group-hover:shadow-lg transition-all duration-300">
        {mediaUrl ? (
          <PDFThumbnail url={mediaUrl} className="w-full h-full" />
        ) : (
          <div className="absolute inset-0 flex items-center justify-center text-stone-300">
            <FileText className="h-12 w-12" />
          </div>
        )}

        {/* Primary badge */}
        {isPrimary && (
          <div className="absolute top-2 left-2 z-10">
            <span className="px-2 py-0.5 text-[10px] font-bold bg-primary text-white rounded shadow-sm">
              ANA KATALOG
            </span>
          </div>
        )}

        {/* Category label */}
        {categoryName && (
          <div className="absolute top-2 right-2 z-10">
            <span className="px-2 py-0.5 text-[10px] font-medium bg-black/50 text-white rounded backdrop-blur-sm">
              {categoryName}
            </span>
          </div>
        )}

        {/* Hover overlay */}
        <div className="absolute inset-0 bg-black/0 group-hover:bg-black/30 transition-colors duration-300 flex flex-col items-center justify-center gap-2 opacity-0 group-hover:opacity-100">
          <div className="flex items-center gap-2 transform translate-y-3 group-hover:translate-y-0 transition-all duration-300">
            <span className="bg-white/95 backdrop-blur rounded-full p-2.5 shadow-lg hover:bg-white transition-colors">
              <Eye className="h-4 w-4 text-stone-700" />
            </span>
            <a
              href={mediaUrl || "#"}
              download
              onClick={(e) => e.stopPropagation()}
              className="bg-white/95 backdrop-blur rounded-full p-2.5 shadow-lg hover:bg-white transition-colors"
            >
              <Download className="h-4 w-4 text-stone-700" />
            </a>
          </div>
        </div>
      </div>

      {/* Title & Info */}
      <div className="mt-3 text-center px-1">
        <h3 className="text-sm font-semibold text-foreground group-hover:text-primary transition-colors line-clamp-2">
          {title}
        </h3>
        {description && (
          <p className="text-xs text-muted-foreground mt-1 line-clamp-1">{description}</p>
        )}
        {fileSize && (
          <p className="text-[11px] text-muted-foreground/60 mt-1">
            PDF &middot; {formatFileSize(fileSize)}
          </p>
        )}
      </div>
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

  // Sort assets by order
  const sortedAssets = [...assets].sort((a, b) => a.order - b.order);

  // Sort category catalogs by order
  const sortedCategoryCatalogs = [...categoryCatalogs].sort((a, b) => a.order - b.order);

  const hasAssets = sortedAssets.length > 0;
  const hasCategoryCatalogs = sortedCategoryCatalogs.length > 0;
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
            Ürün kataloglarımızı indirerek tüm ürün yelpazemizi detaylı inceleyebilirsiniz.
          </p>
        </Container>
      </section>

      {/* Genel Kataloglar - Full width top */}
      <section className="py-12 lg:py-16 border-b">
        <Container>
          <div className="mb-8 flex items-center gap-4">
            <div className="h-10 w-1.5 rounded-sm bg-primary shadow-sm" />
            <div>
              <h2 className="text-2xl font-bold lg:text-3xl text-foreground tracking-tight">
                Genel Kataloglar
              </h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Tüm ürün gruplarına ait ana katalog dosyaları
              </p>
            </div>
          </div>

          {loadingAssets ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {Array.from({ length: 5 }).map((_, i) => (
                <div key={i} className="flex flex-col gap-2">
                  <div className="aspect-[1/1.4] animate-pulse rounded-sm bg-muted/50 border border-border/30" />
                  <div className="h-3 animate-pulse rounded bg-muted/40 w-3/4 mx-auto" />
                </div>
              ))}
            </div>
          ) : hasAssets ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
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
              <BookOpen className="h-8 w-8 text-muted-foreground/40 mb-2" />
              <p className="text-sm text-muted-foreground">
                Henüz genel katalog yüklenmemiştir.
              </p>
            </div>
          )}
        </Container>
      </section>

      {/* Kategori Katalogları - Groups side by side */}
      <section className="py-12 lg:py-16">
        <Container>
          <div className="mb-8 flex items-center gap-4">
            <div className="h-10 w-1.5 rounded-sm bg-primary shadow-sm" />
            <div>
              <h2 className="text-2xl font-bold lg:text-3xl text-foreground tracking-tight">
                Kategori Katalogları
              </h2>
              <p className="text-muted-foreground mt-1 text-sm">
                Ürün kategorilerine özel katalog dosyaları
              </p>
            </div>
          </div>

          {loadingCategoryCatalogs ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {Array.from({ length: 10 }).map((_, i) => (
                <div key={i} className="flex flex-col gap-2">
                  <div className="aspect-[1/1.4] animate-pulse rounded-sm bg-muted/50 border border-border/30" />
                  <div className="h-3 animate-pulse rounded bg-muted/40 w-3/4 mx-auto" />
                </div>
              ))}
            </div>
          ) : hasCategoryCatalogs ? (
            <div className="grid grid-cols-2 sm:grid-cols-3 md:grid-cols-4 lg:grid-cols-5 gap-6">
              {sortedCategoryCatalogs.map((catalog) => (
                <CatalogCard
                  key={catalog.id}
                  title={catalog.title_tr}
                  fileUrl={catalog.file_url}
                  fileSize={catalog.file_size}
                  description={catalog.description}
                  categoryName={catalog.category_name}
                />
              ))}
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center py-12 text-center">
              <FolderOpen className="h-8 w-8 text-muted-foreground/40 mb-2" />
              <p className="text-sm text-muted-foreground">
                Henüz kategori kataloğu yüklenmemiştir.
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
                Katalog Bulunamadı
              </h3>
              <p className="text-sm text-muted-foreground max-w-md">
                Katalog dosyaları yakında eklenecektir. Daha sonra tekrar kontrol edebilirsiniz.
              </p>
            </div>
          </Container>
        </section>
      )}
    </>
  );
}
