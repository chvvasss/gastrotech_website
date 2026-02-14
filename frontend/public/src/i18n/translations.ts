export type Language = "tr" | "en";

export const translations = {
    tr: {
        nav: {
            products: "Ürünler",
            corporate: "Kurumsal",
            references: "Referanslar",
            service: "Servis",
            blog: "Blog/Medya",
            contact: "İletişim",
        },
        common: {
            search: "Ara",
            searchPlaceholder: "Ürün, kategori veya seri ara...",
            cart: "Sepet",
            getQuote: "Teklif Al",
            viewAll: "Tümünü Gör",
            readMore: "Devamını Oku",
            loading: "Yükleniyor...",
            error: "Bir hata oluştu",
            success: "Başarılı",
            viewReferences: "Referanslarımızı Gör",
        },
        home: {
            heroTitle: "Profesyonel Mutfak Çözümleri",
            heroSubtitle: "1985'ten bu yana endüstriyel mutfak sektörüne kaliteli ve yenilikçi çözümler sunuyoruz.",
            discoverProducts: "Ürünleri Keşfet",
        },
        footer: {
            address: "Adres",
            phone: "Telefon",
            email: "E-posta",
            followUs: "Bizi Takip Edin",
            allRightsReserved: "Tüm hakları saklıdır.",
        }
    },
    en: {
        nav: {
            products: "Products",
            corporate: "Corporate",
            references: "References",
            service: "Service",
            blog: "Blog/Media",
            contact: "Contact",
        },
        common: {
            search: "Search",
            searchPlaceholder: "Search products, categories or series...",
            cart: "Cart",
            getQuote: "Get Quote",
            viewAll: "View All",
            readMore: "Read More",
            loading: "Loading...",
            error: "An error occurred",
            success: "Success",
            viewReferences: "View References",
        },
        home: {
            heroTitle: "Professional Kitchen Solutions",
            heroSubtitle: "Providing quality and innovative solutions to the industrial kitchen sector since 1985.",
            discoverProducts: "Discover Products",
        },
        footer: {
            address: "Address",
            phone: "Phone",
            email: "Email",
            followUs: "Follow Us",
            allRightsReserved: "All rights reserved.",
        }
    }
};

export type TranslationKey = keyof typeof translations.tr;
