"use client";

import { useLanguage } from "@/i18n/language-context";
import { Button } from "@/components/ui/button";
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import { Check } from "lucide-react";
import { TurkeyFlag, UKFlag } from "@/components/icons/flags";

export function LanguageSwitcher() {
    const { language, setLanguage } = useLanguage();

    return (
        <DropdownMenu>
            <DropdownMenuTrigger asChild>
                <Button
                    variant="ghost"
                    size="sm"
                    className="relative h-9 w-9 rounded-sm px-0 hover:bg-muted/50 focus-visible:ring-0 focus-visible:ring-offset-0 overflow-hidden"
                >
                    <span className="sr-only">Dil değiştir</span>
                    {language === "tr" ? (
                        <TurkeyFlag className="h-5 w-auto rounded-[2px] shadow-sm" />
                    ) : (
                        <UKFlag className="h-5 w-auto rounded-[2px] shadow-sm" />
                    )}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end" className="w-[160px]">
                <DropdownMenuItem
                    onClick={() => setLanguage("tr")}
                    className="flex items-center justify-between cursor-pointer py-2"
                >
                    <span className="flex items-center gap-3">
                        <TurkeyFlag className="h-4 w-auto rounded-[1px]" />
                        <span className="font-medium">Türkçe</span>
                    </span>
                    {language === "tr" && <Check className="h-4 w-4 text-primary" />}
                </DropdownMenuItem>
                <DropdownMenuItem
                    onClick={() => setLanguage("en")}
                    className="flex items-center justify-between cursor-pointer py-2"
                >
                    <span className="flex items-center gap-3">
                        <UKFlag className="h-4 w-auto rounded-[1px]" />
                        <span className="font-medium">English</span>
                    </span>
                    {language === "en" && <Check className="h-4 w-4 text-primary" />}
                </DropdownMenuItem>
            </DropdownMenuContent>
        </DropdownMenu>
    );
}
