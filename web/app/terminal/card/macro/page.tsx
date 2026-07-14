import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getMacroData } from "@/lib/macro";
import MacroCaptureCard from "@/components/terminal/MacroCaptureCard";
import CardScaleShell from "@/components/terminal/CardScaleShell";

// macro.json is generated on the owner's machine and never committed —
// this route must never be statically prerendered against data that may
// not exist at build time.
export const dynamic = "force-dynamic";

export const metadata: Metadata = {
  title: "Macro desk card · AI STACK TERMINAL",
  robots: { index: false, follow: false },
};

export default async function MacroCaptureCardPage({
  searchParams,
}: {
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const sp = await searchParams;

  // A 404 here is a loud, correct failure for a capture script to catch —
  // never a broken screenshot. Missing macro.json lands here.
  const data = getMacroData();
  if (!data) notFound();

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
        <MacroCaptureCard data={data} />
      ) : (
        <CardScaleShell>
          <MacroCaptureCard data={data} />
        </CardScaleShell>
      )}
    </div>
  );
}
