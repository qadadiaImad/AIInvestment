import type { TaInstrument } from "@/lib/ta";
import { num, signedPct, trendColor, trendLabel } from "@/lib/format";

// Renders a 1080x1350 (4:5) branded capture-card slide for social posting.
// ALL internal sizing is real px (never rem, never %-based layout) so the
// frame never reflows regardless of host viewport/zoom — screenshot
// correctness depends on this.
//
// IMPORTANT (capture correctness): Claude's Playwright screenshot step must
// call page.locator("#capture-canvas").screenshot() — an ELEMENT screenshot
// at native DOM pixel size — never a full-page/viewport screenshot. This
// component is sometimes wrapped by CardScaleShell for on-screen human
// preview with a CSS transform: scale(...); that transform is IRRELEVANT to
// (and must never be picked up by) the actual capture.

function fmt(v: number | null, d: number): string {
  return num(v, d);
}

// Inline server-rendered sparkline SVG — no client JS, no TradingView
// widget (an async cross-origin iframe has no reliable "finished painting"
// signal, which would break a deterministic screenshot).
function CardSparkline({
  points,
  width,
  height,
}: {
  points: { t: string; c: number }[];
  width: number;
  height: number;
}) {
  const closes = points
    .map((p) => p.c)
    .filter((v) => typeof v === "number" && Number.isFinite(v));
  if (closes.length < 2) {
    return (
      <svg width={width} height={height} aria-hidden="true">
        <line
          x1={0}
          y1={height / 2}
          x2={width}
          y2={height / 2}
          stroke="#1f2937"
          strokeWidth={2}
        />
      </svg>
    );
  }
  const min = Math.min(...closes);
  const max = Math.max(...closes);
  const range = max - min || 1;
  const pad = 4;
  const coords = closes.map((v, i) => {
    const x = pad + (i / (closes.length - 1)) * (width - 2 * pad);
    const y = pad + (1 - (v - min) / range) * (height - 2 * pad);
    return [x, y] as const;
  });
  const path = coords
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  const up = closes[closes.length - 1] >= closes[0];
  const stroke = up ? "#34d399" : "#fb7185";
  return (
    <svg width={width} height={height} aria-hidden="true">
      <path d={path} fill="none" stroke={stroke} strokeWidth={4} />
    </svg>
  );
}

function LevelPair({ label, value, d }: { label: string; value: number | null; d: number }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
      <span style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
        {label}
      </span>
      <span style={{ fontSize: 32, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
        {fmt(value, d)}
      </span>
    </div>
  );
}

function humanDate(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return `${dt.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

export default function CaptureCard({
  instrument,
  source,
}: {
  instrument: TaInstrument;
  source: string;
}) {
  const d = instrument.asset_class === "fx" ? 4 : 2;
  const chg = signedPct(instrument.price.day_change_pct);
  const p = instrument.levels.daily_pivots;
  const atr = instrument.atr14;
  const o = instrument.levels.previous_day_ohlc;

  return (
    // Comment directly above #capture-canvas per spec: the scale wrapper
    // (CardScaleShell) is for on-screen human preview ONLY. The Playwright
    // capture step targets this element by id at its native 1080x1350 DOM
    // pixel size — it must never screenshot a scaled ancestor.
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
            ● SESSION LEVELS
          </span>
        </div>

        {/* Headline */}
        <div style={{ marginTop: 40, display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 96, fontWeight: 700, lineHeight: 1 }}>
            {instrument.symbol}
          </span>
          <span style={{ fontSize: 24, color: "#9ca3af" }}>
            {instrument.display_name}
          </span>
        </div>

        {/* Price row */}
        <div
          style={{
            marginTop: 24,
            display: "flex",
            alignItems: "baseline",
            gap: 24,
          }}
        >
          <span
            style={{
              fontSize: 120,
              fontWeight: 700,
              fontVariantNumeric: "tabular-nums",
              lineHeight: 1,
            }}
          >
            {fmt(instrument.price.last, d)}
          </span>
          <span
            style={{
              fontSize: 40,
              fontWeight: 700,
              fontVariantNumeric: "tabular-nums",
              color: chg.cls.includes("emerald")
                ? "#34d399"
                : chg.cls.includes("rose")
                  ? "#fb7185"
                  : "#9ca3af",
            }}
          >
            {chg.text}
          </span>
        </div>

        <div style={{ marginTop: 24 }}>
          <CardSparkline points={instrument.sparkline} width={952} height={140} />
        </div>

        <div
          style={{
            marginTop: 24,
            height: 1,
            backgroundColor: "#1f2937",
          }}
        />

        {/* 2-column level grid */}
        <div
          style={{
            marginTop: 32,
            display: "grid",
            gridTemplateColumns: "1fr 1fr",
            gap: 28,
          }}
        >
          <LevelPair label="PP" value={p.pp} d={d} />
          <LevelPair label="R1" value={p.r1} d={d} />
          <LevelPair label="R2" value={p.r2} d={d} />
          <LevelPair label="S1" value={p.s1} d={d} />
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
              ATR(14) ± band
            </span>
            <span style={{ fontSize: 32, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
              ± {fmt(atr.value, d)}
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4, justifyContent: "center" }}>
            <span
              style={{
                display: "inline-block",
                width: "fit-content",
                padding: "6px 14px",
                fontSize: 22,
                fontWeight: 700,
                textTransform: "uppercase",
                letterSpacing: 1,
                borderRadius: 4,
                border: `2px solid ${trendColor(instrument.trend.state)}`,
                color: trendColor(instrument.trend.state),
              }}
            >
              {trendLabel(instrument.trend.state)}
            </span>
          </div>
        </div>

        {/* Prev-day OHLC small readout */}
        <div
          style={{
            marginTop: 32,
            display: "flex",
            gap: 32,
            fontSize: 18,
            color: "#9ca3af",
            fontVariantNumeric: "tabular-nums",
          }}
        >
          <span>O {fmt(o.open, d)}</span>
          <span>H {fmt(o.high, d)}</span>
          <span>L {fmt(o.low, d)}</span>
          <span>C {fmt(o.close, d)}</span>
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
            Retrieved {humanDate(instrument.retrieved_at)} · {source}
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
