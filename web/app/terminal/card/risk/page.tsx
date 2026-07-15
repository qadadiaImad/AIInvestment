import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getRiskData } from "@/lib/risk";
import RiskCaptureCard from "@/components/terminal/RiskCaptureCard";
import CardScaleShell from "@/components/terminal/CardScaleShell";
import CaptureChromeStrip from "@/components/terminal/CaptureChromeStrip";

// risk.json is generated on the owner's machine and never committed — this
// route must never be statically prerendered against data that may not
// exist at build time.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Risk desk card · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

export default async function RiskCaptureCardPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;

  // A 404 here is a loud, correct failure for a capture script to catch —
  // never a broken screenshot. Missing risk.json lands here.
  const data = getRiskData();
  if (!data) notFound();

  const isCapture = sp.capture === "1";

  return (
    <div className="flex flex-col items-center py-6 px-3">
      {isCapture && <CaptureChromeStrip />}
      {isCapture ? (
        <RiskCaptureCard data={data} />
      ) : (
        <CardScaleShell>
          <RiskCaptureCard data={data} />
        </CardScaleShell>
      )}
    </div>
  );
}
