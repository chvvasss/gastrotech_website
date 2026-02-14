"use client";

import { useState, useEffect, useRef } from "react";
import { useQuery } from "@tanstack/react-query";
import { Download, FileText, Maximize2, ExternalLink } from "lucide-react";
import { fetchCategoryCatalogs } from "@/lib/api";
import { getMediaUrl } from "@/lib/utils";
import type { CategoryCatalog } from "@/lib/api/schemas";

/* ─────────────────────────────────────────────
   PDF Thumbnail Component
   ──────────────────────────────────────────── */
// Singleton PDF.js Loader
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

function PDFThumbnail({ url, className }: { url: string; className?: string }) {
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

                const viewport = page.getViewport({ scale: 0.6 });
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
    }, [url]);

    return (
        <div className={`relative overflow-hidden bg-stone-100 ${className || ""}`}>
            {!loaded && (
                <div className="absolute inset-0 flex items-center justify-center bg-stone-800/10">
                    <div className="h-5 w-5 animate-spin rounded-full border-2 border-stone-300 border-t-stone-500" />
                </div>
            )}
            <canvas ref={canvasRef} className={`w-full h-full object-cover transition-opacity duration-500 ${loaded ? "opacity-100" : "opacity-0"}`} />
        </div>
    );
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
            <div className="flex flex-col items-center justify-center py-24 text-center bg-stone-50 rounded-lg border border-dashed border-stone-200">
                <div className="h-20 w-20 rounded-full bg-stone-100 flex items-center justify-center mb-6">
                    <FileText className="h-10 w-10 text-stone-400" />
                </div>
                <h3 className="text-xl font-bold text-stone-700 mb-2">Bu kategori için katalog bulunmamaktadır</h3>
                <p className="text-stone-500 max-w-md">Katalog dosyaları yakında eklenecektir.</p>
            </div>
        );
    }

    /* Grid View */
    return (
        <div className="w-full">
            <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-6">
                {catalogs.map((catalog) => (
                    <div
                        key={catalog.id}
                        className="group relative flex flex-col cursor-pointer"
                        onClick={() => {
                            if (catalog.file_url) {
                                window.open(getMediaUrl(catalog.file_url), '_blank');
                            }
                        }}
                    >
                        {/* Cover Image */}
                        <div className="relative aspect-[1/1.4] w-full overflow-hidden rounded-lg shadow-sm bg-stone-100 border border-stone-200 group-hover:shadow-md transition-all duration-300">
                            {/* Thumbnail or Icon */}
                            {catalog.file_url ? (
                                <PDFThumbnail
                                    url={getMediaUrl(catalog.file_url)}
                                    className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500"
                                />
                            ) : (
                                <div className="absolute inset-0 flex items-center justify-center text-stone-300">
                                    <FileText className="h-12 w-12" />
                                </div>
                            )}

                            {/* Overlay */}
                            <div className="absolute inset-0 bg-black/0 group-hover:bg-black/10 transition-colors duration-300 flex items-center justify-center opacity-0 group-hover:opacity-100">
                                <div className="bg-white/90 backdrop-blur rounded-full p-3 shadow-lg transform translate-y-2 group-hover:translate-y-0 transition-all duration-300">
                                    <ExternalLink className="h-5 w-5 text-stone-700" />
                                </div>
                            </div>
                        </div>

                        {/* Title */}
                        <div className="mt-3 text-center">
                            <h3 className="text-sm font-medium text-stone-700 group-hover:text-amber-600 transition-colors line-clamp-2">
                                {catalog.title_tr || catalog.title}
                            </h3>
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
}
