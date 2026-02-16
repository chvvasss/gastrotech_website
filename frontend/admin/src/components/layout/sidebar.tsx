"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  MessageSquare,
  Package,
  GitBranch,
  Settings,
  ChevronLeft,
  Menu,
  Upload,
  ClipboardList,
  BookOpen,
  Tags,
  Folder,
  Layers,
  Tag,
  SlidersHorizontal,
  FileText,
  List,
  FileCode,
  QrCode,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import { Separator } from "@/components/ui/separator";
import { Brand } from "@/components/brand";

interface SidebarProps {
  collapsed: boolean;
  onToggle: () => void;
}

interface NavigationItem {
  name: string;
  href: string;
  icon: React.ElementType;
  activeCheck?: (pathname: string) => boolean;
}

const navigation: NavigationItem[] = [
  {
    name: "Dashboard",
    href: "/dashboard",
    icon: LayoutDashboard,
  },
  {
    name: "Talepler",
    href: "/inquiries",
    icon: MessageSquare,
  },
];

const catalogNavigation: NavigationItem[] = [
  {
    name: "Kategoriler",
    href: "/catalog/categories",
    icon: Folder,
    // Only highlight when on exact category management page (not list or [slug])
    activeCheck: (pathname) => pathname === "/catalog/categories",
  },
  {
    name: "Seriler",
    href: "/catalog/series",
    icon: Layers,
  },
  {
    name: "Markalar",
    href: "/catalog/brands",
    icon: Tag,
  },
  {
    name: "Taksonomi",
    href: "/catalog/taxonomy",
    icon: GitBranch,
  },
  {
    name: "Teknik Özellikler",
    href: "/catalog/specs",
    icon: SlidersHorizontal,
  },
  {
    name: "Özellik Şablonları",
    href: "/catalog/templates",
    icon: List,
  },
  {
    name: "Katalog Dosyaları",
    href: "/catalog/assets",
    icon: FileText,
  },
  {
    name: "Kategori Katalogları",
    href: "/catalog/category-catalogs",
    icon: BookOpen,
  },
  {
    name: "Ürünler",
    href: "/catalog/products",
    icon: Package,
    // Highlight for products AND category browsing (list + [slug] pages)
    activeCheck: (pathname) =>
      pathname.startsWith("/catalog/products") ||
      pathname.startsWith("/catalog/categories/list") ||
      pathname.startsWith("/catalog/categories/list") ||
      (pathname.startsWith("/catalog/categories/") && pathname !== "/catalog/categories"),
  },
  {
    name: "JSON İçe Aktar",
    href: "/catalog/json-import",
    icon: FileCode,
  },
];


const contentNavigation: NavigationItem[] = [
  {
    name: "Blog Yazıları",
    href: "/blog",
    icon: BookOpen,
    activeCheck: (pathname) => (pathname === "/blog" || pathname.startsWith("/blog/")) && !pathname.startsWith("/blog/categories"),
  },
  {
    name: "Kategoriler",
    href: "/blog/categories",
    icon: Tags,
  },
];

const opsNavigation: NavigationItem[] = [
  {
    name: "İçe Aktar",
    href: "/ops/import",
    icon: Upload,
  },
  {
    name: "İşlem Geçmişi",
    href: "/ops/audit-logs",
    icon: ClipboardList,
  },
  {
    name: "QR Kod Üretici",
    href: "/qr-generator",
    icon: QrCode,
  },
];

const secondaryNavigation: NavigationItem[] = [
  {
    name: "Ayarlar",
    href: "/settings",
    icon: Settings,
  },
];

interface NavItemProps {
  item: NavigationItem;
  pathname: string;
  collapsed: boolean;
}

