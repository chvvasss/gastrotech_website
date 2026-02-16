"use client";

import { useState, useRef, useEffect } from "react";
import { PLPSortOption } from "@/lib/api/schemas";
import { cn } from "@/lib/utils";
import { ChevronDown, Check } from "lucide-react";

interface SortingDropdownProps {
    sortOptions: PLPSortOption[];
    currentSort: string;
    onSortChange: (sortKey: string) => void;
}

export function SortingDropdown({
    sortOptions,
    currentSort,
    onSortChange,
}: SortingDropdownProps) {
    const [isOpen, setIsOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    // Close dropdown on outside click
    useEffect(() => {
        const handleClickOutside = (event: MouseEvent) => {
            if (
                dropdownRef.current &&
                !dropdownRef.current.contains(event.target as Node)
            ) {
                setIsOpen(false);
            }
        };

        document.addEventListener("mousedown", handleClickOutside);
        return () => document.removeEventListener("mousedown", handleClickOutside);
    }, []);

    const currentOption = sortOptions.find((opt) => opt.key === currentSort);

    return (
        <div ref={dropdownRef} className="relative">
            <button
                onClick={() => setIsOpen(!isOpen)}
                className="flex items-center gap-2 rounded-sm border border-border bg-card px-4 py-2 text-sm font-medium text-foreground transition-colors hover:border-primary/50 hover:bg-card/80"
            >
                <span className="text-muted-foreground">Sıralama:</span>
                <span className="font-semibold">{currentOption?.label ?? "Seçiniz"}</span>
                <ChevronDown
                    className={cn(
                        "h-4 w-4 text-muted-foreground transition-transform",
                        isOpen && "rotate-180"
                    )}
                />
            </button>

            {/* Dropdown menu */}
            {isOpen && (
                <div className="absolute right-0 z-20 mt-1 min-w-[200px] rounded-sm border border-border bg-card shadow-lg">
                    <div className="py-1">
                        {sortOptions.map((option) => {
                            const isSelected = option.key === currentSort;
                            return (
                                <button
                                    key={option.key}
                                    onClick={() => {
                                        onSortChange(option.key);
                                        setIsOpen(false);
                                    }}
                                    className={cn(
                                        "flex w-full items-center justify-between px-4 py-2 text-sm transition-colors",
                                        isSelected
                                            ? "bg-primary/10 text-primary font-medium"
                                            : "text-foreground hover:bg-muted"
                                    )}
                                >
                                    {option.label}
                                    {isSelected && <Check className="h-4 w-4" />}
                                </button>
                            );
                        })}
                    </div>
                </div>
            )}
        </div>
    );
}
