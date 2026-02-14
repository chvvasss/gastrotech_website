import { Inter, Plus_Jakarta_Sans } from "next/font/google";

// Primary UI font - Plus Jakarta Sans (modern, geometric)
export const fontSans = Plus_Jakarta_Sans({
  variable: "--font-sans",
  subsets: ["latin"],
  display: "swap",
  fallback: ["system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "sans-serif"],
  preload: true,
  weight: ["300", "400", "500", "600", "700", "800"],
});

// Secondary font - Inter for data/tables (highly legible)
export const fontMono = Inter({
  variable: "--font-mono",
  subsets: ["latin"],
  display: "swap",
  fallback: ["system-ui", "sans-serif"],
  preload: false,
  weight: ["400", "500", "600"],
});

// Font class names for use in layout
export const fontVariables = `${fontSans.variable} ${fontMono.variable}`;

// CSS variable references
export const fontFamily = {
  sans: "var(--font-sans)",
  mono: "var(--font-mono)",
};
