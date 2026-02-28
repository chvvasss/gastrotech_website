"use client";

import Link from "next/link";
import Image from "next/image";
import { motion } from "framer-motion";
import { Container } from "./container";
import { Mail, Phone, MapPin, Linkedin, Instagram, Youtube, Shield, Award, Truck } from "lucide-react";
import { cn } from "@/lib/utils";

const FOOTER_LINKS = {
  products: {
    title: "Ürünler",
    links: [
      { label: "Tüm Ürünler", href: "/urunler" },
      { label: "Gazlı Ocaklar", href: "/kategori/gazli-ocaklar" },
      { label: "Fırınlar", href: "/kategori/firinlar" },
      { label: "Soğutma", href: "/kategori/sogutma-uniteleri" },
      { label: "Yıkama", href: "/kategori/yikama" },
    ],
  },
  company: {
    title: "Kurumsal",
    links: [
      { label: "Hakkımızda", href: "/kurumsal" },
      { label: "Referanslar", href: "/referanslar" },
      { label: "Kariyer", href: "/kurumsal#kariyer" },
      { label: "Sürdürülebilirlik", href: "/kurumsal#surdurulebilirlik" },
    ],
  },
  support: {
    title: "Destek",
    links: [
      { label: "Satış Sonrası", href: "/satis-sonrasi" },
      { label: "Yedek Parça", href: "/satis-sonrasi#yedek-parca" },
      { label: "Garanti", href: "/satis-sonrasi#garanti" },
      { label: "SSS", href: "/satis-sonrasi#sss" },
    ],
  },
  resources: {
    title: "Kaynaklar",
    links: [
      { label: "Kataloglar", href: "/kataloglar" },
      { label: "Blog", href: "/blog" },
      { label: "Haberler", href: "/blog?category=haberler" },
      { label: "Teklif Al", href: "/iletisim" },
    ],
  },
};

const SOCIAL_LINKS = [
  { icon: Linkedin, href: "https://linkedin.com", label: "LinkedIn" },
  { icon: Instagram, href: "https://instagram.com", label: "Instagram" },
  { icon: Youtube, href: "https://youtube.com", label: "YouTube" },
  { icon: Mail, href: "mailto:info@gastrotech.com.tr", label: "Email" },
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

      {/* Trust Badges Section - Sharp */}
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
                className="flex items-center justify-center sm:justify-start gap-3.5 rounded-sm border border-border/40 bg-white/80 p-3.5 shadow-soft hover:shadow-elevated hover:border-primary/20 transition-all duration-300 w-full max-w-[300px]"
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
              {`1985'ten bu yana profesyonel mutfak ekipmanları üretimi. Kalite, inovasyon ve güvenilirlik ile sektörün öncüsü.`}
            </p>

            {/* Social Links - Sharp */}
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
                  <social.icon className="h-4 w-4" />
                </motion.a>
              ))}
            </div>

            {/* Contact Info - Compact */}
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
                    <li key={link.href}>
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

      {/* Copyright - Darker & Cleaner */}
      <div className="border-t border-border bg-muted/20 py-6">
        <Container>
          <div className="flex flex-col items-center justify-between gap-4 text-xs sm:flex-row text-muted-foreground">
            <p className="font-medium">
              © {new Date().getFullYear()} Gastrotech. Tüm hakları saklıdır.
            </p>
            <div className="flex items-center gap-6">
              <Link href="/gizlilik" className="hover:text-foreground transition-colors hover:underline">
                Gizlilik Politikası
              </Link>
              <Link href="/kullanim-kosullari" className="hover:text-foreground transition-colors hover:underline">
                Kullanım Koşulları
              </Link>
              <Link href="/kvkk" className="hover:text-foreground transition-colors hover:underline">
                KVKK
              </Link>
              <span className="hidden sm:inline text-border">|</span>
              <a
                href="https://mackatech.com"
                target="_blank"
                rel="noopener noreferrer"
                className="hover:text-foreground transition-colors"
              >
                Designed by <span className="font-semibold">Mackatech</span>
              </a>
            </div>
          </div>
        </Container>
      </div>

      {/* Brand Red Bottom Bar */}
      <div className="h-1.5 bg-gradient-to-r from-primary/90 via-primary to-primary/90" />
    </footer>
  );
}
