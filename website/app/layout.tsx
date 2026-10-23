import type { Metadata, Viewport } from "next";
import { Bricolage_Grotesque, IBM_Plex_Mono } from "next/font/google";
import { MotionProvider } from "@/components/Motion";
import "./globals.css";

const sans = Bricolage_Grotesque({ subsets: ["latin"], variable: "--font-sans", display: "swap" });
const mono = IBM_Plex_Mono({ subsets: ["latin"], weight: ["400", "500", "600"], variable: "--font-mono", display: "swap" });

const description =
  "A free Windows tray app. Copy a list once, then press Ctrl+Shift+V to paste it one item at a time. Fill forms and spreadsheets without switching windows.";

// Vercel provides the production domain; social images need an absolute URL
const siteUrl = process.env.VERCEL_PROJECT_PRODUCTION_URL
  ? `https://${process.env.VERCEL_PROJECT_PRODUCTION_URL}`
  : "http://localhost:3010";

export const metadata: Metadata = {
  metadataBase: new URL(siteUrl),
  title: "Sequential Paste: copy once, paste one at a time",
  description,
  openGraph: {
    title: "Sequential Paste",
    description: "Copy a list once. Press Ctrl+Shift+V to paste it one item at a time. Free for Windows.",
    type: "website",
  },
  twitter: { card: "summary_large_image", title: "Sequential Paste", description },
};

export const viewport: Viewport = {
  themeColor: [
    { media: "(prefers-color-scheme: light)", color: "#F2EFE8" },
    { media: "(prefers-color-scheme: dark)", color: "#131311" },
  ],
};

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className={`${sans.variable} ${mono.variable}`}>
      <body>
        <MotionProvider>{children}</MotionProvider>
      </body>
    </html>
  );
}
