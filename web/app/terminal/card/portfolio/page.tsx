import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getPortfolioData, isPortfolioEmpty, toCardData } from "@/lib/portfolio";
import PortfolioCaptureCard from "@/components/terminal/PortfolioCaptureCard";
import CardScaleShell from "@/components/terminal/CardScaleShell";
import CaptureChromeStrip from "@/components/terminal/CaptureChromeStrip";

// web/data/portfolio.json is generated on the owner's machine and never
// committed — this route must never be statically prerendered against data
// that may not exist at build time.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Portfolio card · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

export default async function PortfolioCaptureCardPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;

  // A 404 here is a loud, correct failure for a capture script to catch —
  // never a broken/blank screenshot. Missing portfolio.json AND the
  // "no positions yet" empty-state bundle both land here: there is nothing
  // shareable in an empty-state bundle.
  const data = getPortfolioData();
  if (isPortfolioEmpty(data) || !data) notFound();

  const cardData = toCardData(data);
  const isCapture = sp.capture === "1";

  return (
    <div className="flex flex-col items-center py-6 px-3">
      {isCapture && <CaptureChromeStrip />}
      {isCapture ? (
        <PortfolioCaptureCard data={cardData} />
      ) : (
        <CardScaleShell>
          <PortfolioCaptureCard data={cardData} />
        </CardScaleShell>
      )}
    </div>
  );
}
