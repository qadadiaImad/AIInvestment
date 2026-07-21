import type { ArchetypeKey, ArchetypeStockRecord } from "@/lib/archetypes";
import {
  ARCHETYPE_COLORS,
  ARCHETYPE_LABELS,
  ARCHETYPE_ORDER,
  ARCHETYPE_SUBTITLES,
  archetypeScoreColor,
  archetypeVerdictLabel,
  DASH,
  layerLabel,
} from "@/lib/format";

// Renders a 1080x1350 (4:5) branded archetype-scorecard capture-card slide
// for social posting. NOT a reuse of RiskCaptureCard/CaptureCard (those are
// risk-desk/TA-instrument-shaped) — same construction discipline: all-px
// sizing, #capture-canvas id, data-capture-ready="true", no client JS on
// this route (plain divs, no SVG needed here).
//
// IMPORTANT (capture correctness): Claude's Playwright screenshot step must
// call page.locator("#capture-canvas").screenshot() at native DOM pixel
// size — CardScaleShell's on-screen preview transform is irrelevant to (and
// must never be picked up by) the actual capture.

function humanDate(iso: string | null): string {
  if (!iso) return DASH;
  const dt = new Date(iso);
  if (Number.isNaN(dt.getTime())) return iso;
  return `${dt.toISOString().slice(0, 10)}`;
}

function Row({ archetype, record }: { archetype: ArchetypeKey; record: ArchetypeStockRecord }) {
  const card = record.archetypes[archetype];
  const color = archetypeScoreColor(card.score);
  const accent = ARCHETYPE_COLORS[archetype];
  const bullet = card.likes[0] ?? card.concerns[0] ?? null;
  return (
    <div
      style={{
        display: "flex",
        alignItems: "center",
        gap: 20,
        borderRadius: 8,
        border: "1px solid #1f2937",
        padding: "18px 20px",
      }}
    >
      <div
        style={{
          width: 84,
          height: 84,
          borderRadius: "50%",
          border: `4px solid ${color}`,
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          flexShrink: 0,
          fontSize: 30,
          fontWeight: 700,
          color,
        }}
      >
        {card.score != null ? Math.round(card.score) : DASH}
      </div>
      <div style={{ display: "flex", flexDirection: "column", gap: 4, minWidth: 0, flex: 1 }}>
        <div style={{ display: "flex", alignItems: "baseline", gap: 10 }}>
          <span style={{ fontSize: 24, fontWeight: 700, color: accent, letterSpacing: 0.5 }}>
            {ARCHETYPE_LABELS[archetype].toUpperCase()}
          </span>
          <span style={{ fontSize: 15, color: "#9ca3af" }}>
            {ARCHETYPE_SUBTITLES[archetype]}
          </span>
        </div>
        <span style={{ fontSize: 18, fontWeight: 600, color }}>
          {archetypeVerdictLabel(card.verdict)}
        </span>
        {bullet && (
          <span
            style={{
              fontSize: 14,
              color: "#9ca3af",
              lineHeight: 1.35,
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              overflow: "hidden",
            }}
          >
            {bullet}
          </span>
        )}
      </div>
    </div>
  );
}

export default function ArchetypeCaptureCard({
  record,
  generatedAt,
}: {
  record: ArchetypeStockRecord;
  generatedAt?: string | null;
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
            ● INVESTOR ARCHETYPE SCORECARD
          </span>
        </div>

        {/* Headline */}
        <div style={{ marginTop: 28, display: "flex", alignItems: "baseline", gap: 16 }}>
          <span style={{ fontSize: 64, fontWeight: 700, lineHeight: 1.05 }}>
            {record.symbol}
          </span>
          <span style={{ fontSize: 20, color: "#9ca3af" }}>{layerLabel(record.layer)}</span>
        </div>

        {/* Three scorecard rows */}
        <div style={{ marginTop: 32, display: "flex", flexDirection: "column", gap: 16 }}>
          {ARCHETYPE_ORDER.map((key) => (
            <Row key={key} archetype={key} record={record} />
          ))}
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
            Generated {generatedAt ? humanDate(generatedAt) : humanDate(record.as_of)} ·
            data as of {humanDate(record.as_of)} · Rule-based, zero-LLM checklist ·
            archetypes-v1
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
