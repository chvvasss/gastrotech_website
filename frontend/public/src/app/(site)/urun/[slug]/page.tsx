"use client";

import { useState, useEffect } from "react";
import { useQuery } from "@tanstack/react-query";
import { useParams } from "next/navigation";
import Link from "next/link";
import Image from "next/image";
import { motion, AnimatePresence } from "framer-motion";
import { ChevronLeft, ChevronRight, Download, FileText, Check, Sparkles, ZoomIn, Ruler, Weight, Share2, Printer, ImageOff, X } from "lucide-react";
import { fetchProductDetail } from "@/lib/api";
import { Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { AddToCartButton } from "@/components/cart";
import { getMediaUrl, formatPrice, cn } from "@/lib/utils";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { PriceDisplay } from "@/components/catalog/price-display";
import { useSiteSettings } from "@/hooks/use-site-settings";
import { useToast } from "@/hooks/use-toast";

export default function ProductDetailPage() {
  const params = useParams();
  const slug = params.slug as string;
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [selectedVariantIndex, setSelectedVariantIndex] = useState(0);
  const [isZoomed, setIsZoomed] = useState(false);
  const { showPrices, catalogMode } = useSiteSettings();
  const { toast } = useToast();

  const { data: product, isLoading, error } = useQuery({
    queryKey: ["product", slug],
    queryFn: () => fetchProductDetail(slug),
    enabled: !!slug,
  });

  // Extract data early with safety checks to allow hooks to run unconditionally
  const images = product?.product_media || [];
  const variants = product?.variants || [];

  // Reset variant index if out of bounds (e.g., product data changed)
  useEffect(() => {
    if (selectedVariantIndex >= variants.length && variants.length > 0) {
      setSelectedVariantIndex(0);
    }
  }, [variants.length, selectedVariantIndex]);

  // Reset image index if out of bounds
  useEffect(() => {
    if (selectedImageIndex >= images.length && images.length > 0) {
      setSelectedImageIndex(0);
    }
  }, [images.length, selectedImageIndex]);

  // Sync state with URL query param
  useEffect(() => {
    if (variants.length > 0) {
      // 1. Handle initial load from URL
      const searchParams = new URLSearchParams(window.location.search);
      const variantParam = searchParams.get('variant');

      if (variantParam) {
        const foundIndex = variants.findIndex(v => v.model_code === variantParam);
        if (foundIndex !== -1) {
          setSelectedVariantIndex(foundIndex);
        }
      }
    }
  }, [variants.length]); // Only run once when variants are loaded

  // 2. Update URL when selection changes
  useEffect(() => {
    if (variants.length > 0) {
      const selectedVariant = variants[selectedVariantIndex];
      if (selectedVariant) {
        const url = new URL(window.location.href);
        const currentVariant = url.searchParams.get('variant');

        if (currentVariant !== selectedVariant.model_code) {
          url.searchParams.set('variant', selectedVariant.model_code);
          window.history.replaceState({}, '', url.toString());
        }
      }
    }
  }, [selectedVariantIndex, variants]);

  // Update image when variant changes if that variant has a specific image
  useEffect(() => {
    if (variants.length > 0 && images.length > 0) {
      // Safe access with bounds check
      const safeIndex = Math.min(selectedVariantIndex, Math.max(0, variants.length - 1));
      const selectedVariant = variants[safeIndex];

      if (!selectedVariant) return;

      // Find image linked to this variant
      const linkedImageIndex = images.findIndex((img) => {
        return img.variant_id === selectedVariant.id;
      });

      if (linkedImageIndex !== -1) {
        setSelectedImageIndex(linkedImageIndex);
      }
    }
  }, [selectedVariantIndex, variants, images]);

  if (isLoading) {
    return (
      <Container className="py-6 lg:py-8">
        <div className="grid gap-6 lg:grid-cols-2">
          <div className="aspect-square w-full rounded-sm animate-pulse bg-muted/50" />
          <div className="space-y-3">
            <div className="h-6 w-32 rounded bg-muted/50" />
            <div className="h-10 w-3/4 rounded bg-muted/50" />
            <div className="h-20 w-full rounded bg-muted/50" />
            <div className="h-10 w-40 rounded bg-muted/50" />
          </div>
        </div>
      </Container>
    );
  }

  if (catalogMode) {
    return (
      <Container className="py-12 text-center">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <h1 className="text-xl font-bold">Katalog Modu Aktif</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Urun detaylari su an goruntulenememektedir. Kategorilerdeki PDF kataloglarimiza goz atabilirsiniz.
          </p>
          <Button asChild size="sm" className="mt-4">
            <Link href="/kategori">Kataloglara Goz At</Link>
          </Button>
        </motion.div>
      </Container>
    );
  }

  if (error || !product) {
    return (
      <Container className="py-12 text-center">
        <motion.div initial={{ opacity: 0 }} animate={{ opacity: 1 }}>
          <h1 className="text-xl font-bold">Ürün Bulunamadı</h1>
          <p className="mt-2 text-sm text-muted-foreground">
            Aradığınız ürün mevcut değil veya kaldırılmış olabilir.
          </p>
          <Button asChild size="sm" className="mt-4">
            <Link href="/kategori">Ürünlere Göz At</Link>
          </Button>
        </motion.div>
      </Container>
    );
  }

  const selectedImage = images[selectedImageIndex];

  // Safe access with bounds check
  const safeVariantIndex = Math.min(selectedVariantIndex, Math.max(0, variants.length - 1));
  const selectedVariant = variants.length > 0 ? variants[safeVariantIndex] : undefined;
  const specKeys = product.spec_keys_resolved || [];

  return (
    <Container className="py-6 lg:py-8">
      {/* Breadcrumb - Clean & Minimal */}
      <nav className="mb-4 flex items-center gap-1.5 text-[11px] text-muted-foreground overflow-x-auto whitespace-nowrap pb-1 scrollbar-hide max-w-full">
        <Link href="/" className="hover:text-primary transition-colors font-medium">Ana Sayfa</Link>
        <ChevronRight className="h-3 w-3 text-muted-foreground/40" />
        <Link href={`/urunler/${product.category_slug}`} className="hover:text-primary transition-colors font-medium">{product.category_name}</Link>
        <ChevronRight className="h-3 w-3 text-muted-foreground/40" />
        <Link href={`/urunler/${product.category_slug}/${product.series_slug}`} className="hover:text-primary transition-colors font-medium">{product.series_name}</Link>
        {product.brand_slug && (
          <>
            <ChevronRight className="h-3 w-3 text-muted-foreground/40" />
            <Link href={`/urunler/${product.category_slug}/${product.series_slug}/${product.brand_slug}`} className="hover:text-primary transition-colors font-medium">{product.brand_name}</Link>
          </>
        )}
        <ChevronRight className="h-3 w-3 text-muted-foreground/40" />
        <span className="text-foreground font-semibold truncate">{product.title_tr}</span>
      </nav>

      <div className="grid gap-6 lg:gap-12 lg:grid-cols-[1fr_1fr] items-start pb-4 lg:pb-0 overflow-hidden">
        {/* Gallery Section - Immersive & Interactive */}
        <div className="space-y-3 w-full min-w-0 lg:sticky lg:top-24 flex flex-col self-start overflow-hidden">
          <div
            className="group relative aspect-square w-full overflow-hidden rounded-sm border border-border/50 bg-white shadow-sm hover:shadow-md transition-all duration-300"
            onClick={() => setIsZoomed(true)}
          >
            {selectedImage ? (
              <motion.div
                key={selectedImageIndex}
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                transition={{ duration: 0.3 }}
                className="absolute inset-0 flex items-center justify-center bg-white cursor-zoom-in"
              >
                <Image
                  src={getMediaUrl(selectedImage.file_url)}
                  alt={selectedImage.alt || product.title_tr || ""}
                  fill
                  className="object-contain p-6 transition-transform duration-500 group-hover:scale-105"
                  priority
                />
              </motion.div>
            ) : (
              <div className="flex h-full w-full items-center justify-center text-muted-foreground/40 bg-muted/5">
                <div className="text-center">
                  <ImageOff className="h-8 w-8 mb-2 text-muted-foreground/30" />
                  <span className="text-sm font-medium">Görsel Yok</span>
                </div>
              </div>
            )}

            {/* Hover Actions */}
            <div className="absolute top-4 right-4 opacity-0 group-hover:opacity-100 transition-all duration-300 translate-y-2 group-hover:translate-y-0 z-10">
              <TooltipProvider>
                <Tooltip>
                  <TooltipTrigger asChild>
                    <button className="h-8 w-8 flex items-center justify-center rounded-full bg-white/90 backdrop-blur shadow-sm hover:bg-white text-muted-foreground hover:text-primary transition-colors border border-border/50">
                      <ZoomIn className="h-4 w-4" />
                    </button>
                  </TooltipTrigger>
                  <TooltipContent side="left">Büyüt</TooltipContent>
                </Tooltip>
              </TooltipProvider>
            </div>

            {/* Navigation Arrows */}
            {images.length > 1 && (
              <>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    const newIndex = selectedImageIndex > 0 ? selectedImageIndex - 1 : images.length - 1;
                    setSelectedImageIndex(newIndex);
                    const media = images[newIndex];
                    if (media && media.variant_id) {
                      const variantIndex = variants.findIndex(v => v.id === media.variant_id);
                      if (variantIndex !== -1) setSelectedVariantIndex(variantIndex);
                    }
                  }}
                  className="absolute left-4 top-1/2 -translate-y-1/2 h-8 w-8 flex items-center justify-center rounded-full bg-white/80 backdrop-blur shadow-sm hover:bg-white text-foreground/80 hover:text-primary transition-all opacity-0 group-hover:opacity-100 -translate-x-4 group-hover:translate-x-0"
                >
                  <ChevronLeft className="h-5 w-5" />
                </button>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    const newIndex = selectedImageIndex < images.length - 1 ? selectedImageIndex + 1 : 0;
                    setSelectedImageIndex(newIndex);
                    const media = images[newIndex];
                    if (media && media.variant_id) {
                      const variantIndex = variants.findIndex(v => v.id === media.variant_id);
                      if (variantIndex !== -1) setSelectedVariantIndex(variantIndex);
                    }
                  }}
                  className="absolute right-4 top-1/2 -translate-y-1/2 h-8 w-8 flex items-center justify-center rounded-full bg-white/80 backdrop-blur shadow-sm hover:bg-white text-foreground/80 hover:text-primary transition-all opacity-0 group-hover:opacity-100 translate-x-4 group-hover:translate-x-0"
                >
                  <ChevronRight className="h-5 w-5" />
                </button>
              </>
            )}

            {/* Badges */}
            <div className="absolute top-4 left-4 flex flex-col gap-2">
              {product.is_featured && (
                <Badge className="bg-amber-500 hover:bg-amber-600 text-white border-none px-2.5 py-0.5 text-[10px] font-semibold shadow-sm">
                  <Sparkles className="mr-1 h-3 w-3" />
                  Öne Çıkan
                </Badge>
              )}
            </div>

            {/* Image Counter */}
            {images.length > 1 && (
              <div className="absolute bottom-3 left-1/2 -translate-x-1/2 bg-black/60 backdrop-blur-sm text-white px-2.5 py-0.5 rounded-full text-[10px] font-medium tracking-wider">
                {selectedImageIndex + 1} / {images.length}
              </div>
            )}
          </div>

          {/* Thumbnails - Horizontal Scroll with constrained width */}
          {images.length > 1 && (
            <div className="w-full overflow-hidden">
              <div className="flex gap-2 overflow-x-auto pb-2 pt-1 scrollbar-hide px-1 max-w-full">
                {images.map((media, index) => (
                  <button
                    key={media.id}
                    onClick={() => {
                      setSelectedImageIndex(index);
                      if (media.variant_id) {
                        const variantIndex = variants.findIndex(v => v.id === media.variant_id);
                        if (variantIndex !== -1) setSelectedVariantIndex(variantIndex);
                      }
                    }}
                    className={cn(
                      "relative h-14 w-14 sm:h-16 sm:w-16 flex-shrink-0 overflow-hidden rounded-sm border-2 bg-white transition-all duration-200",
                      selectedImageIndex === index
                        ? "border-primary ring-2 ring-primary/20 shadow-md scale-105 z-10"
                        : "border-transparent hover:border-gray-200 opacity-70 hover:opacity-100 grayscale hover:grayscale-0"
                    )}
                  >
                    <Image
                      src={getMediaUrl(media.file_url)}
                      alt=""
                      fill
                      className="object-contain p-1"
                    />
                  </button>
                ))}
              </div>
            </div>
          )}
        </div>

        {/* Product Details Section */}
        <div className="flex flex-col gap-6 w-full min-w-0 overflow-hidden">
          <div className="space-y-3">
            {/* Header */}
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-1.5 sm:gap-2 mb-2">
                <Link href={`/urunler/${product.category_slug}/${product.series_slug}/${product.brand_slug}`} className="inline-flex items-center gap-1.5 sm:gap-2 px-2 sm:px-3 py-1 sm:py-1.5 rounded-sm bg-gradient-to-r from-primary/10 to-primary/5 text-primary text-[10px] sm:text-xs font-bold hover:from-primary/20 hover:to-primary/10 transition-all border border-primary/10">
                  {product.brand_logo && (
                    <div className="relative h-6 w-6 sm:h-8 sm:w-8 flex-shrink-0">
                      <Image
                        src={getMediaUrl(product.brand_logo)}
                        alt={product.brand_name || ""}
                        fill
                        className="object-contain"
                      />
                    </div>
                  )}
                  <span className="hidden xs:inline">{product.brand_name?.toUpperCase()}</span>
                  <span className="xs:hidden">{product.brand_name}</span>
                </Link>
                <span className="text-muted-foreground/40 text-[10px]">•</span>
                <Link href={`/urunler/${product.category_slug}/${product.series_slug}`} className="text-xs text-muted-foreground hover:text-foreground transition-colors font-medium">
                  {product.series_name}
                </Link>
              </div>

              {/* Gradient accent bar */}
              <div className="h-0.5 w-12 sm:w-16 bg-gradient-to-r from-primary via-primary/70 to-transparent rounded-full"></div>

              <h1 className="text-xl sm:text-2xl lg:text-3xl font-bold tracking-tight bg-gradient-to-br from-foreground to-foreground/70 bg-clip-text leading-tight">
                {product.title_tr}
              </h1>
            </div>

            {/* Features - Premium Gradient Cards */}
            {product.general_features && product.general_features.length > 0 && (
              <div className="space-y-2">
                <h3 className="text-[10px] font-bold text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                  <div className="h-0.5 w-6 bg-gradient-to-r from-primary to-primary/50 rounded-full"></div>
                  Öne Çıkan Özellikler
                </h3>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                  {product.general_features.map((feature, i) => (
                    <motion.div
                      key={i}
                      initial={{ opacity: 0, y: 10 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ delay: i * 0.05 }}
                      className="group relative overflow-hidden rounded-sm bg-gradient-to-br from-primary/10 via-primary/5 to-transparent border border-primary/20 p-2 hover:border-primary/40 transition-all duration-300 hover:shadow-md hover:shadow-primary/10"
                    >
                      {/* Glossy overlay effect */}
                      <div className="absolute inset-0 bg-gradient-to-br from-white/40 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 pointer-events-none"></div>

                      <div className="relative flex items-start gap-2">
                        {/* Icon with gradient background */}
                        <div className="flex-shrink-0 h-5 w-5 rounded-sm bg-gradient-to-br from-primary to-primary/70 flex items-center justify-center shadow-sm group-hover:shadow-md group-hover:shadow-primary/30 transition-all duration-300">
                          <Check className="h-3 w-3 text-white" strokeWidth={2.5} />
                        </div>

                        {/* Feature text */}
                        <p className="text-xs font-medium text-foreground leading-snug pt-0.5 flex-1">
                          {feature}
                        </p>
                      </div>

                      {/* Subtle shine animation */}
                      <div className="absolute inset-0 -translate-x-full group-hover:translate-x-full transition-transform duration-1000 bg-gradient-to-r from-transparent via-white/10 to-transparent pointer-events-none"></div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

            {/* Quick Actions */}
            <div className="flex items-center gap-1 sm:gap-1.5 pt-1">
              <Button
                variant="ghost"
                size="sm"
                className="h-9 text-xs text-muted-foreground hover:text-foreground px-1.5 sm:px-2"
                onClick={async () => {
                  const shareData = {
                    title: product.title_tr || product.slug,
                    text: `${product.title_tr} - ${product.brand_name || 'Gastrotech'}`,
                    url: window.location.href,
                  };
                  if (navigator.share) {
                    try {
                      await navigator.share(shareData);
                    } catch (e) {
                      // User cancelled or error
                    }
                  } else {
                    // Fallback: copy URL to clipboard
                    await navigator.clipboard.writeText(window.location.href);
                    toast({ description: "Link kopyalandı!" });
                  }
                }}
              >
                <Share2 className="mr-1 h-3 w-3" />
                Paylaş
              </Button>
              <Button variant="ghost" size="sm" className="h-9 text-xs text-muted-foreground hover:text-foreground px-1.5 sm:px-2" onClick={() => window.print()}>
                <Printer className="mr-1 h-2.5 w-2.5 sm:h-3 sm:w-3" />
                <span className="hidden xs:inline">Yazdır</span>
                <span className="xs:hidden">Print</span>
              </Button>
            </div>
          </div>

          <Separator />

          {/* Model Selection */}
          {variants.length > 0 && (
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <h3 className="text-sm font-semibold flex items-center gap-2">
                  <div className="h-4 w-0.5 bg-primary rounded-full"></div>
                  Model Seçenekleri
                </h3>
              </div>

              <div className={cn(
                "grid gap-2",
                variants.length > 6 ? "grid-cols-1 sm:grid-cols-2 lg:grid-cols-2 max-h-[300px] overflow-y-auto pr-1 custom-scrollbar" : "grid-cols-1 sm:grid-cols-2"
              )}>
                {variants.map((variant, index) => (
                  <div
                    key={variant.model_code}
                    onClick={() => setSelectedVariantIndex(index)}
                    className={cn(
                      "group relative flex flex-col p-2 rounded-sm border-2 cursor-pointer transition-all duration-200 hover:shadow-sm",
                      selectedVariantIndex === index
                        ? "border-primary bg-primary/5 z-10"
                        : "border-transparent bg-muted/30 hover:bg-muted/50 hover:border-border"
                    )}
                  >
                    <div className="flex justify-between items-start mb-0.5">
                      <span className={cn(
                        "font-bold text-xs",
                        selectedVariantIndex === index ? "text-primary" : "text-foreground"
                      )}>
                        {variant.model_code}
                      </span>
                      {selectedVariantIndex === index && (
                        <span className="flex h-3.5 w-3.5 shrink-0 items-center justify-center rounded-full bg-primary text-white">
                          <Check className="h-2 w-2" />
                        </span>
                      )}
                    </div>

                    {variant.name_tr && (
                      <p className="text-[10px] text-muted-foreground line-clamp-2 mb-1.5 min-h-[2em]">{variant.name_tr}</p>
                    )}

                    {showPrices && variant.list_price && (
                      <div className="mt-auto pt-1.5 border-t border-dashed border-border/50">
                        <p className={cn(
                          "text-xs font-bold text-right tabular-nums",
                          selectedVariantIndex === index ? "text-foreground" : "text-muted-foreground"
                        )}>
                          {formatPrice(variant.list_price)}
                        </p>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Selected Variant Box */}
          <AnimatePresence mode="wait">
            {selectedVariant && (
              <motion.div
                key={selectedVariant.id}
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -10 }}
                transition={{ duration: 0.2 }}
                className="bg-card rounded-sm border shadow-sm overflow-hidden"
              >
                {/* Price Header */}
                <div className="px-4 py-3 bg-muted/30 border-b flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-0.5">Seçili Model</p>
                    <p className="text-base font-bold text-foreground">{selectedVariant.model_code}</p>
                  </div>

                  {showPrices && (
                    <div className="text-right">
                      <PriceDisplay
                        price={selectedVariant.list_price}
                        className="text-2xl font-extrabold text-primary tracking-tight"
                      />
                      <p className="text-[10px] text-muted-foreground mt-0.5">+ KDV</p>
                    </div>
                  )}
                </div>

                {/* Actions & Specs */}
                <div className="p-4 space-y-4">
                  {/* Key Specs Grid */}
                  <div className="grid grid-cols-1 xs:grid-cols-2 gap-2 sm:gap-3">
                    {selectedVariant.dimensions && (
                      <div className="bg-muted/20 p-2.5 rounded-sm border border-border/50">
                        <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                          <Ruler className="h-3.5 w-3.5" />
                          <span className="text-[10px] font-semibold uppercase">Boyutlar</span>
                        </div>
                        <p className="font-mono font-medium text-foreground text-xs">{selectedVariant.dimensions} mm</p>
                      </div>
                    )}
                    {selectedVariant.weight_kg && (
                      <div className="bg-muted/20 p-2.5 rounded-sm border border-border/50">
                        <div className="flex items-center gap-1.5 text-muted-foreground mb-1">
                          <Weight className="h-3.5 w-3.5" />
                          <span className="text-[10px] font-semibold uppercase">Ağırlık</span>
                        </div>
                        <p className="font-mono font-medium text-foreground text-xs">{selectedVariant.weight_kg} kg</p>
                      </div>
                    )}
                  </div>

                  <div className="flex flex-col gap-2 sm:flex-row sm:gap-2.5">
                    <AddToCartButton
                      variantId={selectedVariant.id}
                      size="lg"
                      className="w-full sm:flex-1 font-bold text-xs sm:text-sm shadow-lg shadow-primary/20 hover:shadow-primary/30 transition-all"
                    />
                    <Button variant="outline" size="lg" className="w-full sm:flex-1 border-2 font-semibold hover:bg-muted text-xs sm:text-sm" asChild>
                      <Link href="/iletisim">
                        <FileText className="mr-2 h-3.5 w-3.5" />
                        Teklif İste
                      </Link>
                    </Button>
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>

          {/* Description & Downloads */}
          <div className="space-y-3 pt-3">
            {product.long_description && (
              <div className="prose prose-sm max-w-none">
                <h4 className="text-foreground font-semibold mb-1.5 text-sm flex items-center gap-2">
                  <div className="h-4 w-0.5 bg-primary rounded-full"></div>
                  Ürün Açıklaması
                </h4>
                <div
                  className="leading-relaxed text-sm text-foreground/80"
                  dangerouslySetInnerHTML={{ __html: product.long_description }}
                />
              </div>
            )}

            {product.pdf_ref && (
              <div className="pt-1.5">
                <Button variant="secondary" className="w-full sm:w-auto h-auto py-2.5 px-3 justify-start text-xs" asChild>
                  <a href={getMediaUrl(`/api/v1/media/${product.pdf_ref}/file/`)} target="_blank" rel="noreferrer">
                    <div className="h-8 w-8 rounded-full bg-red-100 text-red-600 flex items-center justify-center mr-2.5">
                      <FileText className="h-4 w-4" />
                    </div>
                    <div className="text-left">
                      <span className="block text-foreground font-semibold text-xs">Teknik Doküman</span>
                      <span className="block text-muted-foreground text-[10px]">PDF İndir</span>
                    </div>
                    <Download className="ml-auto h-3.5 w-3.5 text-muted-foreground" />
                  </a>
                </Button>
              </div>
            )}
          </div>

        </div>
      </div>

      {/* Full Spec Table */}
      {variants.length > 0 && (
        <div className="mt-16 space-y-6 overflow-hidden">
          <div className="flex items-center gap-3">
            <div className="h-8 w-1 bg-primary rounded-full shadow-sm" />
            <div>
              <h2 className="text-xl font-bold tracking-tight">Teknik Tablo</h2>
              <p className="text-xs text-muted-foreground mt-0.5">Tüm modellerin teknik özelliklerini detaylı karşılaştırın.</p>
            </div>
          </div>

          <div className="rounded-sm border border-border/50 overflow-hidden shadow-sm bg-white/50 backdrop-blur-sm">
            <div className="overflow-x-auto">
              <table className="w-full text-xs">
                <thead className="bg-muted/30 border-b border-border/50">
                  <tr>
                    <th className="px-4 py-3 text-left font-bold text-foreground text-[11px]">Model</th>
                    <th className="px-4 py-3 text-left font-semibold text-muted-foreground text-[10px]">Boyutlar</th>
                    <th className="px-4 py-3 text-left font-semibold text-muted-foreground text-[10px]">Ağırlık</th>
                    {specKeys.map(k => (
                      <th key={k.slug} className="px-4 py-3 text-left font-semibold text-muted-foreground whitespace-nowrap text-[10px]">
                        {k.label_tr}
                      </th>
                    ))}
                    {showPrices && (
                      <th className="px-6 py-4 text-right font-semibold text-muted-foreground">Fiyat</th>
                    )}
                    <th className="px-6 py-4 w-[80px]"></th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-border/40">
                  {variants.map((v, i) => (
                    <tr
                      key={v.id}
                      className={cn(
                        "hover:bg-muted/30 cursor-pointer transition-colors group",
                        selectedVariantIndex === i ? "bg-primary/5 hover:bg-primary/10" : ""
                      )}
                      onClick={() => setSelectedVariantIndex(i)}
                    >
                      <td className="px-4 py-3 font-bold text-primary group-hover:underline underline-offset-2 text-xs">{v.model_code}</td>
                      <td className="px-4 py-3 font-mono text-muted-foreground text-[10px]">{v.dimensions || "-"}</td>
                      <td className="px-4 py-3 text-muted-foreground text-xs">{v.weight_kg ? `${v.weight_kg} kg` : "-"}</td>
                      {specKeys.map(k => {
                        const val = v.spec_row?.find(s => s.key === k.slug)?.value;
                        return <td key={k.slug} className="px-4 py-3 text-foreground/90 text-xs">{val || "-"}</td>;
                      })}
                      {showPrices && (
                        <td className="px-6 py-4 text-right font-bold text-foreground tabular-nums">
                          {v.list_price ? formatPrice(v.list_price) : "-"}
                        </td>
                      )}
                      <td className="px-6 py-4 text-center">
                        {selectedVariantIndex === i ? (
                          <div className="flex items-center justify-center">
                            <div className="h-6 w-6 rounded-full bg-primary text-white flex items-center justify-center shadow-md animate-in zoom-in spin-in-12">
                              <Check className="h-3.5 w-3.5" />
                            </div>
                          </div>
                        ) : (
                          <div className="flex items-center justify-center">
                            <div className="h-4 w-4 rounded-full border-2 border-muted-foreground/30 group-hover:border-primary/50 transition-colors" />
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Mobile Sticky Bar - Premium & Tall */}
      <AnimatePresence>
        {selectedVariant && (
          <motion.div
            initial={{ y: 100 }}
            animate={{ y: 0 }}
            exit={{ y: 100 }}
            transition={{ type: "spring", stiffness: 300, damping: 30 }}
            className="fixed bottom-0 left-0 right-0 z-40 lg:hidden safe-area-bottom"
          >
            {/* Background */}
            <div className="absolute inset-0 bg-white/95 backdrop-blur-xl shadow-[0_-4px_24px_rgba(0,0,0,0.1)] border-t border-border/40" />

            {/* Content */}
            <div className="relative px-4 py-3 sm:py-4">
              <div className="flex items-center gap-3">
                {/* Product info */}
                <div className="flex-1 min-w-0">
                  <p className="text-[10px] sm:text-xs text-muted-foreground font-semibold uppercase tracking-wide truncate mb-0.5">
                    {selectedVariant.model_code}
                  </p>
                  <PriceDisplay
                    price={selectedVariant.list_price}
                    className="text-base sm:text-lg font-bold text-primary"
                  />
                </div>

                {/* Actions */}
                <div className="flex items-center gap-2 flex-shrink-0">
                  <Button variant="outline" size="sm" className="h-10 sm:h-11 px-3 sm:px-4 rounded-sm border-primary/20 text-xs font-semibold hover:bg-primary/5" asChild>
                    <Link href="/iletisim">
                      <FileText className="mr-1.5 h-3.5 w-3.5" />
                      <span className="hidden xs:inline">Teklif</span>
                    </Link>
                  </Button>
                  <AddToCartButton
                    variantId={selectedVariant.id}
                    className="shadow-lg shadow-primary/20 text-xs sm:text-sm px-4 sm:px-6 h-10 sm:h-11 rounded-sm whitespace-nowrap font-bold"
                  />
                </div>
              </div>
            </div>
          </motion.div>
        )}
      </AnimatePresence>

      {/* Spacer for mobile sticky bar */}
      <div className="h-20 sm:h-24 lg:hidden" />

      {/* Lightbox */}
      <AnimatePresence>
        {isZoomed && selectedImage && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 z-50 flex items-center justify-center bg-background/95 p-4 backdrop-blur-md"
            onClick={() => setIsZoomed(false)}
          >
            <div className="relative h-full w-full max-w-5xl max-h-[90vh] flex items-center justify-center">
              <Image
                src={getMediaUrl(selectedImage.file_url)}
                alt=""
                fill
                className="object-contain drop-shadow-2xl"
              />
              <button
                onClick={() => setIsZoomed(false)}
                className="absolute top-4 right-4 text-muted-foreground hover:text-foreground bg-muted/20 hover:bg-muted p-2 rounded-sm transition-colors"
              >
                <X className="h-6 w-6" />
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>


    </Container>
  );
}

