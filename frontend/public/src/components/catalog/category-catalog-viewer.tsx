"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileText, ExternalLink, ArrowUpRight } from "lucide-react";
import { fetchCategoryCatalogs } from "@/lib/api";
import { getMediaUrl } from "@/lib/utils";
import type { CategoryCatalog } from "@/lib/api/schemas";

/* ─────────────────────────────────────────────
   PDF Thumbnail Component
   ──────────────────────────────────────────── */
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
                (window as any).pdfjsLib.GlobalWorkerOptions.workerSrc = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/2.16.105/pdf.worker.min.js";
                resolve();
            } else reject("PDF.js object missing");
        };
        s.onerror = reject;
        document.head.appendChild(s);
    });
    return pdfJsLoadingPromise;
};

function PDFThumbnail({ url, className, scale = 0.6 }: { url: string; className?: string; scale?: number }) {
    const canvasRef = useRef<HTMLCanvasElement>(null);
    const [loaded, setLoaded] = useState(false);

    useEffect(() => {
        if (!url) return;
        let cancelled = false;
        ensurePdfJs().then(async () => {
            if (cancelled || !(window as any).pdfjsLib) return;
            try {
                const loadingTask = (window as any).pdfjsLib.getDocument(url);
                const doc = await loadingTask.promise;
                const page = await doc.getPage(1);

                const viewport = page.getViewport({ scale });
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
            } catch (err) { }
        });
        return () => { cancelled = true; };
    }, [url, scale]);

    return (
        <div className={`relative overflow-hidden bg-stone-100 ${className || ""}`}>
            {!loaded && (
                <div className="absolute inset-0 flex items-center justify-center">
                    <div className="flex flex-col items-center gap-3">
                        <div className="h-6 w-6 animate-spin rounded-full border-2 border-stone-300 border-t-primary" />
                        <span className="text-xs text-stone-400 tracking-wide">Yükleniyor</span>
                    </div>
                </div>
            )}
            <canvas
                ref={canvasRef}
                className={`w-full h-full object-cover transition-opacity duration-700 ${loaded ? "opacity-100" : "opacity-0"}`}
            />
        </div>
    );
}

