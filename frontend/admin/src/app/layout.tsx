import type { Metadata, Viewport } from "next";
import "./globals.css";
import { Providers } from "@/components/providers";
import { fontVariables } from "@/lib/fonts";

export const metadata: Metadata = {
  title: {
    default: "Gastrotech Admin",
    template: "%s | Gastrotech Admin",
  },
  description: "Gastrotech B2B Admin Panel - Professional catalog and inquiry management",
  manifest: "/admin/manifest.webmanifest",
  icons: {
    icon: [
      { url: "/admin/favicon.png", type: "image/png" },
      { url: "/admin/brand/logo.png", type: "image/png", sizes: "192x192" },
    ],
    apple: "/admin/brand/logo.png",
    shortcut: "/admin/favicon.png",
  },
  appleWebApp: {
    capable: true,
    statusBarStyle: "default",
    title: "Gastrotech Admin",
  },
  openGraph: {
    type: "website",
    locale: "tr_TR",
    url: "/",
    siteName: "Gastrotech Admin",
    title: "Gastrotech Admin",
    description: "Gastrotech B2B Admin Panel - Professional catalog and inquiry management",
  },
};

export const viewport: Viewport = {
  themeColor: "#BE2328",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  colorScheme: "light",
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="tr" suppressHydrationWarning className={fontVariables}>
      <head>
        {/* Preconnect to Google Fonts for faster loading */}
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
      </head>
      <body className="font-sans antialiased bg-background text-foreground min-h-screen">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
