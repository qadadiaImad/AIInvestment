import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getTaDeskData, getTaInstrument } from "@/lib/ta";
import CaptureCard from "@/components/terminal/CaptureCard";
import CardScaleShell from "@/components/terminal/CardScaleShell";

// ta_desk.json is generated on the owner's machine and never committed —
// this route must never be statically prerendered against a symbol list
// that may not exist at build time.
export const dynamic = "force-dynamic";

// Normalize [symbol] to uppercase [A-Z0-9.-] only before lookup.
function normalizeSymbol(raw: string): string {
  return raw.toUpperCase().replace(/[^A-Z0-9.\-]/g, "");
}

export async function generateMetadata({
  params,
}: {
  params: Promise<{ symbol: string }>;
}): Promise<Metadata> {
  const { symbol } = await params;
  const inst = getTaInstrument(normalizeSymbol(symbol));
  return {
    title: inst ? `${inst.symbol} card · TA Desk` : "Not found · TA Desk",
    robots: { index: false, follow: false },
  };
}

export default async function CaptureCardPage({
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
  // never a broken screenshot. Missing ta_desk.json or unknown symbol both
  // land here.
  const data = getTaDeskData();
  if (!data) notFound();
  const inst = getTaInstrument(normalized);
  if (!inst) notFound();

  const isCapture = sp.capture === "1";

  return (
    <div className="flex flex-col items-center py-6 px-3">
      {isCapture && (
        // Belt-and-suspenders: kill all motion even though this card has no
        // animated elements by construction (pure Server Component, no
        // client state).
        <style>{`* { animation: none !important; transition: none !important; }`}</style>
      )}
      {isCapture ? (
        <CaptureCard instrument={inst} source={data.source} />
      ) : (
        <CardScaleShell>
          <CaptureCard instrument={inst} source={data.source} />
        </CardScaleShell>
      )}
    </div>
  );
}