function NavItem({ item, pathname, collapsed }: NavItemProps) {
  const isActive = item.activeCheck
    ? item.activeCheck(pathname)
    : pathname === item.href || pathname.startsWith(item.href + "/");

  return (
    <Link
      href={item.href}
      className={cn(
        "flex items-center gap-3 rounded-lg px-3 py-2 text-sm font-medium transition-colors",
        isActive
          ? "bg-primary text-white shadow-sm"
          : "text-stone-600 hover:bg-stone-100 hover:text-stone-900",
        collapsed && "justify-center px-2"
      )}
      title={collapsed ? item.name : undefined}
    >
      <item.icon className={cn("h-[1.125rem] w-[1.125rem] shrink-0", isActive && "text-white")} />
      {!collapsed && <span>{item.name}</span>}
    </Link>
  );
}

function NavSection({
  title,
  items,
  pathname,
  collapsed
}: {
  title: string;
  items: NavigationItem[];
  pathname: string;
  collapsed: boolean;
}) {
  return (
    <div className="space-y-1">
      {!collapsed && (
        <p className="px-3 py-1.5 text-label-sm text-stone-400">
          {title}
        </p>
      )}
      {items.map((item) => (
        <NavItem key={item.name} item={item} pathname={pathname} collapsed={collapsed} />
      ))}
    </div>
  );
}

export function Sidebar({ collapsed, onToggle }: SidebarProps) {
  const pathname = usePathname();

  return (
    <aside
      className={cn(
        "fixed left-0 top-0 z-40 h-screen border-r border-stone-200 bg-white transition-all duration-200 flex flex-col",
        collapsed ? "w-16" : "w-64"
      )}
    >
      {/* Brand Header */}
      <div className={cn(
        "relative flex items-center border-b border-stone-200",
        collapsed ? "h-20 justify-center px-2" : "h-28 justify-center px-4"
      )}>
        <Brand
          variant={collapsed ? "sidebar-collapsed" : "sidebar"}
          size={collapsed ? "md" : "xl"}
        />

        {!collapsed && (
          <Button
            variant="ghost"
            size="icon"
            onClick={onToggle}
            className="absolute right-2 text-stone-500 hover:text-stone-900 hover:bg-stone-100 h-8 w-8"
          >
            <ChevronLeft className="h-4 w-4" />
          </Button>
        )}
      </div>

      {/* Collapse toggle for collapsed state */}
      {collapsed && (
        <div className="flex justify-center py-2 border-b border-stone-100 relative z-50">
          <Button
            variant="ghost"
            size="icon"
            onClick={(e) => {
              e.stopPropagation();
              onToggle();
            }}
            title="Menüyü Genişlet"
            className="text-stone-500 hover:text-stone-900 hover:bg-stone-100 h-8 w-8 cursor-pointer"
          >
            <Menu className="h-4 w-4" />
          </Button>
        </div>
      )}

      {/* Navigation */}
      <nav className="flex-1 overflow-y-auto p-2 space-y-4">
        {/* Main */}
        <NavSection title="Ana Menü" items={navigation} pathname={pathname} collapsed={collapsed} />

        <Separator className="bg-stone-100" />

        {/* Catalog */}
        <NavSection title="Katalog" items={catalogNavigation} pathname={pathname} collapsed={collapsed} />

        <Separator className="bg-stone-100" />

        {/* Content */}
        <NavSection title="İçerik Yönetimi" items={contentNavigation} pathname={pathname} collapsed={collapsed} />

        <Separator className="bg-stone-100" />

        {/* Operations */}
        <NavSection title="Operasyonlar" items={opsNavigation} pathname={pathname} collapsed={collapsed} />

        <Separator className="bg-stone-100" />

        {/* Settings at bottom */}
        <div className="space-y-1">
          {secondaryNavigation.map((item) => (
            <NavItem key={item.name} item={item} pathname={pathname} collapsed={collapsed} />
          ))}
        </div>
      </nav>

      {/* Footer */}
      {!collapsed && (
        <div className="p-4 border-t border-stone-100">
          <p className="text-tiny text-stone-400 text-center">
            © {new Date().getFullYear()} Gastrotech
          </p>
        </div>
      )}
    </aside>
  );
}
