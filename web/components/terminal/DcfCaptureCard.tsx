import type { DcfDefaultInputs, DcfResultWithUpside } from "@/lib/dcf";
import { DASH, layerLabel } from "@/lib/format";

// Renders a 1080x1350 (4:5) branded DCF capture-card slide for social
// posting. NOT a reuse of ArchetypeCaptureCard/RiskCaptureCard (those are
// archetype-scorecard/risk-desk-shaped) — same construction discipline:
// all-px sizing, #capture-canvas id, data-capture-ready="true", no client JS
// on this route (plain divs, no SVG needed here). Renders the DCF at PURE
// defaults only — no sliders, no user state (task constraint); the
// interactive version lives in DcfPanel.tsx on /stocks/[symbol].
//
// IMPORTANT (capture correctness): Claude's Playwright screenshot step must
// call page.locator("#capture-canvas").screenshot() at native DOM pixel
// size — CardScaleShell's on-screen preview transform is irrelevant to (and
// must never be picked up by) the actual capture.

function humanDate(iso: string | null): string {
  if (!iso) return DASH;
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return dt.toISOString().slice(0, 10);
}

function fmtPrice(v: number | null): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  return `$${v.toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
}

function fmtSignedPct(v: number | null): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function fmtPct(v: number, dp = 2): string {
  return `${(v * 100).toFixed(dp)}%`;
}

function upsideColor(v: number | null): string {
  if (v == null) return "#e5e7eb";
  if (v > 5) return "#34d399";
  if (v < -5) return "#f87171";
  return "#fbbf24";
}

function basisLabel(basis: "pfcf" | "ps_margin" | "none"): string {
  if (basis === "pfcf") return "price / P-FCF";
  if (basis === "ps_margin") return "price / P-S × FCF margin";
  return "unavailable";
}

function Stat({
  label,
  value,
  color,
}: {
  label: string;
  value: string;
  color?: string;
}) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 15, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
        {label}
      </span>
      <span style={{ fontSize: 30, fontWeight: 700, color: color ?? "#e5e7eb" }}>{value}</span>
    </div>
  );
}

export default function DcfCaptureCard({
  symbol,
  layer,
  asOf,
  generatedAt,
  defaults,
  result,
}: {
  symbol: string;
  layer: string;
  asOf: string | null;
  generatedAt: string | null;
  defaults: DcfDefaultInputs;
  result: DcfResultWithUpside;
}) {
  return (
    <div
      id="capture-canvas"
      data-capture-ready="true"
      style={{
        width: 1080,
        height: 1350,
        position: "relative",
        backgroundColor: "#0b0f17",
        color: "#e5e7eb",
        overflow: "hidden",
        fontFamily:
          "var(--font-jetbrains-mono), ui-monospace, SFMono-Regular, Menlo, Consolas, monospace",
      }}
    >
      <div
        style={{
          position: "absolute",
          inset: 64,
          display: "flex",
          flexDirection: "column",
        }}
      >
        {/* Brand + eyebrow */}
        <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
          <span style={{ fontSize: 28, fontWeight: 700, letterSpacing: 1 }}>
            AI<span style={{ color: "#34d399" }}>·STACK</span>
            <span style={{ color: "#9ca3af" }}>·TERMINAL</span>
          </span>
          <span
            style={{
              fontSize: 18,
              color: "#34d399",
              fontWeight: 600,
              letterSpacing: 2,
            }}
          >
            ● 2-STAGE DCF — TOY MODEL
          </span>
        </div>

        {/* Headline */}
        <div style={{ marginTop: 28, display: "flex", alignItems: "baseline", gap: 16 }}>
          <span style={{ fontSize: 64, fontWeight: 700, lineHeight: 1.05 }}>{symbol}</span>
          <span style={{ fontSize: 20, color: "#9ca3af" }}>{layerLabel(layer)}</span>
        </div>

        {/* Fair value vs price */}
        <div
          style={{
            marginTop: 36,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 24,
            borderRadius: 8,
            border: "1px solid #1f2937",
            padding: "24px 28px",
          }}
        >
          <Stat label="Fair value / share" value={fmtPrice(result.fairValuePerShare)} />
          <Stat label="Current price" value={fmtPrice(result.currentPrice)} />
          <Stat
            label="Upside / (discount)"
            value={fmtSignedPct(result.upsidePct)}
            color={upsideColor(result.upsidePct)}
          />
          <Stat label="Model" value={result.valid ? "Valid" : "Invalid"} />
        </div>

        {/* Assumptions strip */}
        <div
          style={{
            marginTop: 20,
            display: "flex",
            flexDirection: "column",
            gap: 8,
            borderRadius: 8,
            border: "1px solid #1f2937",
            padding: "18px 20px",
          }}
        >
          <span style={{ fontSize: 15, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
            Assumptions (default case)
          </span>
          <span style={{ fontSize: 18, color: "#e5e7eb" }}>
            Growth Y1 {fmtPct(result.inputs.growthY1)} → Terminal {fmtPct(result.inputs.terminalGrowth)} ·
            Discount rate {fmtPct(result.inputs.discountRate)}
          </span>
          <span style={{ fontSize: 15, color: "#6b7280" }}>
            Base FCF/share via {basisLabel(defaults.baseFcf.basis)} · Growth source:{" "}
            {defaults.growth.source === "actual" ? "reported rev YoY (clamped)" : "methodology default"}{" "}
            · Discount source:{" "}
            {defaults.discount.source === "macro_dgs10" ? "10Y Treasury + ERP" : "flat fallback"}
          </span>
        </div>

        {/* 5-year cash flow rows (compact) */}
        <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 10 }}>
          <span style={{ fontSize: 15, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
            5-year forecast — PV / share
          </span>
          <div style={{ display: "flex", gap: 10 }}>
            {result.rows.map((row) => (
              <div
                key={row.year}
                style={{
                  flex: 1,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  gap: 4,
                  borderRadius: 6,
                  border: "1px solid #1f2937",
                  padding: "12px 6px",
                }}
              >
                <span style={{ fontSize: 13, color: "#6b7280" }}>Y{row.year}</span>
                <span style={{ fontSize: 16, fontWeight: 600, color: "#e5e7eb" }}>
                  {fmtPrice(row.pv)}
                </span>
                <span style={{ fontSize: 12, color: "#6b7280" }}>{fmtPct(row.growth, 1)}</span>
              </div>
            ))}
          </div>
        </div>

        {/* Footer, bottom-anchored */}
        <div
          style={{
            marginTop: "auto",
            paddingTop: 32,
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          <span style={{ fontSize: 16, color: "#6b7280" }}>
            Generated {humanDate(generatedAt)} · data as of {humanDate(asOf)} · 2-stage FCF DCF,
            5yr explicit + Gordon-growth terminal value
          </span>
          {/* Renders unconditionally, even outside ?capture=1 — mandatory
              capture-facing footer per root CLAUDE.md. */}
          <span style={{ fontSize: 16, color: "#6b7280", fontWeight: 600 }}>
            TOY MODEL — educational, not a price target. Not financial advice. NFA.
          </span>
        </div>
      </div>
    </div>
  );
}
