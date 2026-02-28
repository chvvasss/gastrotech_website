"use client";

import Link from "next/link";
import Image from "next/image";
import { usePathname } from "next/navigation";
import { useQuery } from "@tanstack/react-query";
import { Menu, Search, ShoppingCart, FileText } from "lucide-react";
import { LanguageSelector } from "@/components/google-translate";
import { useState, useRef, useEffect } from "react";
import { createPortal } from "react-dom";
import { motion, AnimatePresence } from "framer-motion";
import { fetchNav } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Sheet, SheetContent, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet";
import { Container } from "./container";
import { MegaMenuPanel } from "./mega-menu";
import { GlobalSearch } from "./global-search";
import { SearchPrompter } from "./search-prompter";
import { CartDrawer } from "@/components/cart/cart-drawer";
import { useCart } from "@/hooks/use-cart";
import { cn } from "@/lib/utils";

export function Header() {
  const pathname = usePathname();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);
  const [isCartOpen, setIsCartOpen] = useState(false);
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const [activeMenu, setActiveMenu] = useState<string | null>(null);
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0, width: 0 });
  const [prevItemCount, setPrevItemCount] = useState(0);
  const headerRef = useRef<HTMLElement>(null);
  const navRef = useRef<HTMLElement>(null);
  const timeoutRef = useRef<NodeJS.Timeout | null>(null);

  const NAV_ITEMS = [
    { label: "Ürünler", href: "/kategori", hasMegaMenu: true },
    { label: "Kataloglar", href: "/kataloglar" },
    { label: "Kurumsal", href: "/kurumsal" },
    { label: "Referanslar", href: "/referanslar" },
    { label: "Blog", href: "/blog" },
    { label: "Satış Sonrası", href: "/satis-sonrasi" },
    { label: "İletişim", href: "/iletisim" },
  ];

  const { data: categories = [] } = useQuery({
    queryKey: ["nav"],
    queryFn: fetchNav,
    staleTime: 5 * 60 * 1000,
  });

  const { cart } = useCart();
  const itemCount = cart?.totals?.item_count || 0;

  // Track item count changes for animation
  useEffect(() => {
    if (itemCount !== prevItemCount) {
      setPrevItemCount(itemCount);
    }
  }, [itemCount, prevItemCount]);



  const handleMenuEnter = (label: string) => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);

    if (headerRef.current) {
      const rect = headerRef.current.getBoundingClientRect();
      setMenuPosition({
        top: rect.bottom,
        left: 0,
        width: window.innerWidth,
      });
    }
    setActiveMenu(label);
  };

  const handleMenuLeave = () => {
    timeoutRef.current = setTimeout(() => {
      setActiveMenu(null);
    }, 150);
  };

  const handlePanelEnter = () => {
    if (timeoutRef.current) clearTimeout(timeoutRef.current);
  };

  const handlePanelLeave = () => {
    setActiveMenu(null);
  };

  // Check if current path matches nav item
  const isActive = (href: string) => {
    if (href === "/urunler") {
      return pathname?.startsWith("/urun") || pathname?.startsWith("/kategori") || pathname?.startsWith("/seri");
    }
    return pathname?.startsWith(href);
  };

  return (
    <>
      <a
        href="#main-content"
        className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[100] focus:rounded-sm focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:shadow-lg"
      >
        Ana içeriğe git
      </a>
      <header
        ref={headerRef}
        className="sticky top-0 z-50 w-full border-b bg-white shadow-sm transition-all duration-300"
      >
        <Container>
          <div className="relative flex h-16 items-center justify-between gap-2 sm:gap-4 transition-all duration-300">
            {/* Logo */}
            <Link
              href="/"
              className="relative flex-shrink-0 h-9 w-[140px] sm:w-[160px] transition-all duration-300 hover:opacity-80"
            >
              <Image
                src="/assets/logo.png"
                alt="Gastrotech"
                fill
                className="object-contain object-left"
                priority
                sizes="180px"
              />
            </Link>

            {/* Desktop Navigation - Standard Flow to prevent overlap */}
            <nav ref={navRef} className="hidden xl:flex items-center gap-1 mx-auto px-4">
              {NAV_ITEMS.map((item) => (
                <div
                  key={item.href}
                  className="relative"
                  onMouseEnter={() => item.hasMegaMenu && handleMenuEnter(item.label)}
                  onMouseLeave={handleMenuLeave}
                >
                  <Link
                    href={item.href}
                    className={cn(
                      "group relative px-3 py-2 text-sm font-medium transition-all duration-200", // Reduced horizontal padding
                      "hover:text-primary",
                      isActive(item.href)
                        ? "text-primary"
                        : "text-foreground/70 hover:text-foreground",
                      activeMenu === item.label && "text-primary"
                    )}
                  >
                    {item.label}
                    {/* Sharp Animated indicator */}
                    <span
                      className={cn(
                        "absolute bottom-0 left-0 h-[2px] w-full bg-primary origin-left scale-x-0 transition-transform duration-300 group-hover:scale-x-100",
                        isActive(item.href) && "scale-x-100"
                      )}
                    />
                  </Link>
                </div>
              ))}
            </nav>

            {/* Right Actions - Optimized for all screens */}
            <div className="flex items-center gap-1 sm:gap-2 xl:gap-4 shrink-0">
              {/* Language Switcher */}
              <div className="hidden sm:block">
                <LanguageSelector />
              </div>

              {/* Search Button - Responsive Width */}
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsSearchOpen(true)}
                className="group relative hidden md:flex items-center justify-start gap-2 overflow-hidden rounded-sm border border-primary/20 bg-muted/20 w-auto xl:w-[180px] px-3 py-2 hover:bg-muted/40 hover:border-primary/40 transition-all"
                aria-label="Ara"
              >
                <Search className="h-4 w-4 text-muted-foreground group-hover:text-primary transition-colors flex-shrink-0" />
                <span className="hidden xl:inline text-sm font-medium text-muted-foreground group-hover:text-foreground">Ara...</span>
                <span className="hidden lg:inline xl:hidden text-sm font-medium text-muted-foreground group-hover:text-foreground">Ara</span>
              </Button>

              {/* Request Quote CTA - Only on very large screens */}
              <Link href="/iletisim" className="hidden 2xl:block">
                <Button
                  size="sm"
                  className="rounded-sm shadow-sm font-semibold h-9"
                >
                  <FileText className="mr-2 h-4 w-4" />
                  Teklif Al
                </Button>
              </Link>

              {/* Cart Badge */}
              <Button
                variant="ghost"
                size="icon"
                onClick={() => setIsCartOpen(true)}
                className="relative rounded-sm hover:bg-primary/5 hover:text-primary transition-colors h-9 w-9"
                aria-label="Sepet"
              >
                <ShoppingCart className="h-5 w-5" />
                <AnimatePresence mode="wait">
                  {itemCount > 0 && (
                    <motion.span
                      key={itemCount}
                      initial={{ scale: 0.5, opacity: 0 }}
                      animate={{ scale: 1, opacity: 1 }}
                      exit={{ scale: 0.5, opacity: 0 }}
                      transition={{ type: "spring", stiffness: 500, damping: 25 }}
                      className="absolute -right-1 -top-1 flex h-4 w-4 items-center justify-center rounded-sm bg-primary text-[10px] font-bold text-primary-foreground shadow-sm ring-2 ring-background"
                    >
                      {itemCount > 99 ? "99+" : itemCount}
                    </motion.span>
                  )}
                </AnimatePresence>
              </Button>

              {/* Mobile/Tablet Menu Trigger (Visible below 2XL) */}
              <Sheet open={isMobileMenuOpen} onOpenChange={setIsMobileMenuOpen}>
                <SheetTrigger asChild>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="xl:hidden rounded-sm hover:bg-primary/5 h-9 w-9"
                    aria-label="Menü"
                  >
                    <Menu className="h-5 w-5" />
                  </Button>
                </SheetTrigger>
                <SheetContent side="right" className="w-[300px] border-l border-primary/10 p-0 shadow-2xl">
                  <div className="flex flex-col h-full bg-white/95 backdrop-blur-xl">
                    <SheetHeader className="px-6 py-4 border-b text-left">
                      <SheetTitle className="text-lg font-bold flex items-center gap-2">
                        <span className="h-6 w-1 bg-primary rounded-sm" />
                        Menü
                      </SheetTitle>
                    </SheetHeader>
                    <nav className="flex-1 overflow-y-auto py-6 px-4">
                      {/* Mobile Language Selector */}
                      <div className="mb-6 sm:hidden">
                        <LanguageSelector />
                      </div>

                      <div className="space-y-1">
                        {NAV_ITEMS.map((item, index) => (
                          <motion.div
                            key={item.href}
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            transition={{ delay: index * 0.05 }}
                          >
                            <Link
                              href={item.href}
                              onClick={() => setIsMobileMenuOpen(false)}
                              className={cn(
                                "group flex items-center justify-between rounded-sm px-4 py-3 text-base font-medium transition-all",
                                isActive(item.href)
                                  ? "bg-primary/5 text-primary border-l-2 border-primary"
                                  : "text-foreground hover:bg-muted/50 hover:pl-5"
                              )}
                            >
                              {item.label}
                              {isActive(item.href) && (
                                <span className="h-1.5 w-1.5 rounded-sm bg-primary" />
                              )}
                            </Link>
                          </motion.div>
                        ))}
                      </div>

                      <div className="mt-8 space-y-3 px-2">
                        <Link href="/sepet" onClick={() => setIsMobileMenuOpen(false)}>
                          <Button variant="outline" className="w-full justify-between rounded-sm h-12 border-primary/20 hover:bg-primary/5 hover:text-primary">
                            <span className="flex items-center gap-2">
                              <ShoppingCart className="h-4 w-4" />
                              Sepetim
                            </span>
                            {itemCount > 0 && (
                              <span className="flex h-5 w-5 items-center justify-center rounded-sm bg-primary text-[10px] text-primary-foreground">
                                {itemCount}
                              </span>
                            )}
                          </Button>
                        </Link>
                        <Link href="/iletisim" onClick={() => setIsMobileMenuOpen(false)}>
                          <Button className="w-full justify-between rounded-sm h-12 shadow-md shadow-primary/20">
                            <span className="flex items-center gap-2">
                              <FileText className="h-4 w-4" />
                              Teklif İste
                            </span>
                          </Button>
                        </Link>
                      </div>
                    </nav>

                    <div className="p-6 bg-muted/20 border-t">
                      <p className="text-xs text-muted-foreground text-center">
                        Gastrotech Profesyonel Mutfak
                      </p>
                    </div>
                  </div>
                </SheetContent>
              </Sheet>
            </div>
          </div>
        </Container>

        {/* Mobile/Tablet Search Bar - Full Width below header */}
        <div className="md:hidden px-4 pb-3 -mt-1">
          <Button
            variant="outline"
            onClick={() => setIsSearchOpen(true)}
            className="w-full justify-start text-muted-foreground border-border/60 bg-muted/20 h-10 rounded-sm"
          >
            <Search className="mr-2.5 h-4 w-4 text-primary/70" />
            <span className="text-sm">Ürün veya kategori arayın...</span>
          </Button>
        </div>

        {/* Bottom accent line - Subtle & Sharp */}
        <div className="absolute bottom-0 left-0 right-0 h-[1px] bg-border/60" />
      </header>

      {/* Mega Menu Portal */}
      {typeof window !== "undefined" && createPortal(
        <AnimatePresence>
          {activeMenu === "Ürünler" && (
            <MegaMenuPanel
              key="mega-menu"
              categories={categories}
              position={menuPosition}
              onClose={() => setActiveMenu(null)}
              onMouseEnter={handlePanelEnter}
              onMouseLeave={handlePanelLeave}
            />
          )}
        </AnimatePresence>,
        document.body
      )}

      {/* Cart Drawer */}
      <CartDrawer open={isCartOpen} onOpenChange={setIsCartOpen} />

      {/* Global Search */}
      <GlobalSearch open={isSearchOpen} onOpenChange={setIsSearchOpen} />

      {/* Search Prompter - Smart Nudge */}
      <SearchPrompter onSearch={() => setIsSearchOpen(true)} />
    </>
  );
}
