import { Container } from "@/components/layout";

export default function TermsPage() {
    return (
        <section className="py-16 lg:py-24">
            <Container>
                <div className="mx-auto max-w-3xl">
                    <h1 className="mb-8 text-3xl font-bold lg:text-4xl text-primary">Kullanım Koşulları</h1>

                    <div className="prose prose-gray max-w-none dark:prose-invert">
                        <p className="lead text-xl text-muted-foreground mb-8">
                            Gastrotech web sitesini ziyaret ederek veya kullanarak, aşağıdaki kullanım koşullarını
                            kabul etmiş sayılırsınız. Lütfen siteyi kullanmadan önce bu koşulları dikkatlice okuyunuz.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">1. Genel Hükümler</h2>
                        <p className="mb-4">
                            Bu web sitesi, Gastrotech Endüstriyel Mutfak Ekipmanları San. ve Tic. A.Ş. tarafından işletilmektedir.
                            Site içeriğindeki tüm materyaller (metinler, görseller, grafikler, logolar vb.) telif hakları
                            yasaları ile korunmaktadır.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">2. Kullanım Şartları</h2>
                        <p className="mb-4">
                            Kullanıcılar, siteyi yalnızca yasal amaçlar için kullanmayı ve üçüncü şahısların haklarına,
                            veya sitenin işleyişine zarar verecek herhangi bir faaliyette bulunmamayı taahhüt eder.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">3. Sorumluluk Reddi</h2>
                        <p className="mb-4">
                            Gastrotech, sitede yer alan bilgilerin doğruluğunu ve güncelliğini sağlamak için azami gayret
                            gösterir. Ancak, içerikte olabilecek hatalar veya eksikliklerden dolayı sorumlu tutulamaz.
                            Site kullanımıyla ilgili riskler tamamen kullanıcıya aittir.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">4. Değişiklik Hakkı</h2>
                        <p className="mb-4">
                            Gastrotech, bu kullanım koşullarını dilediği zaman önceden bildirmeksizin değiştirme hakkını
                            saklı tutar. Değişiklikler sitede yayınlandığı andan itibaren geçerli olur.
                        </p>

                        <h2 className="mb-4 mt-8 text-2xl font-semibold">5. Uygulanacak Hukuk</h2>
                        <p className="mb-4">
                            Bu kullanım koşullarından doğacak uyuşmazlıklarda Türkiye Cumhuriyeti kanunları uygulanır ve
                            İstanbul mahkemeleri yetkilidir.
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
