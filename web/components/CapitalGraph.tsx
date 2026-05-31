"use client";

import { useEffect, useRef, useState } from "react";
import Script from "next/script";
import type { CapitalWeb, ResiliencyNode } from "@/lib/data";
import { LAYER_COLORS, healthColor } from "@/lib/format";
import {
  buildLayerMap,
  scoreEdge,
  stressColor,
  type StressInputs,
} from "@/lib/stress";

export interface StressOverlay {
  dRateBps: number;
  dElecPct: number;
  dffBase: number;
}

// vis-network is loaded from CDN onto window.vis
declare global {
  interface Window {
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    vis?: any;
  }
}

export type ColorMode = "layer" | "health";

function nodeColor(layer?: string): string {
  if (layer && LAYER_COLORS[layer]) return LAYER_COLORS[layer];
  return "#9ca3af";
}

export default function CapitalGraph({
  web,
  resiliency,
  colorMode = "layer",
  selectedId,
  onSelect,
  stress,
}: {
  web: CapitalWeb;
  resiliency?: ResiliencyNode[];
  colorMode?: ColorMode;
  selectedId?: string | null;
  onSelect?: (id: string | null) => void;
  stress?: StressOverlay;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const networkRef = useRef<any>(null);
  // Keep the edges DataSet around so the stress overlay can recolor edges live
  // without rebuilding the whole network.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const edgesDsRef = useRef<any>(null);
  // Remember each edge's base (unstressed) color so we can restore it when the
  // overlay is turned off.
  const baseEdgeColorRef = useRef<Record<number, { color: string; opacity: number }>>(
    {},
  );
  // Keep the latest onSelect in a ref so the click handler stays stable
  // without forcing a network rebuild whenever the parent re-renders.
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;

  useEffect(() => {
    if (!ready || !containerRef.current || !window.vis) return;
    const vis = window.vis;

    // degree for fallback sizing
    const degree: Record<string, number> = {};
    for (const e of web.edges) {
      degree[e.src] = (degree[e.src] ?? 0) + 1;
      degree[e.dst] = (degree[e.dst] ?? 0) + 1;
    }

    // Join resiliency analysis onto the graph nodes by id.
    const resById = new Map<string, ResiliencyNode>(
      (resiliency ?? []).map((r) => [r.id, r]),
    );

    const nodes = web.nodes.map((n) => {
      const d = degree[n.id] ?? 0;
      const res = resById.get(n.id);
      const isArticulation = !!res?.is_articulation;

      // Color: by layer or by health, per the toggle.
      const color =
        colorMode === "health"
          ? healthColor(res ? res.health : null)
          : nodeColor(n.layer);

      const isPrivate = n.type !== "public";

      // Size scales by pagerank when available so hubs (TSM/NVDA) read large;
      // fall back to degree otherwise.
      const value =
        res && typeof res.pagerank === "number"
          ? 1 + res.pagerank * 600
          : d + 1;

      const titleParts: (string | null)[] = [
        (isArticulation ? "⚠ SPOF · " : "") + (n.name || n.id),
        n.ticker ? `Ticker: ${n.ticker}` : null,
        n.layer ? `Layer: ${n.layer}` : null,
        `Type: ${n.type}`,
        `Connections: ${d}`,
      ];
      if (res) {
        titleParts.push(
          res.health != null
            ? `Health: ${res.health.toFixed(0)}/100`
            : "Health: no data",
        );
        if (isArticulation) titleParts.push("Single point of failure (SPOF)");
      }
      if (n.note) titleParts.push(`Note: ${n.note}`);

      return {
        id: n.id,
        label: (isArticulation ? "⚠ " : "") + (n.name || n.id),
        value,
        shape: isPrivate ? "diamond" : "dot",
        // Articulation points get a thick distinct red ring in BOTH modes.
        borderWidth: isArticulation ? 4 : 1,
        borderWidthSelected: isArticulation ? 5 : 2,
        color: {
          background: color,
          border: isArticulation ? "#ef4444" : color,
          highlight: {
            background: color,
            border: isArticulation ? "#ef4444" : "#ffffff",
          },
        },
        font: { color: "#e5e7eb", face: "JetBrains Mono, monospace", size: 12 },
        title: titleParts.filter(Boolean).join("\n"),
      };
    });

    const edges = web.edges.map((e, i) => {
      const aiExtracted = e.origin === "ai-extracted";
      const rumored = e.certainty === "rumored";
      const dashes = aiExtracted || rumored;
      const color = aiExtracted ? "#a78bfa" : "#475569";
      const opacity = aiExtracted ? 0.6 : 0.85;
      baseEdgeColorRef.current[i] = { color, opacity };
      const parts: string[] = [];
      parts.push(`${e.src} → ${e.dst}`);
      parts.push(`Type: ${e.type}`);
      if (e.certainty) parts.push(`Certainty: ${e.certainty}`);
      if (e.origin) parts.push(`Origin: ${e.origin}`);
      if (typeof e.attrs?.usd === "number")
        parts.push(`USD: ${e.attrs.usd.toLocaleString()}`);
      if (typeof e.attrs?.pct === "number") parts.push(`Stake: ${e.attrs.pct}%`);
      if (e.source_url) parts.push(`Source: ${e.source_url}`);
      if (e.quote) parts.push(`"${e.quote}"`);
      return {
        id: i,
        from: e.src,
        to: e.dst,
        arrows: "to",
        dashes,
        width: aiExtracted ? 1 : 1.4,
        color: { color, highlight: "#ffffff", opacity },
        smooth: { enabled: true, type: "continuous", roundness: 0.2 },
        title: parts.join("\n"),
      };
    });

    const edgesDs = new vis.DataSet(edges);
    edgesDsRef.current = edgesDs;
    const data = {
      nodes: new vis.DataSet(nodes),
      edges: edgesDs,
    };

    const options = {
      autoResize: true,
      nodes: {
        scaling: { min: 6, max: 34, label: { enabled: true, min: 10, max: 18 } },
        borderWidth: 1,
      },
      edges: { selectionWidth: 2 },
      physics: {
        enabled: true,
        solver: "forceAtlas2Based",
        forceAtlas2Based: {
          gravitationalConstant: -60,
          centralGravity: 0.008,
          springLength: 130,
          springConstant: 0.06,
          damping: 0.5,
          avoidOverlap: 0.4,
        },
        stabilization: { enabled: true, iterations: 250, fit: true },
      },
      interaction: {
        hover: true,
        tooltipDelay: 80,
        navigationButtons: false,
        keyboard: false,
      },
    };

    const network = new vis.Network(containerRef.current, data, options);
    networkRef.current = network;

    // Clicking a node selects it; clicking empty canvas clears selection.
    network.on("click", (params: { nodes: string[] }) => {
      const id = params.nodes && params.nodes.length ? params.nodes[0] : null;
      onSelectRef.current?.(id);
    });

    return () => {
      network.destroy?.();
      networkRef.current = null;
      edgesDsRef.current = null;
    };
  }, [ready, web, resiliency, colorMode]);

  // Stress overlay: recolor edges live via the DataSet on slider change, without
  // rebuilding the network. When the shock is 0/0 (or no overlay), restore each
  // edge's base styling so the existing layer/health view is unchanged.
  useEffect(() => {
    const ds = edgesDsRef.current;
    if (!ds) return;
    const active = !!stress && (stress.dRateBps !== 0 || stress.dElecPct !== 0);

    if (!active) {
      const updates = web.edges.map((_e, i) => ({
        id: i,
        color: {
          color: baseEdgeColorRef.current[i]?.color ?? "#475569",
          highlight: "#ffffff",
          opacity: baseEdgeColorRef.current[i]?.opacity ?? 0.85,
        },
      }));
      ds.update(updates);
      return;
    }

    const inp: StressInputs = {
      dRateBps: stress!.dRateBps,
      dElecPct: stress!.dElecPct,
      dffBase: stress!.dffBase,
      layerById: buildLayerMap(web.nodes),
    };
    const updates = web.edges.map((e, i) => {
      const s = scoreEdge(e, inp);
      return {
        id: i,
        color: { color: stressColor(s), highlight: "#ffffff", opacity: 0.95 },
      };
    });
    ds.update(updates);
  }, [stress, web, ready]);

  // React to external selection (dropdown or click): focus + highlight.
  useEffect(() => {
    const network = networkRef.current;
    if (!network) return;
    if (selectedId) {
      try {
        network.selectNodes([selectedId], true);
        network.focus(selectedId, {
          scale: 1.1,
          animation: { duration: 500, easingFunction: "easeInOutQuad" },
        });
      } catch {
        // node may not exist yet; ignore
      }
    } else {
      network.unselectAll?.();
    }
  }, [selectedId, ready]);

  return (
    <>
      <Script
        src="https://unpkg.com/vis-network/standalone/umd/vis-network.min.js"
        strategy="afterInteractive"
        onLoad={() => setReady(true)}
      />
      <div className="relative h-full w-full">
        <div ref={containerRef} className="h-full w-full" />
        {!ready && (
          <div className="absolute inset-0 grid place-items-center text-term-muted text-xs">
            loading relationship graph…
          </div>
        )}
        <GraphLegend colorMode={colorMode} />
      </div>
    </>
  );
}

function GraphLegend({ colorMode }: { colorMode: ColorMode }) {
  const layerItems: { label: string; color: string }[] = [
    { label: "Energy", color: LAYER_COLORS["L0-energy"] },
    { label: "Chips", color: LAYER_COLORS["L1-chips"] },
    { label: "Infra", color: LAYER_COLORS["L2-infra"] },
    { label: "Models", color: LAYER_COLORS["L3-models"] },
    { label: "Apps", color: LAYER_COLORS["L4-application"] },
    { label: "Private lab", color: LAYER_COLORS["private-lab"] },
  ];
  const healthItems: { label: string; color: string }[] = [
    { label: "Resilient >70", color: "#10b981" },
    { label: "Fragile 50-70", color: "#f59e0b" },
    { label: "Critical <50", color: "#ef4444" },
    { label: "No data", color: "#6b7280" },
  ];
  const items = colorMode === "health" ? healthItems : layerItems;
  return (
    <div className="absolute bottom-2 left-2 z-10 rounded-sm border border-term-border bg-[#0b0f17]/90 px-2.5 py-2 text-[10px] leading-relaxed">
      <div className="flex flex-wrap gap-x-3 gap-y-1 max-w-[260px]">
        {items.map((it) => (
          <span key={it.label} className="flex items-center gap-1">
            <span
              className="inline-block h-2 w-2 rounded-full"
              style={{ backgroundColor: it.color }}
            />
            {it.label}
          </span>
        ))}
      </div>
      <div className="mt-1 text-term-muted">
        ◇ private · — reported · - - rumored/AI-extracted ·{" "}
        <span className="text-rose-400">⚠ red ring = SPOF</span>
      </div>
    </div>
  );
}
