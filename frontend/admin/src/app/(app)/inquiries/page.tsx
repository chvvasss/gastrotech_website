"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { type ColumnDef } from "@tanstack/react-table";
import { Search, Filter } from "lucide-react";
import { AppShell, PageHeader } from "@/components/layout";
import { DataTable, Pagination } from "@/components/data-table";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Badge } from "@/components/ui/badge";
import { useInquiries } from "@/hooks/use-inquiries";
import { formatDate } from "@/lib/utils";
import type { InquiryListItem, InquiryStatus } from "@/types/api";

const ALL_STATUS = "_all";

const statusLabels: Record<InquiryStatus, string> = {
  new: "Yeni",
  in_progress: "İşlemde",
  closed: "Kapalı",
};

const statusVariants: Record<InquiryStatus, "info" | "warning" | "success"> = {
  new: "info",
  in_progress: "warning",
  closed: "success",
};

const columns: ColumnDef<InquiryListItem>[] = [
  {
    accessorKey: "full_name",
    header: "Müşteri",
    cell: ({ row }) => (
      <div>
        <p className="font-medium text-stone-900">{row.original.full_name}</p>
        <p className="text-xs text-stone-500">{row.original.email}</p>
      </div>
    ),
  },
  {
    accessorKey: "company",
    header: "Firma",
    cell: ({ row }) => (
      <span className="text-stone-700">{row.original.company || "-"}</span>
    ),
  },
  {
    accessorKey: "items_count",
    header: "Ürün",
    cell: ({ row }) => (
      <div>
        <p className="font-medium text-stone-900">{row.original.items_count} adet</p>
        <p className="text-xs text-stone-500 truncate max-w-[200px]">
          {row.original.items_summary || "-"}
        </p>
      </div>
    ),
  },
  {
    accessorKey: "status",
    header: "Durum",
    cell: ({ row }) => {
      const status = row.original.status;
      return (
        <Badge variant={statusVariants[status]}>{statusLabels[status]}</Badge>
      );
    },
  },
  {
    accessorKey: "created_at",
    header: "Tarih",
    cell: ({ row }) => (
      <span className="text-stone-600">{formatDate(row.original.created_at)}</span>
    ),
  },
];

export default function InquiriesPage() {
  const router = useRouter();
  const [page, setPage] = useState(1);
  const [status, setStatus] = useState<string>(ALL_STATUS);
  const [search, setSearch] = useState("");
  const [searchInput, setSearchInput] = useState("");

  const pageSize = 20;

  const { data, isLoading } = useInquiries({
    page,
    page_size: pageSize,
    status: status === ALL_STATUS ? undefined : (status as InquiryStatus),
    search: search || undefined,
    ordering: "-created_at",
  });

  const handleSearch = () => {
    setSearch(searchInput);
    setPage(1);
  };

  const handleStatusChange = (value: string) => {
    setStatus(value);
    setPage(1);
  };

  const handleRowClick = (row: InquiryListItem) => {
    router.push(`/inquiries/${row.id}`);
  };

  const totalPages = Math.ceil((data?.count ?? 0) / pageSize);

  return (
    <AppShell breadcrumbs={[{ label: "Talepler" }]}>
      <PageHeader
        title="Teklif Talepleri"
        description="Müşterilerden gelen teklif taleplerini yönetin"
      />

      {/* Filters */}
      <div className="flex flex-col sm:flex-row gap-4 mb-6">
        <div className="flex flex-1 gap-2">
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-stone-400" />
            <Input
              placeholder="İsim veya e-posta ile ara..."
              value={searchInput}
              onChange={(e) => setSearchInput(e.target.value)}
              onKeyDown={(e) => e.key === "Enter" && handleSearch()}
              className="pl-10 bg-white border-stone-200"
            />
          </div>
          <Button onClick={handleSearch} variant="secondary" className="bg-stone-100 hover:bg-stone-200 text-stone-700">
            <Search className="h-4 w-4" />
          </Button>
        </div>
        <div className="flex gap-2">
          <Select value={status} onValueChange={handleStatusChange}>
            <SelectTrigger className="w-[160px] bg-white border-stone-200">
              <Filter className="h-4 w-4 mr-2 text-stone-500" />
              <SelectValue placeholder="Tüm durumlar" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value={ALL_STATUS}>Tüm durumlar</SelectItem>
              <SelectItem value="new">Yeni</SelectItem>
              <SelectItem value="in_progress">İşlemde</SelectItem>
              <SelectItem value="closed">Kapalı</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* Table */}
      <DataTable
        columns={columns}
        data={data?.results ?? []}
        loading={isLoading}
        emptyMessage="Talep bulunamadı"
        emptyDescription="Henüz teklif talebi gelmemiş veya filtrelere uygun sonuç yok."
        onRowClick={handleRowClick}
      />

      {/* Pagination */}
      {data && data.count > 0 && (
        <Pagination
          page={page}
          totalPages={totalPages}
          totalItems={data.count}
          pageSize={pageSize}
          onPageChange={setPage}
        />
      )}
    </AppShell>
  );
}
