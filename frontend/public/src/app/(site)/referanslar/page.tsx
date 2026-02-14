"use client";

import Link from "next/link";
import Image from "next/image";
import { Container } from "@/components/layout";
import { Marquee, ReferenceGrid } from "@/components/catalog";

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

// Project gallery images
const PROJECT_IMAGES = [
  { src: "/projects/IMG_6015.jpg", alt: "Profesyonel Mutfak Projesi" },
  { src: "/projects/IMG_6019.jpg", alt: "Endüstriyel Mutfak Kurulumu" },
  { src: "/projects/IMG_6041.jpg", alt: "Otel Mutfak Projesi" },
  { src: "/projects/IMG_6053.jpg", alt: "Restoran Mutfak Ekipmanları" },
  { src: "/projects/IMG_6055.jpg", alt: "Mutfak Sistemleri" },
  { src: "/projects/IMG_8421.jpg", alt: "Gastrotech Referans Projesi" },
  { src: "/projects/IMG_8427.jpg", alt: "Endüstriyel Mutfak Çözümleri" },
  { src: "/projects/IMG_0285-1365x2048.jpg", alt: "Profesyonel Ekipman Kurulumu" },
];



export default function ReferencesPage() {
  return (
    <>
      {/* Header */}
      <section className="relative overflow-hidden bg-gradient-to-br from-primary via-primary to-primary/90 py-16 lg:py-24">
        {/* Decorative elements - Blurred circles */}
        <div className="absolute -right-20 -top-20 h-64 w-64 rounded-sm bg-white/10 blur-[100px]" />
        <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-sm bg-black/20 blur-[100px]" />

        {/* Geometric shapes */}
        <div className="absolute top-8 left-8 w-20 h-20 border-2 border-white/20 rounded-sm hidden lg:block" />
        <div className="absolute top-12 left-12 w-12 h-12 border border-white/10 rounded-sm hidden lg:block" />
        <div className="absolute bottom-8 right-8 w-24 h-24 border-2 border-white/15 rounded-sm hidden lg:block" />
        <div className="absolute top-1/2 right-16 w-4 h-4 bg-white/20 rotate-45 -translate-y-1/2 hidden md:block" />
        <div className="absolute bottom-16 left-1/4 w-6 h-6 bg-white/10 rounded-sm hidden md:block" />

        {/* Lines */}
        <div className="absolute top-0 left-1/3 w-px h-16 bg-gradient-to-b from-transparent via-white/20 to-transparent hidden lg:block" />
        <div className="absolute bottom-0 right-1/3 w-px h-16 bg-gradient-to-t from-transparent via-white/20 to-transparent hidden lg:block" />
        <div className="absolute top-1/2 left-4 w-12 h-0.5 bg-white/15 -translate-y-1/2 hidden md:block" />

        <Container className="relative text-center z-10">
          <h1 className="text-3xl font-bold text-white lg:text-5xl">Referanslarımız</h1>
          <p className="mx-auto mt-4 max-w-2xl text-lg text-white/90">
            {`1985'ten bu yana Türkiye'nin ve dünyanın önde gelen kuruluşlarına
            hizmet vermenin gururunu yaşıyoruz.`}
          </p>
        </Container>
      </section>

      {/* Marquee */}
      <section className="border-b py-12">
        <Container>
          <Marquee items={REFERENCES} speed="slow" />
        </Container>
      </section>

      {/* Project Gallery - Bento Grid */}
      <section className="py-16 lg:py-24">
        <Container>
          <div className="mb-12 text-center">
            <h2 className="text-2xl font-bold lg:text-3xl">Seçkin Projelerimizden Kareler</h2>
            <p className="mt-2 text-muted-foreground">
              Sektördeki imzamızı taşıyan bazı referans projelerimiz
            </p>
          </div>

          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 auto-rows-[200px] gap-4">
            {PROJECT_IMAGES.map((image, i) => (
              <div
                key={i}
                className={`relative group overflow-hidden rounded-sm transition-all duration-300
                  ${i === 0 || i === 7 ? "md:col-span-2 md:row-span-2" : ""}
                  ${i === 2 ? "md:row-span-2" : ""}
                  ${i === 4 ? "md:col-span-2" : ""}
                `}
              >
                <Image
                  src={image.src}
                  alt={image.alt}
                  fill
                  className="object-cover transition-transform duration-500 group-hover:scale-105"
                  sizes="(max-width: 768px) 50vw, (max-width: 1024px) 33vw, 25vw"
                />
                {/* Overlay on hover */}
                <div className="absolute inset-0 bg-gradient-to-t from-black/60 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300" />
                <div className="absolute bottom-0 left-0 right-0 p-4 text-white opacity-0 group-hover:opacity-100 transition-opacity duration-300">
                  <p className="text-sm font-medium">{image.alt}</p>
                </div>
              </div>
            ))}

            {/* "You Are Next" Signature Card */}
            <Link
              href="/iletisim"
              className="relative group overflow-hidden rounded-sm border-2 border-dashed border-primary/30 hover:border-primary bg-primary/5 hover:bg-primary/10 transition-all duration-300 flex flex-col items-center justify-center p-6 text-center cursor-pointer col-span-2 md:col-span-2 md:row-span-2"
            >
              <div className="h-16 w-16 mb-4 rounded-full bg-white flex items-center justify-center shadow-sm group-hover:scale-110 transition-transform duration-300">
                <span className="text-2xl font-bold text-primary">?</span>
              </div>
              <h3 className="text-lg font-bold text-foreground mb-2">Sıradaki Siz Olun</h3>
              <p className="text-sm text-muted-foreground mb-4 max-w-xs mx-auto">
                Sizin başarı hikayenizi de buraya ekleyelim.
              </p>
              <span className="inline-flex items-center text-xs font-bold text-primary uppercase tracking-wider group-hover:underline">
                Projeyi Başlat
              </span>
            </Link>
          </div>
        </Container>
      </section>

      {/* Reduced Motion Fallback */}
      <section className="hidden py-16 motion-reduce:block">
        <Container>
          <h2 className="mb-8 text-center text-xl font-semibold">
            Tüm Referanslarımız
          </h2>
          <ReferenceGrid items={REFERENCES} />
        </Container>
      </section>
    </>
  );
}
