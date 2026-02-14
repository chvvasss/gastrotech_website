"use client";

import { Suspense } from "react";
import Link from "next/link";
import { useSearchParams } from "next/navigation";
import { Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Skeleton } from "@/components/ui/skeleton";
import { CheckCircle, ArrowRight, Phone, Mail } from "lucide-react";

function InquirySuccessContent() {
  const searchParams = useSearchParams();
  const inquiryId = searchParams.get("id");

  return (
    <Container className="py-16 lg:py-24">
      <div className="mx-auto max-w-lg text-center">
        {/* Success Icon */}
        <div className="mx-auto mb-6 flex h-20 w-20 items-center justify-center rounded-sm bg-green-100">
          <CheckCircle className="h-10 w-10 text-green-600" />
        </div>

        {/* Title */}
        <h1 className="text-3xl font-bold">Teklif Talebiniz Alındı!</h1>

        {/* Inquiry ID */}
        {inquiryId && (
          <div className="mt-4 rounded-sm bg-muted px-4 py-2 inline-block">
            <span className="text-sm text-muted-foreground">Talep No: </span>
            <span className="font-mono font-semibold">#{inquiryId}</span>
          </div>
        )}

        {/* Description */}
        <p className="mt-6 text-muted-foreground">
          Teklif talebiniz başarıyla iletildi. Ekibimiz en kısa sürede sizinle
          iletişime geçecektir.
        </p>

        {/* Timeline */}
        <div className="mt-8 rounded-sm border bg-card p-6 text-left">
          <h3 className="mb-4 font-semibold">Sonraki Adımlar</h3>
          <ul className="space-y-3 text-sm">
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-primary text-xs font-bold text-primary-foreground">
                1
              </span>
              <span>
                Talebiniz satış ekibimize iletildi ve inceleniyor.
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-muted text-xs font-bold">
                2
              </span>
              <span className="text-muted-foreground">
                1-2 iş günü içinde size özel teklif hazırlanacak.
              </span>
            </li>
            <li className="flex items-start gap-3">
              <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-muted text-xs font-bold">
                3
              </span>
              <span className="text-muted-foreground">
                Teklif e-posta veya telefon ile size ulaştırılacak.
              </span>
            </li>
          </ul>
        </div>

        {/* Contact Info */}
        <div className="mt-6 rounded-sm bg-muted/50 p-4 text-sm">
          <p className="mb-2 font-medium">Acil mi? Bizi arayın:</p>
          <div className="flex flex-wrap items-center justify-center gap-4">
            <a
              href="tel:+902124567890"
              className="flex items-center gap-2 text-primary hover:underline"
            >
              <Phone className="h-4 w-4" />
              +90 212 456 78 90
            </a>
            <a
              href="mailto:satis@gastrotech.com"
              className="flex items-center gap-2 text-primary hover:underline"
            >
              <Mail className="h-4 w-4" />
              satis@gastrotech.com
            </a>
          </div>
        </div>

        {/* Actions */}
        <div className="mt-8 flex flex-col gap-3 sm:flex-row sm:justify-center">
          <Button asChild size="lg">
            <Link href="/">
              Ana Sayfaya Dön
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg">
            <Link href="/urunler">
              Ürünlere Göz At
              <ArrowRight className="ml-2 h-4 w-4" />
            </Link>
          </Button>
        </div>
      </div>
    </Container>
  );
}

function LoadingFallback() {
  return (
    <Container className="py-16 lg:py-24">
      <div className="mx-auto max-w-lg text-center">
        <Skeleton className="mx-auto h-20 w-20 rounded-sm" />
        <Skeleton className="mx-auto mt-6 h-8 w-64" />
        <Skeleton className="mx-auto mt-4 h-6 w-32" />
        <Skeleton className="mx-auto mt-6 h-16 w-full" />
      </div>
    </Container>
  );
}

export default function InquirySuccessPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <InquirySuccessContent />
    </Suspense>
  );
}
