import type { MacroData, MacroRegimeChip, MacroSeries } from "@/lib/macro";
import { DASH, MACRO_GROUP_ORDER, macroValue, regimeColor, regimeLabel } from "@/lib/format";

// Renders a 1080x1350 (4:5) branded macro-desk capture-card slide for
// social posting. Clone of RiskCaptureCard.tsx's construction discipline:
// all-px sizing, #capture-canvas id, data-capture-ready="true", no client
// JS on this route. Capture cards never import screen components — this
// file owns its own local pill + sparkline clones rather than reusing
// MacroRegimeStrip/MacroPanel/MacroSparkline.
//
// IMPORTANT (capture correctness): Claude's Playwright screenshot step must
// call page.locator("#capture-canvas").screenshot() at native DOM pixel
// size — CardScaleShell's on-screen preview transform is irrelevant to (and
// must never be picked up by) the actual capture.

function humanDate(iso: string): string {
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return `${dt.toISOString().slice(0, 16).replace("T", " ")} UTC`;
}

// Local sparkline clone — capture components never import screen
// components (MacroSparkline.tsx stays screen-only).
function CardMacroSparkline({
  series,
  width = 180,
  height = 44,
}: {
  series: MacroSeries;
  width?: number;
  height?: number;
}) {
  const pts = (series.sparkline ?? []).filter(
    (p): p is { t: string; v: number } =>
      typeof p.v === "number" && Number.isFinite(p.v),
  );
  if (pts.length < 2) {
    return (
      <span style={{ fontSize: 14, color: "#6b7280" }}>{DASH}</span>
    );
  }
  const values = pts.map((p) => p.v);
  const min = Math.min(...values);
  const max = Math.max(...values);
  const range = max - min || 1;
  const pad = 2;
  const coords = pts.map((p, i) => {
    const x = pad + (i / (pts.length - 1)) * (width - 2 * pad);
    const y = pad + (1 - (p.v - min) / range) * (height - 2 * pad);
    return [x, y] as const;
  });
  const path = coords
    .map(([x, y], i) => `${i === 0 ? "M" : "L"}${x.toFixed(1)},${y.toFixed(1)}`)
    .join(" ");
  const up = values[values.length - 1] >= values[0];
  const stroke = up ? "#34d399" : "#fb7185";
  return (
    <svg width={width} height={height} viewBox={`0 0 ${width} ${height}`}>
      <path d={path} fill="none" stroke={stroke} strokeWidth={2} />
    </svg>
  );
}

// Local pill clone (own colored pill, not TrendBadge/MacroRegimeStrip's
// Chip) — matches the color+border+1a-alpha-fill idiom used everywhere
// else on the site, sized for the 1080-wide card.
function CardChip({ chip }: { chip: MacroRegimeChip }) {
  const color = regimeColor(chip.key, chip.state);
  return (
    <div
      style={{
        width: 216,
        display: "flex",
        flexDirection: "column",
        gap: 6,
        borderRadius: 6,
        border: "1px solid #1f2937",
        backgroundColor: "#11161f",
        padding: "12px 14px",
      }}
    >
      <span style={{ fontSize: 14, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 0.5 }}>
        {chip.label}
      </span>
      <span
        style={{
          alignSelf: "flex-start",
          fontSize: 13,
          fontWeight: 700,
          textTransform: "uppercase",
          letterSpacing: 0.5,
          color,
          border: `1px solid ${color}`,
          backgroundColor: `${color}1a`,
          borderRadius: 4,
          padding: "2px 8px",
        }}
      >
        {regimeLabel(chip.state)}
      </span>
      <span style={{ fontSize: 20, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
        {chip.value_label}
      </span>
    </div>
  );
}

export default function MacroCaptureCard({ data }: { data: MacroData }) {
  // Up to 4 headline series rows, one representative series per group
  // present, MACRO_GROUP_ORDER precedence (first series encountered in
  // each group, since series[] is already in fixed §1 table order).
  const bySeriesGroup = new Map<string, MacroSeries>();
  for (const group of MACRO_GROUP_ORDER) {
    const found = data.series.find((s) => s.group === group);
    if (found) bySeriesGroup.set(group, found);
  }
  const headlineSeries = MACRO_GROUP_ORDER.map((g) => bySeriesGroup.get(g)).filter(
    (s): s is MacroSeries => Boolean(s),
  ).slice(0, 4);

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
            ● MACRO PULSE
          </span>
        </div>

        {/* Headline */}
        <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 4 }}>
          <span style={{ fontSize: 56, fontWeight: 700, lineHeight: 1.1 }}>
            MACRO DESK
          </span>
        </div>

        {/* 4 regime chips, card-local colored pills */}
        <div style={{ marginTop: 32, display: "flex", flexWrap: "wrap", gap: 12 }}>
          {data.regime.chips.map((chip) => (
            <CardChip key={chip.key} chip={chip} />
          ))}
        </div>

        <div
          style={{
            marginTop: 32,
            height: 1,
            backgroundColor: "#1f2937",
          }}
        />

        {/* Up to 4 headline series rows, one per group present */}
        <div
          style={{
            marginTop: 32,
            display: "flex",
            flexDirection: "column",
            gap: 20,
          }}
        >
          {headlineSeries.map((s) => (
            <div
              key={s.series_id}
              style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "space-between",
                gap: 16,
              }}
            >
              <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0 }}>
                <span style={{ fontSize: 16, color: "#9ca3af", textTransform: "uppercase", letterSpacing: 1 }}>
                  {s.display_name}
                </span>
                <span style={{ fontSize: 36, fontWeight: 700, fontVariantNumeric: "tabular-nums" }}>
                  {macroValue(s.last, s.unit_kind, s.decimals)}
                </span>
              </div>
              <CardMacroSparkline series={s} />
            </div>
          ))}
          {headlineSeries.length === 0 && (
            <span style={{ fontSize: 20, color: "#6b7280" }}>{DASH}</span>
          )}
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
            Generated {humanDate(data.generated_at)} · macro-desk-v1
          </span>
          {/* Renders unconditionally — mandatory capture-facing footer per
              root CLAUDE.md. */}
          <span style={{ fontSize: 16, color: "#6b7280", fontWeight: 600 }}>
            Educational research only — not financial advice. NFA.
          </span>
        </div>
      </div>
    </div>
  );
}
