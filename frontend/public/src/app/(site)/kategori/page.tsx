"use client";

import { useQuery } from "@tanstack/react-query";
import { fetchNav } from "@/lib/api";
import { Container } from "@/components/layout";
import { BentoCategoryGrid } from "@/components/catalog";
import { motion } from "framer-motion";
import Image from "next/image";

export default function CategoriesPage() {
    const { data: categories = [], isLoading } = useQuery({
        queryKey: ["nav"],
        queryFn: fetchNav,
    });

    return (
        <div className="min-h-screen bg-white">
            {/* Top red stripe with header */}
            <div className="bg-primary relative overflow-hidden">
                {/* Decorative elements */}
                <div className="absolute top-0 left-0 w-32 h-32 bg-white/10 rounded-sm -translate-x-1/2 -translate-y-1/2" />
                <div className="absolute top-1/2 left-8 w-2 h-16 bg-white/20 -translate-y-1/2 hidden md:block" />
                <div className="absolute bottom-0 right-0 w-48 h-48 bg-black/10 rounded-sm translate-x-1/3 translate-y-1/2" />
                <div className="absolute top-4 right-12 w-6 h-6 border-2 border-white/30 rotate-45 hidden lg:block" />
                <div className="absolute bottom-4 left-1/4 w-4 h-4 bg-white/20 rounded-sm hidden md:block" />

                <Container className="py-8 relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="text-center"
                    >
                        <h1 className="text-2xl lg:text-3xl font-bold text-white">
                            Ürün Kategorileri
                        </h1>
                        <p className="text-white/70 mt-1 text-sm">
                            Endüstriyel mutfak ekipmanları
                        </p>
                    </motion.div>
                </Container>
            </div>

            {/* Grid - white background */}
            <Container className="py-8">
                {isLoading ? (
                    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
                        {[1, 2, 3, 4, 5, 6, 7, 8].map((i) => (
                            <div key={i} className="aspect-square bg-gray-100 animate-pulse" />
                        ))}
                    </div>
                ) : (
                    <BentoCategoryGrid categories={categories} variant="cinematic" />
                )}
            </Container>

            {/* Bottom band with logo - Vertical Line Decoration */}
            <div className="flex items-center justify-center relative">
                {/* Left Red Bar */}
                <div className="flex-1 h-20 bg-primary relative overflow-hidden">
                    {/* Vertical White Line (Inset from Right) */}
                    <div className="absolute top-0 bottom-0 right-6 w-1 bg-white/80 z-10" />

                    {/* Decorations */}
                    <div className="absolute top-1/2 left-4 w-3 h-3 bg-white/20 rounded-sm -translate-y-1/2" />
                    <div className="absolute top-1/2 left-12 w-8 h-1 bg-white/15 -translate-y-1/2 hidden sm:block" />
                    <div className="absolute bottom-2 left-1/3 w-16 h-16 border border-white/10 rounded-sm hidden lg:block" />
                </div>

                {/* Center Logo Area */}
                <div className="bg-white px-8 md:px-20 py-6 flex items-center justify-center z-20 relative min-w-[200px]">
                    <Image
                        src="/assets/footer_logo.webp"
                        alt="Gastrotech"
                        width={200}
                        height={50}
                        className="object-contain"
                    />
                </div>

                {/* Right Red Bar */}
                <div className="flex-1 h-20 bg-primary relative overflow-hidden">
                    {/* Vertical White Line (Inset from Left) */}
                    <div className="absolute top-0 bottom-0 left-6 w-1 bg-white/80 z-10" />

                    {/* Decorations */}
                    <div className="absolute top-1/2 right-4 w-3 h-3 bg-white/20 rounded-sm -translate-y-1/2" />
                    <div className="absolute top-1/2 right-12 w-8 h-1 bg-white/15 -translate-y-1/2 hidden sm:block" />
                    <div className="absolute top-2 right-1/4 w-12 h-12 border border-white/10 rounded-sm hidden lg:block" />
                </div>
            </div>
        </div>
    );
}
