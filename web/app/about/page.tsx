import type { Metadata } from "next";
import { getSiteData } from "@/lib/data";
import { LAYER_ORDER, LAYER_LABELS, LAYER_COLORS } from "@/lib/format";

export const metadata: Metadata = {
  title: "About & Methodology · AI STACK",
  description:
    "How this educational AI-sector research terminal is built, what the data means, and why it decays. Not financial advice.",
};

const STACK_DESC: Record<string, string> = {
  "L0-energy": "Power generation, grid, nuclear, gas, and datacenter power/cooling.",
  "L1-chips": "Accelerators, foundries, EDA, memory, and semiconductor equipment.",
  "L2-infra": "Hyperscalers, neoclouds, networking, storage, and datacenter hardware.",
  "L3-models": "Frontier model labs (largely private — shown in the capital web).",
  "L4-application": "Software applying AI to end markets and enterprise workflows.",
};

export default function AboutPage() {
  const data = getSiteData();

  return (
    <div className="px-3 py-4 max-w-3xl flex flex-col gap-6 text-[12.5px] leading-relaxed">
      <section>
        <h1 className="text-base font-bold tracking-tight mb-2">
          About this terminal
        </h1>
        <p className="text-zinc-300">
          This is an <strong>educational research terminal</strong> for studying
          the AI value chain — the companies that supply energy, chips,
          infrastructure, models, and applications, and the capital and compute
          relationships that connect them. It exists to help you{" "}
          <em>understand structure</em>, not to tell you what to do.
        </p>
        <p className="mt-2 text-rose-300 font-semibold">
          Educational research only — not financial advice and not a
          recommendation to buy or sell any security.
        </p>
      </section>

      <section>
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          The AI stack
        </h2>
        <ul className="flex flex-col gap-1.5">
          {LAYER_ORDER.map((l) => (
            <li key={l} className="flex items-start gap-2">
              <span
                className="mt-1 inline-block h-2 w-2 rounded-full shrink-0"
                style={{ backgroundColor: LAYER_COLORS[l] }}
              />
              <span>
                <strong style={{ color: LAYER_COLORS[l] }}>
                  {LAYER_LABELS[l]}
                </strong>{" "}
                <span className="text-term-muted">({l})</span> —{" "}
                {STACK_DESC[l]}
              </span>
            </li>
          ))}
        </ul>
      </section>

      <section>
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          Methodology
        </h2>
        <ul className="list-disc pl-5 flex flex-col gap-1.5 text-zinc-300">
          <li>
            Every figure is a <strong>date-stamped, point-in-time</strong>{" "}
            retrieval from public sources. Numbers are perishable and decay —
            always verify against primary sources before acting.
          </li>
          <li>
            Fundamentals (margins, returns, leverage, multiples, growth) and
            peer percentiles are computed against industry and stack-layer
            cohorts.
          </li>
          <li>
            The <strong>capital web</strong> distinguishes{" "}
            <span className="text-zinc-100">reported</span>,{" "}
            <span className="text-zinc-100">filed</span>, and{" "}
            <span className="text-zinc-100">rumored</span> links, and marks{" "}
            <span style={{ color: "#a78bfa" }}>AI-extracted</span> edges
            (dashed/dimmed) separately from curated ones. Facts are not laundered
            from rumors.
          </li>
          <li>
            &quot;The one bottleneck&quot; for each name highlights the physical
            and regulatory constraints and lead times that gate growth.
          </li>
          <li>
            Narrative scenarios and risks, where present, are analytical framings
            — not forecasts or advice.
          </li>
        </ul>
      </section>

      <section>
        <h2 className="text-[13px] font-semibold uppercase tracking-wider text-zinc-300 mb-2">
          Sources
        </h2>
        <ul className="flex flex-col gap-1">
          {data.sources.map((s) => (
            <li key={s.name}>
              <a
                href={s.url}
                target="_blank"
                rel="noopener noreferrer"
                className="text-blue-400 hover:text-blue-300 underline-offset-2 hover:underline"
              >
                {s.name}
              </a>{" "}
              <span className="text-term-muted">— {s.url}</span>
            </li>
          ))}
        </ul>
        <p className="mt-3 text-[10.5px] text-term-muted">
          Data generated {data.generated_at}.
        </p>
      </section>

      <section className="border-t border-term-border pt-3">
        <p className="text-term-muted text-[11.5px]">{data.disclaimer}</p>
      </section>
    </div>
  );
}
