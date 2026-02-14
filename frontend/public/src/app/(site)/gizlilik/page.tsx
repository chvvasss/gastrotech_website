import { Container } from "@/components/layout";

export default function PrivacyPage() {
    return (
        <section className="py-16 lg:py-24">
            <Container>
                <div className="mx-auto max-w-3xl">
                    <h1 className="mb-8 text-3xl font-bold lg:text-4xl text-primary">Gizlilik Politikası</h1>

                    <div className="prose prose-gray max-w-none dark:prose-invert">
                        <p className="lead text-xl text-muted-foreground mb-8">
                            Gastrotech olarak, kişisel verilerinizin güvenliğine ve gizliliğine önem veriyoruz.
                            Bu politika, web sitemizi ziyaret ettiğinizde verilerinizin nasıl toplandığını,
                            işlendiğini ve korunduğunu açıklamaktadır.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">1. Veri Toplama</h2>
                        <p className="mb-4">
                            Hizmetlerimizi kullandığınızda aşağıdaki bilgileri toplayabiliriz:
                        </p>
                        <ul className="mb-4 list-disc pl-6 space-y-2">
                            <li>İletişim bilgileri (ad, e-posta adresi, telefon numarası)</li>
                            <li>Cihaz ve tarayıcı bilgileri (IP adresi, tarayıcı türü)</li>
                            <li>Kullanım verileri ve çerezler</li>
                        </ul>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">2. Verilerin Kullanımı</h2>
                        <p className="mb-4">
                            Topladığımız verileri şu amaçlarla kullanırız:
                        </p>
                        <ul className="mb-4 list-disc pl-6 space-y-2">
                            <li>Size daha iyi bir hizmet sunmak ve site deneyiminizi kişiselleştirmek</li>
                            <li>Taleplerinize ve sorularınıza yanıt vermek</li>
                            <li>Hizmetlerimizle ilgili güncellemeler ve bilgilendirmeler göndermek</li>
                            <li>Yasal yükümlülüklerimizi yerine getirmek</li>
                        </ul>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">3. Veri Güvenliği</h2>
                        <p className="mb-4">
                            Kişisel verilerinizin güvenliği bizim için önceliklidir. Verilerinizi yetkisiz erişime,
                            kayba veya ifşaya karşı korumak için endüstri standardı güvenlik önlemleri uyguluyoruz.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">4. Çerezler</h2>
                        <p className="mb-4">
                            Web sitemizde, kullanıcı deneyimini iyileştirmek ve site trafiğini analiz etmek için
                            çerezler (cookies) kullanmaktayız. Tarayıcı ayarlarınızdan çerez tercihlerini
                            yönetebilirsiniz.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">5. İletişim</h2>
                        <p className="mb-4">
                            Gizlilik politikamızla ilgili herhangi bir sorunuz varsa, lütfen bizimle
                            <span className="font-semibold text-primary"> info@gastrotech.com</span> adresi üzerinden iletişime geçiniz.
                        </p>

                        <p className="mt-8 text-sm text-muted-foreground">
                            Son güncelleme: {new Date().toLocaleDateString('tr-TR')}
                        </p>
                    </div>
                </div>
            </Container>
        </section>
    );
}
