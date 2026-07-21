import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getSiteData, getStock } from "@/lib/data";
import { getMacroData } from "@/lib/macro";
import { buildDefaultDcfInputs, runDcfWithUpside } from "@/lib/dcf";
import DcfCaptureCard from "@/components/terminal/DcfCaptureCard";
import CardScaleShell from "@/components/terminal/CardScaleShell";
import CaptureChromeStrip from "@/components/terminal/CaptureChromeStrip";

// site.json/macro.json are already loaded server-side via getSiteData()/
// getMacroData() — but the derived DCF inputs depend on which stock the
// caller asks for and whether that stock's fundamentals actually support a
// derivation, so this route must never be statically prerendered against a
// fixed symbol list.
export const dynamic = "force-dynamic";

// Normalize [symbol] to uppercase [A-Z0-9.-] only before lookup — same
// convention as terminal/card/archetype/[symbol]/page.tsx.
function normalizeSymbol(raw: string): string {
  return raw.toUpperCase().replace(/[^A-Z0-9.\-]/g, "");
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const stock = getStock(normalizeSymbol(symbol));
  return {
    title: stock ? `${stock.symbol} DCF card · AI STACK TERMINAL` : "Not found · AI STACK TERMINAL",
    robots: { index: false, follow: false },
  };
}

export default async function DcfCaptureCardPage({
  params,
  searchParams,
}: {
  params: Promise<{ symbol: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { symbol } = await params;
  const sp = await searchParams;
  const normalized = normalizeSymbol(symbol);

  // A 404 here is a loud, correct failure for a capture script to catch —
  // never a broken screenshot. Unknown symbol OR a base-FCF/share that
  // can't be derived from any real fundamentals field both land here (see
  // lib/dcf.ts deriveBaseFcfPerShare — never fabricate a fallback).
  const stock = getStock(normalized);
  if (!stock) notFound();

  const macro = getMacroData();
  const defaults = buildDefaultDcfInputs(stock, macro);
  if (defaults.baseFcf.value == null) notFound();

  const result = runDcfWithUpside(
    {
      baseFcfPerShare: defaults.baseFcf.value,
      growthY1: defaults.growth.rate,
      terminalGrowth: defaults.terminalGrowth,
      discountRate: defaults.discount.rate,
      years: defaults.years,
    },
    defaults.currentPrice,
  );

  const generatedAt = getSiteData().generated_at ?? null;
  const isCapture = sp.capture === "1";

  return (
    <div className="flex flex-col items-center py-6 px-3">
      {isCapture && <CaptureChromeStrip />}
      {isCapture ? (
        <DcfCaptureCard
          symbol={stock.symbol}
          layer={stock.layer}
          asOf={stock.as_of}
          generatedAt={generatedAt}
          defaults={defaults}
          result={result}
        />
      ) : (
        <CardScaleShell>
          <DcfCaptureCard
            symbol={stock.symbol}
            layer={stock.layer}
            asOf={stock.as_of}
            generatedAt={generatedAt}
            defaults={defaults}
            result={result}
          />
        </CardScaleShell>
      )}
    </div>
  );
}
