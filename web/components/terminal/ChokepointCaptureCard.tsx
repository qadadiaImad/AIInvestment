import type { Chokepoint } from "@/lib/data";
import {
  categoryColor,
  categoryLabel,
  severityBand,
  severityColor,
  headlineClaim,
} from "@/lib/data";
import { layerLabel } from "@/lib/format";

// Renders a 1080x1350 (4:5) branded chokepoint capture-card slide for social
// posting. Same construction discipline as RiskCaptureCard.tsx: all-px
// sizing, #capture-canvas id, data-capture-ready="true", no client JS, no
// SVG.
//
// FACT-ONLY HEADLINE RULE (CLAUDE.md rule #5 — never launder a rumor into a
// fact): the headline quote uses headlineClaim(cp), which structurally
// cannot return a rumored claim. Three render paths:
//   1. headlineClaim() is a FACT claim  -> FACT-badged quote.
//   2. headlineClaim() is a REPORTED claim -> REPORTED-badged quote + a
//      "no fact-class source yet" caption.
//   3. headlineClaim() returns null (only rumored claims exist) -> falls
//      back to `summary` with NO class badge at all — never fabricates
//      confidence it doesn't have. Structurally unreachable for the current
//      13-entry dataset (every entry has >=1 non-rumored claim) but the
//      code path must exist per the design spec.
//
// IMPORTANT (capture correctness): Claude's Playwright screenshot step must
// call page.locator("#capture-canvas").screenshot() at native DOM pixel
// size — CardScaleShell's on-screen preview transform is irrelevant to (and
// must never be picked up by) the actual capture.

const MITIGATION_CAP = 2;

function humanDate(iso: string): string {
  if (!iso) return iso;
  // last_reviewed is a plain YYYY-MM-DD date, not a timestamp — render as-is.
  return iso;
}

export default function ChokepointCaptureCard({ cp }: { cp: Chokepoint }) {
  const color = categoryColor(cp.category);
  const headline = headlineClaim(cp);

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
              display: "inline-block",
              width: "fit-content",
              fontSize: 16,
              fontWeight: 700,
              letterSpacing: 2,
              textTransform: "uppercase",
              color,
              border: `1px solid ${color}`,
              backgroundColor: `${color}1a`,
              padding: "4px 10px",
              borderRadius: 3,
            }}
          >
            ⛓ {categoryLabel(cp.category)}
          </span>
        </div>

        {/* Headline block */}
        <div style={{ marginTop: 28, display: "flex", flexDirection: "column", gap: 6 }}>
          <span style={{ fontSize: 52, fontWeight: 700, lineHeight: 1.08 }}>
            {cp.card_tagline}
          </span>
          <span style={{ fontSize: 22, fontWeight: 600, color: "#9ca3af" }}>{cp.name}</span>
        </div>

        {/* Headline claim (fact-only rule — see file header) */}
        <div
          style={{
            marginTop: 28,
            padding: 20,
            borderRadius: 4,
            border: `1px solid ${headline ? (headline.class === "fact" ? "#0ea5e9" : "#10b981") : "#3f3f46"}`,
            backgroundColor: headline
              ? headline.class === "fact"
                ? "rgba(14,165,233,0.08)"
                : "rgba(16,185,129,0.08)"
              : "rgba(63,63,70,0.15)",
            display: "flex",
            flexDirection: "column",
            gap: 8,
          }}
        >
          {headline ? (
            <>
              <span
                style={{
                  fontSize: 15,
                  fontWeight: 700,
                  letterSpacing: 1.5,
                  textTransform: "uppercase",
                  color: headline.class === "fact" ? "#7dd3fc" : "#6ee7b7",
                }}
              >
                {headline.class === "fact" ? "FACT" : "REPORTED"}
              </span>
              <span style={{ fontSize: 21, lineHeight: 1.45, color: "#e5e7eb" }}>
                &ldquo;{headline.text}&rdquo;
              </span>
              <span style={{ fontSize: 15, color: "#9ca3af" }}>— {headline.source_name}</span>
              {headline.class !== "fact" && (
                <span style={{ fontSize: 14, color: "#71717a", fontStyle: "italic" }}>
                  No fact-class (primary/regulatory) source available yet for this
                  chokepoint — treat as credible-but-secondary.
                </span>
              )}
            </>
          ) : (
            <span style={{ fontSize: 21, lineHeight: 1.45, color: "#e5e7eb" }}>{cp.summary}</span>
          )}
        </div>

        {/* ticker strip */}
        {cp.tickers.length > 0 && (
          <div style={{ marginTop: 20, display: "flex", flexWrap: "wrap", gap: 8 }}>
            {cp.tickers.slice(0, 8).map((t) => (
              <span
                key={t}
                style={{
                  fontSize: 15,
                  fontWeight: 600,
                  padding: "3px 9px",
                  borderRadius: 3,
                  backgroundColor: "#18181b",
                  color: "#d4d4d8",
                }}
              >
                {t}
              </span>
            ))}
          </div>
        )}

        <div style={{ marginTop: 28, height: 1, backgroundColor: "#1f2937" }} />

        {/* 3-stat block */}
        <div style={{ marginTop: 28, display: "flex", flexDirection: "column", gap: 20 }}>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span
              style={{
                fontSize: 16,
                color: "#9ca3af",
                textTransform: "uppercase",
                letterSpacing: 1,
              }}
            >
              Severity
            </span>
            <span
              style={{
                fontSize: 36,
                fontWeight: 700,
                fontVariantNumeric: "tabular-nums",
                color: severityColor(cp.severity_score),
              }}
            >
              {cp.severity_score}/100 · {severityBand(cp.severity_score)}
            </span>
          </div>
          <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
            <span
              style={{
                fontSize: 16,
                color: "#9ca3af",
                textTransform: "uppercase",
                letterSpacing: 1,
              }}
            >
              Affected layers
            </span>
            <span style={{ display: "flex", flexWrap: "wrap", gap: 8, marginTop: 2 }}>
              {cp.layers.map((l) => (
                <span
                  key={l}
                  style={{
                    fontSize: 18,
                    fontWeight: 700,
                    padding: "3px 10px",
                    borderRadius: 3,
                    backgroundColor: "#18181b",
                    color: "#e5e7eb",
                  }}
                >
                  {layerLabel(l)}
                </span>
              ))}
            </span>
          </div>
          {cp.mitigation_watch.length > 0 && (
            <div style={{ display: "flex", flexDirection: "column", gap: 4 }}>
              <span
                style={{
                  fontSize: 16,
                  color: "#9ca3af",
                  textTransform: "uppercase",
                  letterSpacing: 1,
                }}
              >
                Mitigation watch
              </span>
              <span style={{ fontSize: 19, lineHeight: 1.5, color: "#d4d4d8" }}>
                {cp.mitigation_watch.slice(0, MITIGATION_CAP).join(" · ")}
              </span>
            </div>
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
            Generated {humanDate(cp.last_reviewed)} · chokepoint-board-v1
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
