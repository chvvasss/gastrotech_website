import Link from "next/link";
import { Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import {
  Wrench,
  Package,
  Shield,
  Settings,
  GraduationCap,
  ClipboardCheck,
  Truck,
} from "lucide-react";

const SERVICES = [
  {
    icon: Wrench,
    title: "Kurulum & Devreye Alma",
    description: "Yeni ekipmanlarınızın profesyonel ekiplerce kurulumu ve kullanıma hazır hale getirilmesi.",
  },
  {
    icon: GraduationCap,
    title: "Kullanım & Eğitim",
    description: "Ekipmanların doğru ve verimli kullanımı için personelinize yönelik detaylı bilgilendirme.",
  },
  {
    icon: Settings,
    title: "Periyodik Bakım Planı",
    description: "Yatırımınızın ömrünü uzatmak için düzenli bakım süreçlerinin planlanması ve takibi.",
  },
  {
    icon: ClipboardCheck,
    title: "Teknik Destek & Arıza",
    description: "Olası teknik sorunlarda hızlı arıza tespiti ve uzman yönlendirmesi.",
  },
  {
    icon: Package,
    title: "Yedek Parça Temini",
    description: "Gerekli yedek parçaların orijinal ve hızlı şekilde tedarik edilmesi süreci.",
  },
  {
    icon: Shield,
    title: "Garanti Süreci Takibi",
    description: "Ürünlerin garanti kapsamındaki süreçlerinin titizlikle izlenmesi ve yönetilmesi.",
  },
];

const FAQ = [
  {
    question: "Hangi alanlarda hizmet veriyorsunuz?",
    answer: "Endüstriyel mutfak ekipmanları başta olmak üzere; bar & kahve ekipmanları, buz makineleri, su arıtma çözümleri ve işletmelerin ihtiyaç duyduğu ekipman gruplarında ürün tedariği ve proje bazlı çözümler sunuyoruz.",
  },
  {
    question: "Projelendirme ve danışmanlık yapıyor musunuz?",
    answer: "Evet. İşletmenizin konsepti, kapasitesi, operasyon akışı ve bütçesine göre doğru ekipman seçimi ve yerleşim planı konusunda danışmanlık sağlıyoruz.",
  },
  {
    question: "Keşif / yerinde inceleme hizmetiniz var mı?",
    answer: "Projenin ihtiyacına göre yerinde keşif veya uzaktan (plan, ölçü, fotoğraf/video) değerlendirme ile ihtiyaç analizi yapılır.",
  },
  {
    question: "Anahtar teslim proje yapıyor musunuz?",
    answer: "Evet. Proje kapsamına göre ekipman seçimi, tekliflendirme, tedarik, kurulum/devreye alma ve kullanım bilgilendirmesi süreçleri tek çatı altında yönetilebilir.",
  },
  {
    question: "Teklif süreci nasıl ilerliyor?",
    answer: "İhtiyaçlar belirlendikten sonra marka/model alternatifleriyle birlikte teklif hazırlanır. Proje bazlı çalışmalarda opsiyonlu tekliflendirme ve revizyon süreçleri yürütülür.",
  },
  {
    question: "Ürün tedarik ve teslimat süreci nasıl işliyor?",
    answer: "Stok durumuna ve ürün grubuna göre teslimat planı oluşturulur. Proje/kurulum planına uygun şekilde sevkiyat ve teslimat organize edilir.",
  },
  {
    question: "Kurulum ve devreye alma hizmeti veriyor musunuz?",
    answer: "Evet. Kurulum ve devreye alma süreçleri, lokasyona ve ekipmana göre planlanır ve ilgili ekip/çözüm ortağı üzerinden koordine edilir.",
  },
  {
    question: "Bar & Kahve tarafında hangi çözümleri sunuyorsunuz?",
    answer: "Espresso makineleri, öğütücüler, bar ekipmanları, buz makineleri, su arıtma ve operasyonu destekleyen tamamlayıcı ürün gruplarında ürün tedariği ve proje desteği sağlıyoruz.",
  },
  {
    question: "Eğitim / kullanım bilgilendirmesi sağlıyor musunuz?",
    answer: "Evet. Kurulum sonrası temel kullanım, doğru işletim ve günlük bakım rutini hakkında bilgilendirme yapılır (ekipman ve proje kapsamına göre değişebilir).",
  },
  {
    question: "Periyodik bakım planlaması yapıyor musunuz?",
    answer: "Evet. Ekipmanın kullanım yoğunluğuna göre bakım periyotları önerilir; bakım süreçleri için yönlendirme ve koordinasyon sağlanır.",
  },
  {
    question: "Yedek parça temini yapıyor musunuz?",
    answer: "Evet. Marka/model ve mümkünse seri numarası ile talep oluşturmanız halinde, uygunluk kontrolü yapılarak yedek parça tedarik süreci yönetilir.",
  },
  {
    question: "Garanti süreci nasıl işliyor?",
    answer: "Garanti kapsamı marka/ürün ve kullanım koşullarına göre değişir. Talebiniz alındıktan sonra gerekli kontroller yapılır ve süreç sizinle paylaşilir.",
  },
  {
    question: "Satış sonrası destek nasıl sağlanıyor?",
    answer: "Teslimat sonrası destek; kurulum, kullanım bilgilendirmesi, bakım/arıza yönlendirmesi ve yedek parça süreçleriyle devam eder. Taleplerinizi iletişim kanallarımız üzerinden iletebilirsiniz.",
  },
  {
    question: "Türkiye geneline hizmet veriyor musunuz?",
    answer: "Evet. Türkiye genelinde birçok ilde çözüm ortağı bağlantılarımızla proje ve satış sonrası süreçlerde yönlendirme/koordinasyon sağlıyoruz.",
  },
  {
    question: "Hızlı destek için hangi bilgileri paylaşmalıyım?",
    answer: "Ürün marka/model, talebin türü (teklif/kurulum/bakım/arıza/yedek parça), lokasyon (il/ilçe), varsa seri numarası ve mümkünse fotoğraf/video paylaşmanız süreci hızlandırır.",
  },
];

export default function ServicePage() {
  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-br from-primary to-rose-700 py-16 lg:py-24 relative overflow-hidden">
        <div className="absolute inset-0 opacity-10" style={{ backgroundImage: 'radial-gradient(circle, white 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
        <Container className="text-center relative">
          <h1 className="text-4xl font-bold text-white lg:text-6xl tracking-tight">Satış Sonrası Hizmetler</h1>
          <p className="mx-auto mt-6 max-w-2xl text-lg text-white/90 leading-relaxed font-light">
            Yatırımınızın uzun ömürlü ve verimli çalışması için satış sonrası süreci titizlikle yönetiyoruz.
            Kurulum, bakım, arıza tespiti ve orijinal yedek parça desteği.
          </p>
        </Container>
      </section>

      {/* Services Grid */}
      <section className="py-20 border-b">
        <Container>
          <div className="mb-12 text-center max-w-3xl mx-auto">
            <h2 className="text-2xl font-bold lg:text-3xl mb-4 tracking-tight">Hizmet Alanlarımız</h2>
            <p className="text-muted-foreground">İşletmenizin sürekliliği için kapsamlı destek paketleri.</p>
          </div>
          <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
            {SERVICES.map((service) => (
              <div
                key={service.title}
                className="group rounded-sm border bg-card p-8 transition-all hover:shadow-lg hover:border-primary/50"
              >
                <div className="mb-6 flex h-12 w-12 items-center justify-center rounded-sm bg-primary/10 text-primary transition-colors group-hover:bg-primary group-hover:text-white">
                  <service.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-3 text-lg font-bold">{service.title}</h3>
                <p className="text-muted-foreground leading-relaxed text-sm">
                  {service.description}
                </p>
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* Service Coordination Model */}
      <section className="bg-muted/30 py-20 border-b">
        <Container>
          <div className="grid gap-12 lg:grid-cols-2 items-center max-w-6xl mx-auto">
            <div className="space-y-6">
              <h2 className="text-3xl font-bold tracking-tight">Servis Noktalarımız</h2>
              <div className="space-y-4 text-lg text-muted-foreground leading-relaxed">
                <p>
                  Gastrotech olarak Türkiye genelinde geniş bir çözüm ortağı ağıyla servis süreçlerini koordine ediyoruz.
                </p>
                <p>
                  Kurulum, bakım, arıza tespiti ve yedek parça süreçlerinde, bulunduğunuz bölgeye en uygun yetkili/uzman
                  servis noktalarına yönlendirme yapıyor ve sürecin takibini sağlıyoruz.
                </p>
                <p>
                  Türkiye’nin birçok ilinde yerel bağlantılarımız sayesinde hızlı aksiyon alarak, operasyonlarınızın kesintisiz
                  devam etmesine destek oluyoruz.
                </p>
              </div>
              <div className="pt-4">
                <Button size="lg" asChild className="rounded-sm px-8 shadow-md">
                  <Link href="/iletisim">Servis Talebi Oluştur</Link>
                </Button>
              </div>
            </div>
            <div className="relative aspect-video rounded-sm overflow-hidden shadow-2xl bg-white border border-border/50 flex items-center justify-center">
              <div className="absolute inset-0 bg-grid-black/[0.02]" />
              <Truck className="h-24 w-24 text-primary opacity-20 relative z-10" />
              <div className="absolute inset-x-0 bottom-0 p-8 bg-gradient-to-t from-black/80 to-transparent z-20">
                <p className="text-white font-bold text-lg">81 İlde Mobil Servis Ağı</p>
                <p className="text-white/80 text-sm">Uzman çözüm ortaklarımızla her noktadayız.</p>
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* FAQ Section */}
      <section id="sss" className="py-24">
        <Container>
          <div className="mb-16 text-center">
            <h2 className="text-3xl font-bold lg:text-4xl mb-4 tracking-tight">Sıkça Sorulan Sorular</h2>
            <p className="text-lg text-muted-foreground">Hizmetlerimiz ve süreçlerimiz hakkında merak edilenler</p>
          </div>
          <div className="mx-auto max-w-4xl space-y-4">
            {FAQ.map((item, index) => (
              <div key={index} className="rounded-sm border bg-card p-6 transition-all hover:border-primary/40 hover:bg-muted/5">
                <h3 className="flex items-start gap-4 text-base font-bold">
                  <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded-sm bg-primary/10 text-xs font-bold text-primary">
                    {index + 1}
                  </span>
                  {item.question}
                </h3>
                <p className="mt-3 pl-10 text-muted-foreground leading-relaxed text-sm">
                  {item.answer}
                </p>
              </div>
            ))}
          </div>
          <div className="mt-16 text-center bg-muted/20 rounded-sm p-10 max-w-3xl mx-auto border border-border/50">
            <h3 className="text-xl font-bold mb-4">Başka bir sorunuz mu var?</h3>
            <p className="text-muted-foreground mb-8">
              Detaylı bilgi ve destek için İletişim sayfamız üzerinden bize ulaşabilirsiniz.
            </p>
            <Button size="lg" variant="outline" asChild className="rounded-sm px-10">
              <Link href="/iletisim">Bize Ulaşın</Link>
            </Button>
          </div>
        </Container>
      </section>
    </>
  );
}
