import type { RiskData } from "@/lib/risk";
import { DASH, layerLabel, riskDivergingColor, contrastText } from "@/lib/format";

// Renders a 1080x1350 (4:5) branded risk-desk capture-card slide for social
// posting. NOT a reuse of CaptureCard.tsx (that component is TA-instrument-
// shaped) — same construction discipline: all-px sizing, #capture-canvas id,
// data-capture-ready="true", no client JS on this route (plain divs, no SVG
// sparkline needed here).
//
// IMPORTANT (capture correctness): Claude's Playwright screenshot step must
// call page.locator("#capture-canvas").screenshot() at native DOM pixel
// size — CardScaleShell's on-screen preview transform is irrelevant to (and
// must never be picked up by) the actual capture.

const TOP_N = 12;
const DAY_CHANGE_DOMAIN = 8;

function humanDate(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return `${dt.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

function fmtPct(v: number | null): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function fmtCorr(v: number | null): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  return v.toFixed(2);
}

export default function RiskCaptureCard({ data }: { data: RiskData }) {
  const top = data.per_stock
    .filter((s) => s.market_cap != null)
    .slice()
    .sort((a, b) => (b.market_cap ?? 0) - (a.market_cap ?? 0))
    .slice(0, TOP_N);

  const h = data.headline;

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
            ● AI STACK HEAT CHECK
          </span>
        </div>

        {/* Headline */}
        <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 56, fontWeight: 700, lineHeight: 1.1 }}>
            RISK DESK
          </span>
        </div>

        {/* Mini heatmap — top ~12 constituents by market cap, universe-wide
            flat mosaic (not layer-grouped — a card is one flat mosaic),
            fixed metric = day_change_pct, no live toggle. */}
        <div
          style={{
            marginTop: 32,
            display: "flex",
            flexWrap: "wrap",
            gap: 8,
          }}
        >
          {top.map((s) => {
            const bg = riskDivergingColor(s.day_change_pct, DAY_CHANGE_DOMAIN);
            const fg = contrastText(bg);
            return (
              <div
                key={s.symbol}
                style={{
                  width: 138,
                  height: 68,
                  borderRadius: 4,
                  backgroundColor: bg,
                  color: fg,
                  display: "flex",
                  flexDirection: "column",
                  alignItems: "center",
                  justifyContent: "center",
                  gap: 2,
                }}
              >
                <span style={{ fontSize: 20, fontWeight: 700 }}>{s.symbol}</span>
                <span style={{ fontSize: 15, fontWeight: 600, opacity: 0.9 }}>
                  {fmtPct(s.day_change_pct)}
                </span>
              </div>
            );
          })}
        </div>

        <div
          style={{
            marginTop: 32,
            height: 1,
            backgroundColor: "#1f2937",
          }}
        />

        {/* 3 headline stats — sourced DIRECTLY from risk.json's headline
            block, zero recomputation here. */}
        <div
          style={{
            marginTop: 32,
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
              Worst layer today
            </span>
            <span style={{ fontSize: 36, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
              {h.worst_layer ? layerLabel(h.worst_layer.layer) : DASH}{" "}
              <span style={{ color: "#fb7185" }}>
                {h.worst_layer ? fmtPct(h.worst_layer.day_change_pct) : ""}
              </span>
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
              Universe VaR95 (1-day)
            </span>
            <span style={{ fontSize: 36, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
              {h.universe_var95_1d_pct != null ? `${h.universe_var95_1d_pct.toFixed(1)}%` : DASH}
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
              Top correlation
            </span>
            <span style={{ fontSize: 36, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
              {h.top_correlation_pair
                ? `${layerLabel(h.top_correlation_pair.a)} ↔ ${layerLabel(h.top_correlation_pair.b)} ${fmtCorr(h.top_correlation_pair.value)}`
                : DASH}
            </span>
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
            Generated {humanDate(data.generated_at)} · risk-desk-v1
          </span>
          {/* Renders unconditionally, even outside ?capture=1 — mandatory
              capture-facing footer per root CLAUDE.md. */}
          <span style={{ fontSize: 16, color: "#6b7280", fontWeight: 600 }}>
            Educational research only — not financial advice. NFA.
          </span>
        </div>
      </div>
    </div>
  );
}
