import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { getChokepointById } from "@/lib/data";
import ChokepointCaptureCard from "@/components/terminal/ChokepointCaptureCard";
import CardScaleShell from "@/components/terminal/CardScaleShell";
import CaptureChromeStrip from "@/components/terminal/CaptureChromeStrip";

// chokepoints.json is generated on the owner's machine and never committed —
// this route must never be statically prerendered against an id list that
// may not exist at build time.
export const dynamic = "force-dynamic";

export async function generateMetadata({
  params,
}: {
  params: Promise<{ id: string }>;
}): Promise<Metadata> {
  const { id } = await params;
  const cp = getChokepointById(id);
  return {
    title: cp ? `${cp.name} card · Chokepoints` : "Not found · Chokepoints",
    robots: { index: false, follow: false },
  };
}

export default async function ChokepointCaptureCardPage({
  params,
  searchParams,
}: {
  params: Promise<{ id: string }>;
  searchParams: Promise<{ [key: string]: string | string[] | undefined }>;
}) {
  const { id } = await params;
  const sp = await searchParams;

  // A 404 here is a loud, correct failure for a capture script to catch —
  // never a broken screenshot. Covers both "chokepoints.json absent" and
  // "unknown id" (getChokepointById degrades to undefined in both cases).
  const cp = getChokepointById(id);
  if (!cp) notFound();

  const isCapture = sp.capture === "1";

  return (
    <div className="flex flex-col items-center py-6 px-3">
      {isCapture && <CaptureChromeStrip />}
      {isCapture ? (
        <ChokepointCaptureCard cp={cp} />
      ) : (
        <CardScaleShell>
          <ChokepointCaptureCard cp={cp} />
        </CardScaleShell>
      )}
    </div>
  );
}
