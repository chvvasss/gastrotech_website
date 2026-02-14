"use client";

import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Container } from "@/components/layout";
import { RefreshCcw, Home } from "lucide-react";
import Link from "next/link";

export default function Error({
    error,
    reset,
}: {
    error: Error & { digest?: string };
    reset: () => void;
}) {
    useEffect(() => {
        // Log the error to an error reporting service
        console.error(error);
    }, [error]);

    return (
        <div className="flex min-h-[70vh] flex-col items-center justify-center bg-muted/10">
            <Container className="text-center">
                <div className="relative inline-block mb-4">
                    <div className="h-24 w-24 rounded-sm bg-red-100 flex items-center justify-center mx-auto">
                        <span className="text-5xl">⚠️</span>
                    </div>
                </div>

                <h1 className="mt-4 text-3xl font-bold text-foreground">
                    Bir Hata Oluştu
                </h1>
                <p className="mx-auto mt-4 max-w-md text-lg text-muted-foreground">
                    Beklenmedik bir sorunla karşılaştık. Lütfen sayfayı yenilemeyi deneyin.
                </p>

                <div className="mt-8 flex flex-col items-center justify-center gap-4 sm:flex-row">
                    <Button onClick={() => reset()} size="lg" className="min-w-[160px] shadow-lg shadow-primary/20">
                        <RefreshCcw className="mr-2 h-4 w-4" />
                        Tekrar Dene
                    </Button>
                    <Button asChild variant="outline" size="lg" className="min-w-[160px]">
                        <Link href="/">
                            <Home className="mr-2 h-4 w-4" />
                            Ana Sayfa
                        </Link>
                    </Button>
                </div>

                {process.env.NODE_ENV === "development" && (
                    <div className="mt-8 overflow-hidden rounded-sm bg-black/5 p-4 text-left max-w-2xl mx-auto">
                        <p className="font-mono text-xs text-red-600 mb-2">Hata Detayı (Geliştirici Modu):</p>
                        <pre className="font-mono text-xs text-muted-foreground whitespace-pre-wrap">
                            {error.message}
                        </pre>
                    </div>
                )}
            </Container>
        </div>
    );
}
