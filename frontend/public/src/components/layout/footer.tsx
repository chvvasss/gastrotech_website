"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { Container } from "./container";
import { Mail, Phone, MapPin, Shield, Award, Truck } from "lucide-react";
import { cn } from "@/lib/utils";

const FOOTER_LINKS = {
  products: {
    title: "Ürünler",
    links: [
      { label: "Tüm Ürünler", href: "/kategori" },
      { label: "Kataloglar", href: "/kataloglar" },
      { label: "Yeni Ürünler", href: "/kategori" },
      { label: "Teklif Al", href: "/iletisim" },
    ],
  },
  company: {
    title: "Kurumsal",
    links: [
      { label: "Hakkımızda", href: "/kurumsal" },
      { label: "Referanslar", href: "/referanslar" },
      { label: "Blog", href: "/blog" },
      { label: "İletişim", href: "/iletisim" },
    ],
  },
  support: {
    title: "Destek",
    links: [
      { label: "Satış Sonrası", href: "/satis-sonrasi" },
      { label: "Yedek Parça", href: "/satis-sonrasi" },
      { label: "Teknik Servis", href: "/satis-sonrasi" },
      { label: "Garanti", href: "/satis-sonrasi" },
    ],
  },
  resources: {
    title: "Kaynaklar",
    links: [
      { label: "Kataloglar", href: "/kataloglar" },
      { label: "Blog", href: "/blog" },
      { label: "SSS", href: "/satis-sonrasi" },
      { label: "KVKK", href: "/kvkk" },
    ],
  },
};

const SOCIAL_LINKS = [
  {
    label: "Instagram",
    href: "https://www.instagram.com/gastrotech.tr/",
    icon: (
      <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
        <path d="M12 2.163c3.204 0 3.584.012 4.85.07 3.252.148 4.771 1.691 4.919 4.919.058 1.265.069 1.645.069 4.849 0 3.205-.012 3.584-.069 4.849-.149 3.225-1.664 4.771-4.919 4.919-1.266.058-1.644.07-4.85.07-3.204 0-3.584-.012-4.849-.07-3.26-.149-4.771-1.699-4.919-4.92-.058-1.265-.07-1.644-.07-4.849 0-3.204.013-3.583.07-4.849.149-3.227 1.664-4.771 4.919-4.919 1.266-.057 1.645-.069 4.849-.069zM12 0C8.741 0 8.333.014 7.053.072 2.695.272.273 2.69.073 7.052.014 8.333 0 8.741 0 12c0 3.259.014 3.668.072 4.948.2 4.358 2.618 6.78 6.98 6.98C8.333 23.986 8.741 24 12 24c3.259 0 3.668-.014 4.948-.072 4.354-.2 6.782-2.618 6.979-6.98.059-1.28.073-1.689.073-4.948 0-3.259-.014-3.667-.072-4.947-.196-4.354-2.617-6.78-6.979-6.98C15.668.014 15.259 0 12 0zm0 5.838a6.162 6.162 0 100 12.324 6.162 6.162 0 000-12.324zM12 16a4 4 0 110-8 4 4 0 010 8zm6.406-11.845a1.44 1.44 0 100 2.881 1.44 1.44 0 000-2.881z" />
      </svg>
    ),
  },
  {
    label: "WhatsApp",
    href: "https://wa.me/902122379055",
    icon: (
      <svg viewBox="0 0 24 24" className="h-4 w-4 fill-current">
        <path d="M17.472 14.382c-.297-.149-1.758-.867-2.03-.967-.273-.099-.471-.148-.67.15-.197.297-.767.966-.94 1.164-.173.199-.347.223-.644.075-.297-.15-1.255-.463-2.39-1.475-.883-.788-1.48-1.761-1.653-2.059-.173-.297-.018-.458.13-.606.134-.133.298-.347.446-.52.149-.174.198-.298.298-.497.099-.198.05-.371-.025-.52-.075-.149-.669-1.612-.916-2.207-.242-.579-.487-.5-.669-.51-.173-.008-.371-.01-.57-.01-.198 0-.52.074-.792.372-.272.297-1.04 1.016-1.04 2.479 0 1.462 1.065 2.875 1.213 3.074.149.198 2.096 3.2 5.077 4.487.709.306 1.262.489 1.694.625.712.227 1.36.195 1.871.118.571-.085 1.758-.719 2.006-1.413.248-.694.248-1.289.173-1.413-.074-.124-.272-.198-.57-.347m-5.421 7.403h-.004a9.87 9.87 0 01-5.031-1.378l-.361-.214-3.741.982.998-3.648-.235-.374a9.86 9.86 0 01-1.51-5.26c.001-5.45 4.436-9.884 9.888-9.884 2.64 0 5.122 1.03 6.988 2.898a9.825 9.825 0 012.893 6.994c-.003 5.45-4.437 9.884-9.885 9.884m8.413-18.297A11.815 11.815 0 0012.05 0C5.495 0 .16 5.335.157 11.892c0 2.096.547 4.142 1.588 5.945L.057 24l6.305-1.654a11.882 11.882 0 005.683 1.448h.005c6.554 0 11.89-5.335 11.893-11.893a11.821 11.821 0 00-3.48-8.413z" />
      </svg>
    ),
  },
  {
    label: "Email",
    href: "mailto:info@gastrotech.com.tr",
    icon: <Mail className="h-4 w-4" />,
  },
];

const TRUST_BADGES = [
  { icon: Shield, label: "2 Yıl Garanti" },
  { icon: Award, label: "ISO 9001" },
  { icon: Truck, label: "Hızlı Teslimat" },
];

