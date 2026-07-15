"use client";

import { useEffect, useRef, useState } from "react";
import Script from "next/script";
import type { CapitalWeb, ResiliencyNode, Chokepoint } from "@/lib/data";
import { LAYER_COLORS, healthColor } from "@/lib/format";
import { categoryColor, categoryLabel } from "@/lib/chokepoints";
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
  chokepoints,
  chokepointMode = false,
  activeChokepointId = null,
  onSelectChokepoint,
}: {
  web: CapitalWeb;
  resiliency?: ResiliencyNode[];
  colorMode?: ColorMode;
  selectedId?: string | null;
  onSelect?: (id: string | null) => void;
  stress?: StressOverlay;
  // Chokepoint layer (Round 6) — all optional so every existing caller
  // (none of which pass these props yet) is unaffected.
  chokepoints?: Chokepoint[];
  chokepointMode?: boolean;
  activeChokepointId?: string | null;
  onSelectChokepoint?: (id: string | null) => void;
}) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [ready, setReady] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const networkRef = useRef<any>(null);
  // Keep the nodes/edges DataSets around so overlays can recolor/dim live
  // without rebuilding the whole network.
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const nodesDsRef = useRef<any>(null);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const edgesDsRef = useRef<any>(null);
  // Remember each edge's base (unstressed) color so we can restore it when the
  // overlay is turned off.
  const baseEdgeColorRef = useRef<Record<number, { color: string; opacity: number }>>(
    {},
  );
  // node id -> chokepoints touching it (severity-sorted, highest first),
  // recomputed whenever the build effect runs; read by the focus effect
  // below without forcing a network rebuild.
  const nodeChokepointsRef = useRef<Map<string, Chokepoint[]>>(new Map());
  // node id -> its base (unfocused) ring width, so the chokepoint-focus
  // effect can bump it (glow) and restore it exactly without rebuilding.
  const baseNodeRingRef = useRef<
    Record<string, { borderWidth: number; borderWidthSelected: number }>
  >({});
  // Keep the latest onSelect/onSelectChokepoint in refs so the click handler
  // stays stable without forcing a network rebuild whenever the parent
  // re-renders.
  const onSelectRef = useRef(onSelect);
  onSelectRef.current = onSelect;
  const onSelectChokepointRef = useRef(onSelectChokepoint);
  useEffect(() => {
    onSelectChokepointRef.current = onSelectChokepoint;
  }, [onSelectChokepoint]);

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

    // Join chokepoint membership onto the graph nodes by id (node_ids ->
    // node). Only built when the overlay is on so ungated rendering paths
    // pay zero cost. Severity-sorted (highest first) per node so the
    // dominant/primary chokepoint drives the ring color when a node belongs
    // to more than one.
    const chokepointsByNode = new Map<string, Chokepoint[]>();
    if (chokepointMode && chokepoints) {
      for (const cp of chokepoints) {
        for (const nid of cp.node_ids) {
          const arr = chokepointsByNode.get(nid) ?? [];
          arr.push(cp);
          chokepointsByNode.set(nid, arr);
        }
      }
      for (const arr of chokepointsByNode.values()) {
        arr.sort((a, b) => b.severity_score - a.severity_score);
      }
    }
    nodeChokepointsRef.current = chokepointsByNode;

    const ringMap: Record<string, { borderWidth: number; borderWidthSelected: number }> = {};

    const nodes = web.nodes.map((n) => {
      const d = degree[n.id] ?? 0;
      const res = resById.get(n.id);
      const isArticulation = !!res?.is_articulation;
      const memberCps = chokepointsByNode.get(n.id) ?? [];
      const isChokepointMember = memberCps.length > 0;
      const topCp = memberCps[0];

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
        (isChokepointMember ? "⛓ " : "") +
          (isArticulation ? "⚠ SPOF · " : "") +
          (n.name || n.id),
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
      for (const cp of memberCps) {
        titleParts.push(
          `⛓ Chokepoint: ${cp.name} (${categoryLabel(cp.category)}) · severity ${cp.severity_score}/100`,
        );
      }

      // Ring: articulation-point (SPOF, red) and chokepoint-membership
      // (category color) rings share the same visual channel. When both
      // apply, the width is BUMPED to the max of the two, never additive —
      // and the chokepoint category color wins the border hue so the newer
      // overlay stays legible; the SPOF fact is preserved via the "⚠ SPOF"
      // label/tooltip text either way.
      const ringWidth = isArticulation || isChokepointMember ? 4 : 1;
      const ringWidthSelected = isArticulation || isChokepointMember ? 5 : 2;
      const ringColor = isChokepointMember
        ? categoryColor(topCp.category)
        : isArticulation
          ? "#ef4444"
          : color;
      ringMap[n.id] = { borderWidth: ringWidth, borderWidthSelected: ringWidthSelected };

      return {
        id: n.id,
        label:
          (isChokepointMember ? "⛓ " : "") +
          (isArticulation ? "⚠ " : "") +
          (n.name || n.id),
        value,
        shape: isPrivate ? "diamond" : "dot",
        borderWidth: ringWidth,
        borderWidthSelected: ringWidthSelected,
        opacity: 1,
        color: {
          background: color,
          border: ringColor,
          highlight: {
            background: color,
            border: isChokepointMember ? ringColor : "#ffffff",
          },
        },
        font: { color: "#e5e7eb", face: "JetBrains Mono, monospace", size: 12 },
        title: titleParts.filter(Boolean).join("\n"),
      };
    });
    baseNodeRingRef.current = ringMap;

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
    const nodesDs = new vis.DataSet(nodes);
    nodesDsRef.current = nodesDs;
    const data = {
      nodes: nodesDs,
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
    // In chokepoint-overlay mode, clicking a chokepoint-member node surfaces
    // that chokepoint (highest-severity one if it belongs to several)
    // instead of drilling into the company value-chain view — the overlay's
    // whole point is staying on the graph while exploring chokepoints.
    network.on("click", (params: { nodes: string[] }) => {
      const id = params.nodes && params.nodes.length ? params.nodes[0] : null;
      if (id && chokepointMode) {
        const members = nodeChokepointsRef.current.get(id);
        if (members && members.length > 0) {
          onSelectChokepointRef.current?.(members[0].id);
          return;
        }
      }
      onSelectRef.current?.(id);
    });

    return () => {
      network.destroy?.();
      networkRef.current = null;
      edgesDsRef.current = null;
      nodesDsRef.current = null;
    };
  }, [ready, web, resiliency, colorMode, chokepoints, chokepointMode]);

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

  // Chokepoint focus overlay: when a chokepoint is active (selected from the
  // side list, claims panel, or a canvas click), fit the view to its member
  // nodes, glow them (opacity 1 + bumped-not-additive ring width), and dim
  // every other node via the same rgba-alpha technique the stress overlay
  // uses on edges. Edges recolor to the chokepoint's category color UNLESS
  // the macro-stress overlay is simultaneously active — stress wins on
  // edges (one live edge-color overlay at a time); node rings/opacity are a
  // different channel and always reflect chokepoint focus regardless.
  useEffect(() => {
    const nodesDs = nodesDsRef.current;
    const edgesDs = edgesDsRef.current;
    const network = networkRef.current;
    if (!nodesDs || !edgesDs || !network) return;

    const cp =
      activeChokepointId && chokepoints
        ? chokepoints.find((c) => c.id === activeChokepointId)
        : undefined;
    const stressActive = !!stress && (stress.dRateBps !== 0 || stress.dElecPct !== 0);

    if (!cp) {
      // Restore full opacity + base ring width on every node.
      nodesDs.update(
        web.nodes.map((n) => {
          const base = baseNodeRingRef.current[n.id] ?? {
            borderWidth: 1,
            borderWidthSelected: 2,
          };
          return {
            id: n.id,
            opacity: 1,
            borderWidth: base.borderWidth,
            borderWidthSelected: base.borderWidthSelected,
          };
        }),
      );
      // Only restore edge color here if the stress effect isn't the one
      // currently driving it (its own effect owns restoration when active).
      if (!stressActive) {
        edgesDs.update(
          web.edges.map((_e, i) => ({
            id: i,
            color: {
              color: baseEdgeColorRef.current[i]?.color ?? "#475569",
              highlight: "#ffffff",
              opacity: baseEdgeColorRef.current[i]?.opacity ?? 0.85,
            },
          })),
        );
      }
      return;
    }

    const memberSet = new Set(cp.node_ids);
    nodesDs.update(
      web.nodes.map((n) => {
        const isMember = memberSet.has(n.id);
        const base = baseNodeRingRef.current[n.id] ?? {
          borderWidth: 1,
          borderWidthSelected: 2,
        };
        return {
          id: n.id,
          opacity: isMember ? 1 : 0.15,
          borderWidth: isMember ? Math.max(base.borderWidth, 6) : base.borderWidth,
          borderWidthSelected: isMember
            ? Math.max(base.borderWidthSelected, 7)
            : base.borderWidthSelected,
        };
      }),
    );

    if (!stressActive) {
      const color = categoryColor(cp.category);
      edgesDs.update(
        web.edges.map((e, i) => {
          const memberEdge = memberSet.has(e.src) || memberSet.has(e.dst);
          return {
            id: i,
            color: { color, highlight: "#ffffff", opacity: memberEdge ? 0.9 : 0.12 },
          };
        }),
      );
    }

    if (memberSet.size > 0) {
      try {
        network.fit({
          nodes: cp.node_ids,
          animation: { duration: 500, easingFunction: "easeInOutQuad" },
        });
      } catch {
        // member ids may not all exist in this filtered/sector view; ignore
      }
    }
  }, [activeChokepointId, chokepoints, stress, web, ready]);

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
        <GraphLegend
          colorMode={colorMode}
          chokepoints={chokepointMode ? chokepoints : undefined}
        />
      </div>
    </>
  );
}

function GraphLegend({
  colorMode,
  chokepoints,
}: {
  colorMode: ColorMode;
  chokepoints?: Chokepoint[];
}) {
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

  // Chokepoint category swatches — only the categories actually present in
  // the currently-loaded dataset, so the legend never lists a category with
  // zero entries.
  const chokepointCategories = chokepoints
    ? [...new Set(chokepoints.map((cp) => cp.category))]
    : [];

  return (
    <div className="absolute bottom-2 left-2 z-10 rounded-sm border border-term-border bg-[#0b0f17]/90 px-2.5 py-2 text-[10px] leading-relaxed max-w-[280px]">
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
      {chokepointCategories.length > 0 && (
        <div className="mt-1.5 pt-1.5 border-t border-term-border/60">
          <div className="text-term-muted mb-0.5">⛓ Chokepoint category</div>
          <div className="flex flex-wrap gap-x-3 gap-y-1">
            {chokepointCategories.map((c) => (
              <span key={c} className="flex items-center gap-1">
                <span
                  className="inline-block h-2 w-2 rounded-full"
                  style={{ backgroundColor: categoryColor(c) }}
                />
                {categoryLabel(c)}
              </span>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
