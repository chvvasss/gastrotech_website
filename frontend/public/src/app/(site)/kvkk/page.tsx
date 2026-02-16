"use client";

import { Container } from "@/components/layout";
import { motion } from "framer-motion";
import {
    Scale,
    FileText,
    UserCheck,
    Target,
    Globe,
    Send,
    ShieldCheck,
    ChevronRight,
} from "lucide-react";
import Link from "next/link";

export default function KvkkPage() {
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
                    <h1 className="text-3xl font-bold text-white lg:text-5xl">
                        Kişisel Verilerin Korunması
                    </h1>
                    <p className="mx-auto mt-4 max-w-2xl text-lg text-white/90">
                        6698 Sayılı Kişisel Verilerin Korunması Kanunu kapsamında aydınlatma metni ve gizlilik
                        politikamız.
                    </p>
                </Container>
            </section>

            {/* Red accent bar quote */}
            <section className="py-16 bg-background border-b">
                <Container>
                    <div className="max-w-4xl mx-auto relative">
                        <div className="absolute -left-4 top-0 w-1 h-full bg-primary" />
                        <p className="text-xl text-foreground font-medium italic leading-relaxed pl-8">
                            &quot;6698 sayılı KVKK uyarınca, kişisel verileriniz veri sorumlusu sıfatıyla Gastrotech
                            tarafından hukuka uygun olarak işlenmekte ve muhafaza edilmektedir.&quot;
                        </p>
                    </div>
                </Container>
            </section>

            {/* Amaç-Kapsam & Veri Sorumlusu */}
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
                                <Target className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">1. Amaç ve Kapsam</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Gastrotech Endüstriyel Mutfak Ekipmanları olarak, müşterilerimizin, potansiyel
                                müşterilerimizin, çalışanlarımızın ve iş ortaklarımızın kişisel verilerinin güvenliğine
                                büyük önem vermekteyiz. Bu metin, KVKK kapsamında kişisel verilerinizin toplanması,
                                işlenmesi, aktarılması ve imhası süreçleri hakkında sizi bilgilendirmek amacıyla
                                hazırlanmıştır.
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
                                <UserCheck className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">2. Veri Sorumlusu</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                KVKK uyarınca, kişisel verileriniz veri sorumlusu sıfatıyla Gastrotech tarafından
                                işlenebilecektir. Şirketimiz, verilerinizin hukuka uygun olarak işlenmesini ve
                                muhafazasını sağlamak için gerekli tüm teknik ve idari tedbirleri almaktadır.
                            </p>
                        </motion.div>
                    </div>
                </Container>
            </section>

            {/* İşlenme Amaçları — accent band */}
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
                        className="max-w-3xl mx-auto"
                    >
                        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-sm bg-primary/10 text-primary">
                            <FileText className="h-8 w-8" />
                        </div>
                        <h2 className="text-3xl font-bold mb-6 tracking-tight text-center">
                            3. Kişisel Verilerin İşlenme Amaçları
                        </h2>
                        <ul className="space-y-4 text-lg text-muted-foreground">
                            <li className="flex items-start gap-3">
                                <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                Ürün ve hizmetlerimizden faydalanmanız için gerekli çalışmaların yapılması
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                Hizmetlerin ihtiyaçlarınıza göre özelleştirilerek size önerilmesi
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                Müşteri ilişkileri yönetimi süreçlerinin planlanması ve icrası
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                Hukuki, teknik ve ticari iş güvenliğinin temini
                            </li>
                            <li className="flex items-start gap-3">
                                <span className="mt-2 w-2 h-2 rounded-sm bg-primary/60 shrink-0" />
                                Sözleşmesel yükümlülüklerin yerine getirilmesi
                            </li>
                        </ul>
                    </motion.div>
                </Container>
            </section>

            {/* Toplanma & Aktarma */}
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
                                <Globe className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">4. Toplanma Yöntemi</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Kişisel verileriniz, internet sitemiz, mobil uygulamalarımız, sosyal medya mecralarımız,
                                doğrudan sözlü veya yazılı iletişim kanalları aracılığıyla elektronik veya fiziki
                                ortamda toplanmaktadır. KVKK&apos;nın 5. ve 6. maddelerinde belirtilen şartlar ve
                                amaçlar kapsamında ele alınmaktadır.
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
                                <Send className="h-6 w-6" />
                            </div>
                            <h2 className="mb-4 text-2xl font-bold tracking-tight">5. Verilerin Aktarılması</h2>
                            <p className="text-muted-foreground leading-relaxed">
                                Kişisel verileriniz; belirtilen amaçlar doğrultusunda, iş ortaklarımıza,
                                tedarikçilerimize, kanunen yetkili kamu kurumlarına ve özel kişilere, KVKK&apos;nın 8.
                                ve 9. maddelerinde belirtilen şartlar çerçevesinde aktarılabilecektir.
                            </p>
                        </motion.div>
                    </div>
                </Container>
            </section>

            {/* Veri Sahibinin Hakları — dark panel */}
            <section className="py-16 lg:py-24 bg-background border-b">
                <Container>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5 }}
                        className="max-w-4xl mx-auto"
                    >
                        <div className="relative rounded-sm overflow-hidden shadow-2xl border border-border/50">
                            <div className="absolute inset-0 bg-gradient-to-br from-zinc-900 via-zinc-800 to-zinc-900" />
                            <div
                                className="absolute inset-0 opacity-[0.04]"
                                style={{
                                    backgroundImage: "radial-gradient(circle, white 1px, transparent 1px)",
                                    backgroundSize: "20px 20px",
                                }}
                            />
                            <div className="absolute bottom-0 left-0 right-0 h-1 bg-primary" />

                            <div className="relative z-10 p-10 lg:p-14">
                                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-sm bg-white/10 text-white">
                                    <ShieldCheck className="h-7 w-7" />
                                </div>
                                <h2 className="text-2xl font-bold text-white mb-6 tracking-tight">
                                    6. Veri Sahibinin Hakları
                                </h2>
                                <p className="text-white/60 mb-6">
                                    KVKK&apos;nın 11. maddesi uyarınca aşağıdaki haklara sahipsiniz:
                                </p>
                                <ul className="grid md:grid-cols-2 gap-4 text-white/70">
                                    <li className="flex items-start gap-3">
                                        <span className="mt-2 w-2 h-2 rounded-sm bg-primary shrink-0" />
                                        Kişisel veri işlenip işlenmediğini öğrenme
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="mt-2 w-2 h-2 rounded-sm bg-primary shrink-0" />
                                        İşlenmiş verilere ilişkin bilgi talep etme
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="mt-2 w-2 h-2 rounded-sm bg-primary shrink-0" />
                                        İşlenme amacını ve uygun kullanımını öğrenme
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="mt-2 w-2 h-2 rounded-sm bg-primary shrink-0" />
                                        Aktarıldığı üçüncü kişileri bilme
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="mt-2 w-2 h-2 rounded-sm bg-primary shrink-0" />
                                        Eksik veya yanlış verilerin düzeltilmesini isteme
                                    </li>
                                    <li className="flex items-start gap-3">
                                        <span className="mt-2 w-2 h-2 rounded-sm bg-primary shrink-0" />
                                        Verilerin silinmesini veya yok edilmesini isteme
                                    </li>
                                </ul>
                            </div>
                        </div>
                    </motion.div>
                </Container>
            </section>

            {/* İletişim */}
            <section className="py-16 bg-background border-b">
                <Container>
                    <motion.div
                        initial={{ opacity: 0, y: 20 }}
                        whileInView={{ opacity: 1, y: 0 }}
                        viewport={{ once: true }}
                        transition={{ duration: 0.5 }}
                        className="max-w-3xl mx-auto text-center"
                    >
                        <div className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-sm bg-primary/10 text-primary">
                            <Scale className="h-8 w-8" />
                        </div>
                        <h2 className="text-3xl font-bold mb-4 tracking-tight">7. İletişim</h2>
                        <p className="text-lg text-muted-foreground leading-relaxed">
                            KVKK kapsamındaki haklarınızla ilgili taleplerinizi{" "}
                            <a
                                href="mailto:info@gastrotech.com.tr"
                                className="font-semibold text-primary hover:underline underline-offset-2"
                            >
                                info@gastrotech.com.tr
                            </a>{" "}
                            adresine iletebilirsiniz.
                        </p>
                    </motion.div>
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
