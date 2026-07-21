import type { PortfolioCardData } from "@/lib/portfolio";
import { DASH, layerColor } from "@/lib/format";

// Renders a 1080x1350 (4:5) branded portfolio capture-card slide for social
// posting. Same construction discipline as RiskCaptureCard.tsx: all-px
// sizing, #capture-canvas id, data-capture-ready="true", no client JS on
// this route.
//
// HARD PRIVACY RULE: the prop type is PortfolioCardData (lib/portfolio.ts),
// a type that structurally OMITS every *_usd field — so an accidental
// future `<PortfolioCaptureCard data={fullPortfolioData} />` wire-up fails
// to typecheck rather than silently leaking a dollar figure onto a
// screenshot. This file must never reference a *_usd field name, and must
// never render a literal "$" character followed by a digit — both are
// grepped for in tests/verification (see lib/portfolio.test.ts's
// toCardData privacy assertions and the runtime DOM grep in the round-5
// verification pass).

const CASH_COLOR = "#a1a1aa"; // zinc-400 — same swatch as PortfolioLayerMix
const UNCLASSIFIED_COLOR = "#6b7280"; // zinc-500 — same swatch as PortfolioLayerMix

function swatchColor(layer: string): string {
  if (layer === "cash") return CASH_COLOR;
  if (layer === "unclassified") return UNCLASSIFIED_COLOR;
  return layerColor(layer);
}

function humanDate(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return `${dt.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

function fmtPct(v: number | null): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  return `${v >= 0 ? "+" : ""}${v.toFixed(1)}%`;
}

function fmtRatio(v: number | null): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return DASH;
  return v.toFixed(2);
}

function pctColor(v: number | null): string {
  if (typeof v !== "number" || !Number.isFinite(v)) return "#e5e7eb";
  if (v > 0) return "#34d399";
  if (v < 0) return "#fb7185";
  return "#e5e7eb";
}

export default function PortfolioCaptureCard({ data }: { data: PortfolioCardData }) {
  const segments = data.layer_exposure.filter((l) => l.weight_pct > 0);
  const risk = data.risk;

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
            ● PORTFOLIO SNAPSHOT
          </span>
        </div>

        {/* Headline */}
        <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 56, fontWeight: 700, lineHeight: 1.1 }}>PORTFOLIO</span>
          <span style={{ fontSize: 16, color: "#6b7280" }}>
            {data.n_positions} position{data.n_positions === 1 ? "" : "s"}
          </span>
        </div>

        {/* Layer-mix mini bar — percent-only, no market_value anywhere on
            this card. */}
        <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 10 }}>
          <span
            style={{ fontSize: 15, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}
          >
            Layer mix
          </span>
          <div
            style={{
              height: 28,
              width: "100%",
              borderRadius: 4,
              overflow: "hidden",
              display: "flex",
              backgroundColor: "#1a2130",
            }}
          >
            {segments.map((l) => (
              <div
                key={l.layer}
                style={{ width: `${l.weight_pct}%`, backgroundColor: swatchColor(l.layer) }}
              />
            ))}
          </div>
          <div style={{ display: "flex", flexWrap: "wrap", gap: 14 }}>
            {segments.map((l) => (
              <div key={l.layer} style={{ display: "flex", alignItems: "center", gap: 6 }}>
                <span
                  style={{
                    width: 10,
                    height: 10,
                    borderRadius: 2,
                    backgroundColor: swatchColor(l.layer),
                    display: "inline-block",
                  }}
                />
                <span style={{ fontSize: 14, color: "#9ca3af", textTransform: "uppercase" }}>
                  {l.layer}
                </span>
                <span style={{ fontSize: 14, color: "#e5e7eb", fontWeight: 600 }}>
                  {fmtPct(l.weight_pct).replace("+", "")}
                </span>
              </div>
            ))}
          </div>
        </div>

        <div style={{ marginTop: 32, height: 1, backgroundColor: "#1f2937" }} />

        {/* 3 headline stats — percentages only. */}
        <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span
              style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}
            >
              Day P&amp;L
            </span>
            <span
              style={{
                fontSize: 36,
                fontWeight: 700,
                fontVariantNumeric: "tabular-nums",
                color: pctColor(data.day_pnl_pct),
              }}
            >
              {fmtPct(data.day_pnl_pct)}
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span
              style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}
            >
              Total Unrealized P&amp;L
            </span>
            <span
              style={{
                fontSize: 36,
                fontWeight: 700,
                fontVariantNumeric: "tabular-nums",
                color: pctColor(data.total_unrealized_pnl_pct),
              }}
            >
              {fmtPct(data.total_unrealized_pnl_pct)}
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span
              style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}
            >
              Top-3 Concentration
            </span>
            <span
              style={{ fontSize: 36, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}
            >
              {data.concentration.top3_weight_pct != null
                ? `${data.concentration.top3_weight_pct.toFixed(1)}%`
                : DASH}
            </span>
          </div>
        </div>

        <div style={{ marginTop: 32, height: 1, backgroundColor: "#1f2937" }} />

        {/* Risk row — vol / VaR95 / Sharpe / beta, all indicative. */}
        <div style={{ marginTop: 24, display: "flex", flexDirection: "column", gap: 10 }}>
          <span
            style={{ fontSize: 15, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}
          >
            Risk (fixed-weight proxy)
          </span>
          <div style={{ display: "flex", gap: 28 }}>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontSize: 13, color: "#6b7280" }}>VOL</span>
              <span style={{ fontSize: 20, fontWeight: 600 }}>
                {risk ? fmtPct(risk.vol_annualized_pct) : DASH}
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontSize: 13, color: "#6b7280" }}>VaR95 1D</span>
              <span style={{ fontSize: 20, fontWeight: 600 }}>
                {risk ? fmtPct(risk.var95_1d_pct) : DASH}
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontSize: 13, color: "#6b7280" }}>SHARPE</span>
              <span style={{ fontSize: 20, fontWeight: 600 }}>
                {risk ? fmtRatio(risk.sharpe_1y) : DASH}
              </span>
            </div>
            <div style={{ display: "flex", flexDirection: "column", gap: 2 }}>
              <span style={{ fontSize: 13, color: "#6b7280" }}>BETA vs SPY</span>
              <span style={{ fontSize: 20, fontWeight: 600 }}>
                {risk ? fmtRatio(risk.beta_vs_spy) : DASH}
              </span>
            </div>
          </div>
          <span style={{ fontSize: 13, color: "#6b7280", fontStyle: "italic" }}>
            Fixed-weight proxy — see terminal for methodology.
          </span>
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
            Generated {humanDate(data.generated_at)} · portfolio-v1
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
