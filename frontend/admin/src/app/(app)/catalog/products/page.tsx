"use client";

import { useMemo } from "react";
import { useSearchParams } from "next/navigation";
import { GitBranch } from "lucide-react";
import Link from "next/link";
import { AppShell, PageHeader } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { ProductsTable } from "@/components/catalog/products-table";
import { useNav } from "@/hooks/use-navigation";

export default function ProductsPage() {
  const searchParams = useSearchParams();
  const { data: categories } = useNav(); // Prefetch validation if needed

  // Allow bare products list - removed redirect that caused infinite loop issues

  const breadcrumbs = useMemo(() => {
    return [
      { label: "Katalog", href: "/catalog/categories/list" },
      { label: "Kategoriler", href: "/catalog/categories/list" },
      { label: "Tüm Ürünler" },
    ];
  }, []);

  return (
    <AppShell breadcrumbs={breadcrumbs}>
      <PageHeader
        title="Tüm Ürünler"
        description="Katalogdaki tüm ürünlerin listesi"
        actions={
          <Button asChild variant="outline" className="gap-2">
            <Link href="/catalog/taxonomy">
              <GitBranch className="h-4 w-4" />
              Taksonomi
            </Link>
          </Button>
        }
      />

      <div className="bg-white p-6 rounded-lg border border-stone-200">
        <ProductsTable scope="all" />
      </div>
    </AppShell>
  );
}
