"use client";

import { Container } from "@/components/layout";
import { motion } from "framer-motion";

export default function KvkkPage() {
    return (
        <div className="min-h-screen bg-white">
            {/* Header Section */}
            <div className="bg-muted/30 border-b border-border/50">
                <Container className="py-16 md:py-24">
                    <motion.div
                        initial={{ opacity: 0, y: 10 }}
                        animate={{ opacity: 1, y: 0 }}
                        className="max-w-3xl"
                    >
                        <h1 className="text-3xl md:text-4xl font-bold text-foreground tracking-tight mb-4">
                            Kişisel Verilerin Korunması (KVKK)
                        </h1>
                        <p className="text-lg text-muted-foreground leading-relaxed">
                            6698 Sayılı Kişisel Verilerin Korunması Kanunu kapsamında aydınlatma metni ve gizlilik politikamız.
                        </p>
                    </motion.div>
                </Container>
            </div>

            {/* Content Section */}
            <Container className="py-16">
                <div className="max-w-4xl mx-auto space-y-12">
                    {/* Introduction */}
                    <Section title="1. Amaç ve Kapsam">
                        <p>
                            Gastrotech Endüstriyel Mutfak Ekipmanları (&quot;Gastrotech&quot; veya &quot;Şirket&quot;) olarak, müşterilerimizin, potansiyel müşterilerimizin, çalışanlarımızın ve iş ortaklarımızın kişisel verilerinin güvenliğine ve gizliliğine büyük önem vermekteyiz. Bu metin, 6698 sayılı Kişisel Verilerin Korunması Kanunu (&quot;KVKK&quot;) kapsamında, kişisel verilerinizin toplanması, işlenmesi, aktarılması ve imhası süreçleri hakkında sizi bilgilendirmek amacıyla hazırlanmıştır.
                        </p>
                    </Section>

                    <Section title="2. Veri Sorumlusu">
                        <p>
                            KVKK uyarınca, kişisel verileriniz; veri sorumlusu sıfatıyla Gastrotech tarafından aşağıda açıklanan kapsamda işlenebilecektir. Şirketimiz, verilerinizin hukuka uygun olarak işlenmesini ve muhafazasını sağlamak için gerekli tüm teknik ve idari tedbirleri almaktadır.
                        </p>
                    </Section>

                    <Section title="3. Kişisel Verilerin İşlenme Amaçları">
                        <p>Toplanan kişisel verileriniz, aşağıdaki amaçlarla işlenmektedir:</p>
                        <ul className="list-disc pl-5 space-y-2 mt-4 text-muted-foreground">
                            <li>Ürün ve hizmetlerimizden faydalanmanız için gerekli çalışmaların iş birimlerimiz tarafından yapılması,</li>
                            <li>Şirketimiz tarafından sunulan ürün ve hizmetlerin beğeni, kullanım alışkanlıkları ve ihtiyaçlarınıza göre özelleştirilerek size önerilmesi,</li>
                            <li>Müşteri ilişkileri yönetimi süreçlerinin planlanması ve icrası,</li>
                            <li>Şirketimizin ve Şirketimizle iş ilişkisi içerisinde olan ilgili kişilerin hukuki, teknik ve ticari iş güvenliğinin temini,</li>
                            <li>Sözleşmesel yükümlülüklerin yerine getirilmesi.</li>
                        </ul>
                    </Section>

                    <Section title="4. Kişisel Verilerin Toplanma Yöntemi ve Hukuki Sebebi">
                        <p>
                            Kişisel verileriniz, internet sitemiz, mobil uygulamalarımız, sosyal medya mecralarımız, doğrudan sözlü veya yazılı iletişim kanalları aracılığıyla elektronik veya fiziki ortamda toplanmaktadır. Bu süreçte toplanan kişisel verileriniz, KVKK&rsquo;nın 5. ve 6. maddelerinde belirtilen kişisel veri işleme şartları ve amaçları kapsamında ele alınmaktadır.
                        </p>
                    </Section>

                    <Section title="5. Kişisel Verilerin Aktarılması">
                        <p>
                            Kişisel verileriniz; yukarıda belirtilen amaçların gerçekleştirilmesi doğrultusunda, iş ortaklarımıza, tedarikçilerimize, kanunen yetkili kamu kurumlarına ve özel kişilere, KVKK&rsquo;nın 8. ve 9. maddelerinde belirtilen kişisel veri işleme şartları çerçevesinde aktarılabilecektir.
                        </p>
                    </Section>

                    <Section title="6. Veri Sahibinin Hakları">
                        <p>KVKK&rsquo;nın 11. maddesi uyarınca veri sahipleri olarak aşağıdaki haklara sahipsiniz:</p>
                        <ul className="list-disc pl-5 space-y-2 mt-4 text-muted-foreground">
                            <li>Kişisel veri işlenip işlenmediğini öğrenme,</li>
                            <li>Kişisel verileri işlenmişse buna ilişkin bilgi talep etme,</li>
                            <li>Kişisel verilerin işlenme amacını ve bunların amacına uygun kullanılıp kullanılmadığını öğrenme,</li>
                            <li>Yurt içinde veya yurt dışında kişisel verilerin aktarıldığı üçüncü kişileri bilme,</li>
                            <li>Kişisel verilerin eksik veya yanlış işlenmiş olması hâlinde bunların düzeltilmesini isteme,</li>
                            <li>İlgili mevzuatta öngörülen şartlar çerçevesinde kişisel verilerin silinmesini veya yok edilmesini isteme.</li>
                        </ul>
                    </Section>

                    <Section title="7. İletişim">
                        <p>
                            KVKK kapsamındaki haklarınızla ilgili taleplerinizi, yazılı olarak veya kayıtlı elektronik posta (KEP) adresi, güvenli elektronik imza, mobil imza ya da bize daha önce bildirdiğiniz ve sistemimizde kayıtlı bulunan elektronik posta adresini kullanmak suretiyle <a href="mailto:info@gastrotech.com.tr" className="text-primary hover:underline">info@gastrotech.com.tr</a> adresine iletebilirsiniz.
                        </p>
                    </Section>

                    <div className="mt-12 p-6 bg-muted/20 rounded-sm border border-border text-sm text-muted-foreground">
                        <p>Son Güncelleme: {new Date().toLocaleDateString('tr-TR')}</p>
                    </div>
                </div>
            </Container>
        </div>
    );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
    return (
        <section className="space-y-4">
            <h2 className="text-2xl font-semibold text-foreground tracking-tight">{title}</h2>
            <div className="text-base leading-7 text-muted-foreground">
                {children}
            </div>
        </section>
    );
}
