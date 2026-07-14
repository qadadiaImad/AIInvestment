import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
import { headers } from "next/headers";
import "./globals.css";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { getSiteData } from "@/lib/data";

const jetbrainsMono = JetBrains_Mono({
  variable: "--font-jetbrains-mono",
  subsets: ["latin"],
});

export const metadata: Metadata = {
  title: "AI STACK · Data Terminal",
  description:
    "Educational AI-sector research terminal — fundamentals, relationships, and the AI value chain. Not financial advice.",
};

// Async so we can read the `x-capture-mode` request header set by proxy.ts
// for /terminal/card/[symbol]?capture=1 requests, and omit Header/Footer
// chrome for those. This is server-rendered — zero hydration flash, so a
// screenshot taken the instant the response arrives is already chrome-free.
// Deliberately NOT a client component (usePathname/useSearchParams): that
// risks one frame of visible chrome before JS strips it, which corrupts a
// pixel-exact capture.
export default async function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const h = await headers();
  const chromeless = h.get("x-capture-mode") === "1";
  const data = getSiteData();
  const generatedAt = data.generated_at;
  return (
    <html lang="en" className={`${jetbrainsMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#0b0f17] text-[#e5e7eb]">
        {!chromeless && <Header generatedAt={generatedAt} />}
        <main className="flex-1 flex flex-col">{children}</main>
        {!chromeless && (
          <Footer
            disclaimer={data.disclaimer}
            sources={data.sources}
            generatedAt={generatedAt}
          />
        )}
      </body>
    </html>
  );
}
