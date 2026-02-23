"use client";

import Link from "next/link";
import Image from "next/image";
import { MapPin, Phone, Mail, Clock, ChevronRight } from "lucide-react";
import { Container } from "./container";

const QUICK_LINKS = [
  { label: "Ürünler", href: "/kategori" },
  { label: "Kataloglar", href: "/kataloglar" },
  { label: "Referanslar", href: "/referanslar" },
  { label: "Blog", href: "/blog" },
  { label: "Kurumsal", href: "/kurumsal" },
  { label: "İletişim", href: "/iletisim" },
];

const SERVICES = [
  { label: "Satış Sonrası Destek", href: "/satis-sonrasi" },
  { label: "Teklif İste", href: "/iletisim" },
  { label: "Teknik Servis", href: "/satis-sonrasi" },
  { label: "Yedek Parça", href: "/satis-sonrasi" },
];

export function Footer() {
  const currentYear = new Date().getFullYear();

  return (
    <footer className="relative bg-primary text-primary-foreground overflow-hidden">
      {/* Top accent line */}
      <div className="h-1 w-full bg-gradient-to-r from-transparent via-white/30 to-transparent" />

      {/* Subtle background pattern */}
      <div
        className="absolute inset-0 opacity-[0.05]"
        style={{
          backgroundImage: "radial-gradient(circle, #ffffff 1px, transparent 1px)",
          backgroundSize: "24px 24px",
        }}
      />

      {/* Main Footer Content */}
      <Container className="relative z-10">
        <div className="py-12 lg:py-16">
          {/* Top: Logo + Description */}
          <div className="flex flex-col lg:flex-row lg:items-start lg:justify-between gap-8 lg:gap-16 mb-10 lg:mb-14">
            <div className="max-w-sm">
              <Link href="/" className="inline-block mb-4">
                <div className="relative h-10 w-[180px]">
                  <Image
                    src="/assets/logo-white.png"
                    alt="Gastrotech"
                    fill
                    className="object-contain object-left"
                    sizes="180px"
                    onError={(e) => {
                      // Fallback if white logo doesn't exist
                      (e.target as HTMLImageElement).src = "/assets/logo.png";
                    }}
                  />
                </div>
              </Link>
              <p className="text-sm text-primary-foreground/90 leading-relaxed">
                1985&apos;ten bu yana endüstriyel mutfak sektöründe kalite ve inovasyonun öncüsü.
                Profesyonel mutfak ekipmanları üretim ve satışında Türkiye&apos;nin lider markası.
              </p>

              {/* Social icons */}
              <div className="flex items-center gap-3 mt-5">
                <a
                  href="https://www.instagram.com/gastrotech.tr/"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex h-9 w-9 items-center justify-center rounded-sm bg-black/10 text-white hover:bg-white hover:text-primary transition-all duration-200 shadow-sm"
                  aria-label="Instagram"
                >
                  <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
                    <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
                  </svg>
                </a>
                <a
                  href="https://wa.me/902122379055"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex h-9 w-9 items-center justify-center rounded-sm bg-black/10 text-white hover:bg-[#25D366] hover:text-white transition-all duration-200 shadow-sm"
                  aria-label="WhatsApp"
                >
                  <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
                    <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
                  </svg>
                </a>
              </div>
            </div>

            {/* Links Grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 gap-8 lg:gap-12">
              {/* Quick Links */}
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                  <span className="h-px w-4 bg-white/50" />
                  Hızlı Erişim
                </h3>
                <ul className="space-y-2.5">
                  {QUICK_LINKS.map((link) => (
                    <li key={link.href}>
                      <Link
                        href={link.href}
                        className="group flex items-center gap-1.5 text-sm text-primary-foreground/80 hover:text-white transition-colors"
                      >
                        <ChevronRight className="h-3 w-3 text-white/50 group-hover:text-white transition-colors" />
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Services */}
              <div>
                <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                  <span className="h-px w-4 bg-white/50" />
                  Hizmetler
                </h3>
                <ul className="space-y-2.5">
                  {SERVICES.map((link, i) => (
                    <li key={i}>
                      <Link
                        href={link.href}
                        className="group flex items-center gap-1.5 text-sm text-primary-foreground/80 hover:text-white transition-colors"
                      >
                        <ChevronRight className="h-3 w-3 text-white/50 group-hover:text-white transition-colors" />
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Contact Info */}
              <div className="col-span-2 sm:col-span-1">
                <h3 className="text-xs font-bold text-white uppercase tracking-widest mb-4 flex items-center gap-2">
                  <span className="h-px w-4 bg-white/50" />
                  İletişim
                </h3>
                <ul className="space-y-3">
                  <li>
                    <a
                      href="tel:+902122379055"
                      className="flex items-start gap-2.5 text-sm text-primary-foreground/80 hover:text-white transition-colors group"
                    >
                      <Phone className="h-4 w-4 mt-0.5 text-white/70 flex-shrink-0" />
                      <span>+90 (212) 237 90 55</span>
                    </a>
                  </li>
                  <li>
                    <a
                      href="mailto:info@gastrotech.com.tr"
                      className="flex items-start gap-2.5 text-sm text-primary-foreground/80 hover:text-white transition-colors group"
                    >
                      <Mail className="h-4 w-4 mt-0.5 text-white/70 flex-shrink-0" />
                      <span>info@gastrotech.com.tr</span>
                    </a>
                  </li>
                  <li className="flex items-start gap-2.5 text-sm text-primary-foreground/80">
                    <MapPin className="h-4 w-4 mt-0.5 text-white/70 flex-shrink-0" />
                    <span>İkitelli OSB, İstanbul</span>
                  </li>
                  <li className="flex items-start gap-2.5 text-sm text-primary-foreground/80">
                    <Clock className="h-4 w-4 mt-0.5 text-white/70 flex-shrink-0" />
                    <span>Pzt-Cmt: 08:30 - 18:00</span>
                  </li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </Container>

      {/* Bottom Bar */}
      <div className="border-t border-white/10 bg-black/10">
        <Container>
          <div className="flex flex-col sm:flex-row items-center justify-between gap-3 py-5">
            <p className="text-xs text-primary-foreground/60 text-center sm:text-left">
              &copy; {currentYear} Gastrotech. Tüm hakları saklıdır.
            </p>
            <div className="flex items-center gap-4">
              <Link href="/gizlilik-politikasi" className="text-xs text-primary-foreground/60 hover:text-white transition-colors">
                Gizlilik Politikası
              </Link>
              <span className="text-white/20">|</span>
              <Link href="/kvkk" className="text-xs text-primary-foreground/60 hover:text-white transition-colors">
                KVKK
              </Link>
            </div>
          </div>
        </Container>
      </div>

      {/* Decorative corner accent */}
      <div className="absolute bottom-0 right-0 w-32 h-32 bg-white/5 rounded-tl-full pointer-events-none" />
    </footer>
  );
}