export function Footer() {
  return (
    <footer className="relative overflow-hidden border-t bg-white">
      {/* Red accent band */}
      <div className="h-[2px] bg-gradient-to-r from-primary/80 via-primary to-primary/80" />

      {/* Trust Badges Section */}
      <div className="border-b border-border/40 bg-white/50 backdrop-blur-sm">
        <Container className="py-6">
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-6 lg:gap-8 justify-items-center sm:justify-items-stretch">
            {TRUST_BADGES.map((badge, index) => (
              <motion.div
                key={badge.label}
                initial={{ opacity: 0, y: 10 }}
                whileInView={{ opacity: 1, y: 0 }}
                viewport={{ once: true }}
                transition={{ delay: index * 0.1 }}
                className="flex items-center justify-center sm:justify-start gap-3.5 rounded-sm border border-border/40 bg-white/80 p-3.5 shadow-sm hover:shadow-md hover:border-primary/20 transition-all duration-300 w-full max-w-[300px]"
              >
                <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-primary/10 text-primary">
                  <badge.icon className="h-5 w-5" />
                </div>
                <span className="text-sm font-semibold text-foreground">{badge.label}</span>
              </motion.div>
            ))}
          </div>
        </Container>
      </div>

      <Container className="py-10 sm:py-16">
        <div className="grid gap-10 grid-cols-1 sm:grid-cols-2 lg:grid-cols-12">
          {/* Brand Section */}
          <div className="lg:col-span-4 space-y-6">
            <Link
              href="/"
              className="relative inline-block h-10 w-[160px] transition-opacity hover:opacity-80"
            >
              <Image
                src="/assets/footer_logo.png"
                alt="Gastrotech"
                fill
                className="object-contain object-left"
                sizes="180px"
              />
            </Link>
            <p className="text-sm leading-relaxed text-muted-foreground max-w-sm">
              1985&apos;ten bu yana profesyonel mutfak ekipmanları üretimi.
              Kalite, inovasyon ve güvenilirlik ile sektörün öncüsü.
            </p>

            {/* Social Links */}
            <div className="flex gap-2">
              {SOCIAL_LINKS.map((social) => (
                <motion.a
                  key={social.label}
                  href={social.href}
                  target="_blank"
                  rel="noopener noreferrer"
                  className={cn(
                    "flex h-10 w-10 items-center justify-center rounded-sm border border-border",
                    "bg-white text-muted-foreground",
                    "transition-all duration-200",
                    "hover:bg-primary hover:text-white hover:border-primary hover:shadow-md",
                  )}
                  whileHover={{ scale: 1.05 }}
                  whileTap={{ scale: 0.95 }}
                  aria-label={social.label}
                >
                  {social.icon}
                </motion.a>
              ))}
            </div>

            {/* Contact Info */}
            <div className="space-y-3 pt-2">
              <a href="tel:+902122379055" className="flex items-center gap-3 text-sm text-muted-foreground hover:text-primary transition-colors group">
                <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-muted group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                  <Phone className="h-4 w-4" />
                </span>
                <span className="font-medium">0212 237 90 55</span>
              </a>
              <a href="mailto:info@gastrotech.com.tr" className="flex items-center gap-3 text-sm text-muted-foreground hover:text-primary transition-colors group">
                <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-muted group-hover:bg-primary/10 group-hover:text-primary transition-colors">
                  <Mail className="h-4 w-4" />
                </span>
                <span className="font-medium">info@gastrotech.com.tr</span>
              </a>
              <div className="flex items-center gap-3 text-sm text-muted-foreground">
                <span className="flex h-8 w-8 items-center justify-center rounded-sm bg-muted">
                  <MapPin className="h-4 w-4" />
                </span>
                <span className="font-medium">İkitelli OSB, İstanbul</span>
              </div>
            </div>
          </div>

          {/* Links Grid */}
          <div className="lg:col-span-8 grid grid-cols-2 md:grid-cols-4 gap-8">
            {Object.values(FOOTER_LINKS).map((section) => (
              <div key={section.title} className="space-y-4">
                <h4 className="font-bold text-foreground flex items-center gap-2 text-sm uppercase tracking-wide">
                  <div className="h-1 w-4 bg-primary rounded-sm" />
                  {section.title}
                </h4>
                <ul className="space-y-2.5">
                  {section.links.map((link) => (
                    <li key={link.href + link.label}>
                      <Link
                        href={link.href}
                        className={cn(
                          "group inline-flex items-center gap-2 text-sm text-muted-foreground",
                          "transition-colors duration-200 hover:text-foreground"
                        )}
                      >
                        <span className="h-1 w-1 rounded-sm bg-border group-hover:bg-primary transition-colors" />
                        {link.label}
                      </Link>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </Container>

      {/* Copyright */}
      <div className="border-t border-border bg-muted/20 py-6">
        <Container>
          <div className="flex flex-col items-center justify-between gap-4 text-xs sm:flex-row text-muted-foreground">
            <p className="font-medium">
              &copy; {new Date().getFullYear()} Gastrotech. Tüm hakları saklıdır.
            </p>
            <div className="flex gap-6">
              <Link href="/gizlilik" className="hover:text-foreground transition-colors hover:underline">
                Gizlilik Politikası
              </Link>
              <Link href="/kullanim-kosullari" className="hover:text-foreground transition-colors hover:underline">
                Kullanım Koşulları
              </Link>
              <Link href="/kvkk" className="hover:text-foreground transition-colors hover:underline">
                KVKK
              </Link>
            </div>
          </div>
        </Container>
      </div>

      {/* Brand Red Bottom Bar */}
      <div className="h-1.5 bg-gradient-to-r from-primary/90 via-primary to-primary/90" />
    </footer>
  );
}
