"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import CapitalGraph from "@/components/CapitalGraph";
import type { CapitalWeb } from "@/lib/data";

// Phone gate for the home-page capital web (mobile audit, 2026-09-25).
//
// The 303-node force graph is the desktop hero, but on a 390px screen it is
// a screen of unreadable specks whose hover tooltips never fire on touch, and
// it eats the whole first viewport. Below `sm` we render a compact prompt and
// mount vis-network only when the reader asks for it; on wider screens the
// graph mounts exactly as before. The graph is client-rendered either way, so
// gating it on a post-mount media query costs no server HTML.
const PHONE = "(max-width: 639px)";

export default function HomeGraph({ web }: { web: CapitalWeb }) {
  const [phone, setPhone] = useState<boolean | null>(null);
  const [expanded, setExpanded] = useState(false);

  useEffect(() => {
    const mq = window.matchMedia(PHONE);
    const apply = () => setPhone(mq.matches);
    apply();
    mq.addEventListener("change", apply);
    return () => mq.removeEventListener("change", apply);
  }, []);

  const showGraph = phone === false || (phone === true && expanded);
  const nodes = web.nodes.length;
  const edges = web.edges.length;

  if (phone && !expanded) {
    return (
      <div className="flex items-center justify-between gap-3 px-3 py-3">
        <p className="text-[11px] text-term-muted leading-snug">
          {nodes} nodes · {edges} edges. The interactive graph is built for a
          wide screen; open it here or use the full map.
        </p>
        <div className="flex flex-col gap-2 shrink-0">
          <button
            type="button"
            onClick={() => setExpanded(true)}
            className="min-h-[44px] px-3 rounded-sm border border-emerald-500/60 text-emerald-400 text-[11px] font-semibold uppercase tracking-wider"
          >
            Show graph
          </button>
          <Link
            href="/map"
            className="min-h-[44px] flex items-center justify-center px-3 rounded-sm border border-term-border text-[11px] text-term-muted uppercase tracking-wider"
          >
            Full map →
          </Link>
        </div>
      </div>
    );
  }

  return (
    <div className="h-[50vh] sm:h-[58vh] sm:min-h-[380px] w-full bg-[#0b0f17]">
      {showGraph ? <CapitalGraph web={web} /> : null}
    </div>
  );
}
