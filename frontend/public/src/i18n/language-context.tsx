"use client";

import React, { createContext, useContext, useState, useEffect } from "react";
import { Language, translations } from "./translations";

interface LanguageContextType {
    language: Language;
    setLanguage: (lang: Language) => void;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    t: (key: string, _params?: Record<string, any>) => string;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    resolveField: (obj: any, fieldPrefix: string) => string | null;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

export function LanguageProvider({ children }: { children: React.ReactNode }) {
    const [language, setLanguage] = useState<Language>("tr");

    // Load language from localStorage just once on mount
    useEffect(() => {
        const saved = localStorage.getItem("language") as Language;
        if (saved && (saved === "tr" || saved === "en")) {
            setLanguage(saved);
        }
    }, []);

    const changeLanguage = (lang: Language) => {
        setLanguage(lang);
        localStorage.setItem("language", lang);
    };

    // Helper to get nested translation
    // usage: t("nav.products")
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const t = (key: string, _params?: Record<string, any>): string => {
        const keys = key.split(".");
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        let value: any = translations[language];

        for (const k of keys) {
            if (value && typeof value === "object") {
                value = value[k];
            } else {
                return key; // Fallback to key if not found
            }
        }

        return typeof value === "string" ? value : key;
    };

    // Helper to resolve dynamic fields like title_tr vs title_en
    // usage: resolveField(product, "title") -> returns product.title_tr or product.title_en
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const resolveField = (obj: any, fieldPrefix: string): string | null => {
        if (!obj) return null;
        const key = `${fieldPrefix}_${language}`;
        return obj[key] || obj[`${fieldPrefix}_tr`] || null; // Fallback to TR
    };

    return (
        <LanguageContext.Provider value={{ language, setLanguage: changeLanguage, t, resolveField }}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage() {
    const context = useContext(LanguageContext);
    if (context === undefined) {
        throw new Error("useLanguage must be used within a LanguageProvider");
    }
    return context;
}
