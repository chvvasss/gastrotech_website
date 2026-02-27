"use client";

import Link from "next/link";
import Image from "next/image";
import { useQuery } from "@tanstack/react-query";
import { useState, useEffect } from "react";
import { ArrowRight, Award, Globe, Users } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { fetchNav } from "@/lib/api";
import { Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { CategoryGrid, Marquee } from "@/components/catalog";
import { PhotoGallery } from "@/components/gallery";
import { FeatureSplitSection } from "@/components/home";

// Logo references from the filesystem
const REFERENCES = [
  "/references/gastrotech-logo1-1-100x100.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-000.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-002.jpg",
  "/references/Gastrotech_2.sayfa_.pdf-image-004.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-006.jpg",
  "/references/Gastrotech_2.sayfa_.pdf-image-008.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-010.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-012.jpg",
  "/references/Gastrotech_2.sayfa_.pdf-image-013.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-017.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-019.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-022.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-024.png",
  "/references/Gastrotech_2.sayfa_.pdf-image-026.png",
];

// Hero background images from gallery
const HERO_BACKGROUND_IMAGES = [
  "/assets/hero-bg.png",
  "/assets/hero-bg-2.png",
  "/assets/hero-bg-3.png",
  "/assets/hero-bg-4.png",
];

// Stats for hero section
const HERO_STATS = [
  { icon: Award, value: "40+", label: "Yıllık Tecrübe" },
  { icon: Globe, value: "50+", label: "Ülkeye İhracat" },
  { icon: Users, value: "1000+", label: "Mutlu Müşteri" },
];

const GALLERY_IMAGES = [
  {
    id: "1",
    src: "/projects/IMG_6015.jpg",
    alt: "Profesyonel Mutfak Projesi",
    title: "Profesyonel Mutfak Çözümleri",
  },
  {
    id: "2",
    src: "/projects/IMG_6041.jpg",
    alt: "Otel Mutfak Projesi",
    title: "Otel Mutfak Kurulumu",
  },
  {
    id: "3",
    src: "/projects/IMG_6053.jpg",
    alt: "Restoran Mutfak Ekipmanları",
    title: "Restoran Projeleri",
  },
];

export default function HomePage() {
  const { data: categories = [], isLoading: loadingCategories } = useQuery({
    queryKey: ["nav"],
    queryFn: fetchNav,
  });

  // Auto-rotating hero background images
  const [currentImageIndex, setCurrentImageIndex] = useState(0);

  useEffect(() => {
    const interval = setInterval(() => {
      setCurrentImageIndex((prev) => (prev + 1) % HERO_BACKGROUND_IMAGES.length);
    }, 5000); // 5 seconds

    return () => clearInterval(interval);
  }, []);

  return (
    <>
      {/* Hero Section - Rotating Background */}
      <section className="relative min-h-[60vh] lg:min-h-[75vh] flex flex-col justify-center overflow-hidden bg-black">
        {/* Background Images */}
        <div className="absolute inset-0 z-0">
          <AnimatePresence mode="wait">
            <motion.div
              key={currentImageIndex}
              initial={{ opacity: 0 }}
              animate={{ opacity: 0.7 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1 }}
              className="absolute inset-0"
            >
              <Image
                src={HERO_BACKGROUND_IMAGES[currentImageIndex]}
                alt="Gastrotech Endüstriyel Mutfak"
                fill
                className="object-cover"
                priority
                sizes="100vw"
              />
            </motion.div>
          </AnimatePresence>
          {/* Overlay */}
          <div className="absolute inset-0 bg-black/40" />
        </div>

        {/* Content */}
        <Container className="relative z-10 py-20 flex-1 flex flex-col justify-center items-center">
          <motion.div
            className="max-w-4xl mx-auto text-center"
            initial={{ opacity: 0, y: 30 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.8 }}
          >
            <h1 className="text-4xl sm:text-5xl lg:text-6xl font-bold text-white tracking-tight leading-tight mb-6 drop-shadow-lg">
              Profesyonel <span className="text-primary">Mutfak Çözümleri</span>
            </h1>

            <p className="text-lg sm:text-xl text-gray-200 max-w-2xl mx-auto font-normal leading-relaxed mb-10 drop-shadow-md">
              1985&apos;ten bu yana endüstriyel mutfak sektöründe kalite öncüsü.
              <br className="hidden sm:block" />
              Size özel projelendirme ve üretim seçenekleriyle.
            </p>

            <div className="flex flex-col sm:flex-row justify-center gap-4">
              <Button
                asChild
                size="lg"
                className="bg-primary hover:bg-primary/90 text-white rounded-sm h-12 px-8 text-base font-semibold tracking-wide shadow-lg shadow-primary/20"
              >
                <Link href="/iletisim">
                  Hemen Teklif Al
                  <ArrowRight className="ml-2 h-4 w-4" />
                </Link>
              </Button>
              <Button
                asChild
                size="lg"
                variant="outline"
                className="bg-transparent border-2 border-white text-white hover:bg-white hover:text-black rounded-sm h-12 px-8 text-base font-semibold tracking-wide"
              >
                <Link href="/kategori">
                  Ürünleri İncele
                </Link>
              </Button>
            </div>
          </motion.div>
        </Container>

        {/* Bottom Section: Indicators & Stats */}
        <div className="relative z-10 w-full border-t border-white/10 bg-black/30 backdrop-blur-md">
          <Container>
            <div className="flex flex-col sm:flex-row items-center justify-between gap-4 py-5">

              {/* Square Indicators */}
              <div className="flex gap-2.5 order-2 sm:order-1">
                {HERO_BACKGROUND_IMAGES.map((_, idx) => (
                  <button
                    key={idx}
                    onClick={() => setCurrentImageIndex(idx)}
                    className={`h-2.5 transition-all duration-300 rounded-sm ${idx === currentImageIndex ? "bg-primary w-8" : "bg-white/30 hover:bg-white/50 w-2.5"
                      }`}
                    aria-label={`Go to slide ${idx + 1}`}
                  />
                ))}
              </div>

              {/* Stats - Linear Layout with Dividers */}
              <div className="flex items-center gap-6 sm:gap-8 order-1 sm:order-2">
                {HERO_STATS.map((stat, i) => (
                  <div key={i} className={`flex items-center gap-3 ${i !== 0 ? "border-l border-white/20 pl-6 sm:pl-8" : ""}`}>
                    <stat.icon className="h-6 w-6 sm:h-7 sm:w-7 text-primary/90 stroke-[1.5]" />
                    <div>
                      <div className="text-xl sm:text-2xl font-bold text-white leading-none tracking-tight">{stat.value}</div>
                      <div className="text-[10px] sm:text-xs text-gray-300 uppercase tracking-wider mt-0.5">{stat.label}</div>
                    </div>
                  </div>
                ))}
              </div>

            </div>
          </Container>
        </div>
      </section>

      {/* Categories Grid Section - Reverted to Standard Grid */}
      <section className="py-16 lg:py-24 border-b bg-gray-50/50 relative overflow-hidden">
        {/* Subtle decorative elements */}
        <div className="absolute top-0 right-0 w-72 h-72 bg-primary/5 rounded-sm translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 left-0 w-56 h-56 bg-primary/5 rounded-sm -translate-x-1/2 translate-y-1/2" />
        <div className="absolute top-20 left-8 w-2 h-16 bg-primary/10 hidden lg:block" />
        <div className="absolute bottom-20 right-8 w-2 h-16 bg-primary/10 hidden lg:block" />

        <Container className="relative z-10">
          <div className="mb-10 flex flex-col sm:flex-row sm:items-end justify-between gap-4">
            <div className="flex items-center gap-4">
              <div className="h-10 w-1.5 rounded-sm bg-primary shadow-sm" />
              <div>
                <h2 className="text-2xl font-bold lg:text-3xl text-foreground tracking-tight">Kategorilerimiz</h2>
                <p className="text-muted-foreground mt-1 text-sm sm:text-base">
                  Profesyonel ihtiyaçlarınız için geniş ürün yelpazesi
                </p>
              </div>
            </div>
            <Link
              href="/kategori"
              className="hidden sm:flex items-center gap-2 text-sm font-semibold text-primary hover:text-primary/80 transition-colors"
            >
              Tüm Kategorileri Gör
              <ArrowRight className="h-4 w-4" />
            </Link>
          </div>

          {loadingCategories ? (
            <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4">
              {[1, 2, 3, 4].map((i) => (
                <div key={i} className="h-64 w-full rounded-sm bg-muted animate-pulse border border-border/50" />
              ))}
            </div>
          ) : (
            <CategoryGrid categories={categories} />
          )}

          {categories.length <= 5 && (
            <div className="mt-8 sm:hidden text-center">
              <Link href="/kategori">
                <Button variant="outline" className="w-full rounded-sm">
                  Tüm Kategorileri Gör
                </Button>
              </Link>
            </div>
          )}
        </Container>
      </section>

      {/* Feature Split Section - About/Catalog */}
      <FeatureSplitSection
        title="Profesyonel Mutfakta 40 Yıllık Deneyim"
        description="Gastrotech, 1985'ten bu yana endüstriyel mutfak sektöründe kalite ve inovasyonun öncüsüdür. Geniş ürün yelpazemiz, uzman ekibimiz ve satış sonrası destek hizmetlerimizle işletmenizin yanındayız."
        bullets={[
          "Geniş ürün yelpazesi ve stok gücü",
          "Hızlı teslimat ve montaj desteği",
          "7/24 Teknik servis ve yedek parça",
        ]}
        imageSrc="/projects/IMG_6019.jpg"
        imageAlt="Gastrotech Endüstriyel Mutfak"
        ctaLabel="Hakkımızda Daha Fazla"
        ctaHref="/kurumsal"
        imagePosition="right"
      />

      {/* Photo Gallery Section */}
      <section className="py-16 lg:py-24 bg-white">
        <Container>
          <motion.div
            className="mb-12 text-center"
            initial={{ opacity: 0, y: 20 }}
            whileInView={{ opacity: 1, y: 0 }}
            viewport={{ once: true }}
          >
            <h2 className="text-2xl lg:text-3xl font-bold tracking-tight mb-4">Projelerimizden Görüntüler</h2>
            <div className="h-1 w-20 bg-primary mx-auto rounded-sm mb-6"></div>
            <p className="text-muted-foreground max-w-2xl mx-auto">
              Yurt içi ve yurt dışında gerçekleştirdiğimiz anahtar teslim mutfak projelerinden seçkiler.
            </p>
          </motion.div>

          <PhotoGallery images={GALLERY_IMAGES} columns={3} />
        </Container>
      </section>

      {/* CTA Section - Light & Clean */}
      <section className="py-16 lg:py-24 relative overflow-hidden bg-primary/5">
        {/* Background pattern */}
        <div className="absolute inset-0 opacity-[0.03]" style={{ backgroundImage: 'radial-gradient(circle, #000000 1px, transparent 1px)', backgroundSize: '30px 30px' }}></div>

        {/* Decorative shapes */}
        <div className="absolute top-0 left-0 w-48 h-48 bg-primary/10 rounded-sm -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-64 h-64 bg-primary/10 rounded-sm translate-x-1/3 translate-y-1/3" />
        <div className="absolute top-1/2 left-4 w-3 h-20 bg-primary/15 -translate-y-1/2 hidden lg:block" />
        <div className="absolute top-1/2 right-4 w-3 h-20 bg-primary/15 -translate-y-1/2 hidden lg:block" />
        <div className="absolute top-8 right-1/4 w-6 h-6 border-2 border-primary/20 rotate-45 hidden md:block" />
        <div className="absolute bottom-8 left-1/4 w-4 h-4 bg-primary/20 rounded-sm hidden md:block" />

        <Container className="relative z-10">
          <motion.div
            className="rounded-sm border border-border/50 bg-white p-8 lg:p-16 text-center shadow-2xl shadow-primary/5 overflow-hidden relative"
            initial={{ opacity: 0, scale: 0.95 }}
            whileInView={{ opacity: 1, scale: 1 }}
            viewport={{ once: true }}
          >
            <div className="absolute -top-24 -right-24 w-64 h-64 bg-primary/10 blur-[120px] rounded-sm pointer-events-none"></div>
            <div className="absolute -bottom-24 -left-24 w-64 h-64 bg-blue-500/10 blur-[120px] rounded-sm pointer-events-none"></div>

            <div className="relative z-10 max-w-2xl mx-auto">
              <h2 className="text-3xl font-bold lg:text-4xl mb-6 text-foreground tracking-tight">
                Projeniz için Özel Çözümler
              </h2>
              <p className="text-lg text-muted-foreground mb-8 leading-relaxed">
                İster yeni bir işletme kuruyor olun, ister mevcut mutfağınızı yenileyin.
                Uzman ekibimiz ücretsiz keşif ve projelendirme için hazır.
              </p>

              <div className="flex flex-col sm:flex-row justify-center gap-4">
                <Button
                  asChild
                  size="lg"
                  className="bg-primary hover:bg-primary/90 text-white rounded-sm h-12 px-8 text-base font-semibold shadow-lg shadow-primary/20"
                >
                  <Link href="/iletisim">
                    Hemen Teklif İste
                  </Link>
                </Button>
                <Button
                  asChild
                  size="lg"
                  variant="outline"
                  className="bg-transparent border-2 border-primary/20 text-primary hover:bg-primary/5 hover:border-primary/40 rounded-sm h-12 px-8 font-semibold"
                >
                  <Link href="/referanslar">Referanslarımız</Link>
                </Button>
              </div>
            </div>
          </motion.div>
        </Container>
      </section>

      {/* References Marquee */}
      <section className="border-t py-12 bg-gray-50">
        <Container>
          <p className="text-center text-sm font-semibold text-muted-foreground uppercase tracking-wider mb-8">
            Bize Güvenen Markalar
          </p>
          <Marquee items={REFERENCES} speed="slow" />
        </Container>
      </section>
    </>
  );
}
