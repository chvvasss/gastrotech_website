import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/layout";
import { Home, Search, ArrowLeft } from "lucide-react";

export default function NotFound() {
  return (
    <div className="flex min-h-[70vh] flex-col items-center justify-center bg-muted/10">
      <Container className="text-center">
        <div className="relative inline-block">
          <p className="text-9xl font-black text-primary/10 select-none">404</p>
          <div className="absolute inset-0 flex items-center justify-center">
            <span className="text-4xl font-bold text-primary">Hay Aksi!</span>
          </div>
        </div>

        <h1 className="mt-4 text-2xl font-bold text-foreground lg:text-3xl">
          Aradığınız Sayfa Bulunamadı
        </h1>
        <p className="mx-auto mt-4 max-w-md text-lg text-muted-foreground">
          İstediğiniz sayfa taşınmış, silinmiş veya hiç var olmamış olabilir.
        </p>

        <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
          <Button asChild size="lg" className="min-w-[160px] shadow-lg shadow-primary/20">
            <Link href="/">
              <Home className="mr-2 h-4 w-4" />
              Ana Sayfa
            </Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="min-w-[160px]">
            <Link href="/kategori">
              <Search className="mr-2 h-4 w-4" />
              Kategorilere Göz At
            </Link>
          </Button>
        </div>

        <Button variant="link" className="mt-8 text-muted-foreground" asChild>
          <Link href="/iletisim">
            <ArrowLeft className="mr-2 h-4 w-4" />
            Bir sorun olduğunu mu düşünüyorsunuz? Bize bildirin.
          </Link>
        </Button>
      </Container>
    </div>
  );
}
