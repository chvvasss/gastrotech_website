"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { Container } from "@/components/layout";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { useCart } from "@/hooks/use-cart";
import { useToast } from "@/hooks/use-toast";
import { createInquiry, InquiryCreateSchema, InquiryCreate, ApiError } from "@/lib/api";
import { Mail, Phone, MapPin, Clock, Loader2, Send, Navigation, ExternalLink } from "lucide-react";
import Link from "next/link";
import Image from "next/image";
// cn removed as unused

// Extend schema for client-side validation
const FormSchema = InquiryCreateSchema.extend({
  consent: z.literal(true, {
    errorMap: () => ({ message: "KVKK metnini onaylamanız gerekmektedir." }),
  }),
});

type FormData = z.infer<typeof FormSchema>;

export default function ContactPage() {
  const router = useRouter();
  const { cart, clear } = useCart();
  const { toast } = useToast();
  const [isSubmitting, setIsSubmitting] = useState(false);

  const hasCartItems = cart && cart.items.length > 0;

  const {
    register,
    handleSubmit,
    formState: { errors },

  } = useForm<FormData>({
    resolver: zodResolver(FormSchema),
    defaultValues: {
      full_name: "",
      email: "",
      phone: "",
      company: "",
      message: "",
      // @ts-expect-error -- Default value false vs schema true mismatch
      consent: false,
    },
  });

  // consent watch removed as unused

  const onSubmit = async (data: FormData) => {
    setIsSubmitting(true);

    try {
      // Exclude consent from API data
      // eslint-disable-next-line @typescript-eslint/no-unused-vars
      const { consent: _consumed, ...apiDataRaw } = data;

      // If cart has items, include them
      const inquiryData: InquiryCreate = {
        ...apiDataRaw,
        items: hasCartItems
          ? cart.items.map((item) => ({
            model_code: item.variant.model_code,
            qty: item.quantity,
          }))
          : undefined,
      };

      console.log("[Inquiry] Form data:", data);
      console.log("[Inquiry] Cart items:", hasCartItems ? cart.items : "none");
      console.log("[Inquiry] Final inquiry data:", inquiryData);

      const result = await createInquiry(inquiryData);

      console.log("[Inquiry] Success! Result:", result);

      // Clear cart after successful inquiry
      if (hasCartItems) {
        console.log("[Inquiry] Clearing cart...");
        clear();
      }

      // Redirect to success page
      console.log("[Inquiry] Redirecting to success page...");
      router.push(`/teklif-basarili?id=${result.id}`);
    } catch (error) {
      console.error("[Inquiry] Full error object:", error);

      let errorMessage = "Teklif gönderilirken bir hata oluştu. Lütfen tekrar deneyin.";
      let errorTitle = "Hata";

      if (error instanceof ApiError) {
        console.error(`[Inquiry] API Error ${error.status}: ${error.body}`);

        if (error.status === 400) {
          errorTitle = "Form Hatası";
          errorMessage = "Lütfen tüm zorunlu alanları doldurduğunuzdan emin olun.";
        } else if (error.status === 429) {
          errorTitle = "Çok Fazla İstek";
          errorMessage = "Lütfen bir süre bekleyip tekrar deneyin.";
        } else if (error.status >= 500) {
          errorTitle = "Sunucu Hatası";
          errorMessage = "Teknisel bir sorun oluştu. Lütfen daha sonra tekrar deneyin.";
        }
      } else if (error instanceof Error) {
        console.error(`[Inquiry] Network/General Error: ${error.message}`);
        if (error.message.includes('fetch')) {
          errorTitle = "Bağlantı Hatası";
          errorMessage = "Sunucuya bağlanılamıyor. İnternet bağlantınızı kontrol edin.";
        }
      }

      toast({
        title: errorTitle,
        description: errorMessage,
        variant: "destructive",
      });
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <>
      {/* Header */}
      <section className="bg-gradient-to-br from-muted/50 to-muted/20 py-16 lg:py-20 border-b border-border/40">
        <Container className="text-center">
          <div className="flex items-center justify-center gap-4 mb-4">
            <div className="h-10 w-1 rounded-sm bg-primary shadow-sm" />
            <h1 className="text-3xl font-bold lg:text-5xl tracking-tight">İletişim</h1>
            <div className="h-10 w-1 rounded-sm bg-primary shadow-sm" />
          </div>
          <p className="mx-auto mt-2 max-w-2xl text-lg text-muted-foreground">
            {hasCartItems
              ? "Sepetinizdeki ürünler için teklif isteyin"
              : "Sorularınız için bizimle iletişime geçin"}
          </p>
        </Container>
      </section>

      <section className="py-12 lg:py-16">
        <Container>
          <div className="grid gap-12 lg:grid-cols-3">
            {/* Contact Info - Red Background */}
            <div className="lg:col-span-1">
              <div className="relative overflow-hidden rounded-sm bg-primary p-8 text-white shadow-xl shadow-primary/20">
                {/* Decorative elements */}
                <div className="absolute -right-10 -top-10 h-40 w-40 rounded-sm bg-white/10 blur-3xl" />
                <div className="absolute -bottom-10 -left-10 h-40 w-40 rounded-sm bg-black/20 blur-3xl" />

                <div className="relative">
                  <h2 className="mb-8 text-2xl font-bold">İletişim Bilgileri</h2>

                  <div className="space-y-8">
                    <div className="flex items-start gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-white/20 backdrop-blur-sm border border-white/10">
                        <Phone className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-white/90 text-sm uppercase tracking-wide">Telefon</p>
                        <a
                          href="tel:+902122379055"
                          className="text-lg text-white hover:text-white/80 transition-colors font-medium"
                        >
                          0212 237 90 55
                        </a>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-white/20 backdrop-blur-sm border border-white/10">
                        <Mail className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-white/90 text-sm uppercase tracking-wide">E-posta</p>
                        <a
                          href="mailto:info@gastrotech.com.tr"
                          className="text-lg text-white hover:text-white/80 transition-colors break-all font-medium"
                        >
                          info@gastrotech.com.tr
                        </a>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-white/20 backdrop-blur-sm border border-white/10">
                        <MapPin className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-white/90 text-sm uppercase tracking-wide">Adres</p>
                        <p className="text-white/95 font-medium leading-relaxed">
                          Küçük Piyale Mah. Toprak Tabya Sok.
                          <br />
                          No:4/6 Beyoğlu - İstanbul
                        </p>
                      </div>
                    </div>

                    <div className="flex items-start gap-4">
                      <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-sm bg-white/20 backdrop-blur-sm border border-white/10">
                        <Clock className="h-5 w-5 text-white" />
                      </div>
                      <div>
                        <p className="font-semibold text-white/90 text-sm uppercase tracking-wide">Çalışma Saatleri</p>
                        <p className="text-white/95 font-medium leading-relaxed">
                          Pazartesi - Cuma: 08:30 - 18:00
                          <br />
                          Cumartesi: 09:00 - 14:00
                        </p>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Form */}
            <div className="lg:col-span-2">
              <div className="rounded-sm border bg-card p-6 lg:p-8 shadow-sm">
                <h2 className="mb-6 text-xl font-bold">
                  {hasCartItems ? "Teklif İste" : "Mesaj Gönder"}
                </h2>

                {/* Cart Items Summary */}
                {hasCartItems && (
                  <div className="mb-6 rounded-sm bg-muted/50 p-4 border border-border/50">
                    <p className="mb-2 text-sm font-medium">
                      Sepetinizdeki Ürünler ({cart.items.length} kalem)
                    </p>
                    <ul className="space-y-1 text-sm text-muted-foreground">
                      {cart.items.slice(0, 5).map((item) => (
                        <li key={item.id}>
                          • {item.variant.model_code} x{item.quantity}
                        </li>
                      ))}
                      {cart.items.length > 5 && (
                        <li>+ {cart.items.length - 5} daha...</li>
                      )}
                    </ul>
                  </div>
                )}

                {/* eslint-disable-next-line @typescript-eslint/no-explicit-any */}
                <form onSubmit={handleSubmit(onSubmit as any)} className="space-y-6">
                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-medium">
                        Ad Soyad *
                      </label>
                      <Input
                        {...register("full_name")}
                        placeholder="Adınız ve soyadınız"
                        className="rounded-sm"
                      />
                      {errors.full_name && (
                        <p className="mt-1 text-sm text-destructive">
                          {errors.full_name.message}
                        </p>
                      )}
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium">
                        E-posta *
                      </label>
                      <Input
                        {...register("email")}
                        type="email"
                        placeholder="info@gastrotech.com.tr"
                        className="rounded-sm"
                      />
                      {errors.email && (
                        <p className="mt-1 text-sm text-destructive">
                          {errors.email.message}
                        </p>
                      )}
                    </div>
                  </div>

                  <div className="grid gap-4 sm:grid-cols-2">
                    <div>
                      <label className="mb-2 block text-sm font-medium">
                        Telefon
                      </label>
                      <Input
                        {...register("phone")}
                        type="tel"
                        placeholder="+90 5XX XXX XX XX"
                        className="rounded-sm"
                      />
                    </div>
                    <div>
                      <label className="mb-2 block text-sm font-medium">
                        Firma
                      </label>
                      <Input
                        {...register("company")}
                        placeholder="Firma adınız"
                        className="rounded-sm"
                      />
                    </div>
                  </div>

                  <div>
                    <label className="mb-2 block text-sm font-medium">
                      Mesajınız
                    </label>
                    <textarea
                      {...register("message")}
                      rows={4}
                      className="w-full rounded-sm border bg-background px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
                      placeholder="Projeniz veya ihtiyaçlarınız hakkında bilgi verin..."
                    />
                  </div>

                  {/* Honeypot field (anti-spam) */}
                  <input
                    type="text"
                    name="website"
                    className="hidden"
                    tabIndex={-1}
                    autoComplete="off"
                  />

                  {/* Consent Checkbox */}
                  <div className="space-y-2">
                    <div className="flex items-start gap-3">
                      <div className="flex items-center h-5">
                        <input
                          id="consent"
                          type="checkbox"
                          {...register("consent")}
                          className="h-4 w-4 rounded border-gray-300 text-primary focus:ring-primary cursor-pointer accent-primary"
                        />
                      </div>
                      <label htmlFor="consent" className="text-sm text-muted-foreground cursor-pointer select-none leading-tight">
                        <Link href="/kvkk" target="_blank" className="font-semibold text-foreground hover:text-primary hover:underline underline-offset-2 transition-colors">
                          KVKK Aydınlatma Metni
                        </Link>
                        &apos;ni okudum ve kişisel verilerimin bu kapsamda işlenmesini kabul ediyorum.
                      </label>
                    </div>
                    {errors.consent && (
                      <p className="text-sm text-destructive pl-7">
                        {errors.consent.message}
                      </p>
                    )}
                  </div>

                  <Button type="submit" size="lg" disabled={isSubmitting} className="rounded-sm w-full sm:w-auto">
                    {isSubmitting ? (
                      <>
                        <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                        Gönderiliyor...
                      </>
                    ) : (
                      <>
                        <Send className="mr-2 h-4 w-4" />
                        {hasCartItems ? "Teklif İste" : "Gönder"}
                      </>
                    )}
                  </Button>
                </form>
              </div>
            </div>
          </div>
        </Container>
      </section>

      {/* Centered Logo */}
      <div className="py-10 flex items-center justify-center bg-white">
        <Image
          src="/assets/logo.png"
          alt="Gastrotech"
          width={180}
          height={45}
          className="object-contain opacity-80"
        />
      </div>

      {/* Google Maps - Modern Floating Card Design */}
      <section className="relative border-t">
        {/* Map Background */}
        <div className="relative h-[500px] lg:h-[550px]">
          <iframe
            src="https://www.google.com/maps/embed?pb=!1m14!1m8!1m3!1d24077.92738494657!2d28.962193858963488!3d41.030923690946196!3m2!1i1024!2i768!4f13.1!3m3!1m2!1s0x14cab70595d20d17%3A0xa47239ad461f4847!2sGASTROTECH%20END%C3%9CSTR%C4%B0YEL%20DEMO%20%26%20STORE!5e0!3m2!1str!2str!4v1769343405611!5m2!1str!2str"
            width="100%"
            height="100%"
            style={{ border: 0 }}
            allowFullScreen
            loading="lazy"
            referrerPolicy="no-referrer-when-downgrade"
            title="Gastrotech Konum"
            className="absolute inset-0 w-full h-full"
          />

          {/* Floating Contact Card - Redesigned */}
          <div className="absolute bottom-6 left-4 right-4 md:bottom-8 md:left-8 md:right-auto md:max-w-xs z-10 transition-all duration-500 ease-in-out">
            <div className="group overflow-hidden bg-white/95 backdrop-blur-xl shadow-2xl shadow-primary/10 border border-white/60">
              <div className="relative p-6 space-y-6">

                {/* Decorative background glow */}
                <div className="absolute -top-10 -right-10 h-32 w-32 bg-primary/5 blur-3xl pointer-events-none" />

                {/* Address Section */}
                <div className="relative flex items-start gap-4 group/item">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors duration-300 group-hover/item:bg-primary group-hover/item:text-white group-hover/item:shadow-lg group-hover/item:shadow-primary/20">
                    <MapPin className="h-5 w-5" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Adres</h4>
                    <p className="text-sm font-medium leading-relaxed text-foreground/90">
                      Küçük Piyale Mah. Toprak Tabya Sok.
                      <br />
                      No:4/6 Beyoğlu - İstanbul
                    </p>
                  </div>
                </div>

                {/* Phone Section */}
                <div className="relative flex items-start gap-4 group/item">
                  <div className="flex h-10 w-10 shrink-0 items-center justify-center rounded-lg bg-primary/10 text-primary transition-colors duration-300 group-hover/item:bg-primary group-hover/item:text-white group-hover/item:shadow-lg group-hover/item:shadow-primary/20">
                    <Phone className="h-5 w-5" />
                  </div>
                  <div className="space-y-1">
                    <h4 className="text-xs font-bold text-muted-foreground uppercase tracking-wider">Telefon</h4>
                    <a href="tel:+902122379055" className="block text-lg font-bold text-foreground hover:text-primary transition-colors">
                      0212 237 90 55
                    </a>
                  </div>
                </div>

                {/* Action Button */}
                <div className="pt-2">
                  <a
                    href="https://www.google.com/maps/dir//GASTROTECH+END%C3%9CSTR%C4%B0YEL+DEMO+%26+STORE/@41.030924,28.962194,15z"
                    target="_blank"
                    rel="noopener noreferrer"
                    className="flex w-full items-center justify-center gap-2 rounded-lg bg-primary py-3.5 text-sm font-bold text-white shadow-lg shadow-primary/25 transition-all duration-300 hover:bg-primary/90 hover:-translate-y-0.5"
                  >
                    <Navigation className="h-4 w-4" />
                    Yol Tarifi Al
                  </a>
                </div>
              </div>
            </div>
          </div>

          {/* Subtle gradient overlay at bottom for better card visibility */}
          <div className="absolute bottom-0 left-0 right-0 h-32 bg-gradient-to-t from-black/20 to-transparent pointer-events-none" />
        </div>
      </section>
    </>
  );
}
