"use client";

import { useEffect, useState, useCallback } from "react";
import { Search, LogOut, User, Rows3, Rows4, Menu } from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { Avatar, AvatarFallback } from "@/components/ui/avatar";
import { useMe, useLogout } from "@/hooks/use-auth";
import { getInitials, cn } from "@/lib/utils";
import { GlobalSearch, useGlobalSearchShortcut } from "./global-search";

interface TopbarProps {
  breadcrumbs?: React.ReactNode;
  onMobileMenuToggle?: () => void;
}

type Density = "compact" | "comfortable";

function useDensity() {
  const [density, setDensityState] = useState<Density>("comfortable");

  useEffect(() => {
    // Load from localStorage on mount
    const saved = localStorage.getItem("admin_density") as Density | null;
    if (saved && (saved === "compact" || saved === "comfortable")) {
      setDensityState(saved);
      document.documentElement.setAttribute("data-density", saved);
    }
  }, []);

  const setDensity = (value: Density) => {
    setDensityState(value);
    localStorage.setItem("admin_density", value);
    document.documentElement.setAttribute("data-density", value);
  };

  return { density, setDensity };
}

export function Topbar({ breadcrumbs, onMobileMenuToggle }: TopbarProps) {
  const { data: user } = useMe();
  const logout = useLogout();
  const { density, setDensity } = useDensity();
  const [searchOpen, setSearchOpen] = useState(false);

  const toggleDensity = () => {
    setDensity(density === "compact" ? "comfortable" : "compact");
  };

  const openSearch = useCallback(() => {
    setSearchOpen(true);
  }, []);

  // Global keyboard shortcut: Ctrl+K / Cmd+K
  useGlobalSearchShortcut(openSearch);

  return (
    <>
      <header className="sticky top-0 z-30 flex h-14 items-center gap-4 border-b border-stone-200 bg-white/95 backdrop-blur-sm px-4 lg:px-6 shadow-sm">
        {/* Mobile Hamburger Menu */}
        {onMobileMenuToggle && (
          <Button
            type="button"
            variant="ghost"
            size="icon"
            onClick={onMobileMenuToggle}
            className="h-9 w-9 lg:hidden text-stone-600 hover:text-stone-900 hover:bg-stone-100 flex-shrink-0"
            aria-label="Menü"
          >
            <Menu className="h-5 w-5" />
          </Button>
        )}

        {/* Left: Breadcrumbs */}
        <div className="flex-shrink-0 min-w-0 max-w-[150px] sm:max-w-[200px] lg:max-w-none hidden sm:block">
          {breadcrumbs}
        </div>

        {/* Center: Global Search - Hero element */}
        <div className="flex-1 flex justify-center px-2">
          <button
            type="button"
            onClick={openSearch}
            className={cn(
              "group relative flex items-center gap-2 w-full max-w-md",
              "px-4 py-2 rounded-lg border border-stone-200 bg-stone-50/80",
              "text-sm text-stone-500 hover:text-stone-700",
              "transition-all duration-200",
              "hover:bg-white hover:border-stone-300",
              "hover:shadow-search-glow",
              "focus:outline-none focus:ring-2 focus:ring-primary/30 focus:border-primary/50",
              "focus:shadow-search-glow-focus"
            )}
            aria-label="Global arama (Ctrl+K)"
          >
            <Search className="h-4 w-4 text-primary/70 group-hover:text-primary transition-colors" />
            <span className="flex-1 text-left truncate">
              Ara... (ürün, kategori, seri)
            </span>
            <kbd className="hidden sm:inline-flex items-center gap-0.5 px-1.5 py-0.5 rounded bg-stone-200/80 text-xs text-stone-500 font-mono">
              <span className="text-[10px]">⌘</span>K
            </kbd>
          </button>
        </div>

        {/* Right: Actions */}
        <div className="flex items-center gap-1 flex-shrink-0">
          {/* Mobile Search Button */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={openSearch}
                  className="h-9 w-9 text-stone-500 hover:text-primary hover:bg-primary/5 sm:hidden"
                  aria-label="Ara"
                >
                  <Search className="h-4 w-4" />
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>Ara (⌘K)</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* Density Toggle */}
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  type="button"
                  variant="ghost"
                  size="icon"
                  onClick={toggleDensity}
                  className="h-9 w-9 text-stone-500 hover:text-stone-900 hover:bg-stone-100"
                  aria-label={density === "compact" ? "Rahat görünüm" : "Sıkı görünüm"}
                >
                  {density === "compact" ? (
                    <Rows3 className="h-4 w-4" />
                  ) : (
                    <Rows4 className="h-4 w-4" />
                  )}
                </Button>
              </TooltipTrigger>
              <TooltipContent>
                <p>{density === "compact" ? "Rahat görünüm" : "Sıkı görünüm"}</p>
              </TooltipContent>
            </Tooltip>
          </TooltipProvider>

          {/* User Menu */}
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                className="relative h-9 w-9 rounded-full hover:bg-stone-100 p-0 ml-1"
              >
                <Avatar className="h-8 w-8 ring-2 ring-stone-100">
                  <AvatarFallback className="bg-primary text-white text-xs font-semibold">
                    {user ? getInitials(user.email) : "?"}
                  </AvatarFallback>
                </Avatar>
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent className="w-56" align="end" forceMount>
              <DropdownMenuLabel className="font-normal">
                <div className="flex flex-col space-y-1">
                  <p className="text-sm font-medium leading-none text-stone-900">
                    {user?.email || "Kullanıcı"}
                  </p>
                  <p className="text-xs leading-none text-stone-500 capitalize">
                    {user?.role || "user"}
                  </p>
                </div>
              </DropdownMenuLabel>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="cursor-pointer text-stone-400" disabled>
                <User className="mr-2 h-4 w-4" />
                <span>Profil (yakında)</span>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem
                onClick={logout}
                className="text-primary cursor-pointer focus:text-primary focus:bg-primary/5"
              >
                <LogOut className="mr-2 h-4 w-4" />
                <span>Çıkış Yap</span>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </header>

      {/* Global Search Dialog */}
      <GlobalSearch open={searchOpen} onOpenChange={setSearchOpen} />
    </>
  );
}
