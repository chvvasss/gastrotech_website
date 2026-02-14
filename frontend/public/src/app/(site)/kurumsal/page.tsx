import Link from "next/link";
import { Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Award, Globe, Target, Zap, Building2 } from "lucide-react";

const VALUES = [
  {
    icon: Target,
    title: "Vizyonumuz",
    description: "Sektörde yenilikçi çözümler, ileri teknoloji donanımlar ve müşteri odaklı yaklaşımlarla Türkiye’de ve uluslararası alanda güvenilir referans olmaktır. Her işletmenin farklı ihtiyaçları olduğunu biliyor ve “ortak akıl” ile özelleştirilmiş projeler geliştiriyoruz.",
  },
  {
    icon: Zap,
    title: "Misyonumuz",
    description: "İşletmenizin mutfak ve bar operasyonlarını kusursuz hâle getirmek; işleyişi ve akışı kolaylaştırmak, zaman ve emeği en verimli şekilde kullanmanızı sağlamak. “Profesyonellerin Tercihi”nden önce, sektörden gelen profesyoneller olarak sektör profesyonellerinin tercihi olmak.",
  },
];

export default function CorporatePage() {
  return (
    <>
      {/* Hero */}
      <section className="relative bg-gradient-to-br from-gray-50 to-gray-100 py-12 lg:py-20 overflow-hidden border-b">
        <div className="absolute inset-0 bg-[radial-gradient(#000000_1px,transparent_1px)] [background-size:16px_16px] opacity-[0.03] pointer-events-none" />

        {/* Decorative shapes */}
        <div className="absolute top-0 right-0 w-64 h-64 bg-primary/5 rounded-sm translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 left-0 w-48 h-48 bg-primary/5 rounded-sm -translate-x-1/2 translate-y-1/2" />
        <div className="absolute top-20 right-20 w-4 h-4 bg-primary/20 rounded-sm hidden lg:block" />
        <div className="absolute bottom-20 left-1/3 w-6 h-6 border-2 border-primary/20 rotate-45 hidden lg:block" />
        <Container className="relative">
          <div className="grid items-center gap-12 lg:grid-cols-2 max-w-6xl mx-auto">
            <div>
              <div className="inline-flex items-center gap-2 px-3 py-1 rounded-sm bg-primary/10 text-primary font-bold text-sm mb-6 border border-primary/20">
                <Building2 className="h-4 w-4" />
                Kurumsal
              </div>
              <h1 className="text-3xl font-bold lg:text-5xl leading-tight tracking-tight text-foreground">
                GASTROTECH
                <span className="block text-primary">Profesyonelliğin Adresi</span>
              </h1>
              <div className="mt-8 space-y-6 text-lg text-muted-foreground leading-relaxed font-light">
                <p>
                  Grubumuza bağlı 7 şirketin son halkası olan Gastrotech, Ankara’nın köklü firmalarından
                  Mutaş Grup ve Metimsan/Süperçelik firmalarının iştirakleri ile 2012 yılında İstanbul’da
                  faaliyetine başlamıştır.
                </p>
                <p>
                  Endüstriyel Mutfak Ekipmanları sektöründeki 42 yıllık tecrübenin
                  harmanlandığı şirketler grubumuz, sektörün en güvenilir çözüm ortaklarından biridir.
                </p>
              </div>
              <div className="mt-10 flex gap-4">
                <Button asChild size="lg" className="rounded-sm px-8 shadow-lg shadow-primary/20">
                  <Link href="/referanslar">Referanslarımız</Link>
                </Button>
                <Button asChild variant="outline" size="lg" className="rounded-sm px-8 border-input bg-background hover:bg-accent hover:text-accent-foreground">
                  <Link href="/iletisim">İletişim</Link>
                </Button>
              </div>
            </div>
            <div className="relative aspect-square lg:aspect-[4/5] overflow-hidden rounded-sm group shadow-2xl border border-border/50">
              <div className="absolute inset-0 bg-primary/10 group-hover:bg-primary/5 transition-colors duration-500" />
              <div className="flex h-full w-full items-center justify-center text-muted-foreground bg-muted font-medium">
                Fabrika & Üretim Görseli
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* Detailed Content */}
      <section className="py-20 bg-background overflow-hidden border-b">
        <Container>
          <div className="grid gap-16 lg:grid-cols-2 max-w-6xl mx-auto items-center">
            <div className="relative">
              <div className="absolute -left-4 top-0 w-1 h-full bg-primary" />
              <p className="text-xl text-foreground font-medium italic leading-relaxed pl-8">
                &quot;Endüstriyel mutfak sektöründe 2 jenerasyonun kümülatif 42 yıllık know-how’ı, toplam 25.000
                m² kapalı alan ve 50.000 m² açık alan içerisinde bulunan üretim tesisimiz, 250’nin üzerindeki
                çalışanımız ile sürdürülebilir çözüm ortaklıkları kuruyoruz.&quot;
              </p>
            </div>
            <div className="space-y-6 text-muted-foreground text-lg leading-relaxed">
              <p>
                Gastrotech olarak mutfak projelerinin yanı sıra, işletmelerin Bar & Kahve operasyonlarına da
                uçtan uca çözümler sunuyoruz. Profesyonel ekipmanlar, doğru ürün seçimi, projelendirme,
                kurulum ve satış sonrası destek süreçlerini tek bir çatı altında yönetiyoruz.
              </p>
              <p>
                Kafe, otel, restoran ve zincir işletmelerin ihtiyaçlarına uygun, performans
                ve verimlilik odaklı çözümler geliştirerek işletmelerin içecek operasyonlarını güçlendirmeyi
                hedefliyoruz.
              </p>
            </div>
          </div>
        </Container>
      </section>

      {/* Stats */}
      <section className="bg-primary/5 py-16 border-b relative overflow-hidden">
        {/* Decorative elements */}
        <div className="absolute top-0 left-0 w-32 h-32 bg-primary/10 rounded-sm -translate-x-1/2 -translate-y-1/2" />
        <div className="absolute bottom-0 right-0 w-40 h-40 bg-primary/10 rounded-sm translate-x-1/2 translate-y-1/2" />
        <div className="absolute top-1/2 left-8 w-2 h-12 bg-primary/15 -translate-y-1/2 hidden md:block" />
        <div className="absolute top-1/2 right-8 w-2 h-12 bg-primary/15 -translate-y-1/2 hidden md:block" />
        <div className="absolute top-4 right-1/4 w-4 h-4 border border-primary/20 rotate-45 hidden lg:block" />

        <Container className="relative z-10">
          <div className="grid gap-12 text-center sm:grid-cols-2 lg:grid-cols-4">
            <div className="space-y-2">
              <p className="text-5xl font-bold tracking-tighter text-primary">42</p>
              <p className="text-muted-foreground font-medium uppercase tracking-widest text-sm">Yıllık Tecrübe</p>
            </div>
            <div className="space-y-2">
              <p className="text-5xl font-bold tracking-tighter text-primary">250+</p>
              <p className="text-muted-foreground font-medium uppercase tracking-widest text-sm">Çalışan</p>
            </div>
            <div className="space-y-2">
              <p className="text-5xl font-bold tracking-tighter text-primary">25K</p>
              <p className="text-muted-foreground font-medium uppercase tracking-widest text-sm">m² Kapalı Alan</p>
            </div>
            <div className="space-y-2">
              <p className="text-5xl font-bold tracking-tighter text-primary">81</p>
              <p className="text-muted-foreground font-medium uppercase tracking-widest text-sm">İlde Satış Ağı</p>
            </div>
          </div>
        </Container>
      </section>

      {/* Vision & Mission */}
      <section className="py-24 lg:py-32 bg-background">
        <Container>
          <div className="grid gap-10 lg:grid-cols-2 max-w-5xl mx-auto">
            {VALUES.map((value) => (
              <div
                key={value.title}
                className="relative group rounded-sm border bg-card p-10 shadow-sm transition-all duration-300 hover:shadow-xl hover:-translate-y-1 hover:border-primary/30"
              >
                <div className="mb-6 flex h-14 w-14 items-center justify-center rounded-sm bg-primary/10 text-primary">
                  <value.icon className="h-6 w-6" />
                </div>
                <h3 className="mb-4 text-2xl font-bold tracking-tight">{value.title}</h3>
                <p className="text-muted-foreground leading-relaxed text-lg">
                  {value.description}
                </p>
              </div>
            ))}
          </div>
        </Container>
      </section>

      {/* Global Reach */}
      <section className="py-20 bg-muted/20 border-t">
        <Container>
          <div className="bg-white border rounded-sm p-12 lg:p-20 text-center max-w-5xl mx-auto relative overflow-hidden shadow-lg">
            <div className="absolute top-0 left-1/2 -translate-x-1/2 w-1/3 h-[2px] bg-primary" />
            <Globe className="h-16 w-16 text-primary mx-auto mb-8 opacity-20" />
            <h2 className="text-3xl font-bold mb-6">Uluslararası Faaliyet</h2>
            <p className="text-xl text-muted-foreground max-w-2xl mx-auto leading-relaxed">
              Şirket merkezimiz ve fabrikalarımız Ankara’da olup, ayrıca Ukrayna’da da faaliyet göstererek
              küresel pazarda gücümüzü artırmaya devam ediyoruz.
            </p>
          </div>
        </Container>
      </section>

      {/* Certifications */}
      <section className="py-16 lg:py-24 border-t">
        <Container>
          <div className="mb-12 text-center">
            <h2 className="text-2xl font-bold lg:text-3xl">Sertifikalar & Belgeler</h2>
            <p className="mt-2 text-muted-foreground">Uluslararası kalite standartlarına uygunluk</p>
          </div>
          <div className="grid gap-6 sm:grid-cols-2 lg:grid-cols-4 max-w-4xl mx-auto">
            {["ISO 9001", "CE", "TSE", "HACCP"].map((cert) => (
              <div
                key={cert}
                className="flex flex-col items-center rounded-sm border bg-card p-8 text-center transition-all hover:border-primary/50 hover:shadow-md"
              >
                <Award className="mb-4 h-10 w-10 text-primary" />
                <p className="font-bold text-lg">{cert}</p>
              </div>
            ))}
          </div>
        </Container>
      </section>
    </>
  );
}
