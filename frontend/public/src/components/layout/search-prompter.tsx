"use client";

import { useState, useEffect } from "react";
import { motion, AnimatePresence } from "framer-motion";
import { Search, X, Sparkles, ArrowRight } from "lucide-react";
import { Button } from "@/components/ui/button";
import { usePathname } from "next/navigation";

interface SearchPrompterProps {
    onSearch: () => void;
}

export function SearchPrompter({ onSearch }: SearchPrompterProps) {
    const [isVisible, setIsVisible] = useState(false);
    const pathname = usePathname();

    useEffect(() => {
        // Only show on validation listing pages or product detail pages
        // User requested: "sitede ürünlerde" (on products) and "kategori sayfasında"
        const isTargetPage = pathname?.startsWith("/urun") || pathname?.startsWith("/kategori");

        if (!isTargetPage) {
            setIsVisible(false);
            return;
        }

        const hasDismissed = sessionStorage.getItem("search_prompter_dismissed");
        if (hasDismissed) return;

        // Wait 15 seconds
        const timer = setTimeout(() => {
            setIsVisible(true);
        }, 15000);

        return () => clearTimeout(timer);
    }, [pathname]); // Reset timer on navigation? Or keep it global? 
    // If we want "15s total site time" -> remove dependency. 
    // If we want "15s on THIS page" -> keep dependency. 
    // User: "sitede ürünlerde 15 saniye geçirdikten sonra" -> implies dwell time on a page.
    // I will keep [pathname] to reset on navigation, so it only shows if they are stuck on a specific page.

    const handleDismiss = () => {
        setIsVisible(false);
        sessionStorage.setItem("search_prompter_dismissed", "true");
    };

    const handleSearchClick = () => {
        setIsVisible(false);
        onSearch();
    };

    return (
        <AnimatePresence>
            {isVisible && (
                <motion.div
                    initial={{ opacity: 0, y: -50, scale: 0.9 }}
                    animate={{ opacity: 1, y: 0, scale: 1 }}
                    exit={{ opacity: 0, y: -20, scale: 0.95 }}
                    transition={{ type: "spring", stiffness: 300, damping: 30 }}
                    className="fixed top-[120px] sm:top-24 left-3 right-3 sm:left-auto sm:right-8 z-40 sm:w-[380px] sm:max-w-[380px]"
                >
                    <div className="relative overflow-hidden rounded-sm border border-primary/20 bg-white/95 backdrop-blur-md shadow-2xl shadow-primary/10 p-3 sm:p-5">
                        {/* Glossy Effect */}
                        <div className="absolute inset-0 bg-gradient-to-br from-white via-white/80 to-transparent z-[-1]" />
                        <div className="absolute -top-10 -right-10 h-32 w-32 bg-primary/10 blur-3xl rounded-full pointer-events-none" />

                        <button
                            onClick={handleDismiss}
                            className="absolute top-2 right-2 text-muted-foreground/50 hover:text-foreground transition-colors p-1.5 z-10"
                        >
                            <X className="h-4 w-4" />
                        </button>

                        <div className="flex gap-3 sm:gap-4">
                            <div className="flex-shrink-0">
                                <div className="h-10 w-10 sm:h-12 sm:w-12 rounded-full bg-gradient-to-br from-primary to-primary/80 flex items-center justify-center shadow-lg shadow-primary/20">
                                    <Search className="h-5 w-5 sm:h-6 sm:w-6 text-white" />
                                </div>
                            </div>

                            <div className="flex-1 min-w-0 pr-4">
                                <h4 className="font-bold text-foreground text-xs sm:text-base flex items-center gap-1.5 sm:gap-2 mb-1">
                                    <span className="truncate">Aradığınızı Bulamadınız mı?</span>
                                    <Sparkles className="h-3 w-3 text-amber-500 animate-pulse flex-shrink-0" />
                                </h4>
                                <p className="text-[11px] sm:text-sm text-muted-foreground leading-snug mb-2 sm:mb-3">
                                    Binlerce ürün arasında size yardımcı olalım.
                                </p>

                                <Button
                                    onClick={handleSearchClick}
                                    className="w-full text-xs sm:text-sm font-semibold h-8 sm:h-9 rounded-sm shadow-md shadow-primary/10 hover:shadow-primary/20 transition-all"
                                >
                                    Hemen Ara
                                    <ArrowRight className="ml-2 h-3 w-3 sm:h-3.5 sm:w-3.5" />
                                </Button>
                            </div>
                        </div>
                    </div>
                </motion.div>
            )}
        </AnimatePresence>
    );
}
