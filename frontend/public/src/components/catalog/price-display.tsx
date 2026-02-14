"use client";

import { useSiteSettings } from "@/hooks/use-site-settings";
import { cn } from "@/lib/utils";
import Link from "next/link";
import { Button } from "@/components/ui/button";

interface PriceDisplayProps {
    price?: number | string | null;
    currency?: string;
    className?: string;
    showCurrency?: boolean;
    fallbackText?: string;
    variant?: "default" | "minimal" | "button";
}

export function PriceDisplay({
    price,
    currency = "₺",
    className,
    showCurrency = true,
    fallbackText = "Teklif Al",
    variant = "default",
}: PriceDisplayProps) {
    const { showPrices, isLoading } = useSiteSettings();

    // Loading state skeleton or invisible?
    // Ideally invisible or subtle to avoid flash.
    // We default showPrices to true in initial state, so it might flash price then hide if false.
    // Better to default to false? The prompt said "ON by default", so flash is okay or we accept it.
    // Actually, if we want to be safe for "hidden" mode, maybe default false?
    // Let's stick to state default (True) but checking logic.

    if (isLoading) {
        return <span className={cn("inline-block h-6 w-16 animate-pulse rounded bg-muted", className)} />;
    }

    // If globally OFF, or no price provided
    if (!showPrices || price === null || price === undefined) {
        if (variant === "button") {
            return (
                <Button asChild size="sm" className={className}>
                    <Link href="/iletisim">{fallbackText}</Link>
                </Button>
            );
        }

        // Minimal text fallback
        if (variant === "minimal") {
            return (
                <span className={cn("text-muted-foreground font-medium text-sm", className)}>
                    {fallbackText}
                </span>
            );
        }

        // Default: Text link or span
        return (
            <Link
                href="/iletisim"
                className={cn("text-primary font-bold hover:underline", className)}
            >
                {fallbackText}
            </Link>
        );
    }

    // If valid price and Show Prices is ON
    // Format price
    const formattedPrice = new Intl.NumberFormat("tr-TR", {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2,
    }).format(Number(price));

    return (
        <span className={cn("font-bold text-foreground", className)}>
            {formattedPrice} {showCurrency && currency}
        </span>
    );
}
