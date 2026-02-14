"use client";

import { useState } from "react";
import Link from "next/link";
import {
  MessageSquare,
  Package,
  Layers,
  FolderTree,
  Image,
  AlertTriangle,
  CheckCircle,
  Clock,
  TrendingUp
} from "lucide-react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  BarChart,
  Bar,
  PieChart,
  Pie,
  Cell,
} from "recharts";
import { AppShell, PageHeader, StatCard } from "@/components/layout";
import { useStats } from "@/hooks/use-products";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";

type DateRange = "7d" | "14d" | "30d" | "90d";

const STATUS_COLORS = {
  active: "#22c55e",
  draft: "#f59e0b",
  archived: "#6b7280",
};

export default function DashboardPage() {
  const [range, setRange] = useState<DateRange>("30d");
  const { data: stats, isLoading } = useStats(range);

  const rangeLabel = {
    "7d": "Son 7 gün",
    "14d": "Son 14 gün",
    "30d": "Son 30 gün",
    "90d": "Son 90 gün",
  }[range];

  // Format date for chart display
  const formatChartDate = (dateStr: string) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString("tr-TR", { day: "2-digit", month: "short" });
  };

  // Prepare pie chart data
  const statusPieData = stats ? [
    { name: "Aktif", value: stats.products_active, fill: STATUS_COLORS.active },
    { name: "Taslak", value: stats.products_draft, fill: STATUS_COLORS.draft },
    { name: "Arşiv", value: stats.products_archived, fill: STATUS_COLORS.archived },
  ] : [];

  return (
    <AppShell breadcrumbs={[{ label: "Dashboard" }]}>
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6">
        <PageHeader
          title="Dashboard"
          description="GastroTech B2B yönetim paneline hoş geldiniz"
        />
        <Select value={range} onValueChange={(v) => setRange(v as DateRange)}>
          <SelectTrigger className="w-full sm:w-[140px] bg-white">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="7d">Son 7 gün</SelectItem>
            <SelectItem value="14d">Son 14 gün</SelectItem>
            <SelectItem value="30d">Son 30 gün</SelectItem>
            <SelectItem value="90d">Son 90 gün</SelectItem>
          </SelectContent>
        </Select>
      </div>

      {/* Primary KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <StatCard
          title="Yeni Talepler"
          value={stats?.inquiries_new_range ?? 0}
          description={rangeLabel}
          icon={MessageSquare}
          loading={isLoading}
          trend={stats?.inquiries_new_range && stats.inquiries_new_range > 0 ? "up" : undefined}
        />
        <StatCard
          title="Açık Talepler"
          value={stats?.inquiries_open ?? 0}
          description="İşlem bekleyen"
          icon={Clock}
          loading={isLoading}
        />
        <StatCard
          title="Aktif Ürünler"
          value={stats?.products_active ?? 0}
          description={`/ ${stats?.products_total ?? 0} toplam`}
          icon={Package}
          loading={isLoading}
        />
        <StatCard
          title="Varyantlar"
          value={stats?.variants_total ?? 0}
          description="Model çeşitleri"
          icon={Layers}
          loading={isLoading}
        />
      </div>

      {/* Secondary KPI Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-6">
        <StatCard
          title="Kategoriler"
          value={stats?.categories_total ?? 0}
          description="Ana kategoriler"
          icon={FolderTree}
          loading={isLoading}
        />
        <StatCard
          title="Seriler"
          value={stats?.series_total ?? 0}
          description="Ürün serileri"
          icon={TrendingUp}
          loading={isLoading}
        />
        <StatCard
          title="Medya"
          value={stats?.media_total ?? 0}
          description={`${stats?.media_unreferenced_total ?? 0} referanssız`}
          icon={Image}
          loading={isLoading}
        />
        <StatCard
          title="Kapalı Talepler"
          value={stats?.inquiries_closed ?? 0}
          description="Tamamlanan"
          icon={CheckCircle}
          loading={isLoading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 lg:grid-cols-2 mb-6">
        {/* Inquiries Line Chart */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Talep Trendi</CardTitle>
            <CardDescription className="text-stone-500">{rangeLabel}</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[250px] w-full" />
            ) : stats?.inquiries_by_day && stats.inquiries_by_day.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <LineChart data={stats.inquiries_by_day}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                  <XAxis
                    dataKey="date"
                    tickFormatter={formatChartDate}
                    tick={{ fontSize: 12 }}
                    stroke="#9ca3af"
                  />
                  <YAxis
                    tick={{ fontSize: 12 }}
                    stroke="#9ca3af"
                    allowDecimals={false}
                  />
                  <Tooltip
                    labelFormatter={(value) => new Date(value).toLocaleDateString("tr-TR")}
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e5e5e5",
                      borderRadius: "8px"
                    }}
                  />
                  <Line
                    type="monotone"
                    dataKey="count"
                    stroke="#dc2626"
                    strokeWidth={2}
                    dot={{ fill: "#dc2626", strokeWidth: 2 }}
                  />
                </LineChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center">
                <p className="text-stone-400">Bu dönemde talep yok</p>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Top Requested Variants Bar Chart */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">En Çok Talep Edilen</CardTitle>
            <CardDescription className="text-stone-500">Varyant bazlı - {rangeLabel}</CardDescription>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[250px] w-full" />
            ) : stats?.top_requested_variants && stats.top_requested_variants.length > 0 ? (
              <ResponsiveContainer width="100%" height={250}>
                <BarChart
                  data={stats.top_requested_variants.slice(0, 5)}
                  layout="vertical"
                  margin={{ left: 20 }}
                >
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e5e5" />
                  <XAxis type="number" tick={{ fontSize: 12 }} stroke="#9ca3af" allowDecimals={false} />
                  <YAxis
                    type="category"
                    dataKey="model_code"
                    tick={{ fontSize: 11 }}
                    width={80}
                    stroke="#9ca3af"
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: "white",
                      border: "1px solid #e5e5e5",
                      borderRadius: "8px"
                    }}
                    formatter={(value, name, props) => [
                      `${value} talep`,
                      props.payload.name_tr || props.payload.model_code
                    ]}
                  />
                  <Bar dataKey="count" fill="#dc2626" radius={[0, 4, 4, 0]} />
                </BarChart>
              </ResponsiveContainer>
            ) : (
              <div className="h-[250px] flex items-center justify-center">
                <p className="text-stone-400">Bu dönemde talep yok</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Products Status + Recent Activity */}
      <div className="grid gap-6 lg:grid-cols-3 mb-6">
        {/* Products by Status Pie Chart */}
        <Card className="border-stone-200 bg-white">
          <CardHeader>
            <CardTitle className="text-lg text-stone-900">Ürün Durumları</CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-[200px] w-full" />
            ) : (
              <div className="flex items-center justify-center">
                <ResponsiveContainer width="100%" height={200}>
                  <PieChart>
                    <Pie
                      data={statusPieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={50}
                      outerRadius={80}
                      paddingAngle={2}
                      dataKey="value"
                    >
                      {statusPieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.fill} />
                      ))}
                    </Pie>
                    <Tooltip
                      contentStyle={{
                        backgroundColor: "white",
                        border: "1px solid #e5e5e5",
                        borderRadius: "8px"
                      }}
                    />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
            <div className="flex justify-center gap-4 mt-2">
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: STATUS_COLORS.active }} />
                <span className="text-xs text-stone-600">Aktif</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: STATUS_COLORS.draft }} />
                <span className="text-xs text-stone-600">Taslak</span>
              </div>
              <div className="flex items-center gap-1">
                <div className="w-3 h-3 rounded" style={{ backgroundColor: STATUS_COLORS.archived }} />
                <span className="text-xs text-stone-600">Arşiv</span>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Recent Inquiries */}
        <Card className="border-stone-200 bg-white">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg text-stone-900">Son Talepler</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/inquiries">Tümü</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-14" />
                ))}
              </div>
            ) : stats?.recently_updated_inquiries?.length ? (
              <div className="space-y-2">
                {stats.recently_updated_inquiries.slice(0, 5).map((inquiry) => (
                  <Link
                    key={inquiry.id}
                    href={`/inquiries/${inquiry.id}`}
                    className="flex items-center justify-between p-2 rounded-lg bg-stone-50 hover:bg-stone-100 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm text-stone-900 truncate">
                        {inquiry.full_name}
                      </p>
                      <p className="text-xs text-stone-500 truncate">
                        {inquiry.company || "—"}
                      </p>
                    </div>
                    <div className="flex items-center gap-2 ml-2">
                      <Badge
                        variant="secondary"
                        className={`text-xs ${inquiry.status === "new"
                            ? "bg-primary/10 text-primary"
                            : inquiry.status === "in_progress"
                              ? "bg-amber-100 text-amber-800"
                              : "bg-green-100 text-green-800"
                          }`}
                      >
                        {inquiry.items_count}
                      </Badge>
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-400 text-center py-8">Talep yok</p>
            )}
          </CardContent>
        </Card>

        {/* Recent Products */}
        <Card className="border-stone-200 bg-white">
          <CardHeader className="pb-3">
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg text-stone-900">Son Güncellenen</CardTitle>
              <Button variant="ghost" size="sm" asChild>
                <Link href="/catalog/products">Tümü</Link>
              </Button>
            </div>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <div className="space-y-3">
                {[1, 2, 3, 4].map((i) => (
                  <Skeleton key={i} className="h-14" />
                ))}
              </div>
            ) : stats?.recently_updated_products?.length ? (
              <div className="space-y-2">
                {stats.recently_updated_products.slice(0, 5).map((product) => (
                  <Link
                    key={product.slug}
                    href={`/catalog/products/${product.slug}`}
                    className="flex items-center justify-between p-2 rounded-lg bg-stone-50 hover:bg-stone-100 transition-colors"
                  >
                    <div className="min-w-0 flex-1">
                      <p className="font-medium text-sm text-stone-900 truncate">
                        {product.title_tr}
                      </p>
                      <p className="text-xs text-stone-400 font-mono truncate">
                        {product.slug}
                      </p>
                    </div>
                    <Badge
                      variant="secondary"
                      className={`text-xs ml-2 ${product.status === "active"
                          ? "bg-green-100 text-green-800"
                          : product.status === "draft"
                            ? "bg-amber-100 text-amber-800"
                            : "bg-stone-100 text-stone-600"
                        }`}
                    >
                      {product.status === "active" ? "Aktif" : product.status === "draft" ? "Taslak" : "Arşiv"}
                    </Badge>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-stone-400 text-center py-8">Ürün yok</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Quick Actions */}
      <Card className="border-stone-200 bg-white">
        <CardHeader>
          <CardTitle className="text-lg text-stone-900">Hızlı Erişim</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
            <Button variant="outline" asChild className="h-auto py-4 flex-col gap-2">
              <Link href="/inquiries">
                <MessageSquare className="h-5 w-5 text-primary" />
                <span className="text-sm">Talepler</span>
              </Link>
            </Button>
            <Button variant="outline" asChild className="h-auto py-4 flex-col gap-2">
              <Link href="/catalog/products">
                <Package className="h-5 w-5 text-primary" />
                <span className="text-sm">Ürünler</span>
              </Link>
            </Button>
            <Button variant="outline" asChild className="h-auto py-4 flex-col gap-2">
              <Link href="/catalog/taxonomy">
                <FolderTree className="h-5 w-5 text-primary" />
                <span className="text-sm">Taksonomi</span>
              </Link>
            </Button>
            <Button variant="outline" asChild className="h-auto py-4 flex-col gap-2">
              <Link href="/debug">
                <AlertTriangle className="h-5 w-5 text-amber-500" />
                <span className="text-sm">Debug</span>
              </Link>
            </Button>
          </div>
        </CardContent>
      </Card>
    </AppShell>
  );
}
