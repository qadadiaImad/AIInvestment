import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getArchetypeData, getArchetypeForSymbol } from "@/lib/archetypes";
import ArchetypeCaptureCard from "@/components/terminal/ArchetypeCaptureCard";
import CardScaleShell from "@/components/terminal/CardScaleShell";
import CaptureChromeStrip from "@/components/terminal/CaptureChromeStrip";

// archetypes.json is generated on the owner's machine and never committed —
// this route must never be statically prerendered against a symbol list
// that may not exist at build time.
export const dynamic = "force-dynamic";

// Normalize [symbol] to uppercase [A-Z0-9.-] only before lookup — same
// convention as terminal/card/[symbol]/page.tsx.
function normalizeSymbol(raw: string): string {
  return raw.toUpperCase().replace(/[^A-Z0-9.\-]/g, "");
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const rec = getArchetypeForSymbol(normalizeSymbol(symbol));
  return {
    title: rec ? `${rec.symbol} archetype card · AI STACK TERMINAL` : "Not found · AI STACK TERMINAL",
    robots: { index: false, follow: false },
  };
}

export default async function ArchetypeCaptureCardPage({
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
  // never a broken screenshot. Missing archetypes.json or unknown symbol
  // both land here.
  const record = getArchetypeForSymbol(normalized);
  if (!record) notFound();
  const generatedAt = getArchetypeData()?.generated_at ?? null;

  const isCapture = sp.capture === "1";

  return (
    <div className="flex flex-col items-center py-6 px-3">
      {isCapture && <CaptureChromeStrip />}
      {isCapture ? (
        <ArchetypeCaptureCard record={record} generatedAt={generatedAt} />
      ) : (
        <CardScaleShell>
          <ArchetypeCaptureCard record={record} generatedAt={generatedAt} />
        </CardScaleShell>
      )}
    </div>
  );
}