function formatFileSize(bytes: number | null | undefined): string | null {
    if (!bytes) return null;
    const mb = bytes / (1024 * 1024);
    return mb >= 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(0)} KB`;
}

/* ─────────────────────────────────────────────
   Main Component
   ──────────────────────────────────────────── */
interface CategoryCatalogViewerProps {
    categorySlug: string;
    catalogs?: CategoryCatalog[];
}

export function CategoryCatalogViewer({ categorySlug, catalogs: initialCatalogs }: CategoryCatalogViewerProps) {
    const { data: catalogs = initialCatalogs || [], isLoading } = useQuery({
        queryKey: ["category-catalogs", categorySlug],
        queryFn: () => fetchCategoryCatalogs(categorySlug),
        enabled: !initialCatalogs,
        initialData: initialCatalogs,
    });

    /* Loading */
    if (isLoading) {
        return (
            <div className="flex flex-col items-center justify-center py-20">
                <div className="h-10 w-10 animate-spin rounded-full border-4 border-primary border-t-transparent mb-4" />
                <p className="text-sm text-muted-foreground">Kataloglar yükleniyor...</p>
            </div>
        );
    }

    /* Empty */
    if (!catalogs || catalogs.length === 0) {
        return (
            <div className="flex flex-col items-center justify-center py-24 text-center bg-stone-50 rounded-sm border border-dashed border-stone-200">
                <div className="h-20 w-20 rounded-full bg-stone-100 flex items-center justify-center mb-6">
                    <FileText className="h-10 w-10 text-stone-400" />
                </div>
                <h3 className="text-xl font-bold text-stone-700 mb-2">Bu kategori için katalog bulunmamaktadır</h3>
                <p className="text-stone-500 max-w-md">Katalog dosyaları yakında eklenecektir.</p>
            </div>
        );
    }

    /* ── Single Catalog: Showcase Layout ── */
    if (catalogs.length === 1) {
        const catalog = catalogs[0];
        const fileUrl = catalog.file_url ? getMediaUrl(catalog.file_url) : null;
        const sizeLabel = formatFileSize(catalog.file_size);

        return (
            <div className="w-full max-w-5xl mx-auto">
                {/* Showcase card */}
                <div className="relative bg-gradient-to-b from-stone-50 to-stone-100/50 rounded-sm border border-stone-200/80 overflow-hidden">
                    {/* Subtle top accent line */}
                    <div className="absolute top-0 inset-x-0 h-[2px] bg-gradient-to-r from-transparent via-primary/60 to-transparent" />

                    <div className="flex flex-col md:flex-row items-center gap-0">
                        {/* PDF Preview — dominant left half */}
                        <div className="w-full md:w-1/2 p-6 sm:p-8 md:p-10 flex items-center justify-center">
                            <div className="relative w-full max-w-[340px]">
                                {/* Shadow/depth layer */}
                                <div className="absolute -bottom-3 left-4 right-4 h-6 rounded-b-xl bg-stone-900/[0.06] blur-xl" />
                                <div className="relative aspect-[1/1.4] w-full overflow-hidden rounded-sm ring-1 ring-stone-900/[0.08] shadow-xl bg-white">
                                    {fileUrl ? (
                                        <PDFThumbnail
                                            url={fileUrl}
                                            className="w-full h-full"
                                            scale={1}
                                        />
                                    ) : (
                                        <div className="absolute inset-0 flex items-center justify-center text-stone-300">
                                            <FileText className="h-16 w-16" />
                                        </div>
                                    )}
                                </div>
                            </div>
                        </div>

                        {/* Info & Actions — right half */}
                        <div className="w-full md:w-1/2 p-6 sm:p-8 md:p-10 md:pl-4 flex flex-col items-center md:items-start text-center md:text-left">
                            {/* Type badge */}
                            <span className="inline-flex items-center gap-1.5 text-[11px] font-semibold tracking-widest uppercase text-primary/80 mb-5">
                                <span className="w-1.5 h-1.5 rounded-full bg-primary/60" />
                                PDF Katalog
                            </span>

                            <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-stone-900 mb-2">
                                {catalog.title_tr || (catalog as any).title}
                            </h2>

                            {catalog.description && (
                                <p className="text-stone-500 text-sm leading-relaxed mb-6 max-w-md">
                                    {catalog.description}
                                </p>
                            )}

                            {/* Meta info */}
                            {(sizeLabel || catalog.filename) && (
                                <div className="flex items-center gap-3 mb-6 text-xs text-stone-400">
                                    {catalog.filename && (
                                        <span className="flex items-center gap-1.5">
                                            <FileText className="h-3 w-3" />
                                            {catalog.filename}
                                        </span>
                                    )}
                                    {sizeLabel && (
                                        <>
                                            <span className="w-px h-3 bg-stone-300" />
                                            <span>{sizeLabel}</span>
                                        </>
                                    )}
                                </div>
                            )}

                            {/* Action buttons */}
                            {fileUrl && (
                                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 w-full sm:w-auto">
                                    <button
                                        onClick={() => window.open(fileUrl, '_blank')}
                                        className="group/btn inline-flex items-center justify-center gap-2 px-6 py-3 bg-primary text-white text-sm font-semibold rounded-sm hover:bg-primary/90 active:scale-[0.98] transition-all shadow-sm"
                                    >
                                        Kataloğu Görüntüle
                                        <ArrowUpRight className="h-4 w-4 transition-transform group-hover/btn:-translate-y-0.5 group-hover/btn:translate-x-0.5" />
                                    </button>
                                    <a
                                        href={fileUrl}
                                        download
                                        className="inline-flex items-center justify-center gap-2 px-6 py-3 text-sm font-semibold text-stone-600 rounded-sm border border-stone-300 hover:border-stone-400 hover:bg-white active:scale-[0.98] transition-all"
                                    >
                                        <Download className="h-4 w-4" />
                                        İndir
                                    </a>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    /* ── Multiple Catalogs: Grid View ── */
    return (
        <div className="w-full">
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-5 lg:gap-6">
                {catalogs.map((catalog) => {
                    const fileUrl = catalog.file_url ? getMediaUrl(catalog.file_url) : null;
                    const sizeLabel = formatFileSize(catalog.file_size);

                    return (
                        <div
                            key={catalog.id}
                            className="group relative flex flex-col cursor-pointer"
                            onClick={() => {
                                if (fileUrl) window.open(fileUrl, '_blank');
                            }}
                        >
                            {/* Card */}
                            <div className="relative aspect-[1/1.4] w-full overflow-hidden rounded-sm bg-white border border-stone-200 shadow-sm group-hover:shadow-lg group-hover:border-stone-300 transition-all duration-300">
                                {/* Thumbnail */}
                                {fileUrl ? (
                                    <PDFThumbnail
                                        url={fileUrl}
                                        className="w-full h-full group-hover:scale-[1.03] transition-transform duration-500"
                                    />
                                ) : (
                                    <div className="absolute inset-0 flex items-center justify-center text-stone-300">
                                        <FileText className="h-12 w-12" />
                                    </div>
                                )}

                                {/* Hover overlay */}
                                <div className="absolute inset-0 bg-gradient-to-t from-black/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none" />

                                {/* Bottom bar on hover */}
                                <div className="absolute inset-x-0 bottom-0 p-3 flex items-center justify-between translate-y-full group-hover:translate-y-0 transition-transform duration-300">
                                    <span className="text-white text-xs font-medium truncate">
                                        {sizeLabel || "PDF"}
                                    </span>
                                    <div className="flex items-center gap-1.5">
                                        <span className="flex items-center justify-center h-7 w-7 rounded-full bg-white/90 backdrop-blur-sm shadow-sm">
                                            <ExternalLink className="h-3.5 w-3.5 text-stone-700" />
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Title */}
                            <div className="mt-2.5 px-0.5">
                                <h3 className="text-sm font-medium text-stone-700 group-hover:text-primary transition-colors line-clamp-2 leading-snug">
                                    {catalog.title_tr || (catalog as any).title}
                                </h3>
                            </div>
                        </div>
                    );
                })}
            </div>
        </div>
    );
}
