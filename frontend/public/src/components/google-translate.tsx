"use client";

import { useEffect, useState } from "react";
import Script from "next/script";
import { parseCookies, setCookie } from "nookies";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { ChevronDown, Globe } from "lucide-react";
import { cn } from "@/lib/utils";
import { TurkeyFlag, UKFlag, GermanyFlag, FranceFlag, ItalyFlag, SaudiArabiaFlag } from "@/components/icons/flags";

declare global {
    interface Window {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        google: any;
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        googleTranslateElementInit: any;
    }
}

const LANGUAGES = [
    { code: "tr", name: "Türkçe", flag: TurkeyFlag },
    { code: "en", name: "English", flag: UKFlag },
    { code: "de", name: "Deutsch", flag: GermanyFlag },
    { code: "fr", name: "Français", flag: FranceFlag },
    { code: "it", name: "Italiano", flag: ItalyFlag },
    { code: "ar", name: "العربية", flag: SaudiArabiaFlag },
];

export function GoogleTranslateScript() {
    useEffect(() => {
        window.googleTranslateElementInit = () => {
            // Initialize Google Translate only if it hasn't been initialized
            if (window.google && window.google.translate && !document.querySelector('.goog-te-combo')) {
                new window.google.translate.TranslateElement(
                    {
                        pageLanguage: "tr",
                        includedLanguages: "en,de,fr,it,ar,tr", // All supported languages
                        layout: window.google.translate.TranslateElement.InlineLayout.SIMPLE,
                        autoDisplay: false,
                    },
                    "google_translate_element"
                );
            }
        };
    }, []);

    return (
        <div className="hidden">
            <div id="google_translate_element" />
            <Script
                src="//translate.google.com/translate_a/element.js?cb=googleTranslateElementInit"
                strategy="lazyOnload"
            />
            {/* Aggressive hiding of ALL Google Translate UI elements */}
            <style jsx global>{`
                /* Hide ALL Google Translate frames and banners */
                .goog-te-banner-frame,
                .goog-te-banner-frame.skiptranslate,
                #goog-gt-tt,
                .goog-te-balloon-frame,
                .goog-te-menu-frame,
                .goog-te-menu2,
                .goog-te-menu-value,
                .goog-te-gadget,
                .goog-te-gadget-simple,
                .goog-te-gadget-icon,
                .goog-te-spinner-pos,
                .goog-tooltip,
                .goog-tooltip:hover,
                .goog-text-highlight,
                #google_translate_element,
                .skiptranslate,
                .goog-te-ftab-float,
                iframe.goog-te-menu-frame,
                iframe.goog-te-banner-frame {
                    display: none !important;
                    visibility: hidden !important;
                    height: 0 !important;
                    width: 0 !important;
                    opacity: 0 !important;
                    pointer-events: none !important;
                }
                
                /* Keep body at top, prevent shift */
                body {
                    top: 0px !important;
                    position: static !important;
                }
                
                /* Hide the -MOST and other Google injected text */
                .goog-te-gadget span,
                .goog-te-gadget a {
                    display: none !important;
                }
                
                /* Reset font tag styles injected by Google Translate */
                font {
                    background-color: transparent !important;
                    box-shadow: none !important;
                    border: none !important;
                }
                
                /* Prevent hover effects on translated text */
                a font,
                a:hover font,
                button font,
                button:hover font,
                font:hover {
                    color: inherit !important;
                    background-color: transparent !important;
                    box-shadow: none !important;
                }
                
                /* Prevent highlight effect */
                .goog-text-highlight {
                    background-color: transparent !important;
                    box-shadow: none !important;
                    border: none !important;
                }
            `}</style>
        </div>
    );
}

export function LanguageSelector({ className }: { className?: string }) {
    const [currentLang, setCurrentLang] = useState("tr");

    useEffect(() => {
        // Check existing cookie on mount
        const cookies = parseCookies();
        const googtrans = cookies["googtrans"]; // Format: /from/to  e.g., /tr/en
        if (googtrans) {
            const langCode = googtrans.split("/").pop();
            if (langCode && LANGUAGES.some(l => l.code === langCode)) {
                setCurrentLang(langCode);
            }
        }
    }, []);

    const handleLanguageChange = (langCode: string) => {
        if (langCode === currentLang) return;

        // Update state immediately for UI response
        setCurrentLang(langCode);

        // 1. Handle Cookies (Persistence)
        if (langCode === "tr") {
            // Restore original -> Clear cookies
            setCookie(null, "googtrans", "", { path: "/", maxAge: -1 });
            setCookie(null, "googtrans", "", { path: "/", domain: window.location.hostname, maxAge: -1 });
        } else {
            // Set translation cookie -> /auto/target_lang or /source/target_lang
            // "/tr/en" tells Google: Source is TR, Target is EN.
            const cookieValue = `/tr/${langCode}`;
            setCookie(null, "googtrans", cookieValue, { path: "/" });
            setCookie(null, "googtrans", cookieValue, { path: "/", domain: window.location.hostname });
        }

        // 2. Trigger Google Translate (Instant Switch without Reload)
        const element = document.querySelector(".goog-te-combo") as HTMLSelectElement;
        if (element) {
            element.value = langCode;
            element.dispatchEvent(new Event("change"));
        } else {
            // Fallback if widget isn't ready or found: Reload page to force cookie read
            window.location.reload();
        }
    };

    const CurrentFlag = LANGUAGES.find(l => l.code === currentLang)?.flag || Globe;

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className={cn(
                        "relative h-9 px-2 gap-2 rounded-sm transition-colors notranslate",
                        "hover:bg-stone-100/50 data-[state=open]:bg-stone-100/50",
                        className
                    )}
                >
                    <span className="sr-only">Dil Değiştir</span>
                    <CurrentFlag className="h-5 w-5 rounded-[3px] shadow-sm object-cover" />
                    <span className="text-xs font-semibold text-stone-600 uppercase tracking-wide">{currentLang}</span>
                    <ChevronDown className="h-3 w-3 text-stone-400 opacity-50" />
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent
                align="end"
                className="w-[180px] p-2 bg-white border-stone-200/60 shadow-xl rounded-sm animate-in fade-in-0 zoom-in-95 notranslate"
            >
                <div className="px-2 py-1.5 mb-1 text-[10px] font-bold text-stone-400 uppercase tracking-wider">
                    Dil Seçimi / Language
                </div>
                {LANGUAGES.map((lang) => (
                    <DropdownMenuItem
                        key={lang.code}
                        onClick={() => handleLanguageChange(lang.code)}
                        className={cn(
                            "flex items-center justify-between cursor-pointer py-2.5 px-3 rounded-sm transition-all duration-200 group notranslate",
                            currentLang === lang.code
                                ? "bg-stone-100 text-stone-900 font-medium"
                                : "text-stone-600 hover:bg-stone-50 hover:text-stone-900"
                        )}
                    >
                        <div className="flex items-center gap-3">
                            <div className={cn(
                                "p-0.5 rounded-[4px] border border-stone-100 transition-shadow",
                                currentLang === lang.code ? "bg-white shadow-sm ring-1 ring-stone-200" : "bg-transparent"
                            )}>
                                <lang.flag className="h-4 w-4 rounded-[2px]" />
                            </div>
                            <span>{lang.name}</span>
                        </div>
                        {currentLang === lang.code && (
                            <div className="h-1.5 w-1.5 rounded-sm bg-primary shadow-[0_0_0_2px_rgba(255,255,255,1)]" />
                        )}
                    </DropdownMenuItem>
                ))}
            </DropdownMenuContent>
        </DropdownMenu>
    );
}


