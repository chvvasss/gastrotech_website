"use client";

import { Container } from "@/components/layout";
import { motion } from "framer-motion";
import { Shield, Database, Eye, Cookie, Mail, ChevronRight } from "lucide-react";
import Link from "next/link";

export default function PrivacyPage() {
    return (
        <>
            {/* Hero — Referanslar tarzı kırmızı şerit */}
            <section className="relative overflow-hidden bg-gradient-to-br from-primary via-primary to-primary/90 py-16 lg:py-24">
                {/* Blurred circles */}
                <div className="absolute -right-20 -top-20 h-64 w-64 rounded-sm bg-white/10 blur-[100px]" />
                <div className="absolute -bottom-20 -left-20 h-64 w-64 rounded-sm bg-black/20 blur-[100px]" />

                {/* Geometric shapes */}
                <div className="absolute top-8 left-8 w-20 h-20 border-2 border-white/20 rounded-sm hidden lg:block" />
                <div className="absolute top-12 left-12 w-12 h-12 border border-white/10 rounded-sm hidden lg:block" />
                <div className="absolute bottom-8 right-8 w-24 h-24 border-2 border-white/15 rounded-sm hidden lg:block" />
                <div className="absolute top-1/2 right-16 w-4 h-4 bg-white/20 rotate-45 -translate-y-1/2 hidden md:block" />
                <div className="absolute bottom-16 left-1/4 w-6 h-6 bg-white/10 rounded-sm hidden md:block" />

                {/* Lines */}
                <div className="absolute top-0 left-1/3 w-px h-16 bg-gradient-to-b from-transparent via-white/20 to-transparent hidden lg:block" />
                <div className="absolute bottom-0 right-1/3 w-px h-16 bg-gradient-to-t from-transparent via-white/20 to-transparent hidden lg:block" />
                <div className="absolute top-1/2 left-4 w-12 h-0.5 bg-white/15 -translate-y-1/2 hidden md:block" />

                <Container className="relative text-center z-10">
                    <h1 className="text-3xl font-bold text-white lg:text-5xl">Gizlilik Politikası</h1>
                    <p className="mx-auto mt-4 max-w-2xl text-lg text-white/90">
                        Gastrotech olarak, kişisel verilerinizin güvenliğine ve gizliliğine önem veriyoruz.
                        Bu politika, verilerinizin nasıl toplandığını ve korunduğunu açıklar.
                    </p>
                </Container>
            </section>

            {/* Red accent bar quote */}
            <section className="py-16 bg-background border-b">
                <Container>
                    <div className="max-w-4xl mx-auto relative">
                        <div className="absolute -left-4 top-0 w-1 h-full bg-primary" />
                        <p className="text-xl text-foreground font-medium italic leading-relaxed pl-8">
                            &quot;Kişisel verileriniz, en üst düzey güvenlik önlemleri ile korunmaktadır. Gastrotech
                            olarak verilerinizin gizliliği ve bütünlüğü en büyük önceliğimizdir.&quot;
                        </p>
                    </div>
                </Container>
            </section>

            {/* Veri Toplama & Kullanımı */}
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
                                <Database className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">1. Veri Toplama</h2>
                            <p className="text-muted-foreground leading-relaxed mb-4">
                                Hizmetlerimizi kullandığınızda aşağıdaki bilgileri toplayabiliriz:
                            </p>
                            <ul className="space-y-3 text-muted-foreground">
                                <li className="flex items-start gap-3">
                                    <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                    İletişim bilgileri (ad, e-posta, telefon)
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                    Cihaz ve tarayıcı bilgileri (IP, tarayıcı türü)
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                    Kullanım verileri ve çerezler
                                </li>
                            </ul>
                        </motion.div>

                        <motion.div
                            initial={{ opacity: 0, y: 20 }}
                            whileInView={{ opacity: 1, y: 0 }}
                            viewport={{ once: true }}
                            transition={{ duration: 0.5, delay: 0.1 }}
                            className="relative group rounded-sm border bg-card p-10 shadow-sm transition-all duration-300 hover:shadow-xl hover:border-primary/30"
                        >
                            <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-sm bg-primary/10 text-primary">
                                <Eye className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">2. Verilerin Kullanımı</h2>
                            <p className="text-muted-foreground leading-relaxed mb-4">
                                Topladığımız verileri şu amaçlarla kullanırız:
                            </p>
                            <ul className="space-y-3 text-muted-foreground">
                                <li className="flex items-start gap-3">
                                    <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                    Site deneyiminizi kişiselleştirmek
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                    Taleplerinize ve sorularınıza yanıt vermek
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                    Hizmet güncellemeleri göndermek
                                </li>
                                <li className="flex items-start gap-3">
                                    <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                    Yasal yükümlülükleri yerine getirmek
                                </li>
                            </ul>
                        </motion.div>
                    </div>
                </Container>
            </section>

            {/* Veri Güvenliği — accent band */}
            <section className="bg-primary/5 py-16 border-b relative overflow-hidden">
                <div className="absolute top-0 left-0 w-32 h-32 bg-primary/10 rounded-sm -translate-x-1/2 -translate-y-1/2" />
                <div className="absolute bottom-0 right-0 w-40 h-40 bg-primary/10 rounded-sm translate-x-1/2 translate-y-1/2" />
                <div className="absolute top-1/2 left-8 w-2 h-12 bg-primary/15 -translate-y-1/2 hidden md:block" />
                <div className="absolute top-1/2 right-8 w-2 h-12 bg-primary/15 -translate-y-1/2 hidden md:block" />

                <Container className="relative z-10">
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5 }}
                        className="max-w-3xl mx-auto text-center"
                    >
                        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-sm bg-primary/10 text-primary">
                            <Shield className="h-8 w-8" />
                        </div>
                        <h2 className="text-3xl font-bold mb-6 tracking-tight">3. Veri Güvenliği</h2>
                        <p className="text-lg text-muted-foreground leading-relaxed">
                            Kişisel verilerinizin güvenliği bizim için önceliklidir. Verilerinizi yetkisiz erişime,
                            kayba veya ifşaya karşı korumak için endüstri standardı güvenlik önlemleri uyguluyoruz.
                        </p>
                    </motion.div>
                </Container>
            </section>

            {/* Çerezler & İletişim */}
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
                                <Cookie className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">4. Çerezler</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Web sitemizde, kullanıcı deneyimini iyileştirmek ve site trafiğini analiz etmek için
                                çerezler (cookies) kullanmaktayız. Tarayıcı ayarlarınızdan çerez tercihlerini
                                yönetebilirsiniz.
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
                                <Mail className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">5. İletişim</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Gizlilik politikamızla ilgili herhangi bir sorunuz varsa, lütfen bizimle{" "}
                                <a
                                    href="mailto:info@gastrotech.com.tr"
                                    className="font-semibold text-primary hover:underline underline-offset-2"
                                >
                                    info@gastrotech.com.tr
                                </a>{" "}
                                adresi üzerinden iletişime geçiniz.
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
                                href="/kvkk"
                                className="inline-flex items-center gap-1 text-primary hover:underline underline-offset-2 font-bold text-sm"
                            >
                                KVKK <ChevronRight className="w-4 h-4" />
                            </Link>
                            <Link
                                href="/kullanim-kosullari"
                                className="inline-flex items-center gap-1 text-primary hover:underline underline-offset-2 font-bold text-sm"
                            >
                                Kullanım Koşulları <ChevronRight className="w-4 h-4" />
                            </Link>
                        </div>
                    </div>
                </Container>
            </section>
        </>
    );
}
