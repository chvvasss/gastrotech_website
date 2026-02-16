"use client";

import { Container } from "@/components/layout";
import { motion } from "framer-motion";
import {
    ScrollText,
    Gavel,
    BookOpen,
    AlertTriangle,
    RefreshCw,
    Scale,
    ChevronRight,
} from "lucide-react";
import Link from "next/link";

export default function TermsPage() {
    return (
        <>
            {/* Hero — Referanslar tarzı kırmızı şerit */}
            <section className="relative overflow-hidden bg-gradient-to-br from-primary via-primary to-primary/90 py-16 lg:py-24">
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-sm bg-white/10 blur-[100px]" />
                <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-sm bg-black/20 blur-[100px]" />

                <div className="absolute top-8 left-8 w-20 h-20 border-2 border-white/20 rounded-sm hidden lg:block" />
                <div className="absolute top-12 left-12 w-12 h-12 border border-white/10 rounded-sm hidden lg:block" />
                <div className="absolute bottom-8 right-8 w-24 h-24 border-2 border-white/15 rounded-sm hidden lg:block" />
                <div className="absolute top-1/2 right-16 w-4 h-4 bg-white/20 rotate-45 -translate-y-1/2 hidden md:block" />
                <div className="absolute bottom-16 left-1/4 w-6 h-6 bg-white/10 rounded-sm hidden md:block" />

                <div className="absolute top-0 left-1/3 w-px h-16 bg-gradient-to-b from-transparent via-white/20 to-transparent hidden lg:block" />
                <div className="absolute bottom-0 right-1/3 w-px h-16 bg-gradient-to-t from-transparent via-white/20 to-transparent hidden lg:block" />
                <div className="absolute top-1/2 left-4 w-12 h-0.5 bg-white/15 -translate-y-1/2 hidden md:block" />

                <Container className="relative text-center z-10">
                    <h1 className="text-3xl font-bold text-white lg:text-5xl">Kullanım Koşulları</h1>
                    <p className="mx-auto mt-4 max-w-2xl text-lg text-white/90">
                        Gastrotech web sitesini ziyaret ederek veya kullanarak, aşağıdaki kullanım koşullarını
                        kabul etmiş sayılırsınız.
                    </p>
                </Container>
            </section>

            {/* Red accent bar quote */}
            <section className="py-16 bg-background border-b">
                <Container>
                    <div className="max-w-4xl mx-auto relative">
                        <div className="absolute -left-4 top-0 w-1 h-full bg-primary" />
                        <p className="text-xl text-foreground font-medium italic leading-relaxed pl-8">
                            &quot;Bu web sitesindeki tüm içerikler telif hakları ile korunmaktadır. Kullanıcılar
                            siteyi yalnızca yasal amaçlar için kullanmayı taahhüt eder.&quot;
                        </p>
                    </div>
                </Container>
            </section>

            {/* Genel Hükümler & Kullanım Şartları */}
            <section className="py-16 lg:py-24 bg-background border-b">
                <Container>
                    <div className="grid gap-16 lg:grid-cols-2 max-w-5xl mx-auto">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5 }}
                            className="relative group rounded-sm border bg-card p-10 shadow-sm transition-all duration-300 hover:shadow-xl hover:border-primary/30"
                        >
                            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-sm bg-primary/10 text-primary">
                                <BookOpen className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">1. Genel Hükümler</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Bu web sitesi, Gastrotech Endüstriyel Mutfak Ekipmanları San. ve Tic. A.Ş. tarafından
                                işletilmektedir. Site içeriğindeki tüm materyaller (metinler, görseller, grafikler,
                                logolar vb.) telif hakları yasaları ile korunmaktadır.
                            </p>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className="relative group rounded-sm border bg-card p-10 shadow-sm transition-all duration-300 hover:shadow-xl hover:border-primary/30"
                        >
                            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-sm bg-primary/10 text-primary">
                                <ScrollText className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">2. Kullanım Şartları</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Kullanıcılar, siteyi yalnızca yasal amaçlar için kullanmayı ve üçüncü şahısların
                                haklarına veya sitenin işleyişine zarar verecek herhangi bir faaliyette bulunmamayı
                                taahhüt eder.
                            </p>
                        </motion.div>
                    </div>
                </Container>
            </section>

            {/* Sorumluluk Reddi — accent band */}
            <section className="bg-primary/5 py-16 border-b relative overflow-hidden">
                <div className="absolute top-0 left-0 w-32 h-32 bg-primary/10 rounded-sm -translate-x-1/2 -translate-y-1/2" />
                <div className="absolute bottom-0 right-0 w-40 h-40 bg-primary/10 rounded-sm translate-x-1/2 translate-y-1/2" />
                <div className="absolute top-1/2 left-8 w-2 h-12 bg-primary/15 -translate-y-1/2 hidden md:block" />
                <div className="absolute top-1/2 right-8 w-2 h-12 bg-primary/15 -translate-y-1/2 hidden md:block" />
                <div className="absolute top-4 right-1/4 w-4 h-4 border border-primary/20 rotate-45 hidden lg:block" />

                <Container className="relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5 }}
                        className="max-w-3xl mx-auto text-center"
                    >
                        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-sm bg-primary/10 text-primary">
                            <AlertTriangle className="h-8 w-8" />
                        </div>
                        <h2 className="text-3xl font-bold mb-6 tracking-tight">3. Sorumluluk Reddi</h2>
                        <p className="text-lg text-muted-foreground leading-relaxed">
                            Gastrotech, sitede yer alan bilgilerin doğruluğunu ve güncelliğini sağlamak için azami
                            gayret gösterir. Ancak, içerikte olabilecek hatalar veya eksikliklerden dolayı sorumlu
                            tutulamaz. Site kullanımıyla ilgili riskler tamamen kullanıcıya aittir.
                        </p>
                    </motion.div>
                </Container>
            </section>

            {/* Değişiklik Hakkı & Uygulanacak Hukuk */}
            <section className="py-16 lg:py-24 bg-background border-b">
                <Container>
                    <div className="grid gap-16 lg:grid-cols-2 max-w-5xl mx-auto">
                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5 }}
                            className="relative group rounded-sm border bg-card p-10 shadow-sm transition-all duration-300 hover:shadow-xl hover:border-primary/30"
                        >
                            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-sm bg-primary/10 text-primary">
                                <RefreshCw className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">4. Değişiklik Hakkı</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Gastrotech, bu kullanım koşullarını dilediği zaman önceden bildirmeksizin değiştirme
                                hakkını saklı tutar. Değişiklikler sitede yayınlandığı andan itibaren geçerli olur.
                            </p>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className="relative group rounded-sm border bg-card p-10 shadow-sm transition-all duration-300 hover:shadow-xl hover:border-primary/30"
                        >
                            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-sm bg-primary/10 text-primary">
                                <Scale className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">5. Uygulanacak Hukuk</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Bu kullanım koşullarından doğacak uyuşmazlıklarda Türkiye Cumhuriyeti kanunları
                                uygulanır ve İstanbul mahkemeleri yetkilidir.
                            </p>
                        </motion.div>
                    </div>
                </Container>
            </section>

            {/* Footer navigation */}
            <section className="py-12 bg-muted/20 border-t">
                <Container>
                    <div className="bg-white border rounded-sm p-10 text-center max-w-3xl mx-auto relative overflow-hidden shadow-lg">
                        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/3 h-[2px] bg-primary" />
                        <p className="text-sm text-muted-foreground mb-6">
                            Son güncelleme: {new Date().toLocaleDateString("tr-TR")}
                        </p>
                        <div className="flex justify-center gap-6">
                            <Link
                                href="/gizlilik"
                                className="inline-flex items-center gap-1 text-primary hover:underline underline-offset-2 font-bold text-sm"
                            >
                                Gizlilik <ChevronRight className="w-4 h-4" />
                            </Link>
                            <Link
                                href="/kvkk"
                                className="inline-flex items-center gap-1 text-primary hover:underline underline-offset-2 font-bold text-sm"
                            >
                                KVKK <ChevronRight className="w-4 h-4" />
                            </Link>
                        </div>
                    </div>
                </Container>
            </section>
        </>
    );
}
