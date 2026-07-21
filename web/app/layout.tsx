import type { Metadata } from "next";
import { JetBrains_Mono } from "next/font/google";
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

// MUST stay synchronous/static: calling headers() (or any request-scoped API)
// here would drag every SSG route (e.g. /stocks/[symbol]) into dynamic
// rendering and turn clean notFound() 404s into DYNAMIC_SERVER_USAGE 500s.
// Chrome-stripping for ?capture=1 card screenshots is handled per-card-page
// via <CaptureChromeStrip /> (a server-rendered global style), never here.
export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  const data = getSiteData();
  const generatedAt = data.generated_at;
  return (
    <html lang="en" className={`${jetbrainsMono.variable} h-full antialiased`}>
      <body className="min-h-full flex flex-col bg-[#0b0f17] text-[#e5e7eb]">
        <Header generatedAt={generatedAt} />
        <main className="flex-1 flex flex-col">{children}</main>
        <Footer
          disclaimer={data.disclaimer}
          sources={data.sources}
          generatedAt={generatedAt}
        />
      </body>
    </html>
  );
}
