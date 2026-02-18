import type { Metadata } from "next";
import { Plus_Jakarta_Sans } from "next/font/google";
import "./globals.css";
import { Providers } from "@/components/providers";
import { GoogleTranslateScript } from "@/components/google-translate";

const plusJakartaSans = Plus_Jakarta_Sans({
  subsets: ["latin"],
  variable: "--font-plus-jakarta-sans",
  display: "swap",
});

export const metadata: Metadata = {
  title: {
    default: "Gastrotech | Endüstriyel Mutfak Ekipmanları",
    template: "%s | Gastrotech",
  },
  description:
    "Profesyonel mutfak ekipmanları üreticisi. Gazlı ocaklar, fırınlar, soğutma sistemleri ve daha fazlası.",
  keywords: ["endüstriyel mutfak", "gastronomi ekipmanları", "profesyonel mutfak", "gastrotech"],
  authors: [{ name: "Gastrotech" }],
  creator: "Gastrotech",
  openGraph: {
    type: "website",
    locale: "tr_TR",
    siteName: "Gastrotech",
  },
  icons: {
    icon: "/favicon.ico",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" suppressHydrationWarning data-scroll-behavior="smooth">
      <body className={`${plusJakartaSans.variable} font-sans`}>
        <GoogleTranslateScript />
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
