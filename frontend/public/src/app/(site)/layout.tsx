import { Header, Footer } from "@/components/layout";
import { SiteSettingsInitializer } from "@/components/common/site-settings-initializer";
import { PageLoader } from "@/components/layout/page-loader";
import { WhatsAppButton } from "@/components/common/whatsapp-button";
import { Suspense } from "react";

export default function SiteLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-screen flex-col">
      <SiteSettingsInitializer />
      <Suspense fallback={null}>
        <PageLoader />
      </Suspense>
      <Header />
      {/* FIXED: Added padding-bottom to ensure content never touches footer */}
      <main className="flex-1 pb-16">{children}</main>
      <WhatsAppButton />
      <Footer />
    </div>
  );
}
